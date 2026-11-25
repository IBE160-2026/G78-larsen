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
