"""Test harness: a fresh PostgreSQL database, the real API in a real uvicorn process, real HTTP.

Needs the data store running:  docker compose up -d db
Nothing here mocks the API, the pool or the database (FR-11: "not a mock").
"""

from __future__ import annotations

import datetime as dt
import os
import socket
import subprocess
import sys
import time

import httpx
import psycopg
import pytest

ADMIN_URL = os.environ.get("BP_TEST_ADMIN_URL", "postgresql://postgres:booking@localhost:55432/postgres")
TEST_DB = "booking_test"
TEST_URL = ADMIN_URL.rsplit("/", 1)[0] + "/" + TEST_DB

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


@pytest.fixture(scope="session")
def database():
    try:
        admin = psycopg.connect(ADMIN_URL, autocommit=True, connect_timeout=5)
    except psycopg.OperationalError as e:
        pytest.exit(f"The PostgreSQL container is not reachable ({e}). Start it with: docker compose up -d db", 2)
    admin.execute(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)")
    admin.execute(f"CREATE DATABASE {TEST_DB}")
    admin.close()
    from booking_platform import db

    assert db.migrate(TEST_URL) is True
    mutate(TEST_URL)
    yield TEST_URL


@pytest.fixture(scope="session")
def server(database):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    env = dict(os.environ, BP_DATABASE_URL=database)
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "booking_platform.app:app", "--port", str(port),
                             "--log-level", "warning"], env=env)
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            if httpx.get(base + "/health", timeout=1).status_code == 200:
                break
        except httpx.HTTPError:
            time.sleep(0.1)
    else:
        proc.kill()
        pytest.exit("the API did not start", 2)
    yield base
    proc.terminate()
    proc.wait(timeout=10)


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
    """Fresh data: four Saunas (44 Seats), three back-to-back Windows, default Settings, the clock at EARLY."""
    pg.execute("TRUNCATE releases, marks, holds, blocks, whole_bookings, bookings, windows, saunas RESTART IDENTITY CASCADE")
    pg.execute("UPDATE settings SET release_on = true, release_time = '06:00', booking_deadline_minutes = 5")
    for i, n, cap in SAUNAS:
        pg.execute("INSERT INTO saunas (id, name, capacity, fill_order) VALUES (%s, %s, %s, %s)", (i, n, cap, i))
    for k in range(3):
        pg.execute("INSERT INTO windows (during) VALUES (tstzrange(%s, %s, '[)'))", (win_start(k), win_start(k + 1)))
    pg.commit()
    set_clock(pg, EARLY)
    return server


@pytest.fixture
def api(world):
    with httpx.Client(base_url=world, timeout=30) as c:
        yield c


def clear(pg: psycopg.Connection) -> None:
    """Remove all Bookings, Holds, Whole-sauna bookings, Blocks and marks (row deletes, so the triggers run)."""
    for t in ("holds", "bookings", "whole_bookings", "blocks", "marks"):
        pg.execute(f"DELETE FROM {t}")
    pg.commit()


def state(pg: psycopg.Connection, wid: int = 1) -> dict:
    """What the store thinks, read in one snapshot. `left` is derived from the rows."""
    pg.rollback()
    row = pg.execute(
        "SELECT seat_capacity, booked, held, window_booked_seats(id), window_open_capacity(id), "
        "window_held_seats(id), seats_left(id) FROM windows WHERE id = %s", (wid,)).fetchone()
    pg.rollback()
    return dict(cap=row[0], booked=row[1], held=row[2], real_booked=row[3], real_cap=row[4], real_held=row[5], left=row[6])
