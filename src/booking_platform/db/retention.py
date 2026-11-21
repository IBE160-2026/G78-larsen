"""SQL for retention (FR-21, AD-4, AD-30): the anonymised values and the two writes of the startup catch-up. Whether a
Booking is due is decided only by the SQL function `retention_due(booking_id)` of `0009_retention.sql`. Every
function takes the connection of the caller's transaction (`db.run`)."""

from __future__ import annotations

import psycopg

# What a due Booking's name and email read as, and become (Lisa, 2026-11-21).
ANONYMISED_NAME = "Anonymised"
ANONYMISED_EMAIL = "anonymised@example.invalid"


def anonymise_bookings(c: psycopg.Connection) -> int:
    """Set the name and email of every due Booking not yet anonymised to the anonymised values. A change of name or
    email neither locks nor recomputes a Window (0006). Returns the rows changed."""
    return c.execute(
        "UPDATE bookings b SET name = %(name)s, email = %(email)s "
        "WHERE (b.name <> %(name)s OR b.email <> %(email)s) AND retention_due(b.id)",
        {"name": ANONYMISED_NAME, "email": ANONYMISED_EMAIL}).rowcount


def clear_emails(c: psycopg.Connection) -> int:
    """Set the recipient and body of every Outbox email of a due Booking to ''. Returns the rows changed."""
    return c.execute(
        "UPDATE outbox_emails o SET recipient = '', body = '' "
        "WHERE o.booking_id IS NOT NULL AND (o.recipient <> '' OR o.body <> '') AND retention_due(o.booking_id)").rowcount
