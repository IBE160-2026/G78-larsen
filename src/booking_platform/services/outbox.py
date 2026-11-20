"""The Outbox (AD-12): `send` is the only way the platform sends an email. It is called inside the action's
transaction, so an email exists exactly when its action committed. Bodies are plain English text built in `services`;
links are absolute, from `BP_BASE_URL` and `config.links`, never from the request."""

from __future__ import annotations

import psycopg

from .. import config
from ..db import bookings as q


def link(path: str) -> str:
    """An absolute link for an email: the base URL plus a path from `config.links`."""
    return config.settings().base_url + path


def send(c: psycopg.Connection, to: str, subject: str, body: str, *, booking_id: int | None = None) -> int:
    """Store the email in the Outbox; returns its id."""
    return q.insert_email(c, to, subject, body, booking_id)


def of_booking(c: psycopg.Connection, booking_id: int) -> list[dict]:
    """The emails sent with a Booking, as `{subject, body}`, oldest first: what the Guest sees as sent."""
    return [{"subject": s, "body": b} for s, b in q.emails_of_booking(c, booking_id)]
