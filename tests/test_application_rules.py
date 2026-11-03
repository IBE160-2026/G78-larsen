"""Rules the application enforces and the store does not (addendum A, "application rules"): Booking deadline,
Hold lifetime, one Hold per session and Window, the Release time limit of FR-39. Through the real API."""

from __future__ import annotations

import datetime as dt

import psycopg
import pytest
from psycopg import errors

from conftest import EARLY, set_clock, win_start
from test_fr10_through_the_api import hold, left


def hold_len(pg, sid):
    return pg.execute("SELECT expires_at - created_at FROM holds WHERE session_id = %s", (sid,)).fetchone()[0]


def test_a_hold_lasts_ten_minutes(api, pg):
    assert api.post("/holds", json=dict(window_id=1, seats=2, session_id="a")).status_code == 200
    assert hold_len(pg, "a") == dt.timedelta(minutes=10)


def test_a_hold_ends_at_the_booking_deadline_when_that_comes_first(api, pg):
    """FR-35: the Hold ends at the earlier of 10 minutes and the Booking deadline (start + 5 min by default)."""
    set_clock(pg, win_start(0) + dt.timedelta(minutes=2))  # the deadline is 3 minutes away
    assert api.post("/holds", json=dict(window_id=1, seats=2, session_id="a")).status_code == 200
    got = hold_len(pg, "a")
    assert dt.timedelta(minutes=2, seconds=59) <= got <= dt.timedelta(minutes=3), got


def test_nothing_can_be_held_booked_or_booked_whole_after_the_booking_deadline(api, pg):
    set_clock(pg, win_start(0) + dt.timedelta(minutes=6))
    for path, body in [("/holds", dict(window_id=1, seats=1, session_id="a")),
                       ("/bookings", dict(window_id=1, seats=1, session_id="a")),
                       ("/whole-bookings", dict(window_id=1, sauna_id=4))]:
        r = api.post(path, json=body)
        assert r.status_code == 409 and r.json()["detail"]["error"] == "deadline_passed", (path, r.text)
    assert api.post("/bookings", json=dict(window_id=2, seats=1, session_id="a")).status_code == 201  # the next Window is open


def test_a_payment_after_the_hold_expired_books_only_if_the_seats_are_free(api, pg):
    """FR-36."""
    assert api.post("/holds", json=dict(window_id=1, seats=10, session_id="a")).status_code == 200
    set_clock(pg, EARLY + dt.timedelta(minutes=11))
    assert api.post("/bookings", json=dict(window_id=1, seats=10, session_id="a")).status_code == 201  # Seats still free
    assert pg.execute("SELECT count(*) FROM holds").fetchone()[0] == 0  # the Hold was consumed

    assert api.post("/holds", json=dict(window_id=2, seats=10, session_id="b")).status_code == 200
    set_clock(pg, EARLY + dt.timedelta(minutes=23))
    assert api.post("/bookings", json=dict(window_id=2, seats=40, session_id="c")).status_code == 201  # someone else took them
    r = api.post("/bookings", json=dict(window_id=2, seats=10, session_id="b"))
    assert r.status_code == 409 and r.json()["detail"]["error"] == "no_seat_free"
    assert left(api, 2) == 4


def test_paying_with_a_hold_does_not_count_the_seats_twice(api):
    assert api.post("/holds", json=dict(window_id=1, seats=44, session_id="a")).status_code == 200
    assert left(api) == 0
    assert api.post("/bookings", json=dict(window_id=1, seats=44, session_id="a")).status_code == 201
    assert left(api) == 0


def test_one_hold_per_session_and_window_and_a_resize_keeps_the_old_hold_when_it_fails(api, pg):
    assert api.post("/holds", json=dict(window_id=1, seats=4, session_id="a")).status_code == 200
    assert api.post("/holds", json=dict(window_id=1, seats=6, session_id="a")).status_code == 200  # resized, not added
    assert pg.execute("SELECT seats FROM holds WHERE session_id = 'a'").fetchall() == [(6,)]
    assert left(api) == 38
    assert api.post("/holds", json=dict(window_id=1, seats=36, session_id="b")).status_code == 200
    r = api.post("/holds", json=dict(window_id=1, seats=9, session_id="a"))  # 3 more than are free (2)
    assert r.status_code == 409 and r.json()["detail"]["error"] == "no_seat_free"
    assert pg.execute("SELECT seats FROM holds WHERE session_id = 'a'").fetchall() == [(6,)]  # the old Hold stays
    assert api.post("/holds", json=dict(window_id=2, seats=2, session_id="a")).status_code == 200  # another Window is fine
    assert api.delete("/holds", params=dict(window_id=1, session_id="a")).json() == {"released": 1}
    assert left(api) == 8


def test_the_store_refuses_a_second_hold_for_the_same_session_and_window(api, pg):
    api.post("/holds", json=dict(window_id=1, seats=1, session_id="a"))
    with pytest.raises(errors.UniqueViolation):
        pg.execute("INSERT INTO holds (window_id, seats, session_id, expires_at) VALUES (1, 1, 'a', app_now() + interval '1 minute')")
    pg.rollback()


def test_marking_is_refused_when_the_release_time_is_later_than_the_booking_deadline(api):
    """FR-41 / FR-39: Release time 06:00 on the day is before the deadline (10:05 Oslo): allowed. Later: refused."""
    ok = dict(release_on=True, release_time="06:00", booking_deadline_minutes=5)
    assert api.put("/settings", json=dict(ok, release_time="11:00")).status_code == 200  # no marks yet: nothing to violate
    r = api.post("/marks", json=dict(window_id=1, sauna_id=4))
    assert r.status_code == 409 and r.json()["detail"]["error"] == "release_after_deadline"
    assert api.put("/settings", json=ok).status_code == 200
    assert api.post("/marks", json=dict(window_id=1, sauna_id=4)).status_code == 201
    assert left(api) == 29


def test_a_settings_change_that_would_break_the_release_limit_is_refused_and_names_the_windows(api):
    ok = dict(release_on=True, release_time="06:00", booking_deadline_minutes=5)
    for w, sauna in [(1, 4), (2, 3), (3, 2)]:
        assert api.post("/marks", json=dict(window_id=w, sauna_id=sauna)).status_code == 201
    # the Booking deadlines are 10:05, 11:35 and 13:05 Oslo; 11:40 is after the first two only
    r = api.put("/settings", json=dict(ok, release_time="11:40"))
    assert r.status_code == 409 and r.json()["detail"]["message"] == "Windows: 1, 2", r.text
    # a deadline before the Release time of a marked Window is refused in the same way
    r = api.put("/settings", json=dict(ok, booking_deadline_minutes=-400))
    assert r.status_code == 409 and r.json()["detail"]["error"] == "release_after_deadline"
    assert api.put("/settings", json=dict(ok, release_on=False, release_time="11:40")).status_code == 200  # off: no limit
    assert api.put("/settings", json=dict(ok, booking_deadline_minutes=46)).status_code == 422  # never later than 45 min


def test_a_release_that_was_already_due_stays_when_the_release_time_is_moved_later(api, pg):
    """FR-41: "the release is a condition checked against the data store's clock" - a release that has happened
    is permanent, so moving the Release time later afterwards does not close the Sauna again."""
    ok = dict(release_on=True, release_time="06:00", booking_deadline_minutes=5)
    assert api.post("/marks", json=dict(window_id=1, sauna_id=4)).status_code == 201
    assert left(api) == 29
    set_clock(pg, EARLY + dt.timedelta(hours=2, minutes=5))  # 06:05 Oslo
    assert left(api) == 44
    assert api.put("/settings", json=dict(ok, release_time="09:00")).status_code == 200
    assert left(api) == 44
