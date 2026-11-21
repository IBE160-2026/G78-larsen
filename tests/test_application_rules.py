"""Rules the application enforces and the store does not (addendum A, "application rules"): Booking deadline,
Hold lifetime, one Hold per session and Window, the Release time limit of FR-39. Through the real API."""

from __future__ import annotations

import datetime as dt

import psycopg
import pytest
from psycopg import errors

from client import api_client, booking_body, new_key
from conftest import EARLY, set_clock, win_start
from test_fr10_through_the_api import fill, hold, left


def hold_len(pg, sid):
    return pg.execute("SELECT expires_at - created_at FROM holds WHERE session_id = %s", (sid,)).fetchone()[0]


def test_a_hold_lasts_ten_minutes(api, pg):
    assert api.post("/api/holds", json=dict(window_id=1, seats=2)).status_code == 200
    assert hold_len(pg, api.session_id) == dt.timedelta(minutes=10)


def test_a_hold_ends_at_the_booking_deadline_when_that_comes_first(api, pg):
    """FR-35: the Hold ends at the earlier of 10 minutes and the Booking deadline (start + 5 min by default)."""
    set_clock(pg, win_start(0) + dt.timedelta(minutes=2))  # the deadline is 3 minutes away
    assert api.post("/api/holds", json=dict(window_id=1, seats=2)).status_code == 200
    got = hold_len(pg, api.session_id)
    assert dt.timedelta(minutes=2, seconds=59) <= got <= dt.timedelta(minutes=3), got


def test_nothing_can_be_held_booked_or_booked_whole_after_the_booking_deadline(api, admin, pg):
    set_clock(pg, win_start(0) + dt.timedelta(minutes=6))
    for c, path, body in [(api, "/api/holds", dict(window_id=1, seats=1)),
                          (api, "/api/bookings", booking_body(1, 1)),
                          (admin, "/api/admin/whole-bookings", dict(window_id=1, sauna_id=4))]:
        r = c.post(path, json=body, headers=new_key())
        assert r.status_code == 409 and r.json()["detail"]["error"] == "deadline_passed", (path, r.text)
    assert api.book(2, 1).status_code == 201  # the next Window is open


def test_nothing_can_be_held_booked_or_booked_whole_beyond_the_booking_horizon(api, admin, pg):
    """FR-18 IV-2, FR-29: a Window that starts after the end of the Booking horizon (28 days)."""
    set_clock(pg, win_start(0) - dt.timedelta(days=29))
    for c, path, body in [(api, "/api/holds", dict(window_id=1, seats=1)),
                          (api, "/api/bookings", booking_body(1, 1)),
                          (admin, "/api/admin/whole-bookings", dict(window_id=1, sauna_id=4))]:
        r = c.post(path, json=body, headers=new_key())
        assert r.status_code == 409 and r.json()["detail"]["error"] == "outside_horizon", (path, r.text)
    written = pg.execute("SELECT (SELECT count(*) FROM holds), (SELECT count(*) FROM bookings), "
                         "(SELECT count(*) FROM whole_bookings), (SELECT count(*) FROM payments), "
                         "(SELECT count(*) FROM outbox_emails), (SELECT count(*) FROM idempotency_keys)").fetchone()
    pg.rollback()
    assert written == (0, 0, 0, 0, 0, 0)


def test_a_payment_after_the_hold_expired_books_only_if_the_seats_are_free(api, world, pg):
    """FR-36."""
    a, b, c = api, api_client(world), api_client(world)
    assert a.post("/api/holds", json=dict(window_id=1, seats=10)).status_code == 200
    set_clock(pg, EARLY + dt.timedelta(minutes=11))
    assert a.book(1, 10).status_code == 201  # Seats still free
    assert pg.execute("SELECT count(*) FROM holds").fetchone()[0] == 0  # the Hold was consumed

    assert b.post("/api/holds", json=dict(window_id=2, seats=10)).status_code == 200
    set_clock(pg, EARLY + dt.timedelta(minutes=23))
    fill(c, 40, wid=2)  # someone else took them, in Bookings of at most 10, each a 201 (AD-21)
    r = b.book(2, 10)
    assert r.status_code == 409 and r.json()["detail"]["error"] == "no_seat_free"
    assert left(api, 2) == 4


def test_paying_with_a_hold_does_not_count_the_seats_twice(api, pg):
    # a Hold of 44 is above the API's 10 Seats: a raw Hold of the session's (AD-21)
    pg.execute("INSERT INTO holds (window_id, seats, session_id, created_at, expires_at) "
               "SELECT 1, 44, %s, n, n + interval '10 minutes' FROM (SELECT app_now() AS n) x", (api.session_id,))
    pg.commit()
    assert left(api) == 0
    fill(api, 44)  # the session pays for its 44 held Seats in Bookings of at most 10, each a 201
    assert left(api) == 0


def test_one_hold_per_session_and_window_and_a_resize_keeps_the_old_hold_when_it_fails(api, world, pg):
    a = api
    held_by_a = "SELECT seats FROM holds WHERE session_id = %s"
    assert a.post("/api/holds", json=dict(window_id=1, seats=4)).status_code == 200
    assert a.post("/api/holds", json=dict(window_id=1, seats=6)).status_code == 200  # resized, not added
    assert pg.execute(held_by_a, (a.session_id,)).fetchall() == [(6,)]
    assert left(api) == 38
    for n in (10, 10, 10, 6):  # 36 held by others, in Holds of at most 10 (AD-21)
        with api_client(world) as b:
            assert b.post("/api/holds", json=dict(window_id=1, seats=n)).status_code == 200
    r = a.post("/api/holds", json=dict(window_id=1, seats=9))  # 3 more than are free (2)
    assert r.status_code == 409 and r.json()["detail"]["error"] == "no_seat_free"
    assert pg.execute(held_by_a, (a.session_id,)).fetchall() == [(6,)]  # the old Hold stays
    assert a.post("/api/holds", json=dict(window_id=2, seats=2)).status_code == 200  # another Window is fine
    assert a.delete("/api/holds", params=dict(window_id=1)).json() == {"released": 1}
    assert left(api) == 8


def test_the_store_refuses_a_second_hold_for_the_same_session_and_window(api, pg):
    api.post("/api/holds", json=dict(window_id=1, seats=1))
    with pytest.raises(errors.UniqueViolation):
        pg.execute("INSERT INTO holds (window_id, seats, session_id, expires_at) VALUES (1, 1, %s, app_now() + interval '1 minute')",
                   (api.session_id,))
    pg.rollback()


def test_marking_is_refused_when_the_release_time_is_later_than_the_booking_deadline(api, admin):
    """FR-41 / FR-39: Release time 06:00 on the day is before the deadline (10:05 Oslo): allowed. Later: refused."""
    ok = dict(release_on=True, release_time="06:00", booking_deadline_minutes=5)
    assert admin.put("/api/admin/settings", json=dict(ok, release_time="11:00")).status_code == 200  # no marks yet: nothing to violate
    r = admin.post("/api/admin/marks", json=dict(window_id=1, sauna_id=4))
    assert r.status_code == 409 and r.json()["detail"]["error"] == "release_after_deadline"
    assert admin.put("/api/admin/settings", json=ok).status_code == 200
    assert admin.post("/api/admin/marks", json=dict(window_id=1, sauna_id=4)).status_code == 201
    assert left(api) == 29


def test_a_settings_change_that_would_break_the_release_limit_is_refused_and_names_the_windows(admin):
    ok = dict(release_on=True, release_time="06:00", booking_deadline_minutes=5)
    for w, sauna in [(1, 4), (2, 3), (3, 2)]:
        assert admin.post("/api/admin/marks", json=dict(window_id=w, sauna_id=sauna)).status_code == 201
    # the Booking deadlines are 10:05, 11:35 and 13:05 Oslo; 11:40 is after the first two only
    r = admin.put("/api/admin/settings", json=dict(ok, release_time="11:40"))
    assert r.status_code == 409 and r.json()["detail"]["message"] == "Windows: 1, 2", r.text
    # a deadline before the Release time of a marked Window is refused in the same way
    r = admin.put("/api/admin/settings", json=dict(ok, booking_deadline_minutes=-400))
    assert r.status_code == 409 and r.json()["detail"]["error"] == "release_after_deadline"
    assert admin.put("/api/admin/settings", json=dict(ok, release_on=False, release_time="11:40")).status_code == 200  # off: no limit
    assert admin.put("/api/admin/settings", json=dict(ok, booking_deadline_minutes=46)).status_code == 422  # never later than 45 min


def test_a_release_that_was_already_due_stays_when_the_release_time_is_moved_later(api, admin, pg):
    """FR-41: "the release is a condition checked against the data store's clock" - a release that has happened
    is permanent, so moving the Release time later afterwards does not close the Sauna again."""
    ok = dict(release_on=True, release_time="06:00", booking_deadline_minutes=5)
    assert admin.post("/api/admin/marks", json=dict(window_id=1, sauna_id=4)).status_code == 201
    assert left(api) == 29
    set_clock(pg, EARLY + dt.timedelta(hours=2, minutes=5))  # 06:05 Oslo
    assert left(api) == 44
    assert admin.put("/api/admin/settings", json=dict(ok, release_time="09:00")).status_code == 200
    assert left(api) == 44


def _not_bookable_whole(api, admin, pg):
    pg.execute("UPDATE saunas SET bookable_whole = false WHERE id = 4")
    pg.commit()


def _blocked(api, admin, pg):
    st = win_start(0)
    assert admin.post("/api/admin/blocks", json=dict(sauna_id=4, start=st.isoformat(),
                                                     end=(st + dt.timedelta(minutes=90)).isoformat())).status_code == 201


def _seats_placed(api, admin, pg):
    fill(api, 40)  # Seats reach into every Sauna


def _started_with_seat_bookings(api, admin, pg):
    assert api.book(1, 1).status_code == 201
    set_clock(pg, win_start(0) + dt.timedelta(minutes=2))  # started, before the Booking deadline


@pytest.mark.parametrize("setup,path,sauna", [
    (_not_bookable_whole, "/api/admin/whole-bookings", 4),
    (_blocked, "/api/admin/whole-bookings", 4),
    (_seats_placed, "/api/admin/whole-bookings", 1),
    (_started_with_seat_bookings, "/api/admin/whole-bookings", 4),
    (_not_bookable_whole, "/api/admin/marks", 4),
    (_seats_placed, "/api/admin/marks", 4),
], ids=["whole_not_bookable", "whole_blocked", "whole_seats_placed", "whole_window_started",
        "mark_not_bookable", "mark_seats_placed"])
def test_each_named_store_refusal_is_rule_refused(api, admin, pg, setup, path, sauna):
    """AD-1: the named trigger refusals of 0003 reach the API as 409 rule_refused."""
    setup(api, admin, pg)
    r = admin.post(path, json=dict(window_id=1, sauna_id=sauna))
    assert r.status_code == 409 and r.json()["detail"]["error"] == "rule_refused", r.text
