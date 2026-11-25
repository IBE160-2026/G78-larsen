"""FR-28 / AD-30 / AD-13 / AD-31 / AD-9 (Story 4.4): pay for all or part of a Seat booking with a Voucher.

`POST /api/vouchers/quote {code, kind: 'seats', window_id, seats}` needs a session, takes no lock, writes nothing and
returns `{voucher_part_ore, card_part_ore}` (the Voucher part is the lesser of the balance and the total). `POST
/api/bookings` takes an optional `voucher_code` with the quoted `voucher_part_ore`: the card part is decided before the
lock (`charge()` only when it is above 0), and after the lock, the Window rules, capacity and the Booking insert, one
conditional UPDATE takes the part from the Voucher. The ledger gets `charge`/`voucher` (with the Voucher id) plus
`charge`/`card` for any rest. Every unusable code (unknown, malformed, longer than 32 characters, expired, used up, not
enough left, or a part that does not fit the total) is the same `409 voucher_invalid` with no facts, and nothing is
written. No response, log line or table holds the code, a balance or an expiry.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import threading
import time
import uuid

import psycopg
import pytest

from booking_platform.services import voucher as voucher_service
from client import COOKIE, ApiClient, _TLS, api_client
from conftest import clear, raw_booking, set_clock, start_backend
from test_fr10_through_the_api import guests, parallel
from test_fr25_manage_link import BEFORE, TOKEN, open_link, rows
from test_fr26_move import DAY, before_cutoff, everything, fill, guest, left_in, move  # noqa: F401
from test_fr27_voucher_for_seats import LAST_VALID, code_of, give_up, ledger, not_in_store, opened, walk

ROUNDS = 100  # FR-11 repetitions
INVALID = {"detail": {"error": "voucher_invalid"}}
SIMULATED = "Simulated payment: no money moves"


def quote(client, code, window_id: int = 1, seats: int = 2, **extra):
    return client.post("/api/vouchers/quote", json={"code": code, "kind": "seats", "window_id": window_id,
                                                     "seats": seats, **extra})


def pay(client, window_id: int, seats: int, code, part, key: str | None = None):
    """`POST /api/bookings` with a Voucher."""
    return client.book(window_id, seats, key=key, voucher_code=code, voucher_part_ore=part)


def voucher(client, seats_given_up: int = 1, window_id: int = 2) -> str:
    """A Voucher worth `seats_given_up` x NOK 250 from a give-up through the Manage link; its displayed code."""
    ref, _ = opened(client, window_id, seats_given_up + 1)
    r = give_up(client, ref, seats_given_up)
    assert r.status_code == 200, r.text
    return code_of(r.json()["emails"][0]["body"])


def balance(pg, code: str) -> int:
    h = voucher_service.code_hash(voucher_service.normalise(code))
    return rows(pg, "SELECT balance_ore FROM vouchers WHERE code_hash = %s", (h,))[0][0]


def voucher_id(pg, code: str) -> int:
    h = voucher_service.code_hash(voucher_service.normalise(code))
    return rows(pg, "SELECT id FROM vouchers WHERE code_hash = %s", (h,))[0][0]


def all_vouchers(pg) -> list:
    return rows(pg, "SELECT id, balance_ore, value_ore, expires_at FROM vouchers ORDER BY id")


def payments_of(pg, ref: str) -> list:
    return rows(pg, "SELECT p.direction, p.method, p.amount_ore, p.voucher_id FROM payments p "
                    "JOIN bookings b ON b.id = p.booking_id WHERE b.reference = %s ORDER BY p.id", (ref,))


def typed(code: str) -> str:
    """The code as a Guest might type it: lower case, spaces for some hyphens, look-alike letters for 1 and 0."""
    raw = code.replace("-", "")
    swapped = raw.replace("1", "l").replace("0", "o").lower()
    return f"{swapped[:4]} {swapped[4:8]}-{swapped[8:12]} {swapped[12:]}"


# ------------------------------------------------------------------ normalisation (AD-30)


@pytest.mark.parametrize(("text", "expected"), [
    ("ABCD-EFGH-JKMN-PQRS", "ABCDEFGHJKMNPQRS"),
    ("abcd efgh-ijkl-mnop", "ABCDEFGH1JK1MN0P"),
    ("0123456789ABCDEF", "0123456789ABCDEF"),
    ("oOiIlL0123456789", "001111" + "0123456789"),
    ("  abcd-efgh-jkmn-pqrs  ", "ABCDEFGHJKMNPQRS"),
    ("a-b-c-d-e-f-g-h-j-k-m-n-p-q-r-s", "ABCDEFGHJKMNPQRS"),  # 31 characters: still at most 32
    ("ABCD-EFGH-JKMN-PQR", None),  # 15 characters
    ("ABCD-EFGH-JKMN-PQRST", None),  # 17 characters
    ("ABCD-EFGH-JKMN-PQRU", None),  # U is not Crockford
    ("ABCD_EFGH_JKMN_PQRS", None),
    ("ABCD\tEFGH\tJKMN\tPQRS", None),  # only spaces and hyphens are removed
    ("ÅBCD-EFGH-JKMN-PQRS", None),
    ("abcd-efgh-jkmn-pqrs" + " " * 14, None),  # 33 characters, even though it would normalise
    ("", None),
    ("-" * 32, None),
    (None, None),
    (1234567890123456, None),
    (["ABCDEFGHJKMNPQRS"], None),
])
def test_normalise(text, expected):
    assert voucher_service.normalise(text) == expected


def test_a_typed_code_hashes_like_the_issued_code(guest, pg):
    code = voucher(guest)
    raw = code.replace("-", "")
    assert voucher_service.normalise(code) == voucher_service.normalise(typed(code)) == raw
    r = quote(guest, typed(code), seats=1)
    assert r.status_code == 200 and r.json() == {"voucher_part_ore": 25000, "card_part_ore": 0}, r.text


# ------------------------------------------------------------------ the quote


def test_the_quote_gives_the_parts_and_writes_nothing(guest, pg, backend):
    small = voucher(guest, 1)  # NOK 250
    large = voucher(guest, 2)  # NOK 500
    before, vouchers_before = everything(pg), all_vouchers(pg)
    cases = [(small, 2, {"voucher_part_ore": 25000, "card_part_ore": 25000}),
             (small, 1, {"voucher_part_ore": 25000, "card_part_ore": 0}),
             (large, 1, {"voucher_part_ore": 25000, "card_part_ore": 0}),
             (large, 3, {"voucher_part_ore": 50000, "card_part_ore": 25000})]
    for code, seats, parts in cases:
        r = quote(guest, code, seats=seats)
        assert r.status_code == 200 and r.json() == parts, r.text
    assert everything(pg) == before and all_vouchers(pg) == vouchers_before
    # no balance, value or expiry: a NOK 500 Voucher quoted for NOK 250 says only what it pays
    body = quote(guest, large, seats=1).json()
    assert set(body) == {"voucher_part_ore", "card_part_ore"} and 50000 not in body.values()
    for code in (small, large):
        raw = code.replace("-", "")
        assert code not in backend.output() and raw not in backend.output()


def test_the_quote_takes_no_lock(guest, pg):
    code = voucher(guest)
    vid = voucher_id(pg, code)
    pg.rollback()
    # another transaction holds the Window lock and the Voucher row: the quote answers at once
    pg.execute("SELECT lock_windows(ARRAY[1])")
    pg.execute("SELECT id FROM vouchers WHERE id = %s FOR UPDATE", (vid,))
    try:
        started = time.monotonic()
        r = quote(guest, code, seats=2)
        assert r.status_code == 200, r.text
        assert time.monotonic() - started < 5
    finally:
        pg.rollback()


def test_every_unusable_code_is_the_same_voucher_invalid(guest, pg):
    code = voucher(guest)  # NOK 250, used up below
    used_up = voucher(guest)
    assert pay(guest, 1, 1, used_up, 25000).status_code == 201
    assert balance(pg, used_up) == 0
    unknown = voucher_service.display(voucher_service.new_code())
    before, vouchers_before = everything(pg), all_vouchers(pg)
    answers = [quote(guest, unknown), quote(guest, "hello"), quote(guest, ""), quote(guest, used_up),
               quote(guest, code + " " * 14),  # 33 characters
               quote(guest, "x" * 1024)]
    for r in answers:
        assert r.status_code == 409 and r.json() == INVALID, r.text
    assert len({r.content for r in answers}) == 1  # byte for byte the same answer
    assert everything(pg) == before and all_vouchers(pg) == vouchers_before


def test_an_expired_code_is_voucher_invalid_from_its_expiry(before_cutoff, guest, pg):
    code = voucher(guest)
    # issued at BEFORE (Venue date 30 November 2026): valid through 30 November 2027, so until 1 December 00:00 Oslo
    expiry = dt.datetime(2027, 11, 30, 23, 0, tzinfo=dt.timezone.utc)
    set_clock(pg, expiry - dt.timedelta(minutes=1))
    with api_client(before_cutoff) as later:  # a session opened a year on
        assert quote(later, code, seats=1).json() == {"voucher_part_ore": 25000, "card_part_ore": 0}
        set_clock(pg, expiry)
        r = quote(later, code, seats=1)
        assert r.status_code == 409 and r.json() == INVALID
    assert balance(pg, code) == 25000


def test_the_quote_needs_a_session_and_a_known_window(before_cutoff, guest, pg):
    code = voucher(guest)
    with api_client(before_cutoff, session=False) as anon:
        r = quote(anon, code)
        assert r.status_code == 401 and r.json() == {"detail": {"error": "no_session"}}
    r = quote(guest, code, window_id=999_999)
    assert r.status_code == 404 and r.json() == {"detail": {"error": "not_found"}}


@pytest.mark.parametrize("body", [
    {"code": "x" * 1025, "kind": "seats", "window_id": 1, "seats": 1},
    {"code": 1234, "kind": "seats", "window_id": 1, "seats": 1},
    {"code": None, "kind": "seats", "window_id": 1, "seats": 1},
    {"code": "ABCD", "kind": "whole", "window_id": 1, "seats": 1},  # Whole-sauna quotes are Epic 5
    {"code": "ABCD", "window_id": 1, "seats": 1},
    {"code": "ABCD", "kind": "seats", "window_id": 1, "seats": 11},
    {"code": "ABCD", "kind": "seats", "window_id": 0, "seats": 1},
    {"code": "ABCD", "kind": "seats", "window_id": 1, "seats": 1, "balance": 1},
])
def test_a_quote_of_the_wrong_shape_is_422(guest, body):
    r = guest.post("/api/vouchers/quote", json=body)
    assert r.status_code == 422 and r.json()["detail"]["error"] == "invalid_input", r.text


def test_a_quote_from_another_origin_is_403(guest):
    r = guest.post("/api/vouchers/quote", json={"code": "ABCD", "kind": "seats", "window_id": 1, "seats": 1},
                   headers={"Origin": "https://evil.example"})
    assert r.status_code == 403


# ------------------------------------------------------------------ paying with a Voucher


def test_a_partial_payment_charges_the_voucher_and_the_card(guest, admin, pg, backend):
    code = voucher(guest)  # NOK 250
    vid = voucher_id(pg, code)
    assert quote(guest, code, seats=2).json() == {"voucher_part_ore": 25000, "card_part_ore": 25000}
    r = pay(guest, 1, 2, code, 25000)
    assert r.status_code == 201, r.text
    body = r.json()
    b = body["booking"]
    assert (b["seats"], b["price_per_seat_ore"], b["total_ore"]) == (2, 25000, 50000)
    assert b["paid"] == {"voucher_ore": 25000, "card_ore": 25000}
    ref = b["reference"]
    assert payments_of(pg, ref) == [("charge", "voucher", 25000, vid), ("charge", "card", 25000, None)]
    assert ledger(pg, ref) == 50000 == b["total_ore"]  # AD-31: the charges add up to the total
    assert balance(pg, code) == 0
    # the email: the payment rows after the total, the payment note kept (a card part was paid)
    [email] = body["emails"]
    lines = email["body"].split("\n")
    at = lines.index("Total: NOK 500 incl. VAT")
    assert lines[at + 1:at + 4] == ["Paid with voucher: NOK 250", "Paid by card: NOK 250", "Email: guest@example.com"]
    assert lines[-1] == SIMULATED
    # the confirmation read shows the same, and the Booking list the stored total
    assert guest.get(f"/api/bookings/{ref}/confirmation").json() == body
    listing = admin.get("/api/admin/bookings", params={"date": DAY}).json()
    [listed] = [x for w in listing["windows"] for x in w["bookings"] if x["reference"] == ref]
    assert listed["total_ore"] == 50000
    # the code is in no response, table or log line
    raw = code.replace("-", "")
    for text in walk(body):
        assert raw not in text.replace("-", "")
    assert raw not in json.dumps(listing)
    not_in_store(pg, code, raw)
    assert code not in backend.output() and raw not in backend.output()


def test_a_voucher_that_covers_the_total_pays_alone_and_keeps_the_rest(guest, pg):
    code = voucher(guest, 2)  # NOK 500
    vid = voucher_id(pg, code)
    r = pay(guest, 1, 1, code, 25000)
    assert r.status_code == 201, r.text
    b = r.json()["booking"]
    assert (b["total_ore"], b["paid"]) == (25000, {"voucher_ore": 25000, "card_ore": 0})
    assert payments_of(pg, b["reference"]) == [("charge", "voucher", 25000, vid)]  # no card row
    assert ledger(pg, b["reference"]) == 25000
    assert balance(pg, code) == 25000  # the rest stays on the Voucher until it expires
    lines = r.json()["emails"][0]["body"].split("\n")
    at = lines.index("Total: NOK 250 incl. VAT")
    assert lines[at + 1:at + 3] == ["Paid with voucher: NOK 250", "Email: guest@example.com"]
    assert not any(line.startswith("Paid by card") for line in lines)
    assert SIMULATED not in lines  # no card part: no payment note
    assert lines[-2] == "Before you come"
    # the rest pays for another Booking, then the Voucher is used up
    assert pay(guest, 1, 1, typed(code), 25000).status_code == 201
    assert balance(pg, code) == 0
    r = pay(guest, 1, 1, code, 25000)
    assert r.status_code == 409 and r.json() == INVALID


def test_without_a_voucher_nothing_changes(guest, pg):
    r = guest.book(1, 2)
    assert r.status_code == 201
    b = r.json()["booking"]
    assert b["paid"] == {"voucher_ore": 0, "card_ore": 50000}
    lines = r.json()["emails"][0]["body"].split("\n")
    assert not any(line.startswith("Paid ") for line in lines) and lines[-1] == SIMULATED


def test_without_a_card_part_charge_is_not_called(guest, pg, database, tmp_path):
    """With `payment = "fail"`, a Voucher that covers the total still books (no charge() at all); one that leaves a
    card part is `payment_failed` before the lock, and the Voucher keeps its balance."""
    whole = voucher(guest, 2)
    partial = voucher(guest, 1)
    b = start_backend(database, tmp_path, name="payment-fail", switches='payment = "fail"\n', sample_bookings=False)
    try:
        with ApiClient(base_url=b.base, timeout=60, headers={"Origin": b.base}, verify=_TLS) as c:
            c.cookies.set(COOKIE, guest.token, domain="127.0.0.1")
            r = pay(c, 1, 2, partial, 25000)
            assert r.status_code == 409 and r.json() == {"detail": {"error": "payment_failed"}}, r.text
            r = pay(c, 1, 2, whole, 50000)
            assert r.status_code == 201, r.text
            assert r.json()["booking"]["paid"] == {"voucher_ore": 50000, "card_ore": 0}
    finally:
        b.stop()
    assert balance(pg, partial) == 25000 and balance(pg, whole) == 0


def test_the_request_hash_holds_the_voucher_part_and_never_the_code(guest, pg):
    code = voucher(guest)
    key = str(uuid.uuid4())
    assert pay(guest, 1, 2, code, 25000, key=key).status_code == 201
    stored = rows(pg, "SELECT request_hash FROM idempotency_keys WHERE key = %s", (key,))[0][0]
    canonical = json.dumps({"endpoint": "POST /api/bookings", "seats": 2, "voucher_part_ore": 25000, "window_id": 1},
                           sort_keys=True, separators=(",", ":"))
    assert bytes(stored) == hashlib.sha256(canonical.encode()).digest()


# ------------------------------------------------------------------ every unusable Voucher writes nothing


def test_every_unusable_voucher_refuses_the_booking_and_writes_nothing(guest, pg):
    code = voucher(guest)  # NOK 250
    used_up = voucher(guest)
    assert pay(guest, 1, 1, used_up, 25000).status_code == 201
    unknown = voucher_service.display(voucher_service.new_code())
    left = left_in(guest, 1)
    before, vouchers_before = everything(pg), all_vouchers(pg)
    answers = [
        pay(guest, 1, 1, unknown, 25000),
        pay(guest, 1, 1, "hello", 25000),
        pay(guest, 1, 1, code + " " * 14, 25000),  # 33 characters
        pay(guest, 1, 1, used_up, 25000),
        pay(guest, 1, 2, code, 50000),  # more than its balance
        pay(guest, 1, 1, code, 50000),  # tampered: the part is more than the total
        pay(guest, 1, 1, code, 2_147_483_647),
    ]
    for r in answers:
        assert r.status_code == 409 and r.json() == INVALID, r.text
    assert len({r.content for r in answers}) == 1
    assert everything(pg) == before and all_vouchers(pg) == vouchers_before
    assert left_in(guest, 1) == left  # no Seat taken
    # the same key books once a usable Voucher is sent (a refusal stores no key)
    key = str(uuid.uuid4())
    assert pay(guest, 1, 1, "hello", 25000, key=key).status_code == 409
    assert pay(guest, 1, 1, code, 25000, key=key).status_code == 201


def test_an_expired_voucher_refuses_the_booking(guest, pg):
    code = voucher(guest)
    # the Voucher expires an hour after BEFORE; Window 1 can still be booked then
    pg.execute("UPDATE vouchers SET expires_at = issued_at + interval '1 hour'")
    pg.commit()
    set_clock(pg, BEFORE + dt.timedelta(hours=2))
    before, vouchers_before = everything(pg), all_vouchers(pg)
    r = pay(guest, 1, 1, code, 25000)
    assert r.status_code == 409 and r.json() == INVALID, r.text
    assert everything(pg) == before and all_vouchers(pg) == vouchers_before


@pytest.mark.parametrize("body", [
    {"voucher_code": "ABCD"},  # both or neither
    {"voucher_part_ore": 25000},
    {"voucher_code": "ABCD", "voucher_part_ore": 0},
    {"voucher_code": "ABCD", "voucher_part_ore": -1},
    {"voucher_code": "ABCD", "voucher_part_ore": 2_147_483_648},
    {"voucher_code": 1234, "voucher_part_ore": 25000},
    {"voucher_code": "x" * 1025, "voucher_part_ore": 25000},
    {"voucher_code": ["ABCD", "EFGH"], "voucher_part_ore": 25000},  # one code per Booking
    {"voucher_codes": ["ABCD"], "voucher_part_ore": 25000},
])
def test_a_voucher_of_the_wrong_shape_is_422(guest, pg, body):
    before = everything(pg)
    r = guest.book(1, 1, **body)
    assert r.status_code == 422 and r.json()["detail"]["error"] == "invalid_input", r.text
    assert everything(pg) == before


# ------------------------------------------------------------------ refusals before the Voucher (store order)


def test_a_full_window_or_a_passed_deadline_refuses_first_and_spends_nothing(guest, pg):
    code = voucher(guest)
    fill(pg, 3, 44)
    before, vouchers_before = everything(pg), all_vouchers(pg)
    # capacity is judged before the Voucher, even for a code that could never be used
    for c in (code, "hello"):
        r = pay(guest, 3, 1, c, 25000)
        assert r.status_code == 409 and r.json() == {"detail": {"error": "no_seat_free", "seats_left": 0}}, r.text
    late = pg.execute("INSERT INTO windows (during) VALUES (tstzrange('2027-03-01 09:00Z', '2027-03-01 10:30Z')) "
                      "RETURNING id").fetchone()[0]
    started = pg.execute("INSERT INTO windows (during) VALUES (tstzrange(%s, %s)) RETURNING id",
                         (BEFORE - dt.timedelta(minutes=30), BEFORE + dt.timedelta(minutes=60))).fetchone()[0]
    pg.commit()
    before, vouchers_before = everything(pg), all_vouchers(pg)
    for c in (code, "hello"):
        r = pay(guest, started, 1, c, 25000)
        assert r.status_code == 409 and r.json()["detail"]["error"] == "deadline_passed", r.text
        r = pay(guest, late, 1, c, 25000)
        assert r.status_code == 409 and r.json()["detail"]["error"] == "outside_horizon", r.text
    assert everything(pg) == before and all_vouchers(pg) == vouchers_before
    assert balance(pg, code) == 25000


# ------------------------------------------------------------------ repeats (AD-9)


def test_a_repeat_returns_the_first_outcome_and_spends_once(guest, pg):
    code = voucher(guest, 2)  # NOK 500
    key = str(uuid.uuid4())
    first = pay(guest, 1, 1, code, 25000, key=key)
    assert first.status_code == 201, first.text
    before, vouchers_before = everything(pg), all_vouchers(pg)
    again = pay(guest, 1, 1, code, 25000, key=key)
    assert again.status_code == 201 and again.json() == first.json()
    assert everything(pg) == before and all_vouchers(pg) == vouchers_before
    assert balance(pg, code) == 25000
    # another body under the same key: another part, or no Voucher
    for r in (pay(guest, 1, 1, code, 20000, key=key), guest.book(1, 1, key=key)):
        assert r.status_code == 409 and r.json() == {"detail": {"error": "invalid_key"}}, r.text
    assert everything(pg) == before and balance(pg, code) == 25000


# ------------------------------------------------------------------ parallel spends (FR-11 repetitions)


def test_parallel_spends_never_take_the_balance_below_zero(world, pg):
    """One NOK 250 Voucher, two parallel bookings that each want all of it, 100 times: exactly one wins, the balance
    ends at 0, the Voucher charges never exceed its value, and the loser gets `voucher_invalid` and writes nothing."""
    set_clock(pg, BEFORE)
    for r in range(ROUNDS):
        clear(pg)
        pg.execute(raw_booking(2, 1))
        bid = rows(pg, "SELECT max(id) FROM bookings")[0][0]
        vid, code, _ = voucher_service.issue(pg, bid, 25000)
        pg.commit()
        ca, cb = guests(world, 2)
        a, b = parallel([lambda: pay(ca, 1, 1, code, 25000), lambda: pay(cb, 1, 1, code, 25000)])
        loser = cb if a.status_code == 201 else ca
        lost = b if a.status_code == 201 else a
        loser_session = loser.session_id
        ca.close(), cb.close()
        assert sorted([a.status_code, b.status_code]) == [201, 409], (r, a.text, b.text)
        assert lost.json() == INVALID, (r, lost.text)
        assert rows(pg, "SELECT balance_ore, value_ore FROM vouchers WHERE id = %s", (vid,)) == [(0, 25000)], r
        assert rows(pg, "SELECT COALESCE(sum(amount_ore), 0) FROM payments WHERE voucher_id = %s AND "
                        "direction = 'charge'", (vid,)) == [(25000,)], r
        assert rows(pg, "SELECT count(*) FROM bookings WHERE session_id IS NOT NULL") == [(1,)], r
        assert rows(pg, "SELECT count(*) FROM bookings WHERE session_id = %s", (loser_session,)) == [(0,)], r
        assert rows(pg, "SELECT count(*) FROM idempotency_keys WHERE session_id = %s", (loser_session,)) == [(0,)], r
        assert rows(pg, "SELECT count(*) FROM outbox_emails") == [(1,)], r
        assert rows(pg, "SELECT count(*) FROM payments") == [(1,)], r


def test_many_parallel_partial_spends_stay_within_the_balance(world, pg):
    """One NOK 1000 Voucher and six parallel bookings that each want NOK 250 of it (NOK 1500 together), 100 times, in
    two Windows: the Voucher charges add up to at most its value and the balance never goes below 0."""
    set_clock(pg, BEFORE)
    for r in range(ROUNDS):
        clear(pg)
        pg.execute(raw_booking(3, 1))
        bid = rows(pg, "SELECT max(id) FROM bookings")[0][0]
        vid, code, _ = voucher_service.issue(pg, bid, 100000)
        pg.commit()
        cs = guests(world, 6)
        res = parallel([lambda c=c, i=i: pay(c, 1 + i % 2, 2, code, 25000) for i, c in enumerate(cs)])
        for c in cs:
            c.close()
        won = [x for x in res if x.status_code == 201]
        assert len(won) == 4, (r, [x.text for x in res])
        assert all(x.json() == INVALID for x in res if x.status_code != 201), r
        assert rows(pg, "SELECT balance_ore FROM vouchers WHERE id = %s", (vid,)) == [(0,)], r
        assert rows(pg, "SELECT sum(amount_ore) FROM payments WHERE voucher_id = %s", (vid,)) == [(100000,)], r
        assert rows(pg, "SELECT count(*) FROM bookings WHERE session_id IS NOT NULL") == [(4,)], r
        # each winner: NOK 250 by Voucher, NOK 250 by card; the losers wrote nothing
        assert rows(pg, "SELECT count(*) FROM payments WHERE method = 'card'") == [(4,)], r


def test_the_window_lock_comes_before_the_voucher_update(guest, pg, database):
    """A booking waits for the Window lock before it touches the Voucher: while another transaction holds Window 1, the
    Voucher's balance stays and its row is not locked by the waiting booking."""
    code = voucher(guest)
    vid = voucher_id(pg, code)
    pg.rollback()
    pg.execute("SELECT lock_windows(ARRAY[1])")
    result = {}
    t = threading.Thread(target=lambda: result.setdefault("r", pay(guest, 1, 1, code, 25000)))
    t.start()
    try:
        time.sleep(1.0)
        assert t.is_alive()  # waiting for the Window lock
        with psycopg.connect(database) as other:
            # the Voucher row is free: the booking has not reached its UPDATE
            row = other.execute("SELECT balance_ore FROM vouchers WHERE id = %s FOR UPDATE NOWAIT", (vid,)).fetchone()
            assert row == (25000,)
    finally:
        pg.rollback()
    t.join(30)
    assert result["r"].status_code == 201, result["r"].text
    assert balance(pg, code) == 0


# ------------------------------------------------------------------ giving up never renews a Voucher (Lisa, 2026-11-24)


def _short_lived(pg, code: str, days: int) -> str:
    """Make the Voucher expire `days` after it was issued; returns its last valid date (ISO)."""
    pg.execute("UPDATE vouchers SET expires_at = issued_at + make_interval(days => %s) WHERE id = %s",
               (days, voucher_id(pg, code)))
    pg.commit()
    return rows(pg, "SELECT ((v.expires_at AT TIME ZONE st.venue_tz)::date - 1)::text FROM vouchers v "
                    "CROSS JOIN settings st WHERE v.id = %s", (voucher_id(pg, code),))[0][0]


def _paid_and_opened(guest, code: str, part: int, seats: int = 2) -> str:
    r = pay(guest, 1, seats, code, part)
    assert r.status_code == 201, r.text
    m = TOKEN.search(r.json()["emails"][0]["body"])
    assert m and open_link(guest, m.group(1)).status_code == 200
    return r.json()["booking"]["reference"]


def test_giving_up_seats_paid_with_a_voucher_keeps_its_last_valid_date(guest, pg):
    code = voucher(guest)  # NOK 250, valid one year
    last = _short_lived(pg, code, 30)
    assert last < LAST_VALID
    ref = _paid_and_opened(guest, code, 25000)  # half by Voucher, half by card
    assert guest.get(f"/api/manage/{ref}").json()["voucher_last_valid_date"] == last
    r = give_up(guest, ref, 2)
    assert r.status_code == 200, r.text
    assert r.json()["voucher"] == {"value_ore": 50000, "last_valid_date": last}
    new_code = code_of(r.json()["emails"][0]["body"])
    assert rows(pg, "SELECT ((v.expires_at AT TIME ZONE st.venue_tz)::date - 1)::text FROM vouchers v "
                    "CROSS JOIN settings st WHERE v.id = %s", (voucher_id(pg, new_code),))[0][0] == last


def test_a_booking_split_off_by_a_move_keeps_the_spent_vouchers_date(guest, pg):
    code = voucher(guest)
    last = _short_lived(pg, code, 60)
    ref = _paid_and_opened(guest, code, 25000)
    r = move(guest, ref, 3, 1)  # one Seat to another Window: a new Booking without payments rows
    assert r.status_code == 200, r.text
    new_ref = r.json()["new_booking"]["reference"]
    assert rows(pg, "SELECT count(*) FROM payments p JOIN bookings b ON b.id = p.booking_id "
                    "WHERE b.reference = %s", (new_ref,)) == [(0,)]
    assert guest.get(f"/api/manage/{new_ref}").json()["voucher_last_valid_date"] == last
    r = give_up(guest, new_ref, 1)
    assert r.status_code == 200, r.text
    assert r.json()["voucher"] == {"value_ore": 25000, "last_valid_date": last}


def test_a_booking_paid_by_card_alone_gives_a_voucher_of_one_year(guest):
    ref, _ = opened(guest, 2, 2)
    assert guest.get(f"/api/manage/{ref}").json()["voucher_last_valid_date"] == LAST_VALID
    r = give_up(guest, ref, 1)
    assert r.json()["voucher"]["last_valid_date"] == LAST_VALID
