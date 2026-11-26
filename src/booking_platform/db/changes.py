"""SQL for Changes of a Booking (FR-26, AD-9, AD-29): the unlocked and the locked read of the Booking, the grant re-check,
the two UPDATEs of a Seat move, the two UPDATEs of a Voucher Change, the cancellation by the Guest, the history
(`booking_changes`), the returns of a cancelled Booking and the one-time key of a Change. Only `services.history` calls
the functions that write or read `booking_changes`, with one exception: `has_split` is read by
`services.payment.refund` (AD-31). Every function takes the connection of
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
    kind: str
    sauna_id: int | None
    total_ore: int


def lock_booking(c: psycopg.Connection, booking_id: int) -> Locked | None:
    """Re-read the Booking `FOR NO KEY UPDATE`, after its Windows are locked (AD-3, AD-29). `change_allowed` and
    `cutoff_at` are judged in the same statement on app_now() (AD-4)."""
    row = c.execute(
        "SELECT b.id, b.reference, b.status, b.version, b.seats, b.window_id, b.price_per_seat_ore, b.cutoff, b.name, "
        "b.email, app_now() < lower(w.during) - b.cutoff, lower(w.during) - b.cutoff, b.kind, b.sauna_id, b.total_ore "
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


# ------------------------------------------------------------------ the Voucher instead of Seats (FR-27, AD-29)


def give_up_for_voucher(c: psycopg.Connection, booking_id: int, seats: int) -> None:
    """Give up some of the Booking's Seats for a Voucher: the same UPDATE as a split's (`total_ore` follows the
    stored price per Seat, `version + 1`)."""
    give_up_seats(c, booking_id, seats)


def cancel_by_guest(c: psycopg.Connection, booking_id: int, remedy: str) -> None:
    """Cancel the Booking at the Guest's request: one UPDATE (`status = 'cancelled'`, `cancelled_at = app_now()`,
    `cancel_cause = 'guest'`, `cancel_remedy`, `version + 1`). Seats, Sauna and total stay on the row. Only `status` is
    in the AD-7 trigger column list, so the Window is recomputed at once. A Seat booking is cancelled only with
    `voucher` (FR-27; the store's `seat_guest_refund_forbidden`), a Whole-sauna booking with `refund` or `voucher`
    (FR-33); its capacity row is deleted next (AD-23's write order)."""
    c.execute("UPDATE bookings SET status = 'cancelled', cancelled_at = app_now(), cancel_cause = 'guest', "
              "cancel_remedy = %s, version = version + 1 WHERE id = %s", (remedy, booking_id))


def has_split(c: psycopg.Connection, booking_id: int) -> bool:
    """Whether the Booking has a split in its history: a move split Seats off it, or it was split off another
    (AD-31)."""
    return c.execute("SELECT EXISTS (SELECT 1 FROM booking_changes WHERE new_booking_id = %(b)s "
                     "OR (booking_id = %(b)s AND new_booking_id IS NOT NULL))", {"b": booking_id}).fetchone()[0]


# ------------------------------------------------------------------ history (only services.history calls these)


def insert_change(c: psycopg.Connection, booking_id: int, action: str, cols: dict) -> int:
    """Insert one `booking_changes` row at app_now(); `cols` are its optional columns. Returns its id."""
    names = ["booking_id", "action", *cols]
    placeholders = ", ".join(["%s"] * len(names))
    return c.execute(f"INSERT INTO booking_changes ({', '.join(names)}) VALUES ({placeholders}) RETURNING id",
                     (booking_id, action, *cols.values())).fetchone()[0]


HISTORY_COLUMNS = frozenset({"seats", "from_window_id", "to_window_id", "from_sauna_id", "to_sauna_id",
                             "new_booking_id", "voucher_id"})

_HISTORY = (
    "SELECT h.id, h.booking_id, h.action, h.at, h.seats, h.from_window_id, lower(fw.during), upper(fw.during), "
    "h.to_window_id, lower(tw.during), upper(tw.during), nb.reference, v.value_ore "
    "FROM booking_changes h "
    "LEFT JOIN vouchers v ON v.id = h.voucher_id "
    "LEFT JOIN windows fw ON fw.id = h.from_window_id LEFT JOIN windows tw ON tw.id = h.to_window_id "
    "LEFT JOIN bookings nb ON nb.id = h.new_booking_id ")


def history_of(c: psycopg.Connection, booking_ids: list[int]) -> list[tuple]:
    """(id, booking_id, action, at, seats, from window id, from start, from end, to window id, to start, to end,
    new Booking's reference, Voucher value) of every Change of these Bookings, oldest first."""
    return c.execute(_HISTORY + "WHERE h.booking_id = ANY(%s) ORDER BY h.at, h.id", (booking_ids,)).fetchall()


def change(c: psycopg.Connection, change_id: int) -> tuple[int, int | None, int | None, str] | None:
    """(booking_id, new_booking_id, voucher_id, action) of a Change, or None."""
    return c.execute("SELECT booking_id, new_booking_id, voucher_id, action FROM booking_changes WHERE id = %s",
                     (change_id,)).fetchone()


def returns(c: psycopg.Connection, booking_id: int) -> tuple[int | None, int | None]:
    """(card_ore, voucher_id) of the Booking's returns: the sum of its `refund`/`card` rows (None without one) and the
    Voucher of its `refund`/`voucher` row (None without one; a Whole-sauna cancellation writes at most one)."""
    return c.execute(
        "SELECT SUM(amount_ore) FILTER (WHERE method = 'card')::bigint, "
        "MAX(voucher_id) FILTER (WHERE method = 'voucher') "
        "FROM payments WHERE booking_id = %s AND direction = 'refund'", (booking_id,)).fetchone()


# ------------------------------------------------------------------ the one-time key of a Change (AD-9)


def insert_key(c: psycopg.Connection, key: uuid.UUID, session_id: int, endpoint: str, request_hash: bytes,
               change_id: int) -> None:
    """Store the key of a successful Change: `change_id` set, `booking_id` NULL."""
    c.execute("INSERT INTO idempotency_keys (key, session_id, endpoint, request_hash, change_id) "
              "VALUES (%s, %s, %s, %s, %s)", (key, session_id, endpoint, request_hash, change_id))
