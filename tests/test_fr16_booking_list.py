"""FR-16, FR-18, FR-3, AD-4, AD-5, RB-1: the Administrator's Booking list `GET /api/admin/bookings?date=YYYY-MM-DD`.

- It answers `{"today", "date", "windows"}`; without a date, `date` is the API's `today`. Every Window of the Venue
  date is listed in time order (bookable or not), with `seat_capacity`, `seats_booked` and `seats_left` from the store
  functions, and its Bookings (active and cancelled) oldest first with reference, name, email, Seats, `total_ore`,
  `created_at`, `status` and `history` (Story 4.2; the history itself is tested in `test_fr26_move.py`).
- Windows without Bookings have `bookings: []`; a date with no Windows (after the horizon) has `windows: []`.
- Seats left equals the Guest listing (`GET /api/windows`) after Guest-flow Bookings make one Window 42 of 44 and
  another full; a Booking made between two reads is on the second.
- A malformed date or an unknown field is `422 invalid_input` and writes nothing; an anonymous caller or a Guest
  session is `401 not_signed_in`. A read writes nothing apart from `ensure_generated()` (row counts and `xmin`).
- Stored text comes back as given (IV-5).
"""

from __future__ import annotations

import datetime as dt

import pytest

from client import api_client
from conftest import raw_booking

DAY = "2026-12-01"  # the Venue date of `world`'s three Windows and of its clock (EARLY)
NOT_SIGNED_IN = {"detail": {"error": "not_signed_in"}}


def booking_list(c, **params) -> dict:
    r = c.get("/api/admin/bookings", params=params)
    assert r.status_code == 200, r.text
    return r.json()


def book_seats(api, window_id: int, seats: int) -> list[str]:
    """Book `seats` in one Window through the Guest flow, at most 10 per Booking. Returns the references."""
    refs = []
    while seats:
        n = min(seats, 10)
        r = api.book(window_id, n)
        assert r.status_code == 201, r.text
        refs.append(r.json()["booking"]["reference"])
        seats -= n
    return refs


def written(pg) -> tuple:
    """Every row count the read could touch, and the `xmin` of every row of the tables it reads."""
    pg.rollback()
    row = pg.execute(
        "SELECT (SELECT count(*) FROM windows), (SELECT count(*) FROM bookings), (SELECT count(*) FROM outbox_emails), "
        "(SELECT count(*) FROM holds), (SELECT count(*) FROM payments), "
        "(SELECT array_agg(xmin::text ORDER BY id) FROM windows), "
        "(SELECT array_agg(xmin::text ORDER BY id) FROM bookings), "
        "(SELECT array_agg(xmin::text ORDER BY id) FROM outbox_emails), "
        "(SELECT xmin::text || windows_generated_through::text FROM settings)").fetchone()
    pg.rollback()
    return tuple(row)


# ------------------------------------------------------------------ the shape


def test_no_date_is_the_apis_today(admin):
    body = booking_list(admin)
    assert body["today"] == DAY and body["date"] == DAY
    assert set(body) == {"today", "date", "windows"}


def test_a_day_with_bookings_lists_every_window_in_order_and_bookings_oldest_first(admin, api, pg):
    first = book_seats(api, 2, 3)[0]
    raw = pg.execute(raw_booking() + " RETURNING reference", (2, 1)).fetchone()[0]
    pg.commit()
    second = book_seats(api, 2, 2)[0]
    body = booking_list(admin, date=DAY)
    ws = body["windows"]
    assert [w["id"] for w in ws][:3] == [1, 2, 3]
    starts = [w["start"] for w in ws]
    assert starts == sorted(starts)
    assert all(w["start"].startswith(DAY) for w in ws)
    assert ws[0]["start"] == "2026-12-01T10:00:00+01:00" and ws[0]["end"] == "2026-12-01T11:30:00+01:00"
    w2 = ws[1]
    assert set(w2) == {"id", "start", "end", "seat_capacity", "seats_booked", "seats_left", "bookings", "placement"}
    assert (w2["seat_capacity"], w2["seats_booked"], w2["seats_left"]) == (44, 6, 38)
    assert [b["reference"] for b in w2["bookings"]] == [first, raw, second]
    b = w2["bookings"][0]
    assert set(b) == {"reference", "kind", "name", "email", "seats", "sauna", "total_ore", "created_at", "status",
                      "cancelled_at", "cancel_cause", "cancel_remedy", "history"}  # Story 4.3: the cancellation columns
    assert (b["kind"], b["sauna"]) == ("seats", None)  # Story 5.2: a Whole-sauna booking names its Sauna instead
    assert (b["name"], b["email"], b["seats"], b["total_ore"]) == ("Test Guest", "guest@example.com", 3, 75000)
    assert (b["status"], b["history"]) == ("active", [])  # Story 4.2: status and Change history (FR-16)
    assert (b["cancelled_at"], b["cancel_cause"], b["cancel_remedy"]) == (None, None, None)
    created = dt.datetime.fromisoformat(b["created_at"])
    assert created.utcoffset() == dt.timedelta(hours=1)  # Venue time
    assert ws[0]["bookings"] == [] and ws[2]["bookings"] == []


def test_the_figures_come_from_the_store_functions(admin, api, pg):
    book_seats(api, 1, 4)
    assert api.post("/api/holds", json={"window_id": 1, "seats": 5}).status_code == 200  # held Seats count too
    w = booking_list(admin, date=DAY)["windows"][0]
    pg.rollback()
    cap, booked, left = pg.execute("SELECT window_open_capacity(1), window_booked_seats(1), seats_left(1)").fetchone()
    pg.rollback()
    assert (w["seat_capacity"], w["seats_booked"], w["seats_left"]) == (cap, booked, left) == (44, 4, 35)


def test_cancelled_bookings_are_listed_with_their_status_outside_the_seats_booked(admin, api, pg):
    """Story 4.2 (Lisa, 2026-11-24): a cancelled Booking stays in the list with its status; it takes no Seats."""
    ref = book_seats(api, 1, 2)[0]
    other = book_seats(api, 1, 3)[0]
    pg.execute("UPDATE bookings SET status = 'cancelled', cancelled_at = app_now(), cancel_cause = 'guest', cancel_remedy = 'voucher' WHERE reference = %s", (ref,))
    pg.commit()
    w = booking_list(admin, date=DAY)["windows"][0]
    assert [(b["reference"], b["status"]) for b in w["bookings"]] == [(ref, "cancelled"), (other, "active")]
    assert (w["seats_booked"], w["seats_left"]) == (3, 41)


def test_an_empty_day_lists_every_window_with_no_bookings(admin):
    ws = booking_list(admin, date=DAY)["windows"]
    assert len(ws) >= 3 and all(w["bookings"] == [] and w["seats_left"] == 44 for w in ws)


def test_a_date_after_the_horizon_has_no_windows(admin):
    body = booking_list(admin, date="2027-06-01")
    assert body == {"today": DAY, "date": "2027-06-01", "windows": []}


def test_a_past_date_is_allowed(admin):
    assert booking_list(admin, date="2026-11-30")["windows"] == []


# ------------------------------------------------------------------ equal to what Guests see (FR-3, FR-16)


def test_seats_left_equals_the_guest_listing_with_a_42_of_44_and_a_full_window(admin, api):
    book_seats(api, 1, 42)
    book_seats(api, 2, 44)
    mine = {w["id"]: w for w in booking_list(admin, date=DAY)["windows"]}
    r = api.get("/api/windows", params={"date": DAY})
    assert r.status_code == 200, r.text
    guest = {w["id"]: w["seats_left"] for w in r.json()["windows"]}
    assert (mine[1]["seats_booked"], mine[1]["seats_left"]) == (42, 2)
    assert (mine[2]["seats_booked"], mine[2]["seats_left"]) == (44, 0)
    assert len(guest) >= 3
    for wid, left in guest.items():
        assert mine[wid]["seats_left"] == left, wid


def test_a_booking_made_between_two_reads_is_on_the_second(admin, api):
    assert booking_list(admin, date=DAY)["windows"][2]["bookings"] == []
    ref = book_seats(api, 3, 2)[0]
    assert [b["reference"] for b in booking_list(admin, date=DAY)["windows"][2]["bookings"]] == [ref]


def test_stored_text_comes_back_as_given(admin, pg):
    name, email = "<script>alert(1)</script>", "x'); DROP TABLE bookings; --"
    pg.execute("INSERT INTO bookings (window_id, seats, reference, name, email, price_per_seat_ore, total_ore) "
               "VALUES (1, 1, 'HHHHHHHH', %s, %s, 25000, 25000)", (name, email))
    pg.commit()
    b = booking_list(admin, date=DAY)["windows"][0]["bookings"][0]
    assert (b["name"], b["email"]) == (name, email)


# ------------------------------------------------------------------ reads write nothing (AD-4)


def test_a_read_writes_nothing_but_generation(admin, api, pg):
    book_seats(api, 1, 2)
    booking_list(admin, date=DAY)  # generation happens here, once
    before = written(pg)
    booking_list(admin, date=DAY)
    booking_list(admin)
    booking_list(admin, date="2027-06-01")
    assert written(pg) == before


# ------------------------------------------------------------------ refused requests (FR-18, RB-1)


@pytest.mark.parametrize("params", [{"date": "2026-1-1"}, {"date": "x"}, {"date": "2026-02-30"}, {"foo": "1"},
                                    {"date": DAY, "seats": "2"}],
                         ids=["short", "word", "no-such-day", "unknown", "seats"])
def test_a_malformed_query_is_422_and_writes_nothing(admin, pg, params):
    before = written(pg)
    r = admin.get("/api/admin/bookings", params=params)
    assert r.status_code == 422 and r.json()["detail"]["error"] == "invalid_input", r.text
    assert written(pg) == before


def test_an_anonymous_caller_gets_401_and_nothing(world, pg):
    before = written(pg)
    with api_client(world, session=False) as anon:
        r = anon.get("/api/admin/bookings", params={"date": DAY})
    assert r.status_code == 401 and r.json() == NOT_SIGNED_IN
    assert written(pg) == before


def test_a_guest_session_gets_401_and_nothing(api, pg):
    book_seats(api, 1, 2)
    before = written(pg)
    r = api.get("/api/admin/bookings", params={"date": DAY})
    assert r.status_code == 401 and r.json() == NOT_SIGNED_IN
    assert written(pg) == before
