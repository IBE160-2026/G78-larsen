"""SQL for Whole-sauna bookings (FR-29, FR-30, AD-23, AD-24): the pairs of Sauna and Window a Guest may book whole.

FR-29's store rule is only `whole_bookable()` (0013); the time rules are the listing's `_BOOKABLE` predicates of
`db.windows` (`within_horizon`, `booking_deadline`). Every function takes the connection of the caller's transaction
(`db.run`).
"""

from __future__ import annotations

import datetime as dt

import psycopg

from .windows import _BOOKABLE


def pairs_on(c: psycopg.Connection, date: dt.date, ignore_booking: int | None = None) -> list[tuple]:
    """(sauna_id, name, capacity, whole_price_ore, window_id, start, end, already_started) of every pair on a Venue
    date where the Window is inside the Booking horizon and before its Booking deadline and `whole_bookable` holds
    (judged as if the capacity row of `ignore_booking` did not exist). Saunas in Fill order, then Windows in time
    order. Reads only."""
    return c.execute(
        "SELECT s.id, s.name, s.capacity, s.whole_price_ore, w.id, lower(w.during), upper(w.during), "
        "       window_started(w.id) "
        "FROM saunas s CROSS JOIN windows w "
        f"WHERE venue_date(w.id) = %s AND {_BOOKABLE} AND whole_bookable(w.id, s.id, %s) "
        "ORDER BY s.fill_order, lower(w.during)", (date, ignore_booking)).fetchall()


# ------------------------------------------------------------------ the Whole-sauna booking (Story 5.2)


def price(c: psycopg.Connection, sauna_id: int) -> tuple[int | None] | None:
    """(whole_price_ore,) of a Sauna, the price NULL when it is not offered whole (not `bookable_whole`, or no price,
    AD-23); None for an unknown Sauna. Reads only, takes no lock."""
    return c.execute("SELECT CASE WHEN bookable_whole THEN whole_price_ore END FROM saunas WHERE id = %s",
                     (sauna_id,)).fetchone()


def insert_booking(c: psycopg.Connection, reference: str, window_id: int, sauna_id: int, name: str, email: str,
                   total_ore: int, session_id: int) -> int | None:
    """Insert a Whole-sauna booking under `reference` (AD-23): `kind = 'whole'`, the Sauna, `seats` and
    `price_per_seat_ore` NULL, `total_ore` the Sauna's price. None when the reference is taken: `ON CONFLICT
    (reference) DO NOTHING`, so a clash neither raises nor aborts the transaction (AD-20). The time of booking and the
    entry time are one `app_now()` (AD-7); the Booking keeps its own copy of the Whole-sauna Cutoff
    (`settings.cutoff_whole`, AD-4). Its capacity row is `insert_capacity`, written next."""
    row = c.execute(
        "INSERT INTO bookings (reference, window_id, kind, sauna_id, name, email, total_ore, session_id, "
        "created_at, entry_time, cutoff) "
        "SELECT %s, %s, 'whole', %s, %s, %s, %s, %s, n, n, (SELECT cutoff_whole FROM settings) "
        "FROM (SELECT app_now() AS n) x "
        "ON CONFLICT (reference) DO NOTHING RETURNING id",
        (reference, window_id, sauna_id, name, email, total_ore, session_id)).fetchone()
    return None if row is None else row[0]


def insert_capacity(c: psycopg.Connection, booking_id: int, window_id: int, sauna_id: int) -> None:
    """The Booking's capacity row in `whole_bookings`, after the Booking (AD-23's write order). `trg_check_whole`
    judges FR-29 here (`whole_bookable`), the capacity triggers recompute the Window (`booked_within_capacity`) and
    the `(window_id, sauna_id)` key refuses a second row for the pair."""
    c.execute("INSERT INTO whole_bookings (window_id, sauna_id, booking_id) VALUES (%s, %s, %s)",
              (window_id, sauna_id, booking_id))
