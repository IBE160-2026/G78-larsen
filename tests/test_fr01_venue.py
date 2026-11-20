"""FR-1, AD-16, AD-18, NFR-10: the seed and the Venue facts, against a fresh database of their own.

The backend applies `seeds/venue.json` after the migrations at every start, writes only absent rows or NULL
seed-owned columns, and never overwrites a value the store holds. `GET /api/venue` needs no session, writes
nothing and sets no cookie. An invalid seed stops startup with one line that names the file and the field.

This module does not use `world` (it truncates the Saunas); it starts its own backends with `start_backend`.
"""

from __future__ import annotations

import json
import shutil
import time

import httpx
import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from booking_platform import config
from conftest import ADMIN_URL, TEST_URL, start_backend

SEED = json.loads((config.paths.SEEDS / "venue.json").read_text(encoding="utf-8"))

EXPECTED = {
    "name": "Saunalöyly",
    "address_lines": ["Badstubrygga 4", "0000 Havbukta"],
    "phone": "+47 01 23 45 67",
    "email": "hello@saunaloyly.example",
    "opening_time": "10:00",
    "closing_time": "22:00",
    "session_minutes": 90,
    "price_per_seat_ore": 25000,
    "saunas": [
        {"id": 1, "name": "Rauha", "capacity": 7},
        {"id": 2, "name": "Löyly", "capacity": 10},
        {"id": 3, "name": "Kajo", "capacity": 12},
        {"id": 4, "name": "Lumo", "capacity": 15},
    ],
}

SETTINGS = ("SELECT venue_name, address_lines, phone, email, opening_time, closing_time, session_minutes, "
            "price_per_seat_ore, release_on, release_time, booking_deadline_minutes, venue_tz FROM settings")


def _recreate(name: str) -> str:
    with psycopg.connect(ADMIN_URL, autocommit=True) as c:
        c.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))
        c.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    return make_conninfo(TEST_URL, dbname=name)


def _drop(name: str) -> None:
    with psycopg.connect(ADMIN_URL, autocommit=True) as c:
        c.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))


@pytest.fixture
def fresh_db(database):  # `database` only makes sure the PostgreSQL container is up
    name = "booking_test_venue"
    yield _recreate(name)
    _drop(name)


def snapshot(url: str) -> dict:
    with psycopg.connect(url) as c:
        return {
            "saunas": c.execute("SELECT id, name, capacity, fill_order, bookable_whole FROM saunas ORDER BY id")
                       .fetchall(),
            "settings": c.execute(SETTINGS).fetchall(),
            "sessions": c.execute("SELECT count(*) FROM sessions").fetchone()[0],
            "windows": c.execute("SELECT count(*) FROM windows").fetchone()[0],
        }


def test_the_seed_file_holds_the_venue_facts_of_the_story():
    """The seed is the source of the values; the migration's defaults are the same values (AD-18)."""
    venue = SEED["venue"]
    assert {k: venue[k] for k in venue} == {
        "name": EXPECTED["name"], "address_lines": EXPECTED["address_lines"], "phone": EXPECTED["phone"],
        "email": EXPECTED["email"], "opening_time": "10:00", "closing_time": "22:00", "session_minutes": 90,
        "price_per_seat_ore": 25000}
    assert [(s["id"], s["name"], s["capacity"], s["fill_order"]) for s in SEED["saunas"]] == [
        (1, "Rauha", 7, 1), (2, "Löyly", 10, 2), (3, "Kajo", 12, 3), (4, "Lumo", 15, 4)]


def test_the_migration_defaults_equal_the_seed(fresh_db):
    """On a freshly migrated database with no seed applied, the `settings` row's Venue values are 0004's column
    defaults, and they equal the `venue` block of `seeds/venue.json` (AD-18): the seed never writes them."""
    from booking_platform.db import migrate as migrations

    migrations.migrate(fresh_db)
    with psycopg.connect(fresh_db) as c:
        row = c.execute("SELECT venue_name, address_lines, phone, email, to_char(opening_time, 'HH24:MI'), "
                        "to_char(closing_time, 'HH24:MI'), session_minutes, price_per_seat_ore FROM settings"
                        ).fetchone()
    venue = SEED["venue"]
    assert row == (venue["name"], venue["address_lines"], venue["phone"], venue["email"], venue["opening_time"],
                   venue["closing_time"], venue["session_minutes"], venue["price_per_seat_ore"])


def test_fresh_start_restart_and_a_value_the_store_owns(fresh_db, tmp_path):
    # Fresh start: the four Saunas and every Venue fact are seeded. Without the sample Bookings (Story 1.5): a Sauna
    # is deleted below, and the store refuses that under Windows they fill (tests/test_dr5_seed_bookings.py has them).
    first = start_backend(fresh_db, tmp_path, name="venue-1", sample_bookings=False)
    try:
        r = httpx.get(first.base + "/api/venue", timeout=10)
        assert r.status_code == 200
        assert r.json() == EXPECTED
        assert "set-cookie" not in r.headers
    finally:
        first.stop()
    seeded = snapshot(fresh_db)
    assert [row[:4] for row in seeded["saunas"]] == [(1, "Rauha", 7, 1), (2, "Löyly", 10, 2), (3, "Kajo", 12, 3),
                                                    (4, "Lumo", 15, 4)]

    # Restart: the same rows, none duplicated or changed.
    second = start_backend(fresh_db, tmp_path, name="venue-2", sample_bookings=False)
    second.stop()
    assert snapshot(fresh_db) == seeded

    # The store owns a value: a changed price survives a restart, and a deleted Sauna is seeded again.
    with psycopg.connect(fresh_db) as c:
        c.execute("UPDATE settings SET price_per_seat_ore = 30000")
        c.execute("DELETE FROM saunas WHERE id = 4")
    third = start_backend(fresh_db, tmp_path, name="venue-3", sample_bookings=False)
    try:
        body = httpx.get(third.base + "/api/venue", timeout=10).json()
        assert body["price_per_seat_ore"] == 30000
        assert body["saunas"] == EXPECTED["saunas"]
    finally:
        third.stop()
    after = snapshot(fresh_db)
    assert after["saunas"] == seeded["saunas"]
    assert after["settings"][0][7] == 30000
    assert after["settings"][0][:7] == seeded["settings"][0][:7]


def test_venue_facts_need_no_session_set_no_cookie_and_write_nothing(server, database):
    before = snapshot(database)
    with httpx.Client(base_url=server, timeout=10) as c:
        r = c.get("/api/venue")
        assert r.status_code == 200
        assert "set-cookie" not in r.headers
        assert not c.cookies
    body = r.json()
    assert set(body) == set(EXPECTED)
    assert [set(s) for s in body["saunas"]] == [{"id", "name", "capacity"}] * len(body["saunas"])
    assert snapshot(database) == before


def _invalid_root(tmp_path, change) -> tuple:
    root = tmp_path / "root"
    shutil.copytree(config.paths.MIGRATIONS, root / "migrations")
    (root / "config").mkdir()
    (root / "seeds").mkdir()
    data = json.loads(json.dumps(SEED))
    change(data)
    (root / "seeds" / "venue.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return root


@pytest.mark.parametrize(("field", "change"), [
    ("saunas.0.capacity", lambda d: d["saunas"][0].update(capacity=-1)),
    ("venue.price_per_seat_ore", lambda d: d["venue"].update(price_per_seat_ore=-1)),
])
def test_an_invalid_seed_stops_startup_with_one_line_naming_file_and_field(fresh_db, tmp_path, field, change):
    root = _invalid_root(tmp_path, change)
    b = start_backend(fresh_db, tmp_path, name="invalid", wait=False, env={"BP_ROOT": str(root)})
    try:
        deadline = time.monotonic() + 90
        while b.proc.poll() is None and time.monotonic() < deadline:
            time.sleep(0.2)
        assert b.proc.returncode not in (None, 0), b.output()[-2000:]
        lines = [line for line in b.output().splitlines() if "venue.json" in line]
        assert len(lines) == 1, b.output()[-2000:]
        assert "seeds/venue.json" in lines[0] and field in lines[0], lines[0]
        assert "Traceback" not in b.output()
    finally:
        b.stop()
    with psycopg.connect(fresh_db) as c:  # stopped before anything was written
        assert c.execute("SELECT to_regclass('public.saunas')").fetchone()[0] is None
