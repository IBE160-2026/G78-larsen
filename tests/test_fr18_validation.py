"""FR-18 IV-1 to IV-5, FR-5 and FR-9 for `POST /api/bookings`: invalid input is refused before anything is written
(no Booking, payment, email or key), and stored text is only ever data.

- IV-1: Seats 0, negative, fractional, not a number or above 10.
- IV-2: a malformed Window (422) or an unknown one (404 `not_found`).
- IV-3: a missing required field, an unknown extra field.
- IV-4 / FR-5: a name that is empty or over 100 characters; an email that is empty, over 254 characters or malformed.
- FR-9: more than one Window (`window_ids`) is an unknown field.
- IV-5: a name with SQL, a script tag or HTML is stored as given and returned as JSON text, never executed.
"""

from __future__ import annotations

import pytest

from client import GUEST, booking_body, new_key


def written(pg) -> tuple:
    pg.rollback()
    row = pg.execute("SELECT (SELECT count(*) FROM bookings), (SELECT count(*) FROM payments), "
                     "(SELECT count(*) FROM outbox_emails), (SELECT count(*) FROM idempotency_keys), "
                     "(SELECT count(*) FROM holds)").fetchone()
    pg.rollback()
    return tuple(row)


def without(field: str) -> dict:
    body = booking_body(1, 2)
    del body[field]
    return body


LONG_EMAIL = "a" * 243 + "@example.com"  # 255 characters

INVALID = [
    # IV-1
    (booking_body(1, 0), ["seats"]),
    (booking_body(1, -1), ["seats"]),
    (booking_body(1, 1.5), ["seats"]),
    (booking_body(1, "x"), ["seats"]),
    (booking_body(1, 11), ["seats"]),
    (booking_body(1, None), ["seats"]),
    # IV-2: malformed Windows
    (booking_body("one", 2), ["window_id"]),
    (booking_body(0, 2), ["window_id"]),
    (booking_body(2**31, 2), ["window_id"]),
    (booking_body(1.5, 2), ["window_id"]),
    # IV-3
    (without("window_id"), ["window_id"]),
    (without("seats"), ["seats"]),
    (without("name"), ["name"]),
    (without("email"), ["email"]),
    (booking_body(1, 2, guest="x"), ["guest"]),
    (booking_body(1, 2, price_per_seat_ore=0), ["price_per_seat_ore"]),
    # FR-9: one Window per Booking
    (booking_body(1, 2, window_ids=[1, 2]), ["window_ids"]),
    ({**GUEST, "window_id": [1, 2], "seats": 2}, ["window_id"]),
    # IV-4 / FR-5
    (booking_body(1, 2, name=""), ["name"]),
    (booking_body(1, 2, name="   "), ["name"]),
    (booking_body(1, 2, name="n" * 101), ["name"]),
    (booking_body(1, 2, name=7), ["name"]),
    (booking_body(1, 2, email=""), ["email"]),
    (booking_body(1, 2, email=LONG_EMAIL), ["email"]),
    (booking_body(1, 2, email="no-at.example.com"), ["email"]),
    (booking_body(1, 2, email="two@@example.com"), ["email"]),
    (booking_body(1, 2, email="space in@example.com"), ["email"]),
    (booking_body(1, 2, email="nodot@example"), ["email"]),
    # control characters (PostgreSQL refuses NUL in text: never a 500)
    (booking_body(1, 2, name="Ada\x00Lovelace"), ["name"]),
    (booking_body(1, 2, name="Ada\x1bLovelace"), ["name"]),
    (booking_body(1, 2, name="Ada\x7f"), ["name"]),
    (booking_body(1, 2, email="ada\x00@example.com"), ["email"]),
    (booking_body(1, 2, email="ada@exam\x01ple.com"), ["email"]),
]


@pytest.mark.parametrize("body,fields", INVALID, ids=[f"{i}-{f[0]}" for i, (_, f) in enumerate(INVALID)])
def test_invalid_input_is_422_and_writes_nothing(api, pg, body, fields):
    r = api.post("/api/bookings", json=body, headers=new_key())
    assert r.status_code == 422, r.text
    assert r.json() == {"detail": {"error": "invalid_input", "fields": fields}}
    assert written(pg) == (0, 0, 0, 0, 0)


def test_a_body_that_is_not_an_object_is_422(api, pg):
    for content in (b"[1, 2]", b'"x"', b"{not json"):
        r = api.post("/api/bookings", content=content, headers={"content-type": "application/json", **new_key()})
        assert r.status_code == 422 and r.json()["detail"]["error"] == "invalid_input", r.text
    assert written(pg) == (0, 0, 0, 0, 0)


def test_an_unknown_window_is_404_and_writes_nothing(api, pg):
    r = api.book(99999, 2)
    assert r.status_code == 404 and r.json() == {"detail": {"error": "not_found"}}, r.text
    assert written(pg) == (0, 0, 0, 0, 0)


def test_the_edges_are_accepted(api, pg):
    assert len(LONG_EMAIL) == 255
    email_254 = LONG_EMAIL[1:]
    r = api.book(1, 1, name="n" * 100, email=email_254)
    assert r.status_code == 201, r.text
    assert (r.json()["booking"]["name"], r.json()["booking"]["email"]) == ("n" * 100, email_254)
    r = api.book(1, 1, name="  Ingrid Hansen ", email=" ingrid@example.com ")  # outer spaces are not part of it
    assert (r.json()["booking"]["name"], r.json()["booking"]["email"]) == ("Ingrid Hansen", "ingrid@example.com")


@pytest.mark.parametrize("name", [
    "<script>alert(1)</script>",
    "Robert'); DROP TABLE bookings;--",
    '<img src=x onerror="alert(1)"> & <b>bold</b>',
], ids=["script", "sql", "html"])
def test_stored_text_is_data_never_markup_or_sql(api, pg, name):
    r = api.book(1, 2, name=name)
    assert r.status_code == 201, r.text
    assert r.headers["content-type"].startswith("application/json")
    ref = r.json()["booking"]["reference"]
    assert r.json()["booking"]["name"] == name
    assert api.get(f"/api/bookings/{ref}/confirmation").json()["booking"]["name"] == name
    stored = pg.execute("SELECT name FROM bookings WHERE reference = %s", (ref,)).fetchone()[0]
    tables = pg.execute("SELECT to_regclass('public.bookings') IS NOT NULL").fetchone()[0]
    pg.rollback()
    assert stored == name and tables
