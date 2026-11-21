"""FR-21, AD-4, AD-12: retention of a Booking's name and email, decided only by `retention_due(booking_id)`.

- Once app_now() (moved through `clock.off`) is more than 12 months after the end of a Booking's Window, the Booking
  list returns its name and email as "Anonymised" / "anonymised@example.invalid", and the row is not written.
- One day before the limit nothing is masked.
- `services.catchup.run()` anonymises the due Bookings and sets the recipient and body of their Outbox emails to '';
  Bookings not due and their emails are untouched; a second run counts 0 and changes nothing.
- A backend started with the clock past the limit anonymises at startup and logs the counts only.
"""

from __future__ import annotations

import datetime as dt

import pytest

from booking_platform import db
from booking_platform.services import catchup
from client import admin_client
from conftest import set_clock, start_backend, win_start

DAY = "2026-12-01"
NAME, EMAIL = "Anonymised", "anonymised@example.invalid"
# Window 1 ends at win_start(1); 12 months later, and one second past that.
LIMIT = win_start(1).replace(year=win_start(1).year + 1)
PAST = LIMIT + dt.timedelta(seconds=1)


def rows(pg) -> tuple:
    pg.rollback()
    out = (pg.execute("SELECT id, window_id, name, email, xmin::text FROM bookings ORDER BY id").fetchall(),
           pg.execute("SELECT id, booking_id, recipient, subject, body, xmin::text FROM outbox_emails "
                      "ORDER BY id").fetchall())
    pg.rollback()
    return out


@pytest.fixture
def booked(api):
    """Two Guest-flow Bookings: one in Window 1 (due first) and one in Window 3 (ends 3 hours later)."""
    refs = {}
    for wid in (1, 3):
        r = api.book(wid, 2, name="Ingrid Berg", email="ingrid@example.com")
        assert r.status_code == 201, r.text
        refs[wid] = r.json()["booking"]["reference"]
    return refs


@pytest.fixture
def pool(world, database):
    db.open_pool(database, max_size=2)
    yield
    db.close_pool()


def window_bookings(world) -> dict[int, list[dict]]:
    """The Booking list of DAY, read by an Administrator signed in on the clock as it is now (a move of a year ends
    any earlier sign-in)."""
    with admin_client(world) as admin:
        r = admin.get("/api/admin/bookings", params={"date": DAY})
    assert r.status_code == 200, r.text
    return {w["id"]: w["bookings"] for w in r.json()["windows"]}


def test_the_predicate(booked, pg):
    pg.rollback()
    for ts, due in ((LIMIT - dt.timedelta(days=1), False), (LIMIT - dt.timedelta(minutes=1), False),
                    (PAST, True)):
        set_clock(pg, ts)
        assert pg.execute("SELECT retention_due(id) FROM bookings WHERE window_id = 1").fetchone()[0] is due, ts
        assert pg.execute("SELECT retention_due(id) FROM bookings WHERE window_id = 3").fetchone()[0] is False
        pg.rollback()
    assert pg.execute("SELECT retention_due(-1)").fetchone()[0] is False
    pg.rollback()


def test_a_read_past_the_limit_masks_without_writing(booked, world, pg):
    set_clock(pg, PAST)
    window_bookings(world)  # generation for the new today happens on the first read
    before = rows(pg)
    got = window_bookings(world)
    assert [(b["reference"], b["name"], b["email"]) for b in got[1]] == [(booked[1], NAME, EMAIL)]
    assert [(b["name"], b["email"]) for b in got[3]] == [("Ingrid Berg", "ingrid@example.com")]
    assert rows(pg) == before
    assert all(name == "Ingrid Berg" for _, _, name, _, _ in before[0])


def test_one_day_before_the_limit_nothing_is_masked(booked, world, pg):
    set_clock(pg, LIMIT - dt.timedelta(days=1))
    got = window_bookings(world)
    assert [(b["name"], b["email"]) for b in got[1] + got[3]] == [("Ingrid Berg", "ingrid@example.com")] * 2


def test_the_catch_up_anonymises_and_clears_emails_once(booked, pool, pg):
    set_clock(pg, LIMIT - dt.timedelta(days=1))
    assert catchup.run() == {"bookings_anonymised": 0, "emails_cleared": 0}
    set_clock(pg, PAST)
    assert catchup.run() == {"bookings_anonymised": 1, "emails_cleared": 1}
    bookings, emails = rows(pg)
    by_window = {wid: (name, email) for _, wid, name, email, _ in bookings}
    assert by_window == {1: (NAME, EMAIL), 3: ("Ingrid Berg", "ingrid@example.com")}
    due_id = next(bid for bid, wid, *_ in bookings if wid == 1)
    for _, booking_id, recipient, subject, body, _ in emails:
        if booking_id == due_id:
            assert (recipient, body) == ("", "") and subject
        else:
            assert recipient == "ingrid@example.com" and body
    after = rows(pg)
    assert catchup.run() == {"bookings_anonymised": 0, "emails_cleared": 0}
    assert rows(pg) == after  # not even rewritten (xmin unchanged)


def test_a_backend_started_past_the_limit_anonymises_at_startup(booked, pg, database, tmp_path):
    set_clock(pg, PAST)
    b = start_backend(database, tmp_path, name="retention", sample_bookings=False)
    b.stop()
    bookings, emails = rows(pg)
    assert {wid: (name, email) for _, wid, name, email, _ in bookings} == {
        1: (NAME, EMAIL), 3: ("Ingrid Berg", "ingrid@example.com")}
    assert sum(1 for e in emails if e[2] == "" and e[4] == "") == 1
    log = b.output()
    assert "retention catch-up: 1 bookings anonymised, 1 emails cleared" in log
    assert "Ingrid Berg" not in log and "ingrid@example.com" not in log
