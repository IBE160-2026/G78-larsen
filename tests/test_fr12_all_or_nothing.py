"""FR-12 / FR-18 IV-2 / AD-4 / AD-16: a booking request is judged after the lock, as a whole, and a refusal writes
nothing.

- A6: 42 of 44 Seats booked, 3 requested: `409 no_seat_free` with `seats_left` 2, and nothing changes.
- A7: all 44 booked, 1 requested: `409 no_seat_free` with `seats_left` 0, and nothing changes.
- A Window that starts after the end of the Booking horizon is `409 outside_horizon`; one past its Booking deadline is
  `409 deadline_passed`; when both hold, `outside_horizon` is judged first. The clock moves only through `clock.off`
  (NFR-11).
"""

from __future__ import annotations

import datetime as dt

from client import api_client
from conftest import set_clock, win_start
from test_fr10_through_the_api import fill, left


def everything(pg) -> dict:
    """Every table a booking writes, and the Window's Seats left."""
    pg.rollback()
    row = pg.execute("SELECT (SELECT count(*) FROM bookings), (SELECT count(*) FROM payments), "
                     "(SELECT count(*) FROM outbox_emails), (SELECT count(*) FROM idempotency_keys), "
                     "(SELECT count(*) FROM holds), seats_left(1), (SELECT booked FROM windows WHERE id = 1)"
                     ).fetchone()
    pg.rollback()
    return dict(bookings=row[0], payments=row[1], emails=row[2], keys=row[3], holds=row[4], left=row[5],
                booked=row[6])


def test_a6_a_request_for_more_than_is_left_is_refused_as_a_whole(api, pg):
    fill(api, 42)
    before = everything(pg)
    r = api.book(1, 3)
    assert r.status_code == 409, r.text
    assert r.json() == {"detail": {"error": "no_seat_free", "seats_left": 2}}
    assert everything(pg) == before
    assert left(api) == 2 and before["booked"] == 42
    assert api.book(1, 2).status_code == 201  # the two that are left can still be booked
    r = api.book(1, 1)
    assert r.status_code == 409 and left(api) == 0


def test_a7_a_request_when_every_seat_is_booked_is_refused(api, pg):
    fill(api, 44)
    before = everything(pg)
    r = api.book(1, 1)
    assert r.status_code == 409, r.text
    assert r.json() == {"detail": {"error": "no_seat_free", "seats_left": 0}}
    assert everything(pg) == before
    assert left(api) == 0


def test_seats_left_counts_other_sessions_holds_but_not_the_payers_own(api, world, pg):
    """The fact is Seats left after the payer's own Hold is released: another session's live Hold still counts."""
    fill(api, 30)
    with api_client(world) as other:
        assert other.post("/api/holds", json=dict(window_id=1, seats=10)).status_code == 200
    assert api.post("/api/holds", json=dict(window_id=1, seats=4)).status_code == 200
    before = everything(pg)
    r = api.book(1, 5)
    assert r.status_code == 409 and r.json() == {"detail": {"error": "no_seat_free", "seats_left": 4}}, r.text
    assert everything(pg) == before  # the payer's Hold is back: the refusal rolled its delete back
    assert api.book(1, 4).status_code == 201


def test_a_window_after_the_booking_horizon_is_outside_horizon(api, pg):
    set_clock(pg, win_start(0) - dt.timedelta(days=29))  # the horizon is 28 days
    before = everything(pg)
    r = api.book(1, 1)
    assert r.status_code == 409 and r.json()["detail"]["error"] == "outside_horizon", r.text
    assert everything(pg) == before


def test_a_window_past_its_booking_deadline_is_deadline_passed(api, pg):
    set_clock(pg, win_start(0) + dt.timedelta(minutes=6))  # the deadline is start + 5 minutes
    before = everything(pg)
    r = api.book(1, 1)
    assert r.status_code == 409 and r.json()["detail"]["error"] == "deadline_passed", r.text
    assert everything(pg) == before


def test_outside_horizon_is_judged_before_deadline_passed(api, pg):
    """A Window both beyond the horizon and past its deadline (a deadline two days before the start, a one-day
    horizon) is `outside_horizon`."""
    pg.execute("UPDATE settings SET booking_horizon_days = 1, booking_deadline_minutes = -2880")
    pg.commit()
    set_clock(pg, win_start(0) - dt.timedelta(hours=36))
    assert pg.execute("SELECT NOT within_horizon(1) AND app_now() >= booking_deadline(1)").fetchone()[0]
    pg.rollback()
    r = api.book(1, 1)
    assert r.status_code == 409 and r.json()["detail"]["error"] == "outside_horizon", r.text
    assert everything(pg)["bookings"] == 0
