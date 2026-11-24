"""FR-6 / AD-9 / AD-13 / AD-20: the Simulated payment creates the Booking, and a one-time key makes a repeat return the
first outcome.

`POST /api/bookings` with `{window_id, seats, name, email}` and an `Idempotency-Key` writes, in one transaction, the
Booking (an 8-character Crockford reference, the stored price and total), one card `payments` row, one Outbox email
and one key row. A repeat from the same session with the same Window and Seats writes nothing and returns the first
outcome (the name and email are not part of the request hash). Any other known key is `409 invalid_key`. A missing or
malformed key is a shape error.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid

import pytest

from client import api_client, booking_body
from conftest import clear
from test_fr10_through_the_api import left, parallel

REFERENCE = re.compile(r"[0-9A-HJKMNP-TV-Z]{8}")


def counts(pg) -> dict:
    pg.rollback()
    row = pg.execute("SELECT (SELECT count(*) FROM bookings), (SELECT count(*) FROM payments), "
                     "(SELECT count(*) FROM outbox_emails), (SELECT count(*) FROM idempotency_keys), "
                     "(SELECT count(*) FROM holds)").fetchone()
    pg.rollback()
    return dict(bookings=row[0], payments=row[1], emails=row[2], keys=row[3], holds=row[4])


NOTHING = dict(bookings=0, payments=0, emails=0, keys=0, holds=0)
ONE = dict(bookings=1, payments=1, emails=1, keys=1, holds=0)


def test_pay_creates_the_booking_one_charge_one_email_and_one_key(api, pg):
    key = str(uuid.uuid4())
    r = api.book(1, 2, key=key)
    assert r.status_code == 201, r.text
    body = r.json()
    assert set(body) == {"booking", "emails"}
    b = body["booking"]
    assert set(b) == {"reference", "date", "start", "end", "seats", "price_per_seat_ore", "total_ore", "name", "email",
                      "status"}
    assert REFERENCE.fullmatch(b["reference"]), b["reference"]
    assert (b["date"], b["start"], b["end"]) == ("2026-12-01", "2026-12-01T10:00:00+01:00",
                                                 "2026-12-01T11:30:00+01:00")
    assert (b["seats"], b["price_per_seat_ore"], b["total_ore"]) == (2, 25000, 50000)
    assert (b["name"], b["email"], b["status"]) == ("Test Guest", "guest@example.com", "active")
    assert [e["subject"] for e in body["emails"]] == [f"Booking confirmed: {b['reference']}"]
    assert counts(pg) == ONE
    assert left(api) == 42  # Seats left drops by exactly the Seats booked

    row = pg.execute("SELECT b.window_id, b.session_id, b.reference, b.status, b.entry_time = b.created_at, "
                     "p.direction, p.method, p.amount_ore, o.recipient, o.subject, k.key::text, k.endpoint, "
                     "k.session_id, k.booking_id = b.id, o.booking_id = b.id "
                     "FROM bookings b JOIN payments p ON p.booking_id = b.id JOIN outbox_emails o ON o.booking_id = b.id "
                     "JOIN idempotency_keys k ON k.booking_id = b.id").fetchone()
    pg.rollback()
    assert row == (1, api.session_id, b["reference"], "active", True, "charge", "card", 50000, "guest@example.com",
                   f"Booking confirmed: {b['reference']}", key, "POST /api/bookings", api.session_id, True, True)


def test_the_paying_sessions_hold_on_the_window_is_used_up(api, pg):
    assert api.post("/api/holds", json=dict(window_id=1, seats=2)).status_code == 200
    assert api.book(1, 2).status_code == 201
    assert counts(pg) == ONE
    assert left(api) == 42


def test_a_repeat_returns_the_first_outcome_and_writes_nothing(api, pg):
    key = str(uuid.uuid4())
    first = api.book(1, 2, key=key)
    assert first.status_code == 201
    again = api.book(1, 2, key=key)  # double click, reload or retry
    assert again.status_code == 201
    assert again.json() == first.json()
    assert counts(pg) == ONE
    assert left(api) == 42


def test_a_repeat_with_another_name_or_email_returns_the_first_outcome(api, pg):
    key = str(uuid.uuid4())
    first = api.book(1, 2, key=key).json()
    again = api.book(1, 2, key=key, name="Someone Else", email="else@example.com")
    assert again.status_code == 201 and again.json() == first
    assert again.json()["booking"]["name"] == "Test Guest"
    assert counts(pg) == ONE


@pytest.mark.parametrize("window_id,seats", [(1, 3), (2, 2)], ids=["other_seats", "other_window"])
def test_the_same_key_for_another_request_is_invalid_key_and_writes_nothing(api, pg, window_id, seats):
    key = str(uuid.uuid4())
    assert api.book(1, 2, key=key).status_code == 201
    r = api.book(window_id, seats, key=key)
    assert r.status_code == 409 and r.json() == {"detail": {"error": "invalid_key"}}, r.text
    assert counts(pg) == ONE
    assert left(api, 2) == 44


def test_a_key_known_from_another_session_is_invalid_key(api, world, pg):
    key = str(uuid.uuid4())
    assert api.book(1, 2, key=key).status_code == 201
    with api_client(world) as other:
        r = other.book(1, 2, key=key)
    assert r.status_code == 409 and r.json() == {"detail": {"error": "invalid_key"}}, r.text
    assert counts(pg) == ONE


@pytest.mark.parametrize("headers", [{}, {"Idempotency-Key": "not-a-uuid"}, {"Idempotency-Key": ""}],
                         ids=["missing", "malformed", "empty"])
def test_a_missing_or_malformed_key_is_422_and_writes_nothing(api, pg, headers):
    r = api.post("/api/bookings", json=booking_body(1, 2), headers=headers)
    assert r.status_code == 422, r.text
    assert r.json() == {"detail": {"error": "invalid_input", "fields": ["Idempotency-Key"]}}
    assert counts(pg) == NOTHING


def test_only_a_success_stores_a_key(api, pg):
    """A refused request stores nothing under its key, so a retry with the same key runs again (AD-9)."""
    key = str(uuid.uuid4())
    for _ in range(4):
        assert api.book(1, 10).status_code == 201
    r = api.book(1, 10, key=key)  # 50 of 44: refused by the store
    assert r.status_code == 409 and r.json()["detail"]["error"] == "no_seat_free"
    assert counts(pg) == dict(bookings=4, payments=4, emails=4, keys=4, holds=0)
    r = api.book(1, 4, key=key)  # the same key, a request that fits: the retry runs again
    assert r.status_code == 201, r.text
    assert left(api) == 0


def test_the_request_hash_covers_the_window_and_seats_and_never_the_name_or_email(api, pg):
    key = str(uuid.uuid4())
    assert api.book(1, 2, key=key, name="Ada Lovelace", email="ada@example.com").status_code == 201
    stored = pg.execute("SELECT request_hash FROM idempotency_keys WHERE key = %s", (key,)).fetchone()[0]
    columns = [r[0] for r in pg.execute("SELECT column_name FROM information_schema.columns "
                                        "WHERE table_name = 'idempotency_keys'").fetchall()]
    pg.rollback()
    canonical = json.dumps({"endpoint": "POST /api/bookings", "seats": 2, "window_id": 1}, sort_keys=True,
                           separators=(",", ":"))
    assert bytes(stored) == hashlib.sha256(canonical.encode()).digest()
    assert sorted(columns) == ["booking_id", "change_id", "created_at", "endpoint", "id", "key", "request_hash",
                               "session_id"]  # change_id: Story 4.2 (AD-9)


def test_the_stored_price_is_what_the_booking_keeps(api, pg):
    """AD-13: a later price change does not change a Booking's value; the response shows the stored values."""
    key = str(uuid.uuid4())
    first = api.book(1, 2, key=key).json()["booking"]
    pg.execute("UPDATE settings SET price_per_seat_ore = 30000")
    pg.commit()
    try:
        again = api.book(1, 2, key=key).json()["booking"]
        assert (again["price_per_seat_ore"], again["total_ore"]) == (25000, 50000) == (
            first["price_per_seat_ore"], first["total_ore"])
        assert api.book(2, 2).json()["booking"]["total_ore"] == 60000  # a new Booking pays the new price
    finally:
        pg.rollback()
        pg.execute("UPDATE settings SET price_per_seat_ore = 25000")
        pg.commit()


def test_one_key_raced_for_two_windows_books_once(api, pg):
    """The same key sent at once for two different Windows: both requests pass the key read (each locks only its own
    Window), and the store's UNIQUE key decides. Exactly one Booking; the other is `409 invalid_key` (AD-9)."""
    for r in range(10):
        clear(pg)
        key = str(uuid.uuid4())
        a, b = parallel([lambda: api.book(1, 2, key=key), lambda: api.book(2, 2, key=key)])
        assert sorted([a.status_code, b.status_code]) == [201, 409], (r, a.text, b.text)
        loser = a if a.status_code == 409 else b
        assert loser.json() == {"detail": {"error": "invalid_key"}}, (r, loser.text)
        assert counts(pg) == ONE, r


def test_a_free_price_books_without_a_payment_row(api, pg):
    """A price of 0 is a Booking with `total_ore` 0 and no charge (`payments.amount_ore > 0`)."""
    pg.execute("UPDATE settings SET price_per_seat_ore = 0")
    pg.commit()
    try:
        r = api.book(1, 2)
        assert r.status_code == 201, r.text
        assert (r.json()["booking"]["price_per_seat_ore"], r.json()["booking"]["total_ore"]) == (0, 0)
        assert counts(pg) == dict(bookings=1, payments=0, emails=1, keys=1, holds=0)
        assert "\nTotal: NOK 0 incl. VAT\n" in r.json()["emails"][0]["body"]
    finally:
        pg.rollback()
        pg.execute("UPDATE settings SET price_per_seat_ore = 25000")
        pg.commit()
