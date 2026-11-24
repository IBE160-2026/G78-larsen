"""FR-17, FR-20, FR-8, AD-4, AD-12, RB-1: the Administrator's Outbox `GET /api/admin/outbox`.

- It answers `{"emails": [...]}`: every `outbox_emails` row newest first (`created_at`, then `id`, both descending),
  each with `id`, `created_at` (Venue time), `recipient`, `subject` and `body` exactly as stored.
- A Guest-flow Booking's confirmation is there, first, and its body equals the email the Confirmation response
  showed; every link in it is absolute and starts with `BP_BASE_URL`.
- An empty Outbox is `{"emails": []}`. Any query field is `422 invalid_input`. An anonymous caller or a Guest session
  is `401 not_signed_in` and learns nothing, not even a count. A read writes nothing (row counts and `xmin`).
- Retention masking is in `test_fr21_retention.py`.
"""

from __future__ import annotations

import datetime as dt
import re

import pytest

from client import api_client
from test_fr08_confirmation import expected_body, with_link_masked
from test_fr16_booking_list import NOT_SIGNED_IN, book_seats, written

KEYS = {"id", "created_at", "recipient", "subject", "body"}


def outbox(c) -> list[dict]:
    r = c.get("/api/admin/outbox")
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"emails"}
    return body["emails"]


def raw_email(pg, created_at: dt.datetime, subject: str, body: str = "Body", recipient: str = "raw@example.com",
              booking_id: int | None = None) -> int:
    """An Outbox row written straight to the store, around the API (AD-21)."""
    eid = pg.execute("INSERT INTO outbox_emails (created_at, recipient, subject, body, booking_id) "
                     "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                     (created_at, recipient, subject, body, booking_id)).fetchone()[0]
    pg.commit()
    return eid


def test_an_empty_outbox(admin):
    assert outbox(admin) == []


def test_a_guest_flow_booking_confirmation_is_first_and_as_the_confirmation_showed(admin, api, world, pg):
    raw_email(pg, dt.datetime(2026, 11, 30, 12, 0, tzinfo=dt.timezone.utc), "Older")
    r = api.book(2, 2)
    assert r.status_code == 201, r.text
    paid = r.json()
    ref = paid["booking"]["reference"]
    emails = outbox(admin)
    assert [e["subject"] for e in emails] == [f"Booking confirmed: {ref}", "Older"]
    first = emails[0]
    assert set(first) == KEYS
    assert first["recipient"] == "guest@example.com"
    assert first["body"] == paid["emails"][0]["body"]
    assert with_link_masked(first["body"], world) == expected_body(ref, world)  # the Manage link (Story 4.1) aside
    links = re.findall(r"https?://\S+", first["body"])
    assert links and all(link.startswith(world + "/") for link in links)
    # the time is the stored one, in Venue time (Europe/Oslo, +01:00 in December)
    stored = pg.execute("SELECT id, created_at FROM outbox_emails WHERE subject = %s",
                        (f"Booking confirmed: {ref}",)).fetchone()
    pg.rollback()
    assert first["id"] == stored[0]
    assert first["created_at"].endswith("+01:00")
    assert dt.datetime.fromisoformat(first["created_at"]) == stored[1]


def test_newest_first_ties_by_id_descending(admin, pg):
    t = dt.datetime(2026, 11, 30, 12, 0, tzinfo=dt.timezone.utc)
    a = raw_email(pg, t, "A")
    b = raw_email(pg, t + dt.timedelta(hours=1), "B")
    c = raw_email(pg, t, "C")  # same time as A, higher id
    d = raw_email(pg, t - dt.timedelta(days=1), "D")
    emails = outbox(admin)
    assert [e["id"] for e in emails] == [b, c, a, d]
    assert emails[0]["created_at"] == "2026-11-30T14:00:00+01:00"


def test_stored_text_comes_back_exactly_as_stored(admin, pg):
    body = "<script>alert(1)</script>\n<b>x</b>\r\n  spaced  \n"
    raw_email(pg, dt.datetime(2026, 11, 30, 12, 0, tzinfo=dt.timezone.utc), "<i>subject</i>", body=body,
              recipient="Øyvind <o@example.com>")
    (e,) = outbox(admin)
    assert (e["recipient"], e["subject"], e["body"]) == ("Øyvind <o@example.com>", "<i>subject</i>", body)


def test_a_read_writes_nothing(admin, api, pg):
    book_seats(api, 1, 3)
    before = written(pg)
    for _ in range(2):
        assert len(outbox(admin)) == 1
    assert written(pg) == before


@pytest.mark.parametrize("params", [{"foo": "1"}, {"date": "2026-12-01"}, {"limit": "10"}],
                         ids=["unknown", "date", "limit"])
def test_any_query_field_is_422_and_writes_nothing(admin, pg, params):
    before = written(pg)
    r = admin.get("/api/admin/outbox", params=params)
    assert r.status_code == 422 and r.json()["detail"]["error"] == "invalid_input", r.text
    assert written(pg) == before


def test_an_anonymous_caller_gets_401_and_nothing(world, api, pg):
    book_seats(api, 1, 2)
    before = written(pg)
    with api_client(world, session=False) as anon:
        r = anon.get("/api/admin/outbox")
    assert r.status_code == 401 and r.json() == NOT_SIGNED_IN
    assert written(pg) == before


def test_a_guest_session_gets_401_and_nothing(api, pg):
    book_seats(api, 1, 2)
    before = written(pg)
    r = api.get("/api/admin/outbox")
    assert r.status_code == 401 and r.json() == NOT_SIGNED_IN
    assert written(pg) == before
