"""DR-5 / AD-18 / NFR-10: the sample Bookings of `seeds/bookings.json`, against a fresh database of their own.

At startup, after the Windows are generated, each sample Booking is created through `services.booking.create` under
one fixed seed session (it never expires) with its fixed idempotency key, as days after the Venue date of the run. A
restart, also on a later day, creates none twice. The list (Lisa, 2026-11-20): +1 day 14:30, 2 Seats; +2 days 17:30,
42 of 44; +3 days 19:00, full; +5 days 10:00, 4 Seats; nothing today. An invalid file stops startup with one line
naming the file and the field (IV-6).
"""

from __future__ import annotations

import json
import shutil
import time

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from booking_platform import config
from conftest import ADMIN_URL, TEST_URL, start_backend

SEED = json.loads((config.paths.SEEDS / "bookings.json").read_text(encoding="utf-8"))
DB = "booking_test_seed_bookings"

PER_WINDOW = """
SELECT venue_date(w.id) - venue_today(), to_char(lower(w.during) AT TIME ZONE 'Europe/Oslo', 'HH24:MI'),
       window_booked_seats(w.id), seats_left(w.id)
FROM windows w WHERE window_booked_seats(w.id) > 0 ORDER BY lower(w.during)"""


@pytest.fixture
def fresh_db():
    with psycopg.connect(ADMIN_URL, autocommit=True) as c:
        c.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(DB)))
        c.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB)))
    yield make_conninfo(TEST_URL, dbname=DB)
    with psycopg.connect(ADMIN_URL, autocommit=True) as c:
        c.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(DB)))


def snapshot(url: str) -> dict:
    with psycopg.connect(url) as c:
        return {
            "bookings": c.execute("SELECT reference, window_id, seats, name, email, total_ore, session_id, status "
                                  "FROM bookings ORDER BY id").fetchall(),
            "payments": c.execute("SELECT booking_id, direction, method, amount_ore FROM payments ORDER BY id").fetchall(),
            "emails": c.execute("SELECT booking_id, recipient, subject FROM outbox_emails ORDER BY id").fetchall(),
            "keys": c.execute("SELECT key::text, session_id, booking_id FROM idempotency_keys ORDER BY id").fetchall(),
            "sessions": c.execute("SELECT id, role, expires_at = 'infinity' FROM sessions ORDER BY id").fetchall(),
        }


def test_the_sample_bookings_exist_once_also_after_restarts_on_later_days(fresh_db, tmp_path):
    first = start_backend(fresh_db, tmp_path, name="seed-1")
    first.stop()
    with psycopg.connect(fresh_db) as c:
        per_window = c.execute(PER_WINDOW).fetchall()
    assert per_window == [(1, "14:30", 2, 42), (2, "17:30", 42, 2), (3, "19:00", 44, 0), (5, "10:00", 4, 40)]
    seeded = snapshot(fresh_db)
    entries = SEED["bookings"]
    assert len(seeded["bookings"]) == len(entries) == 12
    assert [(b[3], b[4], b[2]) for b in seeded["bookings"]] == [(e["name"], e["email"], e["seats"]) for e in entries]
    assert all(b[4].endswith("@example.com") for b in seeded["bookings"])
    # one fixed seed session that never expires, and every Booking paid by it, with its charge, email and key
    assert seeded["sessions"] == [(seeded["bookings"][0][6], "guest", True)]
    assert {b[6] for b in seeded["bookings"]} == {seeded["sessions"][0][0]}
    assert [p[1:] for p in seeded["payments"]] == [("charge", "card", b[5]) for b in seeded["bookings"]]
    assert [e[2] for e in seeded["emails"]] == [f"Booking confirmed: {b[0]}" for b in seeded["bookings"]]
    assert sorted(k[0] for k in seeded["keys"]) == sorted(e["key"] for e in entries)

    # a restart the same day, and one three days later: nothing is created twice
    second = start_backend(fresh_db, tmp_path, name="seed-2")
    second.stop()
    assert snapshot(fresh_db) == seeded
    with psycopg.connect(fresh_db) as c:
        c.execute("UPDATE clock SET off = off + interval '3 days'")
    third = start_backend(fresh_db, tmp_path, name="seed-3")
    third.stop()
    assert snapshot(fresh_db) == seeded
    assert "sample booking" not in third.output()  # no entry was even tried again


@pytest.mark.parametrize(("field", "change"), [
    ("bookings.0.seats", lambda d: d["bookings"][0].update(seats=11)),
    ("bookings.0.email", lambda d: d["bookings"][0].update(email="not-an-email")),
    ("bookings.0.name", lambda d: d["bookings"][0].update(name="")),
])
def test_an_invalid_sample_booking_stops_startup_with_one_line(fresh_db, tmp_path, field, change):
    root = tmp_path / "root"
    shutil.copytree(config.paths.MIGRATIONS, root / "migrations")
    shutil.copytree(config.paths.SEEDS, root / "seeds")
    shutil.copytree(config.paths.CONTENT, root / "content")
    (root / "config").mkdir()
    data = json.loads(json.dumps(SEED))
    change(data)
    (root / "seeds" / "bookings.json").write_text(json.dumps(data), encoding="utf-8")
    b = start_backend(fresh_db, tmp_path, name="invalid", wait=False, env={"BP_ROOT": str(root)})
    try:
        deadline = time.monotonic() + 90
        while b.proc.poll() is None and time.monotonic() < deadline:
            time.sleep(0.2)
        assert b.proc.returncode not in (None, 0), b.output()[-2000:]
        lines = [line for line in b.output().splitlines() if "bookings.json" in line]
        assert len(lines) == 1 and "seeds/bookings.json" in lines[0] and field in lines[0], b.output()[-2000:]
        assert "Traceback" not in b.output()
    finally:
        b.stop()
