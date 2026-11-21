"""The startup catch-up of retention (FR-21, AD-4, AD-12): what reads only mask is written here, once the app starts.

One function per effect, each one `db.run` that returns its count. A Booking is due only by `retention_due()`
(`0009_retention.sql`). A second run changes nothing: both writes skip rows that already hold the anonymised values.
"""

from __future__ import annotations

from .. import db
from ..db import retention as q


def anonymise_bookings() -> int:
    """Set the name and email of due Bookings not yet anonymised to "Anonymised" / "anonymised@example.invalid"."""
    return db.run(q.anonymise_bookings)


def clear_emails() -> int:
    """Set the recipient and body of the Outbox emails of due Bookings to ''."""
    return db.run(q.clear_emails)


def run() -> dict[str, int]:
    """Both effects, in order. Returns the counts only (AD-19: never the rows)."""
    return {"bookings_anonymised": anonymise_bookings(), "emails_cleared": clear_emails()}
