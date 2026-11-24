"""SQL for one Window, Seats left, Holds and Seat bookings; the dated listing is in `db.windows`. Every function takes
the connection of the caller's transaction (`db.run`)."""

from __future__ import annotations

import psycopg

_WINDOW = "SELECT id, lower(during), upper(during), seats_left(id) FROM windows"


def get_window(c: psycopg.Connection, window_id: int) -> tuple | None:
    return c.execute(_WINDOW + " WHERE id = %s", (window_id,)).fetchone()


def before_booking_deadline(c: psycopg.Connection, window_id: int) -> bool | None:
    """True while the Window's Booking deadline has not passed, judged on app_now(); None for an unknown Window."""
    row = c.execute("SELECT app_now() < booking_deadline(id) FROM windows WHERE id = %s", (window_id,)).fetchone()
    return None if row is None else row[0]


def within_horizon(c: psycopg.Connection, window_id: int) -> bool | None:
    """True while the Window starts no later than the end of the Booking horizon, judged on app_now() (the SQL
    predicate `within_horizon`); None for an unknown Window."""
    row = c.execute("SELECT within_horizon(id) FROM windows WHERE id = %s", (window_id,)).fetchone()
    return None if row is None else row[0]


def seats_left(c: psycopg.Connection, window_id: int) -> int:
    """Seats left in the Window now (the store's `seats_left()`, counting live Holds)."""
    return c.execute("SELECT seats_left(%s)", (window_id,)).fetchone()[0]


def live_hold(c: psycopg.Connection, session_id: int, window_id: int) -> int | None:
    row = c.execute("SELECT id FROM holds WHERE session_id = %s AND window_id = %s AND expires_at > app_now()",
                    (session_id, window_id)).fetchone()
    return None if row is None else row[0]


def resize_hold(c: psycopg.Connection, hold_id: int, seats: int) -> None:
    c.execute("UPDATE holds SET seats = %s WHERE id = %s", (seats, hold_id))


def delete_holds(c: psycopg.Connection, session_id: int, window_id: int) -> int:
    return c.execute("DELETE FROM holds WHERE session_id = %s AND window_id = %s", (session_id, window_id)).rowcount


def insert_hold(c: psycopg.Connection, session_id: int, window_id: int, seats: int) -> int:
    """A Hold ends at the earlier of 10 minutes and the Booking deadline (FR-35)."""
    return c.execute(
        "INSERT INTO holds (window_id, seats, session_id, created_at, expires_at) "
        "SELECT %s, %s, %s, n, LEAST(n + interval '10 minutes', booking_deadline(%s)) FROM (SELECT app_now() AS n) x "
        "RETURNING id", (window_id, seats, session_id, window_id)).fetchone()[0]


def insert_booking(c: psycopg.Connection, reference: str, window_id: int, seats: int, name: str, email: str,
                   price_per_seat_ore: int, session_id: int) -> int | None:
    """Insert a Seat booking under `reference`, its total `seats × price_per_seat_ore` (AD-13). None when the reference
    is taken: `ON CONFLICT (reference) DO NOTHING`, so a clash neither raises nor aborts the transaction (AD-20). The
    time of booking and the entry time are one `app_now()` (AD-7). The Booking keeps its own copy of the Seat Cutoff
    (`settings.cutoff_seats`, AD-4)."""
    row = c.execute(
        "INSERT INTO bookings (reference, window_id, seats, name, email, price_per_seat_ore, total_ore, session_id, "
        "created_at, entry_time, cutoff) "
        "SELECT %s, %s, %s, %s, %s, %s, %s, %s, n, n, (SELECT cutoff_seats FROM settings) "
        "FROM (SELECT app_now() AS n) x "
        "ON CONFLICT (reference) DO NOTHING RETURNING id",
        (reference, window_id, seats, name, email, price_per_seat_ore, seats * price_per_seat_ore,
         session_id)).fetchone()
    return None if row is None else row[0]
