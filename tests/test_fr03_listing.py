"""FR-2, FR-3, FR-13 E2/E4, AD-4, AD-5, AD-16: the dated Window listing `GET /api/windows?date=&seats=`.

Every response carries `today`, `horizon_end`, `horizon_days` and `dates`; with a date it lists that Venue date's
Windows inside the Booking horizon and before their Booking deadline, in time order, with Seats left from
`seats_left()` and `already_started`; with Seats and no room on the date it adds up to three nearest Windows with
room. A malformed value is `422 invalid_input`, a date outside the horizon `409 outside_horizon`, and a refused
listing writes nothing. The listing needs no session and sets no cookie.
"""

from __future__ import annotations

import datetime as dt

import pytest

from client import api_client
from conftest import set_clock

UTC = dt.timezone.utc
SLOTS = ["10:00", "11:30", "13:00", "14:30", "16:00", "17:30", "19:00", "20:30"]
ALL_SAUNAS = (1, 2, 3, 4)


@pytest.fixture
def anon(world):
    """A client with no session: the listing needs none."""
    with api_client(world, session=False) as c:
        yield c


def listing(c, **params):
    r = c.get("/api/windows", params=params)
    assert r.status_code == 200, r.text
    return r.json()


def wid(pg, date: str, hhmm: str) -> int:
    pg.rollback()
    row = pg.execute("SELECT id FROM windows WHERE venue_date(id) = %s "
                     "AND to_char(lower(during) AT TIME ZONE 'Europe/Oslo', 'HH24:MI') = %s", (date, hhmm)).fetchone()
    pg.rollback()
    return row[0]


def block_day(pg, date: str, saunas=ALL_SAUNAS) -> None:
    """Block Saunas for a whole Venue date (the triggers recompute every overlapping Window)."""
    start = dt.datetime.fromisoformat(date).replace(hour=0)
    for s in saunas:
        pg.execute("INSERT INTO blocks (sauna_id, during) VALUES (%s, tstzrange("
                   "(%s::timestamp) AT TIME ZONE 'Europe/Oslo', (%s::timestamp + interval '1 day') AT TIME ZONE "
                   "'Europe/Oslo', '[)'))", (s, start, start))
    pg.commit()


def book(pg, window_id: int, seats: int) -> None:
    pg.execute("INSERT INTO bookings (window_id, seats) VALUES (%s, %s)", (window_id, seats))
    pg.commit()


def written(pg) -> tuple:
    pg.rollback()
    row = pg.execute("SELECT (SELECT count(*) FROM windows), (SELECT windows_generated_through FROM settings), "
                     "(SELECT count(*) FROM sessions), (SELECT count(*) FROM bookings)").fetchone()
    pg.rollback()
    return tuple(row)


# ------------------------------------------------------------------ the listing


def test_without_parameters_only_the_time_facts_and_the_dates(anon):
    r = anon.get("/api/windows")
    assert r.status_code == 200 and "set-cookie" not in r.headers
    body = r.json()
    assert set(body) == {"today", "horizon_end", "horizon_days", "dates"}
    assert (body["today"], body["horizon_end"], body["horizon_days"]) == ("2026-12-01", "2026-12-29", 28)
    # at 04:00 the horizon ends 12-29 04:00, before that day's first Window, so 12-29 is not a date yet
    assert body["dates"] == [(dt.date(2026, 12, 1) + dt.timedelta(days=i)).isoformat() for i in range(28)]


def test_a_date_lists_its_windows_in_time_order_with_the_time_facts(anon):
    body = listing(anon, date="2026-12-01", seats=2)
    assert set(body) == {"today", "horizon_end", "horizon_days", "dates", "windows"}  # room, so no nearest
    ws = body["windows"]
    assert [w["start"][11:16] for w in ws] == SLOTS
    assert [w["end"][11:16] for w in ws] == SLOTS[1:] + ["22:00"]
    assert all(w["start"].startswith("2026-12-01T") and w["start"].endswith("+01:00") for w in ws)
    assert [w["id"] for w in ws[:3]] == [1, 2, 3]  # the world's Windows, on the seed's slots
    for w in ws:
        assert set(w) == {"id", "start", "end", "seats_left", "already_started"}  # no price, no Sauna
        assert w["seats_left"] == 44 and w["already_started"] is False


def test_seats_left_is_capacity_minus_seats_booked_and_windows_are_independent(anon, pg):
    listing(anon, date="2026-12-01")
    book(pg, 2, 10)
    book(pg, 2, 3)
    left = {w["id"]: w["seats_left"] for w in listing(anon, date="2026-12-01")["windows"]}
    assert left[2] == 44 - 13
    assert left[1] == left[3] == 44  # Seats booked in one Window leave another unchanged (E2, E4)
    assert len({v for k, v in left.items() if k != 2}) == 1
    # a Block lowers the Seat capacity of the Windows it overlaps only
    pg.execute("INSERT INTO blocks (sauna_id, during) SELECT 1, during FROM windows WHERE id = 3")
    pg.commit()
    left = {w["id"]: w["seats_left"] for w in listing(anon, date="2026-12-01")["windows"]}
    assert (left[1], left[2], left[3]) == (44, 31, 44 - 7)


def test_a_started_window_before_its_deadline_is_listed_as_already_started_then_left_out(anon, pg):
    set_clock(pg, dt.datetime(2026, 12, 1, 9, 3, tzinfo=UTC))  # 10:03 Oslo: Window 1 started, deadline 10:05
    ws = listing(anon, date="2026-12-01")["windows"]
    assert ws[0]["id"] == 1 and ws[0]["already_started"] is True
    assert [w["already_started"] for w in ws[1:]] == [False] * 7
    set_clock(pg, dt.datetime(2026, 12, 1, 9, 5, tzinfo=UTC))  # the deadline itself: no longer bookable
    ws = listing(anon, date="2026-12-01")["windows"]
    assert [w["start"][11:16] for w in ws] == SLOTS[1:]


def test_after_the_last_deadline_of_the_day_today_has_no_windows_and_is_not_a_date(anon, pg):
    set_clock(pg, dt.datetime(2026, 12, 1, 19, 40, tzinfo=UTC))  # 20:40 Oslo
    body = listing(anon, date="2026-12-01")
    assert body["today"] == "2026-12-01" and body["windows"] == []
    assert body["dates"][0] == "2026-12-02"


def test_the_last_horizon_day_lists_only_windows_inside_the_horizon(anon, pg):
    set_clock(pg, dt.datetime(2026, 12, 1, 12, 0, tzinfo=UTC))  # 13:00 Oslo: the horizon ends 12-29 13:00
    body = listing(anon, date="2026-12-29")
    assert [w["start"][11:16] for w in body["windows"]] == ["10:00", "11:30", "13:00"]
    assert body["dates"][-1] == "2026-12-29"


# ------------------------------------------------------------------ the nearest Windows


def test_no_room_on_the_date_returns_up_to_three_nearest_with_room_in_time_order(anon, pg):
    listing(anon)
    block_day(pg, "2026-12-02")
    # on 12-03, 10:00 keeps 1 Seat: the three Saunas after Rauha are Blocked and 6 of Rauha's 7 are booked
    early = wid(pg, "2026-12-03", "10:00")
    pg.execute("INSERT INTO blocks (sauna_id, during) SELECT s, during FROM windows, unnest(ARRAY[2, 3, 4]) s "
               "WHERE id = %s", (early,))
    pg.commit()
    book(pg, early, 6)
    body = listing(anon, date="2026-12-02", seats=2)
    assert [w["seats_left"] for w in body["windows"]] == [0] * 8
    near = body["nearest"]
    assert [(n["date"], n["start"][11:16]) for n in near] == [("2026-12-03", "11:30"), ("2026-12-03", "13:00"),
                                                              ("2026-12-03", "14:30")]
    for n in near:
        assert set(n) == {"id", "date", "start", "end", "seats_left", "already_started"}
        assert n["seats_left"] == 44
    # one Seat fits the 10:00 Window, so it comes first
    near = listing(anon, date="2026-12-02", seats=1)["nearest"]
    assert [(n["date"], n["start"][11:16], n["seats_left"]) for n in near][0] == ("2026-12-03", "10:00", 1)
    assert len(near) == 3


def test_nearest_is_returned_only_when_no_window_of_the_date_has_room(anon, pg):
    """The nearest search starts on the date itself, but a Window there with room means no nearest at all, so with
    no room on the date the nearest come from the following days, by start."""
    listing(anon)
    block_day(pg, "2026-12-05", saunas=(2, 3, 4))  # 7 Seats left in every Window of 12-05
    body = listing(anon, date="2026-12-05", seats=8)
    assert {w["seats_left"] for w in body["windows"]} == {7}
    assert [n["date"] for n in body["nearest"]] == ["2026-12-06"] * 3
    assert "nearest" not in listing(anon, date="2026-12-05", seats=7)  # room on the date: no nearest


def test_no_room_anywhere_in_the_horizon_returns_no_nearest(anon, pg):
    listing(anon)
    for i in range(29):
        block_day(pg, (dt.date(2026, 12, 1) + dt.timedelta(days=i)).isoformat())
    body = listing(anon, date="2026-12-10", seats=2)
    assert body["nearest"] == []


# ------------------------------------------------------------------ refusals write nothing


@pytest.mark.parametrize("params,fields", [
    (dict(date="2026-13-01"), ["date"]),
    (dict(date="2026-12-32"), ["date"]),
    (dict(date="2026-12-1"), ["date"]),
    (dict(date="01.12.2026"), ["date"]),
    (dict(date=""), ["date"]),
    (dict(date="2026-12-01T00:00:00"), ["date"]),
    (dict(date="2026-12-01\n"), ["date"]),
    (dict(date="٢٠٢٦-١٢-٠١"), ["date"]),  # digits, but not ASCII ones
    (dict(date="2026-12-01", seats=0), ["seats"]),
    (dict(date="2026-12-01", seats=11), ["seats"]),
    (dict(date="2026-12-01", seats="2.5"), ["seats"]),
    (dict(seats=""), ["seats"]),
    (dict(date="2026-12-01", sauna=1), ["sauna"]),
], ids=["month-13", "day-32", "short", "dotted", "empty", "datetime", "newline", "non-ascii", "seats-0", "seats-11",
        "seats-fraction", "seats-empty", "unknown"])
def test_a_malformed_value_is_422_and_nothing_is_written(anon, pg, params, fields):
    before = written(pg)
    r = anon.get("/api/windows", params=params)
    assert r.status_code == 422, r.text
    assert r.json() == {"detail": {"error": "invalid_input", "fields": fields}}
    assert written(pg) == before == (3, None, 0, 0)


@pytest.mark.parametrize("date", ["2026-11-30", "2026-12-30", "2027-06-01"], ids=["yesterday", "after", "far"])
def test_a_date_outside_the_horizon_is_409_and_nothing_is_written(anon, pg, date):
    before = written(pg)
    r = anon.get("/api/windows", params=dict(date=date, seats=2))
    assert r.status_code == 409, r.text
    assert r.json() == {"detail": {"error": "outside_horizon", "today": "2026-12-01", "horizon_end": "2026-12-29"}}
    assert written(pg) == before == (3, None, 0, 0)
    assert "set-cookie" not in r.headers


def test_the_horizon_edges_are_accepted(anon):
    assert anon.get("/api/windows", params=dict(date="2026-12-01")).status_code == 200
    assert anon.get("/api/windows", params=dict(date="2026-12-29")).status_code == 200


def test_a_shorter_horizon_moves_horizon_end(anon, pg):
    pg.execute("UPDATE settings SET booking_horizon_days = 7")
    pg.commit()
    body = listing(anon)
    assert (body["horizon_end"], body["horizon_days"]) == ("2026-12-08", 7)
    assert anon.get("/api/windows", params=dict(date="2026-12-09")).json()["detail"]["error"] == "outside_horizon"


def test_the_listing_needs_no_session_and_sets_no_cookie(anon, pg):
    r = anon.get("/api/windows", params=dict(date="2026-12-01", seats=2))
    assert r.status_code == 200
    assert "set-cookie" not in r.headers and not anon.cookies
    assert written(pg)[2] == 0
