"""FR-29 / FR-30 / FR-8 / FR-28 / AD-9 / AD-23 / AD-24 (Story 5.2): book and pay for a Private sauna, against the real API.

`POST /api/bookings` with `kind: 'whole'`, `window_id`, `sauna_id`, name, email and an `Idempotency-Key` runs
`services.whole.create` in one `db.run`: the charge is decided before `lock_windows`, then the key read,
`outside_horizon`, `deadline_passed`, the Booking (`kind = 'whole'`, `total_ore = whole_price_ore`,
`price_per_seat_ore` NULL, the 72-hour Whole-sauna Cutoff) and its `whole_bookings` row, the `payments` rows, the
Manage token and the confirmation email. FR-29 is judged again by the store at the capacity row; in this action
`whole_bookable`, `booked_within_capacity` and the `(window_id, sauna_id)` key are `409 sauna_unavailable`, and nothing
is charged, written or emailed. No Hold is read, released or written.

The test Saunas are Rauha 7, Loyly 10, Kajo 12 and Lumo 15 in Fill order (`world`), priced as the seed: Rauha NOK 1850,
Loyly NOK 2600, Kajo NOK 3150, Lumo NOK 3950. Catalogue examples are named by ID (B7, C1); C1 runs 100 times.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import uuid

import pytest

from booking_platform.services import whole as whole_service
from booking_platform.services.booking import request_hash as seat_hash
from client import GUEST, api_client
from conftest import clear, raw_booking, raw_whole, state
from test_fr10_through_the_api import guests, parallel
from test_fr25_manage_link import BEFORE, NOT_FOUND, TOKEN, open_link, rows
from test_fr26_move import DAY, before_cutoff, everything, guest  # noqa: F401
from test_fr27_voucher_for_seats import ledger
from test_fr28_voucher import balance, payments_of, voucher, voucher_id

ROUNDS = 100  # FR-11 repetitions
KAJO, LUMO, RAUHA = 3, 4, 1
UNAVAILABLE = {"detail": {"error": "sauna_unavailable"}}
SIMULATED = "Simulated payment: no money moves"
TERMS_WHOLE = ["A booking for a fixed date cannot be withdrawn.",
               "Up to 72 hours before the session starts, you can cancel for a refund or a voucher, or move the booking "
               "to another session.",
               "If Saunalöyly cancels your session, you choose a refund or a voucher."]


def whole_body(window_id, sauna_id, **fields) -> dict:
    return {"kind": "whole", "window_id": window_id, "sauna_id": sauna_id, **GUEST, **fields}


def book_whole(client, window_id: int, sauna_id: int, *, key: str | None = None, **fields):
    """`POST /api/bookings` for a Whole-sauna booking, with a new `Idempotency-Key` unless `key` is given."""
    return client.post("/api/bookings", json=whole_body(window_id, sauna_id, **fields),
                       headers={"Idempotency-Key": key or str(uuid.uuid4())})


def quote_whole(client, code, window_id: int = 1, sauna_id: int = KAJO, **extra):
    return client.post("/api/vouchers/quote", json={"code": code, "kind": "whole", "window_id": window_id,
                                                     "sauna_id": sauna_id, **extra})


def counts(pg) -> dict:
    pg.rollback()
    row = pg.execute("SELECT (SELECT count(*) FROM bookings), (SELECT count(*) FROM whole_bookings), "
                     "(SELECT count(*) FROM payments), (SELECT count(*) FROM outbox_emails), "
                     "(SELECT count(*) FROM idempotency_keys), (SELECT count(*) FROM access_tokens)").fetchone()
    pg.rollback()
    return dict(bookings=row[0], whole=row[1], payments=row[2], emails=row[3], keys=row[4], tokens=row[5])


NOTHING = dict(bookings=0, whole=0, payments=0, emails=0, keys=0, tokens=0)
ONE = dict(bookings=1, whole=1, payments=1, emails=1, keys=1, tokens=1)


def left(c, wid: int = 1) -> int:
    return c.get(f"/api/windows/{wid}").json()["seats_left"]


# ------------------------------------------------------------------ the happy path


def test_paying_creates_the_whole_sauna_booking_its_capacity_row_one_charge_one_email_and_one_key(api, world, pg):
    key = str(uuid.uuid4())
    r = book_whole(api, 1, KAJO, key=key)
    assert r.status_code == 201, r.text
    body = r.json()
    assert set(body) == {"booking", "emails"}
    b = body["booking"]
    assert set(b) == {"reference", "kind", "date", "start", "end", "seats", "price_per_seat_ore", "sauna", "total_ore",
                      "name", "email", "status", "paid"}
    assert (b["kind"], b["sauna"], b["seats"], b["price_per_seat_ore"]) == ("whole", {"id": 3, "name": "Kajo"}, None,
                                                                            None)
    assert (b["total_ore"], b["paid"]) == (315000, {"voucher_ore": 0, "card_ore": 315000})
    assert (b["date"], b["start"], b["end"]) == ("2026-12-01", "2026-12-01T10:00:00+01:00",
                                                 "2026-12-01T11:30:00+01:00")
    assert (b["name"], b["email"], b["status"]) == ("Test Guest", "guest@example.com", "active")
    assert "capacity" not in json.dumps(body).lower()  # never the Sauna's Capacity (AD-23)
    assert counts(pg) == ONE

    row = rows(pg, "SELECT b.kind, b.sauna_id, b.seats, b.price_per_seat_ore, b.total_ore, b.cutoff, b.session_id, "
                   "b.entry_time = b.created_at, wb.window_id, wb.sauna_id, p.direction, p.method, p.amount_ore, "
                   "k.key::text, k.endpoint, k.booking_id = b.id, o.booking_id = b.id "
                   "FROM bookings b JOIN whole_bookings wb ON wb.booking_id = b.id "
                   "JOIN payments p ON p.booking_id = b.id JOIN idempotency_keys k ON k.booking_id = b.id "
                   "JOIN outbox_emails o ON o.booking_id = b.id")
    assert row == [("whole", 3, None, None, 315000, dt.timedelta(hours=72), api.session_id, True, 1, 3,
                    "charge", "card", 315000, key, "POST /api/bookings", True, True)]
    assert left(api) == 32  # Kajo's 12 Seats are gone from the Window at once (AD-5)
    assert api.get(f"/api/bookings/{b['reference']}/confirmation").json() == body


def test_the_email_names_the_sauna_and_the_whole_sauna_terms(api, world):
    body = book_whole(api, 1, KAJO).json()
    ref = body["booking"]["reference"]
    [email] = body["emails"]
    assert email["subject"] == f"Booking confirmed: {ref}"
    lines = email["body"].split("\n")
    at = lines.index(f"Booking reference: {ref}")
    assert lines[at:at + 6] == [f"Booking reference: {ref}", "Date: Tuesday 1 December 2026", "Session: 10:00–11:30",
                                "Sauna: Kajo", "Total: NOK 3150 incl. VAT", "Email: guest@example.com"]
    assert not any(line.startswith("Seats") for line in lines)
    assert not any("Holds" in line or "capacity" in line.lower() for line in lines)  # never the Sauna's Capacity
    assert not any("12" in line for line in lines[:lines.index("Manage your booking")])
    terms = lines.index("Booking terms")
    assert lines[terms + 1:terms + 4] == TERMS_WHOLE
    assert "Keep your booking reference and give it at reception when you arrive." in lines
    manage = lines.index("Manage your booking")
    assert TOKEN.search(lines[manage + 1]) and lines[manage + 1].startswith(f"{world}/manage#t=")
    assert lines[manage + 3] == "Before you come" and lines[manage + 4].startswith(world + "/")
    assert lines[-1] == SIMULATED


def test_no_hold_is_read_released_or_written(api, pg):
    assert api.post("/api/holds", json=dict(window_id=1, seats=2)).status_code == 200
    held = rows(pg, "SELECT id, seats, session_id FROM holds")
    assert book_whole(api, 1, LUMO).status_code == 201
    assert rows(pg, "SELECT id, seats, session_id FROM holds") == held


# ------------------------------------------------------------------ B7: Seats left falls by the Sauna's Seats


def test_b7_lumo_booked_whole_in_an_empty_window_leaves_29_seats(api, admin, pg):
    assert left(api) == 44
    assert book_whole(api, 1, LUMO).status_code == 201
    assert left(api) == 29  # one Window
    listing = api.get("/api/windows", params={"date": DAY}).json()
    assert {w["id"]: w["seats_left"] for w in listing["windows"] if w["id"] in (1, 2, 3)} == {1: 29, 2: 44, 3: 44}
    day = admin.get("/api/admin/bookings", params={"date": DAY}).json()
    figures = {w["id"]: (w["seat_capacity"], w["seats_booked"], w["seats_left"]) for w in day["windows"]
               if w["id"] in (1, 2, 3)}
    assert figures == {1: (29, 0, 29), 2: (44, 0, 44), 3: (44, 0, 44)}
    s = state(pg)
    assert s["cap"] == s["real_cap"] == 29 and s["left"] == 29
    # Seat bookings in the Window are now judged on 29 Seats (FR-13 E4); other Windows are unchanged
    for n in (10, 10, 9):
        assert api.book(1, n).status_code == 201
    r = api.book(1, 1)
    assert r.status_code == 409 and r.json() == {"detail": {"error": "no_seat_free", "seats_left": 0}}, r.text
    assert left(api, 2) == 44 and left(api, 3) == 44


# ------------------------------------------------------------------ the Sauna taken while the Guest typed (FR-29)


def _refused_and_nothing_written(api, pg, wid: int, sid: int) -> None:
    before = everything(pg)
    r = book_whole(api, wid, sid)
    assert r.status_code == 409 and r.json() == UNAVAILABLE, r.text
    assert everything(pg) == before


def test_a_pair_booked_whole_meanwhile_is_sauna_unavailable(api, pg):
    raw_whole(pg, 1, KAJO)
    _refused_and_nothing_written(api, pg, 1, KAJO)
    assert counts(pg) == dict(NOTHING, bookings=1, whole=1)  # only the raw one


def test_a_blocked_sauna_is_sauna_unavailable(api, pg):
    pg.execute("INSERT INTO blocks (sauna_id, during) SELECT %s, during FROM windows WHERE id = 1", (KAJO,))
    pg.commit()
    _refused_and_nothing_written(api, pg, 1, KAJO)


def test_seats_that_no_longer_fit_the_room_ahead_are_sauna_unavailable(api, pg):
    pg.execute(raw_booking(1, 20))  # [7, 10, 3, 0]: Kajo's Room ahead is 17
    pg.commit()
    _refused_and_nothing_written(api, pg, 1, KAJO)
    assert book_whole(api, 1, LUMO).status_code == 201  # Lumo's Room ahead (29) still fits


def test_held_seats_that_no_longer_fit_are_sauna_unavailable(api, pg):
    """FR-29: Seats booked plus held. 20 held Seats (a raw Hold, AD-21) sit as [7, 10, 3, 0]."""
    pg.execute("INSERT INTO holds (window_id, seats, session_id, expires_at) "
               "VALUES (1, 20, NULL, app_now() + interval '5 minutes')")
    pg.commit()
    _refused_and_nothing_written(api, pg, 1, KAJO)


@pytest.mark.parametrize("change", ["UPDATE saunas SET whole_price_ore = NULL WHERE id = 3",
                                    "UPDATE saunas SET bookable_whole = false WHERE id = 3"],
                         ids=["no-price", "not-bookable-whole"])
def test_a_sauna_no_longer_offered_whole_is_sauna_unavailable(api, pg, change):
    pg.execute(change)
    pg.commit()
    _refused_and_nothing_written(api, pg, 1, KAJO)


def test_the_store_judges_fr29_after_the_lock_and_the_seat_flow_keeps_no_seat_free(api, pg):
    """The store's refusal names stay global for Seats: a full Window is `no_seat_free` for a Seat booking and
    `sauna_unavailable` for a Whole-sauna booking (the per-action mapping, AD-24)."""
    pg.execute(raw_booking(1, 44))
    pg.commit()
    r = api.book(1, 1)
    assert r.status_code == 409 and r.json() == {"detail": {"error": "no_seat_free", "seats_left": 0}}
    r = book_whole(api, 1, LUMO)
    assert r.status_code == 409 and r.json() == UNAVAILABLE


# ------------------------------------------------------------------ the refusal order


def test_the_refusal_order_is_horizon_then_deadline_then_sauna_unavailable(guest, pg):
    late = pg.execute("INSERT INTO windows (during) VALUES (tstzrange('2027-03-01 09:00Z', '2027-03-01 10:30Z')) "
                      "RETURNING id").fetchone()[0]
    started = pg.execute("INSERT INTO windows (during) VALUES (tstzrange(%s, %s)) RETURNING id",
                         (BEFORE - dt.timedelta(minutes=30), BEFORE + dt.timedelta(minutes=60))).fetchone()[0]
    pg.commit()
    for wid in (late, started, 1):
        raw_whole(pg, wid, KAJO)  # taken in each Window
    before = everything(pg)
    for wid, code in ((late, "outside_horizon"), (started, "deadline_passed"), (1, "sauna_unavailable")):
        r = book_whole(guest, wid, KAJO)
        assert r.status_code == 409 and r.json()["detail"]["error"] == code, (wid, r.text)
    # a Voucher that could never be used changes nothing: the Sauna is refused first
    r = book_whole(guest, 1, KAJO, voucher_code="hello", voucher_part_ore=1000)
    assert r.status_code == 409 and r.json() == UNAVAILABLE, r.text
    assert everything(pg) == before


# ------------------------------------------------------------------ C1: two Guests pay for the same pair


def test_c1_two_parallel_payments_for_one_pair_have_exactly_one_winner(api, world, pg):
    """C1, FR-11 repetitions: exactly one Booking, the other `409 sauna_unavailable` with no charge, key or email;
    after each run one active capacity row for the pair, and the INV pair: Seats left = Seat capacity - Seats booked
    - held, and the stored counters equal the rows. 100 repetitions."""
    for r in range(ROUNDS):
        clear(pg)
        ca, cb = guests(world, 2)
        a, b = parallel([lambda: book_whole(ca, 1, KAJO), lambda: book_whole(cb, 1, KAJO)])
        loser = cb if a.status_code == 201 else ca
        lost = b if a.status_code == 201 else a
        loser_session = loser.session_id
        ca.close(), cb.close()
        assert sorted([a.status_code, b.status_code]) == [201, 409], (r, a.text, b.text)
        assert lost.json() == UNAVAILABLE, (r, lost.text)
        assert counts(pg) == ONE, r
        assert rows(pg, "SELECT count(*) FROM whole_bookings wb JOIN bookings b ON b.id = wb.booking_id "
                        "WHERE wb.window_id = 1 AND wb.sauna_id = 3 AND b.status = 'active'") == [(1,)], r
        assert rows(pg, "SELECT count(*) FROM bookings WHERE session_id = %s", (loser_session,)) == [(0,)], r
        s = state(pg)
        assert (s["cap"], s["booked"], s["held"]) == (s["real_cap"], s["real_booked"], s["real_held"]), (r, s)
        assert s["left"] == s["real_cap"] - s["real_booked"] - s["real_held"] == 32, (r, s)
        assert left(api) == 32, r


# ------------------------------------------------------------------ repeats (AD-9)


def test_a_repeat_returns_the_first_outcome_and_writes_nothing(api, pg):
    key = str(uuid.uuid4())
    first = book_whole(api, 1, KAJO, key=key)
    assert first.status_code == 201
    before = everything(pg)
    again = book_whole(api, 1, KAJO, key=key, name="Someone Else")  # the name is not part of the request
    assert again.status_code == 201 and again.json() == first.json()
    assert everything(pg) == before


def test_any_other_use_of_a_known_key_is_invalid_key(api, world, pg):
    key = str(uuid.uuid4())
    assert book_whole(api, 1, KAJO, key=key).status_code == 201
    before = everything(pg)
    for r in (book_whole(api, 1, LUMO, key=key),  # another Sauna
              book_whole(api, 2, KAJO, key=key),  # another Window
              api.book(1, 2, key=key)):  # Seats
        assert r.status_code == 409 and r.json() == {"detail": {"error": "invalid_key"}}, r.text
    with api_client(world) as other:  # another session
        r = book_whole(other, 1, KAJO, key=key)
        assert r.status_code == 409 and r.json() == {"detail": {"error": "invalid_key"}}, r.text
    seat_key = str(uuid.uuid4())
    assert api.book(2, 2, key=seat_key).status_code == 201
    r = book_whole(api, 2, KAJO, key=seat_key)  # a Seat key cannot book a Sauna
    assert r.status_code == 409 and r.json() == {"detail": {"error": "invalid_key"}}, r.text
    assert rows(pg, "SELECT count(*) FROM bookings WHERE kind = 'whole'") == [(1,)]
    assert everything(pg)[0][:1] == before[0][:1]  # the Whole-sauna booking is as it was


def test_the_request_hash_holds_kind_and_sauna_and_never_name_email_or_code():
    h = whole_service.request_hash(1, KAJO)
    expected = json.dumps({"endpoint": "POST /api/bookings", "kind": "whole", "sauna_id": 3, "window_id": 1},
                          sort_keys=True, separators=(",", ":"))
    assert h == hashlib.sha256(expected.encode()).digest()
    assert h != whole_service.request_hash(1, LUMO) != whole_service.request_hash(2, KAJO)
    assert whole_service.request_hash(1, KAJO, 1000) != h
    assert h not in {seat_hash(1, 3), seat_hash(1, 12)}


def test_a_refusal_stores_no_key_so_the_retry_runs_again(api, pg):
    key = str(uuid.uuid4())
    pg.execute("UPDATE saunas SET whole_price_ore = NULL WHERE id = 3")
    pg.commit()
    assert book_whole(api, 1, KAJO, key=key).status_code == 409
    pg.execute("UPDATE saunas SET whole_price_ore = 315000 WHERE id = 3")
    pg.commit()
    assert book_whole(api, 1, KAJO, key=key).status_code == 201


# ------------------------------------------------------------------ invalid input (FR-18, AD-16)


INVALID = [
    ({k: v for k, v in whole_body(1, KAJO).items() if k != "sauna_id"}, ["sauna_id"]),
    (whole_body(1, KAJO, seats=2), ["seats"]),
    (whole_body(1, KAJO, guest="x"), ["guest"]),
    (whole_body(1, KAJO, price_ore=1), ["price_ore"]),
    (whole_body(1, KAJO, email="no-at.example.com"), ["email"]),
    (whole_body(1, KAJO, name=""), ["name"]),
    (whole_body(1, KAJO, name="Ada\x00"), ["name"]),
    (whole_body(1, 0), ["sauna_id"]),
    (whole_body(1, 2**31), ["sauna_id"]),
    (whole_body(1, "Kajo"), ["sauna_id"]),
    (whole_body(1, None), ["sauna_id"]),
    (whole_body(0, KAJO), ["window_id"]),
    (whole_body(1, KAJO, voucher_code="ABCD"), ["body"]),  # a Voucher code without its part
    ({**whole_body(1, KAJO), "kind": "private"}, ["kind", "sauna_id", "seats"]),
    ({**whole_body(1, KAJO), "kind": None}, ["kind", "sauna_id", "seats"]),
    ({**GUEST, "window_id": 1, "seats": 2, "sauna_id": 3}, ["sauna_id"]),  # a Seat booking names no Sauna
]


@pytest.mark.parametrize("body,fields", INVALID, ids=[f"{i}-{f[0]}" for i, (_, f) in enumerate(INVALID)])
def test_invalid_input_is_422_and_writes_nothing(api, pg, body, fields):
    r = api.post("/api/bookings", json=body, headers={"Idempotency-Key": str(uuid.uuid4())})
    assert r.status_code == 422, r.text
    assert r.json() == {"detail": {"error": "invalid_input", "fields": fields}}
    assert counts(pg) == NOTHING


def test_an_unknown_sauna_or_window_is_404_and_writes_nothing(api, pg):
    for wid, sid in ((1, 99), (99999, KAJO)):
        r = book_whole(api, wid, sid)
        assert r.status_code == 404 and r.json() == NOT_FOUND, r.text
    assert counts(pg) == NOTHING


def test_paying_needs_a_session(world, pg):
    with api_client(world, session=False) as c:
        r = book_whole(c, 1, KAJO)
    assert r.status_code == 401 and r.json() == {"detail": {"error": "no_session"}}
    assert counts(pg) == NOTHING


# ------------------------------------------------------------------ paying with a Voucher (FR-28, AD-30)


def test_the_quote_is_against_the_whole_price_and_writes_nothing(guest, pg):
    code = voucher(guest)  # NOK 250
    before = everything(pg)
    r = quote_whole(guest, code)
    assert r.status_code == 200 and r.json() == {"voucher_part_ore": 25000, "card_part_ore": 290000}, r.text
    assert quote_whole(guest, code, sauna_id=LUMO).json() == {"voucher_part_ore": 25000, "card_part_ore": 370000}
    assert quote_whole(guest, "hello").json() == {"detail": {"error": "voucher_invalid"}}
    assert quote_whole(guest, code, sauna_id=99).json() == NOT_FOUND
    assert quote_whole(guest, code, window_id=99999).json() == NOT_FOUND
    pg.execute("UPDATE saunas SET whole_price_ore = NULL WHERE id = 2")
    pg.commit()
    r = quote_whole(guest, code, sauna_id=2)
    assert r.status_code == 409 and r.json() == UNAVAILABLE
    for bad, fields in (({"code": code, "kind": "whole", "window_id": 1}, ["sauna_id"]),
                        ({"code": code, "kind": "whole", "window_id": 1, "sauna_id": 3, "seats": 2}, ["seats"])):
        r = guest.post("/api/vouchers/quote", json=bad)
        assert r.status_code == 422 and r.json()["detail"]["fields"] == fields, r.text
    pg.execute("UPDATE saunas SET whole_price_ore = 260000 WHERE id = 2")
    pg.commit()
    assert everything(pg) == before


def test_a_partial_voucher_pays_with_a_voucher_row_and_a_card_row(guest, pg):
    code = voucher(guest)  # NOK 250
    vid = voucher_id(pg, code)
    r = book_whole(guest, 1, KAJO, voucher_code=code, voucher_part_ore=25000)
    assert r.status_code == 201, r.text
    b = r.json()["booking"]
    assert (b["total_ore"], b["paid"]) == (315000, {"voucher_ore": 25000, "card_ore": 290000})
    assert payments_of(pg, b["reference"]) == [("charge", "voucher", 25000, vid), ("charge", "card", 290000, None)]
    assert ledger(pg, b["reference"]) == 315000  # AD-31: the charges add up to the total
    assert balance(pg, code) == 0
    lines = r.json()["emails"][0]["body"].split("\n")
    at = lines.index("Total: NOK 3150 incl. VAT")
    assert lines[at + 1:at + 4] == ["Paid with voucher: NOK 250", "Paid by card: NOK 2900", "Email: guest@example.com"]
    assert lines[-1] == SIMULATED


def test_a_voucher_that_covers_the_total_pays_alone(guest, pg):
    code = voucher(guest, 8)  # NOK 2000, more than Rauha's NOK 1850
    vid = voucher_id(pg, code)
    r = book_whole(guest, 1, RAUHA, voucher_code=code, voucher_part_ore=185000)
    assert r.status_code == 201, r.text
    b = r.json()["booking"]
    assert b["paid"] == {"voucher_ore": 185000, "card_ore": 0}
    assert payments_of(pg, b["reference"]) == [("charge", "voucher", 185000, vid)]  # no card row
    assert balance(pg, code) == 15000
    assert SIMULATED not in r.json()["emails"][0]["body"].split("\n")


def test_a_voucher_part_that_does_not_fit_the_price_is_voucher_invalid(guest, pg):
    code = voucher(guest)
    before = everything(pg)
    for part in (25000 + 1, 315000 + 1):
        r = book_whole(guest, 1, KAJO, voucher_code=code, voucher_part_ore=part)
        assert r.status_code == 409 and r.json() == {"detail": {"error": "voucher_invalid"}}, r.text
    assert everything(pg) == before and balance(pg, code) == 25000


# ------------------------------------------------------------------ the Booking list (FR-16)


def test_the_booking_list_shows_the_sauna_in_place_of_seats(api, admin, pg):
    ref = book_whole(api, 1, KAJO).json()["booking"]["reference"]
    seat_ref = api.book(1, 2).json()["booking"]["reference"]
    day = admin.get("/api/admin/bookings", params={"date": DAY}).json()
    [w1] = [w for w in day["windows"] if w["id"] == 1]
    assert (w1["seat_capacity"], w1["seats_booked"], w1["seats_left"]) == (32, 2, 30)
    by_ref = {b["reference"]: b for b in w1["bookings"]}
    whole_row, seat_row = by_ref[ref], by_ref[seat_ref]
    assert (whole_row["kind"], whole_row["seats"], whole_row["sauna"], whole_row["total_ore"]) == (
        "whole", None, {"id": 3, "name": "Kajo"}, 315000)
    assert (whole_row["name"], whole_row["email"], whole_row["status"]) == ("Test Guest", "guest@example.com",
                                                                            "active")
    assert (seat_row["kind"], seat_row["seats"], seat_row["sauna"]) == ("seats", 2, None)


# ------------------------------------------------------------------ Manage before Story 5.3


def test_the_manage_link_opens_the_booking_and_seat_changes_refuse_it(before_cutoff, pg):
    with api_client(before_cutoff) as c:
        body = book_whole(c, 2, KAJO).json()
        ref = body["booking"]["reference"]
        token = TOKEN.search(body["emails"][0]["body"]).group(1)
        assert open_link(c, token).json() == {"reference": ref}
        read = c.get(f"/api/manage/{ref}")
        assert read.status_code == 200, read.text
        m = read.json()
        assert (m["kind"], m["seats"], m["sauna"], m["total_ore"], m["status"]) == (
            "whole", None, {"id": 3, "name": "Kajo"}, 315000, "active")
        assert m["history"] == [] and "capacity" not in json.dumps(m).lower()
        before = everything(pg)
        for path, payload in (("seats/move", {"window_id": 3, "seats": 1, "version": 0}),
                              ("seats/voucher", {"seats": 1, "version": 0})):
            r = c.post(f"/api/manage/{ref}/{path}", json=payload, headers={"Idempotency-Key": str(uuid.uuid4())})
            assert r.status_code == 404 and r.json() == NOT_FOUND, (path, r.text)
        assert everything(pg) == before
