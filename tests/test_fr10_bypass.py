"""FR-10, second bullet: "In every phase, the data store refuses a write that would exceed Seat capacity even when
the application's own check is bypassed." These tests write straight to PostgreSQL, around the API, while the
real API process is running against the same database.
"""

from __future__ import annotations

import datetime as dt

import psycopg
import pytest
from psycopg import errors

from client import api_client
from conftest import EARLY, clear, raw_booking, raw_whole, set_clock, state, win_start
from test_fr10_through_the_api import fill, left, parallel


def refused(pg, sql, params=(), want=errors.CheckViolation):
    """The write must be rejected, whether at the statement or at COMMIT."""
    with pytest.raises(want):
        pg.execute(sql, params)
        pg.commit()
    pg.rollback()


def accepted(pg, sql, params=()):
    pg.execute(sql, params)
    pg.commit()


def test_core_an_over_capacity_booking_written_around_the_api_is_refused(api, pg):
    fill(api, 42)
    refused(pg, raw_booking(1, 3))
    refused(pg, raw_booking(1, 45))
    assert state(pg)["real_booked"] == 42 and left(api) == 2
    accepted(pg, raw_booking(1, 2))  # exactly full is allowed
    refused(pg, raw_booking(1, 1))
    assert left(api) == 0


def test_core_raising_a_booking_after_the_fact_is_refused(api, pg):
    for _ in range(8):  # Bookings of 5, so one raised by 5 still holds at most 10 Seats (`bookings_kind_shape`)
        assert api.book(1, 5).status_code == 201
    with pytest.raises(errors.CheckViolation) as e:
        pg.execute("UPDATE bookings SET seats = seats + 5, total_ore = (seats + 5) * price_per_seat_ore "
                   "WHERE id = (SELECT min(id) FROM bookings)")  # the value follows, so only capacity can refuse it
        pg.commit()
    pg.rollback()
    assert e.value.diag.constraint_name == "booked_within_capacity"
    assert state(pg)["real_booked"] == 40


def test_the_stored_numbers_cannot_be_tampered_with(api, pg):
    """Writing a bigger capacity or a smaller booked number into the Window is refused at commit,
    and a booking written after such a tamper attempt is still judged on the real capacity."""
    fill(api, 44)
    refused(pg, "UPDATE windows SET seat_capacity = 1000 WHERE id = 1")
    refused(pg, "UPDATE windows SET booked = 0 WHERE id = 1")
    refused(pg, "UPDATE windows SET held = -1 WHERE id = 1")
    refused(pg, raw_booking(1, 1))
    assert state(pg)["real_booked"] == 44


def test_whole_sauna_bookings_and_blocks_change_the_capacity_the_store_enforces(api, pg):
    raw_whole(pg, 1, 4)  # a paired Whole-sauna booking (AD-21, AD-23): 15 Seats gone, 29 left
    assert left(api) == 29
    fill(api, 29)
    refused(pg, raw_booking(1, 1))
    # a Sauna cannot be booked whole over Seats placed in it, nor a Block laid over a full Window
    with pytest.raises(errors.CheckViolation):
        raw_whole(pg, 1, 1)
    refused(pg, "INSERT INTO blocks (sauna_id, during) SELECT 1, during FROM windows WHERE id = 1")
    # and in another, empty Window a Block removes capacity at once
    accepted(pg, "INSERT INTO blocks (sauna_id, during) SELECT 3, during FROM windows WHERE id = 2")
    assert left(api, 2) == 32
    refused(pg, raw_booking(2, 33))


def test_a_block_that_would_leave_too_little_capacity_is_refused_by_the_api_as_well(api, admin, pg):
    fill(api, 40)  # Sauna 4 (the last in the Fill order) is the one that gives up Seats
    st = win_start(0)
    r = admin.post("/api/admin/blocks", json=dict(sauna_id=4, start=st.isoformat(), end=(st + dt.timedelta(minutes=90)).isoformat()))
    assert r.status_code == 409 and r.json()["detail"]["error"] in ("no_seat_free", "rule_refused")
    assert left(api) == 4


def test_holds_count_in_the_store(api, pg):
    accepted(pg, "INSERT INTO holds (window_id, seats, session_id, expires_at) VALUES (1, 40, NULL, app_now() + interval '5 minutes')")
    assert left(api) == 4
    refused(pg, raw_booking(1, 5))
    refused(pg, "INSERT INTO holds (window_id, seats, session_id, expires_at) VALUES (1, 5, NULL, app_now() + interval '5 minutes')")
    refused(pg, "INSERT INTO holds (window_id, seats, session_id, expires_at) VALUES (1, 1, NULL, app_now() + interval '11 minutes')")
    accepted(pg, raw_booking(1, 4))
    set_clock(pg, EARLY + dt.timedelta(minutes=6))  # the Hold has expired, no cleanup has run
    assert left(api) == 40
    accepted(pg, raw_booking(1, 40))


def test_marks_and_the_release_time_in_the_store(api, pg):
    accepted(pg, "INSERT INTO marks (window_id, sauna_id) VALUES (1, 4)")  # Sauna 4 closed for Seats: 29 left
    assert left(api) == 29
    refused(pg, "INSERT INTO releases (window_id, sauna_id, released_at) VALUES (1, 4, app_now())")  # cannot be forged early
    fill(api, 29)
    set_clock(pg, EARLY + dt.timedelta(hours=2, minutes=5))  # 05:05Z = 06:05 Oslo: the Release time has passed
    assert left(api) == 15  # the marked Sauna is open for Seats again
    refused(pg, raw_booking(1, 16))
    accepted(pg, raw_booking(1, 15))
    refused(pg, raw_booking(1, 1))


def test_a_mark_is_refused_while_seats_are_placed_in_the_sauna(api, admin, pg):
    fill(api, 40)  # Seats reach into Sauna 4
    refused(pg, "INSERT INTO marks (window_id, sauna_id) VALUES (1, 4)")
    r = admin.post("/api/admin/marks", json=dict(window_id=1, sauna_id=4))
    assert r.status_code == 409


def test_a_direct_write_races_the_api_for_the_last_seat(api, world, pg, database):
    """The API and a bypassing client write at the same moment: exactly one gets the Seat."""
    dsn = database
    for r in range(40):
        clear(pg)
        fill(api, 43)

        def direct():
            with psycopg.connect(dsn) as c:
                try:
                    c.execute(raw_booking(1, 1))
                    c.commit()
                    return 201
                except errors.CheckViolation:
                    return 409

        guest = api_client(world)  # its session is made before the barrier

        def via_api():
            return guest.book(1, 1).status_code

        got = sorted(parallel([direct, via_api]))
        guest.close()
        assert got == [201, 409], (r, got)
        assert state(pg)["real_booked"] == 44


def test_direct_writers_in_parallel_cannot_oversell(api, pg, database):
    """Twelve bypassing clients each try to book 5 of 44 Seats at the same moment."""
    dsn = database
    for r in range(10):
        clear(pg)

        def direct():
            with psycopg.connect(dsn) as c:
                try:
                    c.execute(raw_booking(1, 5))
                    c.commit()
                    return 5
                except errors.CheckViolation:
                    return 0

        total = sum(parallel([direct] * 12))
        assert total == 40, (r, total)
        assert state(pg)["left"] == 4
