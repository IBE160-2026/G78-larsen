"""Test harness: a fresh PostgreSQL database, the real API in a real backend process, real HTTP.

The session fixture first runs `docker compose up -d --wait db`, recreates `booking_test`, migrates it, applies
the mutation (if any) and starts the backend with `uv run booking-platform serve` on its own port, with its own
base URL and test switch file. Nothing here mocks the API, the pool or the database (FR-11: "not a mock").
"""

from __future__ import annotations

import datetime as dt
import os
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
import psycopg
import pytest
from psycopg.conninfo import make_conninfo

import client
from booking_platform import config
from booking_platform.db import migrate as migrations
from client import admin_client, api_client

ROOT = Path(__file__).resolve().parents[1]
TEST_DB = "booking_test"
# The harness derives its admin URL from BP_DATABASE_URL (AD-22) by swapping the database for `postgres`.
_DB_URL = config.load_settings().database_url
ADMIN_URL = make_conninfo(_DB_URL, dbname="postgres")
TEST_URL = make_conninfo(_DB_URL, dbname=TEST_DB)
client.DATABASE_URL = TEST_URL

# Window k starts at WIN0 + k * 90 minutes (UTC); the Venue is Europe/Oslo (UTC+1 in December).
WIN0 = dt.datetime(2026, 12, 1, 9, 0, tzinfo=dt.timezone.utc)
SAUNAS = [(1, "Rauha", 7), (2, "Loyly", 10), (3, "Kajo", 12), (4, "Lumo", 15)]  # 44 Seats in Fill order 1..4
EARLY = dt.datetime(2026, 12, 1, 3, 0, tzinfo=dt.timezone.utc)  # before the 06:00 Oslo (05:00Z) Release time


def win_start(k: int) -> dt.datetime:
    return WIN0 + k * dt.timedelta(minutes=90)


# Mutation check: BP_TEST_MUTATE=<name> switches ONE protection of the store off, to prove the tests bite.
_NOLOCK = """
DROP TRIGGER a_lock_bookings ON bookings; DROP TRIGGER a_lock_whole ON whole_bookings; DROP TRIGGER a_lock_marks ON marks;
DROP TRIGGER a_lock_holds ON holds; DROP TRIGGER a_lock_blocks ON blocks;
CREATE OR REPLACE FUNCTION lock_windows(ids int[]) RETURNS void LANGUAGE sql AS 'SELECT 1';
"""
_NOLOCK_RECOMPUTE = """
CREATE OR REPLACE FUNCTION recompute_window(wid int) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  UPDATE windows SET seat_capacity = window_open_capacity(wid), booked = window_booked_seats(wid),
                     held = window_held_seats(wid) WHERE id = wid;
END $$;
"""
MUTATIONS = {
    "nocheck": "ALTER TABLE windows DROP CONSTRAINT booked_within_capacity",
    "noverify": "DROP TRIGGER t_verify ON windows",
    "nolock": _NOLOCK + _NOLOCK_RECOMPUTE,
    "nolock+noverify": _NOLOCK + _NOLOCK_RECOMPUTE + "DROP TRIGGER t_verify ON windows",
    "nohold": "ALTER TABLE windows DROP CONSTRAINT booked_within_capacity; "
              "ALTER TABLE windows ADD CONSTRAINT booked_within_capacity CHECK (booked >= 0 AND booked <= seat_capacity)",
    "nofresh": "CREATE OR REPLACE FUNCTION window_held_seats(wid int) RETURNS int LANGUAGE sql VOLATILE AS "
               "$$ SELECT COALESCE(SUM(seats), 0)::int FROM holds WHERE window_id = wid $$",
    "notriggers": "DROP TRIGGER t_bookings ON bookings",
}


def mutate(url: str) -> None:
    name = os.environ.get("BP_TEST_MUTATE")
    if name:
        with psycopg.connect(url) as c:
            c.execute(MUTATIONS[name])


def _compose_db() -> None:
    try:
        r = subprocess.run(["docker", "compose", "up", "-d", "--wait", "db"], cwd=ROOT, capture_output=True,
                           text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as e:
        pytest.exit(f"docker compose up -d --wait db failed: {e}", 2)
    if r.returncode != 0:
        pytest.exit(f"docker compose up -d --wait db failed: {r.stderr.strip()[-500:]}", 2)


@pytest.fixture(scope="session")
def database():
    _compose_db()
    try:
        admin = psycopg.connect(ADMIN_URL, autocommit=True, connect_timeout=5)
    except psycopg.OperationalError as e:
        pytest.exit(f"The PostgreSQL container is not reachable ({e}). Start it with: docker compose up -d db", 2)
    admin.execute(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)")
    admin.execute(f"CREATE DATABASE {TEST_DB}")
    admin.close()
    assert migrations.migrate(TEST_URL)  # every migration is applied to the fresh database
    mutate(TEST_URL)
    yield TEST_URL


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@dataclass
class Backend:
    proc: subprocess.Popen
    base: str
    log: Path

    def stop(self) -> None:
        if self.proc.poll() is None and os.name == "nt":
            # `uv run` starts the backend as a child process; on Windows, terminating uv alone leaves it running
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(self.proc.pid)], capture_output=True)
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=15)

    def output(self) -> str:
        return self.log.read_text(encoding="utf-8", errors="replace")


def root_without_sample_bookings(workdir: Path) -> Path:
    """A `BP_ROOT` like the repository's, without `seeds/bookings.json`: for a second backend started on a `world` that
    a test counts Bookings in (the sample Bookings would land in the Windows it generates)."""
    root = workdir / "root-no-sample-bookings"
    if not root.exists():
        shutil.copytree(config.paths.MIGRATIONS, root / "migrations")
        shutil.copytree(config.paths.CONTENT, root / "content")
        (root / "seeds").mkdir()
        shutil.copy(config.paths.SEEDS / "venue.json", root / "seeds" / "venue.json")
        (root / "config").mkdir()
    return root


def start_backend(database_url: str, workdir: Path, *, switches: str = "", name: str = "backend",
                  wait: bool = True, env: dict[str, str] | None = None, sample_bookings: bool = True) -> Backend:
    """Start `uv run booking-platform serve` on a free port with its own base URL and switch file; its output
    goes to a log file in `workdir`. With `sample_bookings=False` it runs without `seeds/bookings.json`."""
    workdir.mkdir(parents=True, exist_ok=True)
    if not sample_bookings:
        env = {"BP_ROOT": str(root_without_sample_bookings(workdir)), **(env or {})}
    port = free_port()
    switch_file = workdir / f"{name}-switches.toml"
    switch_file.write_text(switches, encoding="utf-8")
    log = workdir / f"{name}.log"
    base = f"http://127.0.0.1:{port}"
    full_env = {**os.environ, "BP_DATABASE_URL": database_url, "BP_HOST": "127.0.0.1", "BP_PORT": str(port),
                "BP_BASE_URL": base, "BP_TEST_SWITCHES": str(switch_file), "BP_HTTPS": "off", **(env or {})}
    with open(log, "wb") as out:
        proc = subprocess.Popen(["uv", "run", "booking-platform", "serve"], cwd=ROOT, env=full_env,
                                stdout=out, stderr=subprocess.STDOUT)
    backend = Backend(proc, base, log)
    if not wait:
        return backend
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"the backend exited with {proc.returncode}: {backend.output()[-2000:]}")
        try:
            if httpx.get(base + "/api/health", timeout=1).status_code == 200:
                return backend
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    backend.stop()
    raise RuntimeError("the backend did not start: " + backend.output()[-2000:])


@pytest.fixture(scope="session")
def backend(database, tmp_path_factory):
    try:
        b = start_backend(database, tmp_path_factory.mktemp("backend"))
    except RuntimeError as e:
        pytest.exit(str(e), 2)
    yield b
    b.stop()


@pytest.fixture(scope="session")
def server(backend):
    return backend.base


def set_clock(c: psycopg.Connection, ts: dt.datetime) -> None:
    c.execute("UPDATE clock SET off = %s - clock_timestamp()", (ts,))
    c.commit()


@pytest.fixture
def pg(database):
    """A raw connection that goes around the application."""
    with psycopg.connect(database) as c:
        yield c


@pytest.fixture
def world(pg, server):
    """Fresh data: four Saunas (44 Seats), three back-to-back Windows, default Settings, the clock at EARLY.

    The three Windows sit on the seed schedule's 10:00, 11:30 and 13:00 Oslo slots of 2026-12-01. No Window has been
    generated yet (`windows_generated_through` is NULL); the first Window listing generates the rest of the horizon
    and skips these three, which overlap."""
    pg.execute("TRUNCATE releases, marks, holds, blocks, whole_bookings, idempotency_keys, payments, outbox_emails, "
               "bookings, windows, saunas, sessions RESTART IDENTITY CASCADE")
    pg.execute("UPDATE settings SET release_on = true, release_time = '06:00', booking_deadline_minutes = 5, "
               "booking_horizon_days = 28, windows_generated_through = NULL")
    for i, n, cap in SAUNAS:
        pg.execute("INSERT INTO saunas (id, name, capacity, fill_order) VALUES (%s, %s, %s, %s)", (i, n, cap, i))
    for k in range(3):
        pg.execute("INSERT INTO windows (during) VALUES (tstzrange(%s, %s, '[)'))", (win_start(k), win_start(k + 1)))
    pg.commit()
    set_clock(pg, EARLY)
    return server


@pytest.fixture
def api(world):
    """A Guest client with its own session."""
    with api_client(world) as c:
        yield c


@pytest.fixture
def admin(world, pg):
    """A client with an Administrator session (inserted by the fixture until Story 2.1)."""
    with admin_client(world, pg) as c:
        yield c


def clear(pg: psycopg.Connection) -> None:
    """Remove all Bookings (with their keys, payments and emails), Holds, Whole-sauna bookings, Blocks and marks (row
    deletes, so the triggers run)."""
    for t in ("holds", "idempotency_keys", "payments", "outbox_emails", "bookings", "whole_bookings", "blocks",
              "marks"):
        pg.execute(f"DELETE FROM {t}")
    pg.commit()


# A Seat booking written straight to the store, around the API (AD-21), with every NOT NULL column of Story 1.5. `{w}`
# and `{s}` are SQL expressions or placeholders for the Window and the Seats; the reference is 8 random hex
# characters (hex is a subset of Crockford base32).
RAW_BOOKING = ("INSERT INTO bookings (window_id, seats, reference, name, email, price_per_seat_ore, total_ore) "
               "SELECT v.w, v.s, upper(substr(md5(random()::text || clock_timestamp()::text), 1, 8)), 'Raw Guest', "
               "'raw@example.com', 25000, v.s * 25000 FROM (VALUES ({w}, {s})) AS v(w, s)")


def raw_booking(window: object = "%s", seats: object = "%s") -> str:
    """The SQL of one raw Seat booking (see RAW_BOOKING)."""
    return RAW_BOOKING.format(w=window, s=seats)


def state(pg: psycopg.Connection, wid: int = 1) -> dict:
    """What the store thinks, read in one snapshot. `left` is derived from the rows."""
    pg.rollback()
    row = pg.execute(
        "SELECT seat_capacity, booked, held, window_booked_seats(id), window_open_capacity(id), "
        "window_held_seats(id), seats_left(id) FROM windows WHERE id = %s", (wid,)).fetchone()
    pg.rollback()
    return dict(cap=row[0], booked=row[1], held=row[2], real_booked=row[3], real_cap=row[4], real_held=row[5], left=row[6])
