"""FR-8 / FR-20 RB-4 / AD-12: the confirmation email and the confirmation read.

The email is plain text in the line layout of `mockups/key-confirmation.html`: Venue identity and contact, the
reference, date, session, Seats, the stored total, the Guest's email, the reception sentence without a heading, the
booking terms with the change statement, the Manage link `<BP_BASE_URL>/manage#t=<token>` (Story 4.1), an absolute
"Before you come" link from `BP_BASE_URL`, and the payment note. No Sauna.
`GET /api/bookings/{reference}/confirmation` returns the Booking and the stored email to the paying session only; any
other session, no session, an unknown, malformed or lower-case reference all get the same `404 not_found`.
"""

from __future__ import annotations

import re

import pytest

from client import api_client

NOT_FOUND = {"detail": {"error": "not_found"}}
LINK = "<the Manage link>"


def manage_link(base: str) -> re.Pattern:
    """The Manage link line: the base URL, `/manage` and a 43-character URL-safe token in the fragment."""
    return re.compile(r"(?m)^" + re.escape(base) + r"/manage#t=[A-Za-z0-9_-]{43}$")


def with_link_masked(body: str, base: str) -> str:
    masked, n = manage_link(base).subn(LINK, body)
    assert n == 1, body
    return masked


def snapshot(pg) -> tuple:
    pg.rollback()
    row = pg.execute("SELECT (SELECT count(*) FROM bookings), (SELECT count(*) FROM payments), "
                     "(SELECT count(*) FROM outbox_emails), (SELECT count(*) FROM idempotency_keys), "
                     "(SELECT count(*) FROM sessions)").fetchone()
    pg.rollback()
    return tuple(row)


def expected_body(reference: str, base: str) -> str:
    return "\n".join([
        "Booking confirmed",
        "",
        "Saunalöyly",
        "Badstubrygga 4, 0000 Havbukta",
        "+47 01 23 45 67",
        "hello@saunaloyly.example",
        "",
        f"Booking reference: {reference}",
        "Date: Tuesday 1 December 2026",
        "Session: 11:30–13:00",
        "Seats: 2",
        "Total: NOK 500 incl. VAT",
        "Email: guest@example.com",
        "",
        "Keep your booking reference and give it at reception when you arrive.",
        "",
        "Booking terms",
        "A booking for a fixed date cannot be withdrawn.",
        "Up to 12 hours before the session starts, you can move some or all seats to another session, or give them "
        "up for a voucher. Money is not refunded.",
        "If Saunalöyly cancels your session, you choose a refund or a voucher.",
        "",
        "Manage your booking",
        LINK,
        "",
        "Before you come",
        f"{base}/#before-you-come",
        "",
        "Simulated payment: no money moves",
    ])


def test_the_email_follows_the_confirmation_layout(api, world, pg):
    r = api.book(2, 2)
    assert r.status_code == 201, r.text
    ref = r.json()["booking"]["reference"]
    [email] = r.json()["emails"]
    assert email["subject"] == f"Booking confirmed: {ref}"
    assert with_link_masked(email["body"], world) == expected_body(ref, world)
    stored = pg.execute("SELECT recipient, subject, body FROM outbox_emails").fetchall()
    pg.rollback()
    assert [(to, subject, with_link_masked(body, world)) for to, subject, body in stored] == [
        ("guest@example.com", f"Booking confirmed: {ref}", expected_body(ref, world))]
    assert stored[0][2] == email["body"]  # the response shows the email as stored, link included
    assert "cannot be changed or refunded" not in stored[0][2]


def test_the_paying_session_reads_the_booking_and_the_email_as_sent(api, pg):
    paid = api.book(2, 2).json()
    ref = paid["booking"]["reference"]
    before = snapshot(pg)
    for _ in range(2):  # a reload shows it again
        r = api.get(f"/api/bookings/{ref}/confirmation")
        assert r.status_code == 200, r.text
        assert r.json() == paid
    assert snapshot(pg) == before  # the read writes nothing


def test_another_session_no_session_and_unknown_references_get_the_same_404(api, world, pg):
    ref = api.book(2, 2).json()["booking"]["reference"]
    other = "Z" * 8 if ref != "Z" * 8 else "Y" * 8
    before = snapshot(pg)
    answers = []
    with api_client(world) as stranger, api_client(world, session=False) as anonymous:
        answers.append(stranger.get(f"/api/bookings/{ref}/confirmation"))
        answers.append(anonymous.get(f"/api/bookings/{ref}/confirmation"))
        for guess in (other, ref.lower(), ref[:7], ref + "0", "IIIIIIII", "%20" * 8):
            answers.append(api.get(f"/api/bookings/{guess}/confirmation"))
    for r in answers:
        assert r.status_code == 404 and r.json() == NOT_FOUND, (r.request.url, r.text)
    assert len({r.content for r in answers}) == 1  # byte for byte the same answer
    assert snapshot(pg)[:4] == before[:4]


@pytest.mark.parametrize("path", ["/api/bookings/{ref}/confirmation/", "/api/bookings/{ref}"])
def test_other_paths_are_the_json_404(api, path):
    ref = api.book(2, 1).json()["booking"]["reference"]
    r = api.get(path.format(ref=ref))
    assert r.status_code == 404 and r.json() == NOT_FOUND
