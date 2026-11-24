"""The Outbox (AD-12): `send` is the only way the platform sends an email. It is called inside the action's
transaction, so an email exists exactly when its action committed. Bodies are plain English text built in `services`;
links are absolute, from `BP_BASE_URL` and `config.links`, never from the request.

`listing` is the Administrator's read (FR-17, FR-21, AD-4): one `db.run` of one SELECT (the Venue time zone
included), no lock, no write. An email of a Booking due for retention reads with its recipient and body masked
(`db.outbox`); nothing is written for it."""

from __future__ import annotations

from zoneinfo import ZoneInfo

import psycopg

from .. import config, db
from ..db import bookings as q
from ..db import outbox as oq


def link(path: str) -> str:
    """An absolute link for an email: the base URL plus a path from `config.links`."""
    return config.settings().base_url + path


def send(c: psycopg.Connection, to: str, subject: str, body: str, *, booking_id: int | None = None,
         change_id: int | None = None) -> int:
    """Store the email in the Outbox; returns its id. An email a Change sends carries the Change's id (AD-29)."""
    return q.insert_email(c, to, subject, body, booking_id, change_id)


def of_booking(c: psycopg.Connection, booking_id: int) -> list[dict]:
    """The emails sent with a Booking, as `{subject, body}`, oldest first: what the Guest sees as sent."""
    return [{"subject": s, "body": b} for s, b in q.emails_of_booking(c, booking_id)]


def of_change(c: psycopg.Connection, change_id: int) -> list[dict]:
    """The emails a Change sent, as `{id, subject, body}`, oldest first (AD-9: a repeat reads them back by id)."""
    return [{"id": i, "subject": s, "body": b} for i, s, b in q.emails_by_change(c, change_id)]


def listing() -> dict:
    """`{"emails": [...]}`: every Outbox email, newest first, each with `id`, `created_at` (Venue time), `recipient`,
    `subject` and `body` exactly as stored, or masked when its Booking is due for retention."""

    def work(c):
        return {"emails": [
            {"id": eid, "created_at": created_at.astimezone(ZoneInfo(tz)).isoformat(), "recipient": recipient,
             "subject": subject, "body": body}
            for eid, created_at, recipient, subject, body, tz in oq.all_emails(c)]}

    return db.run(work)
