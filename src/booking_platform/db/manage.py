"""SQL for Manage links (AD-28): the hashed tokens (`access_tokens`), the session grants (`manage_grants`), the
Booking read of the Manage page and the startup purge. Validity is never stored: it is judged by the SQL predicates
`manage_token_valid`, `manage_grant_valid` and `change_allowed` (migration 0010). Only `services.manage` calls the
functions that write `access_tokens`."""

from __future__ import annotations

import uuid

import psycopg

# ------------------------------------------------------------------ tokens (only services.manage writes them)


def lock_booking(c: psycopg.Connection, booking_id: int) -> None:
    """Lock the Booking row `FOR NO KEY UPDATE` before its token is replaced (AD-28, Issue)."""
    c.execute("SELECT id FROM bookings WHERE id = %s FOR NO KEY UPDATE", (booking_id,))


def revoke(c: psycopg.Connection, booking_id: int) -> int:
    """Revoke the Booking's unrevoked Manage token, if it has one."""
    return c.execute("UPDATE access_tokens SET revoked_at = app_now() "
                     "WHERE booking_id = %s AND purpose = 'manage' AND revoked_at IS NULL", (booking_id,)).rowcount


def insert_token(c: psycopg.Connection, booking_id: int, token_hash: bytes) -> int:
    return c.execute("INSERT INTO access_tokens (purpose, booking_id, token_hash) VALUES ('manage', %s, %s) "
                     "RETURNING id", (booking_id, token_hash)).fetchone()[0]


def valid_token(c: psycopg.Connection, token_hash: bytes) -> tuple[int, int, str] | None:
    """(token id, booking id, reference) of a valid Manage token with this hash; None when it is unknown, revoked or
    its Window has ended."""
    return c.execute(
        "SELECT t.id, b.id, b.reference FROM access_tokens t JOIN bookings b ON b.id = t.booking_id "
        "WHERE t.token_hash = %s AND t.purpose = 'manage' AND manage_token_valid(t.id)", (token_hash,)).fetchone()


# ------------------------------------------------------------------ grants


def upsert_grant(c: psycopg.Connection, session_id: int, token_id: int) -> bool:
    """Give the session a grant through the token, or renew its `last_used_at`; only while the token is valid. False
    when it is not (any more)."""
    row = c.execute(
        "INSERT INTO manage_grants (session_id, token_id, last_used_at) "
        "SELECT %(s)s, %(t)s, app_now() WHERE manage_token_valid(%(t)s) "
        "ON CONFLICT (session_id, token_id) DO UPDATE SET last_used_at = EXCLUDED.last_used_at RETURNING id",
        {"s": session_id, "t": token_id}).fetchone()
    return row is not None


def check_and_touch(c: psycopg.Connection, session_id: int, reference: str) -> int | None:
    """The Booking id when the session holds a valid grant for the Booking with this reference, its `last_used_at`
    touched in the same statement; None otherwise. Run as one autocommit statement (`db.statement`), outside every
    action transaction (AD-4)."""
    row = c.execute(
        "UPDATE manage_grants g SET last_used_at = app_now() "
        "FROM access_tokens t JOIN bookings b ON b.id = t.booking_id "
        "WHERE g.token_id = t.id AND g.session_id = %(s)s AND b.reference = %(r)s "
        "AND t.purpose = 'manage' AND t.revoked_at IS NULL AND manage_grant_valid(%(s)s, b.id) "
        "RETURNING b.id", {"s": session_id, "r": reference}).fetchone()
    return None if row is None else row[0]


def purge(c: psycopg.Connection) -> int:
    """Startup: delete the grants of expired sessions and of tokens whose Window has ended."""
    return c.execute(
        "DELETE FROM manage_grants g USING access_tokens t, bookings b, windows w, sessions s "
        "WHERE t.id = g.token_id AND b.id = t.booking_id AND w.id = b.window_id AND s.id = g.session_id "
        "AND (s.expires_at <= app_now() OR upper(w.during) <= app_now())").rowcount


# ------------------------------------------------------------------ the Manage page's read


def booking(c: psycopg.Connection, booking_id: int) -> tuple | None:
    """(reference, seats, window id, venue date, start, end, total_ore, status, version, change_allowed, cutoff_at,
    cancelled_at, venue_tz, kind, sauna_id, sauna name, cancel_remedy) of a Booking as it is now. Times are timestamptz; the date is
    the Venue date the Window starts on. The Sauna id and name are NULL for a Seat booking (AD-23, AD-25)."""
    return c.execute(
        "SELECT b.reference, b.seats, w.id, venue_date(w.id), lower(w.during), upper(w.during), b.total_ore, "
        "b.status, b.version, change_allowed(b.id), lower(w.during) - b.cutoff, b.cancelled_at, st.venue_tz, "
        "b.kind, s.id, s.name, b.cancel_remedy "
        "FROM bookings b JOIN windows w ON w.id = b.window_id CROSS JOIN settings st "
        "LEFT JOIN saunas s ON s.id = b.sauna_id WHERE b.id = %s",
        (booking_id,)).fetchone()


# ------------------------------------------------------------------ the seed's samples


def recipient(c: psycopg.Connection, booking_id: int) -> str:
    """The Booking's email address, for the seed's Manage email."""
    return c.execute("SELECT email FROM bookings WHERE id = %s", (booking_id,)).fetchone()[0]


def samples_without_token(c: psycopg.Connection, keys: list[uuid.UUID]) -> list[int]:
    """The ids of the active Bookings created under these idempotency keys that have no unrevoked Manage token and
    whose Window has not ended, oldest first."""
    return [r[0] for r in c.execute(
        "SELECT b.id FROM idempotency_keys k JOIN bookings b ON b.id = k.booking_id "
        "JOIN windows w ON w.id = b.window_id "
        "WHERE k.key = ANY(%s) AND b.status = 'active' AND app_now() < upper(w.during) "
        "AND NOT EXISTS (SELECT 1 FROM access_tokens t WHERE t.booking_id = b.id AND t.purpose = 'manage' "
        "AND t.revoked_at IS NULL) ORDER BY b.id", (keys,)).fetchall()]
