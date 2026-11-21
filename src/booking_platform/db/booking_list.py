"""SQL for the Administrator's Booking list (FR-16, FR-21, AD-4, AD-5): every Window of a Venue date and its active
Bookings. Reads only: no lock, no write. The figures come only from `window_open_capacity()`,
`window_booked_seats()` and `seats_left()`; a Booking due for retention (`retention_due()`) reads with the anonymised
name and email, masked in the SELECT, never by writing. Every function takes the connection of the caller's
transaction (`db.run`)."""

from __future__ import annotations

import datetime as dt

import psycopg

from .retention import ANONYMISED_EMAIL, ANONYMISED_NAME


def windows_on(c: psycopg.Connection, date: dt.date) -> list[tuple]:
    """(id, start, end, seat_capacity, seats_booked, seats_left) of every Window of a Venue date, bookable or not, in
    time order."""
    return c.execute(
        "SELECT w.id, lower(w.during), upper(w.during), window_open_capacity(w.id), window_booked_seats(w.id), "
        "seats_left(w.id) FROM windows w WHERE venue_date(w.id) = %s ORDER BY lower(w.during)", (date,)).fetchall()


def bookings_on(c: psycopg.Connection, date: dt.date) -> list[tuple]:
    """(window_id, reference, name, email, seats, total_ore, created_at) of every active Booking in a Window of a
    Venue date, oldest first (`created_at`, then `id`). Name and email are masked when the Booking is due."""
    return c.execute(
        "SELECT b.window_id, b.reference, "
        "       CASE WHEN retention_due(b.id) THEN %(name)s ELSE b.name END, "
        "       CASE WHEN retention_due(b.id) THEN %(email)s ELSE b.email END, "
        "       b.seats, b.total_ore, b.created_at "
        "FROM bookings b JOIN windows w ON w.id = b.window_id "
        "WHERE venue_date(w.id) = %(date)s AND b.status = 'active' "
        "ORDER BY b.created_at, b.id",
        {"date": date, "name": ANONYMISED_NAME, "email": ANONYMISED_EMAIL}).fetchall()
