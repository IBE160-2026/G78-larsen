"""SQL for Changes of a Booking (FR-26, AD-9, AD-29): the unlocked and the locked read of the Booking, the grant re-check,
the two UPDATEs of a Seat move, the history (`booking_changes`) and the one-time key of a Change. Only
`services.history` calls the functions that write or read `booking_changes`. Every function takes the connection of
the caller's transaction (`db.run`)."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import NamedTuple

import psycopg

# ------------------------------------------------------------------ the Booking, unlocked and locked


def window_of(c: psycopg.Connection, booking_id: int) -> int | None:
    """The Booking's `window_id`, read without a lock (the first read of AD-29), or None for an unknown Booking."""
    row = c.execute("SELECT window_id FROM bookings WHERE id = %s", (booking_id,)).fetchone()
    return None if row is None else row[0]


class Locked(NamedTuple):
    """A Booking as the locked re-read sees it."""

    id: int
    reference: str
    status: str
    version: int
    seats: int
    window_id: int
    price_per_seat_ore: int
    cutoff: dt.timedelta
    name: str
    email: str
    change_allowed: bool
    cutoff_at: dt.datetime


def lock_booking(c: psycopg.Connection, booking_id: int) -> Locked | None:
    """Re-read the Booking `FOR NO KEY UPDATE`, after its Windows are locked (AD-3, AD-29). `change_allowed` and
    `cutoff_at` are judged in the same statement on app_now() (AD-4)."""
    row = c.execute(
        "SELECT b.id, b.reference, b.status, b.version, b.seats, b.window_id, b.price_per_seat_ore, b.cutoff, b.name, "
        "b.email, app_now() < lower(w.during) - b.cutoff, lower(w.during) - b.cutoff "
        "FROM bookings b JOIN windows w ON w.id = b.window_id WHERE b.id = %s FOR NO KEY UPDATE OF b",
        (booking_id,)).fetchone()
    return None if row is None else Locked(*row)


def grant_valid(c: psycopg.Connection, session_id: int, booking_id: int) -> bool:
    """The grant re-check by join after the locked re-read (AD-28): the SQL predicate `manage_grant_valid`."""
    return c.execute("SELECT manage_grant_valid(%s, %s)", (session_id, booking_id)).fetchone()[0]


def venue_tz(c: psycopg.Connection) -> str:
    return c.execute("SELECT venue_tz FROM settings").fetchone()[0]


# ------------------------------------------------------------------ the move (AD-29)


def move_all(c: psycopg.Connection, booking_id: int, window_id: int) -> None:
    """Move the whole Booking to another Window: one UPDATE with `entry_time = app_now()` and `version + 1`. The store's
    `booked_within_capacity` refuses it when the Window has no room (FR-10)."""
    c.execute("UPDATE bookings SET window_id = %s, entry_time = app_now(), version = version + 1 WHERE id = %s",
              (window_id, booking_id))


def give_up_seats(c: psycopg.Connection, booking_id: int, seats: int) -> None:
    """Take `seats` Seats off the Booking (a split): its total follows its stored price per Seat (AD-13), and its
    `version` rises in the same UPDATE."""
    c.execute("UPDATE bookings SET seats = seats - %(n)s, total_ore = (seats - %(n)s) * price_per_seat_ore, "
              "version = version + 1 WHERE id = %(b)s", {"n": seats, "b": booking_id})


# ------------------------------------------------------------------ history (only services.history calls these)


def insert_change(c: psycopg.Connection, booking_id: int, action: str, cols: dict) -> int:
    """Insert one `booking_changes` row at app_now(); `cols` are its optional columns. Returns its id."""
    names = ["booking_id", "action", *cols]
    placeholders = ", ".join(["%s"] * len(names))
    return c.execute(f"INSERT INTO booking_changes ({', '.join(names)}) VALUES ({placeholders}) RETURNING id",
                     (booking_id, action, *cols.values())).fetchone()[0]


HISTORY_COLUMNS = frozenset({"seats", "from_window_id", "to_window_id", "from_sauna_id", "to_sauna_id",
                             "new_booking_id"})

_HISTORY = (
    "SELECT h.id, h.booking_id, h.action, h.at, h.seats, h.from_window_id, lower(fw.during), upper(fw.during), "
    "h.to_window_id, lower(tw.during), upper(tw.during), nb.reference "
    "FROM booking_changes h "
    "LEFT JOIN windows fw ON fw.id = h.from_window_id LEFT JOIN windows tw ON tw.id = h.to_window_id "
    "LEFT JOIN bookings nb ON nb.id = h.new_booking_id ")


def history_of(c: psycopg.Connection, booking_ids: list[int]) -> list[tuple]:
    """(id, booking_id, action, at, seats, from window id, from start, from end, to window id, to start, to end,
    new Booking's reference) of every Change of these Bookings, oldest first."""
    return c.execute(_HISTORY + "WHERE h.booking_id = ANY(%s) ORDER BY h.at, h.id", (booking_ids,)).fetchall()


def change(c: psycopg.Connection, change_id: int) -> tuple[int, int | None] | None:
    """(booking_id, new_booking_id) of a Change, or None."""
    return c.execute("SELECT booking_id, new_booking_id FROM booking_changes WHERE id = %s", (change_id,)).fetchone()


# ------------------------------------------------------------------ the one-time key of a Change (AD-9)


def insert_key(c: psycopg.Connection, key: uuid.UUID, session_id: int, endpoint: str, request_hash: bytes,
               change_id: int) -> None:
    """Store the key of a successful Change: `change_id` set, `booking_id` NULL."""
    c.execute("INSERT INTO idempotency_keys (key, session_id, endpoint, request_hash, change_id) "
              "VALUES (%s, %s, %s, %s, %s)", (key, session_id, endpoint, request_hash, change_id))
