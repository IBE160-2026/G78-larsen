"""SQL for what a Booking leaves behind besides its row (Story 1.5): one-time keys (AD-9), payments (AD-13), the Outbox
(AD-12), and the Booking facts that the response, the confirmation read and the email show. The Booking row itself is
inserted by `db.seats.insert_booking`. Every function takes the connection of the caller's transaction (`db.run`)."""

from __future__ import annotations

import datetime as dt
import uuid

import psycopg

# ------------------------------------------------------------------ one-time keys (AD-9)


def key(c: psycopg.Connection, key: uuid.UUID) -> tuple[int, str, bytes, int] | None:
    """(session_id, endpoint, request_hash, booking_id) of a known key, or None."""
    return c.execute("SELECT session_id, endpoint, request_hash, booking_id FROM idempotency_keys WHERE key = %s",
                     (key,)).fetchone()


def key_exists(c: psycopg.Connection, key: uuid.UUID) -> bool:
    return c.execute("SELECT EXISTS (SELECT 1 FROM idempotency_keys WHERE key = %s)", (key,)).fetchone()[0]


def insert_key(c: psycopg.Connection, key: uuid.UUID, session_id: int, endpoint: str, request_hash: bytes,
               booking_id: int) -> None:
    c.execute("INSERT INTO idempotency_keys (key, session_id, endpoint, request_hash, booking_id) "
              "VALUES (%s, %s, %s, %s, %s)", (key, session_id, endpoint, request_hash, booking_id))


# ------------------------------------------------------------------ payments (AD-13)


def insert_payment(c: psycopg.Connection, booking_id: int, direction: str, method: str, amount_ore: int) -> int:
    return c.execute("INSERT INTO payments (booking_id, direction, method, amount_ore) VALUES (%s, %s, %s, %s) "
                     "RETURNING id", (booking_id, direction, method, amount_ore)).fetchone()[0]


# ------------------------------------------------------------------ the Outbox (AD-12)


def insert_email(c: psycopg.Connection, recipient: str, subject: str, body: str, booking_id: int | None) -> int:
    return c.execute("INSERT INTO outbox_emails (recipient, subject, body, booking_id) VALUES (%s, %s, %s, %s) "
                     "RETURNING id", (recipient, subject, body, booking_id)).fetchone()[0]


def emails_of_booking(c: psycopg.Connection, booking_id: int) -> list[tuple[str, str]]:
    """(subject, body) of the emails sent with a Booking, oldest first."""
    return c.execute("SELECT subject, body FROM outbox_emails WHERE booking_id = %s ORDER BY id",
                     (booking_id,)).fetchall()


# ------------------------------------------------------------------ Booking facts


def booking(c: psycopg.Connection, booking_id: int) -> tuple | None:
    """(reference, venue date, start, end, seats, price_per_seat_ore, total_ore, name, email, status, venue_tz) of a
    Booking as it is now. Start and end are timestamptz; the date is the Venue date the Window starts on."""
    return c.execute(
        "SELECT b.reference, venue_date(w.id), lower(w.during), upper(w.during), b.seats, b.price_per_seat_ore, "
        "b.total_ore, b.name, b.email, b.status, st.venue_tz "
        "FROM bookings b JOIN windows w ON w.id = b.window_id CROSS JOIN settings st WHERE b.id = %s",
        (booking_id,)).fetchone()


def paid_by_session(c: psycopg.Connection, reference: str, session_id: int) -> int | None:
    """The id of the Booking with this reference paid by this session, or None (unknown, or another session's)."""
    row = c.execute("SELECT id FROM bookings WHERE reference = %s AND session_id = %s",
                    (reference, session_id)).fetchone()
    return None if row is None else row[0]


def window_at(c: psycopg.Connection, date: dt.date, start: dt.time) -> int | None:
    """The Window that starts at `start` Venue time on the Venue date `date`, or None."""
    row = c.execute(
        "SELECT w.id FROM windows w, settings st WHERE venue_date(w.id) = %s "
        "AND (lower(w.during) AT TIME ZONE st.venue_tz)::time = %s", (date, start)).fetchone()
    return None if row is None else row[0]


def venue_today(c: psycopg.Connection) -> dt.date:
    return c.execute("SELECT venue_today()").fetchone()[0]
