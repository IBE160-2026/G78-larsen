"""SQL for the Administrator's Outbox (FR-17, FR-21, AD-4, AD-12): every simulated email, newest first. Reads only:
no lock, no write. An email linked to a Booking due for retention (`retention_due()`) reads with its recipient and
body masked to the values the startup catch-up stores (`retention.CLEARED`), in the SELECT, never by writing. Emails
with no Booking are never masked. Every function takes the connection of the caller's transaction (`db.run`)."""

from __future__ import annotations

import psycopg

from .retention import CLEARED


def all_emails(c: psycopg.Connection) -> list[tuple]:
    """(id, created_at, recipient, subject, body, venue_tz) of every Outbox email, newest first (`created_at`, then
    `id`). Whether an email is masked is decided once per row (`retention_due()` reads the clock), so recipient and
    body are always masked together. The Venue time zone comes with each row, so the read is one SELECT."""
    return c.execute(
        "SELECT o.id, o.created_at, "
        "       CASE WHEN m.due THEN %(cleared)s ELSE o.recipient END, "
        "       o.subject, "
        "       CASE WHEN m.due THEN %(cleared)s ELSE o.body END, "
        "       s.venue_tz "
        "FROM outbox_emails o "
        "CROSS JOIN LATERAL (SELECT o.booking_id IS NOT NULL AND retention_due(o.booking_id) AS due) m "
        "CROSS JOIN settings s "
        "ORDER BY o.created_at DESC, o.id DESC",
        {"cleared": CLEARED}).fetchall()
