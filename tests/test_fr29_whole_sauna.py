"""FR-29 / FR-30 (Story 5.1, AD-24): the Private sauna listing `GET /api/private-saunas?date=`, against the real API.

The catalogue examples of FR-29 are named by ID. The test Saunas are Rauha 7, Loyly 10, Kajo 12 and Lumo 15 in Fill
order, each with a Whole-sauna price (`world`). Seats are booked as raw rows (AD-21), which the store places in Fill
order: 20 Seats sit as [7, 10, 3, 0], 29 as [7, 10, 12, 0]. Each example asserts the exact set of Saunas listed for
the Window. Window k starts at 10:00 + 90 min * k Oslo time on 2026-12-01; the clock is at 04:00 Oslo (`EARLY`).
"""

from __future__ import annotations

import datetime as dt
import threading

import httpx
import psycopg

from conftest import raw_booking, raw_whole, set_clock, win_start

DATE = "2026-12-01"


def listing(c, date: str = DATE) -> httpx.Response:
    return c.get("/api/private-saunas", params=dict(date=date))


def listed(c, wid: int, date: str = DATE) -> set[str]:
    """The names of the Saunas the listing offers whole in Window `wid`."""
    r = listing(c, date)
    assert r.status_code == 200, r.text
    return {s["name"] for s in r.json()["saunas"] if any(w["id"] == wid for w in s["windows"])}


def book_raw(pg, wid: int, seats: int) -> None:
    pg.execute(raw_booking(wid, seats))
    pg.commit()


ALL = {"Rauha", "Loyly", "Kajo", "Lumo"}


def test_b1_lumo_is_listed_with_20_seats_booked(api, pg):
    book_raw(pg, 1, 20)  # [7, 10, 3, 0]: Lumo's Room ahead is 29
    assert listed(api, 1) == {"Lumo"}


def test_b2_kajo_holding_seats_is_not_listed(api, pg):
    book_raw(pg, 1, 20)  # Kajo holds 3 of the 20 Seats: its Room ahead (17) is too small
    got = listed(api, 1)
    assert "Kajo" not in got
    assert got == {"Lumo"}


def test_held_seats_fill_room_ahead_as_booked_ones_do(api, pg):
    """FR-29: Seats booked plus held. 20 held Seats (a raw Hold, AD-21) sit as [7, 10, 3, 0], so Kajo is not listed."""
    pg.execute("INSERT INTO holds (window_id, seats, session_id, expires_at) VALUES (1, 20, NULL, app_now() + interval '5 minutes')")
    pg.commit()
    assert listed(api, 1) == {"Lumo"}


def test_b3_rauha_is_not_listed_with_1_seat_booked(api, pg):
    book_raw(pg, 1, 1)  # the Seat sits in Rauha, which has no Room ahead
    assert listed(api, 1) == {"Loyly", "Kajo", "Lumo"}


def test_b7_lumo_is_listed_in_an_empty_window(api):
    got = listed(api, 1)
    assert "Lumo" in got
    assert got == ALL


def test_h12_lumo_is_not_listed_in_a_started_window_with_29_seats_booked(api, pg):
    book_raw(pg, 1, 29)  # [7, 10, 12, 0]: Lumo's Room ahead (29) would fit, but the Window has started
    set_clock(pg, win_start(0) + dt.timedelta(minutes=2))  # started, before its Booking deadline
    assert listed(api, 1) == set()
    assert listed(api, 2) == ALL  # the next Window has not started


def test_a_started_window_without_seat_bookings_is_listed_as_started(api, pg):
    set_clock(pg, win_start(0) + dt.timedelta(minutes=2))
    body = listing(api).json()
    started = {w["id"]: w["already_started"] for s in body["saunas"] for w in s["windows"]}
    assert started[1] is True and started[2] is False
    assert listed(api, 1) == ALL


def test_a_sauna_without_a_price_is_never_listed(api, pg):
    pg.execute("UPDATE saunas SET whole_price_ore = NULL WHERE id = 4")
    pg.commit()
    assert listed(api, 1) == {"Rauha", "Loyly", "Kajo"}
    body = listing(api).json()
    assert all(s["whole_price_ore"] is not None for s in body["saunas"])
    assert "Lumo" not in {s["name"] for s in body["saunas"]}


def test_a_sauna_that_is_blocked_booked_whole_or_not_bookable_whole_is_not_listed(api, admin, pg):
    pg.execute("UPDATE saunas SET bookable_whole = false WHERE id = 1")
    pg.commit()
    st = win_start(0)
    assert admin.post("/api/admin/blocks", json=dict(sauna_id=2, start=st.isoformat(),
                                                     end=(st + dt.timedelta(minutes=90)).isoformat())).status_code == 201
    raw_whole(pg, 1, 4)
    assert listed(api, 1) == {"Kajo"}
    assert listed(api, 2) == {"Loyly", "Kajo", "Lumo"}


def test_a_window_past_its_booking_deadline_is_not_listed(api, pg):
    set_clock(pg, win_start(0) + dt.timedelta(minutes=6))  # Window 1's deadline (start + 5 min) has passed
    assert listed(api, 1) == set()
    assert listed(api, 2) == ALL


def test_a_date_outside_the_horizon_is_409_outside_horizon(api, pg):
    for date in ("2026-11-30", "2026-12-30"):  # yesterday, and the day after the 28-day horizon ends (12-29)
        r = listing(api, date)
        assert r.status_code == 409, r.text
        assert r.json() == {"detail": {"error": "outside_horizon", "today": "2026-12-01",
                                       "horizon_end": "2026-12-29"}}
    assert listing(api, "2026-12-29").status_code == 200


def test_the_date_is_required_and_written_yyyy_mm_dd(api):
    for params in ({}, {"date": "01.12.2026"}, {"date": "2026-12-01", "seats": "2"}):
        r = api.get("/api/private-saunas", params=params)
        assert r.status_code == 422 and r.json()["detail"]["error"] == "invalid_input", (params, r.text)


def test_the_shape_saunas_in_fill_order_and_saunas_without_a_pair_left_out(api, pg):
    book_raw(pg, 1, 1)
    body = listing(api).json()
    assert set(body) == {"saunas", "horizon_end", "horizon_days"}
    assert (body["horizon_end"], body["horizon_days"]) == ("2026-12-29", 28)
    assert [s["name"] for s in body["saunas"]] == ["Rauha", "Loyly", "Kajo", "Lumo"]  # Fill order
    rauha, lumo = body["saunas"][0], body["saunas"][3]
    assert {k: v for k, v in lumo.items() if k != "windows"} == {
        "id": 4, "name": "Lumo", "capacity": 15, "whole_price_ore": 395000}
    assert set(lumo["windows"][0]) == {"id", "start", "end", "already_started"}
    assert lumo["windows"][:3] == [
        {"id": 1, "start": "2026-12-01T10:00:00+01:00", "end": "2026-12-01T11:30:00+01:00", "already_started": False},
        {"id": 2, "start": "2026-12-01T11:30:00+01:00", "end": "2026-12-01T13:00:00+01:00", "already_started": False},
        {"id": 3, "start": "2026-12-01T13:00:00+01:00", "end": "2026-12-01T14:30:00+01:00", "already_started": False}]
    starts = [w["start"] for w in lumo["windows"]]
    assert starts == sorted(starts)
    assert 1 not in [w["id"] for w in rauha["windows"]]
    # a Sauna with no free Window that day is left out, not listed empty
    for wid in [w["id"] for w in rauha["windows"]]:
        book_raw(pg, wid, 1)
    assert "Rauha" not in [s["name"] for s in listing(api).json()["saunas"]]


def _counts(pg) -> tuple:
    pg.rollback()
    row = pg.execute("SELECT (SELECT count(*) FROM bookings), (SELECT count(*) FROM whole_bookings), "
                     "(SELECT count(*) FROM holds), (SELECT count(*) FROM sessions), (SELECT count(*) FROM windows), "
                     "(SELECT windows_generated_through FROM settings), "
                     "(SELECT array_agg(seat_capacity || ',' || booked || ',' || held ORDER BY id) FROM windows)"
                     ).fetchone()
    pg.rollback()
    return tuple(row)


def test_the_listing_needs_no_session_sets_no_cookie_takes_no_lock_and_writes_nothing(world, pg, database):
    with httpx.Client(base_url=world, timeout=10) as c:  # no session cookie, no Origin
        assert listing(c).status_code == 200  # the first listing generates the horizon's Windows
        before = _counts(pg)
        r = listing(c)
        assert r.status_code == 200 and "set-cookie" not in r.headers and not c.cookies
        assert _counts(pg) == before
        # a Window row locked by another transaction does not hold the listing up
        holder = psycopg.connect(database)
        try:
            holder.execute("SELECT 1 FROM windows WHERE id = 1 FOR UPDATE")
            done: list = []
            t = threading.Thread(target=lambda: done.append(listing(c).status_code))
            t.start()
            t.join(timeout=8)
            assert done == [200]
        finally:
            holder.rollback()
            holder.close()
        assert listing(c, "2027-06-01").status_code == 409  # a refused listing writes nothing either
        assert _counts(pg) == before
