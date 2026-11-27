"""SQL for the Administrator's Booking list (FR-16, FR-21, AD-4, AD-5): every Window of a Venue date and its Bookings
(active and cancelled). Reads only: no lock, no write. The figures come only from `window_open_capacity()`,
`window_booked_seats()` and `seats_left()`, and each Window's Placement only from `placement()` (AD-25, Story 5.4);
a Booking due for retention (`retention_due()`) reads with the anonymised name and email, masked in the SELECT, never
by writing. Every function takes the connection of the caller's
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


def placement_on(c: psycopg.Connection, date: dt.date) -> list[tuple]:
    """(window_id, sauna_id, sauna name, capacity, state, seats, reference) of every Sauna of every Window of a Venue
    date, from `placement(w.id)` (AD-25) as given, ordered by Window start, then Fill order. `reference` is the active
    Whole-sauna booking's (through `whole_bookings.booking_id`) when `state` is `whole`, else NULL."""
    return c.execute(
        "SELECT w.id, p.sauna_id, s.name, s.capacity, p.state, p.seats, "
        "       CASE WHEN p.state = 'whole' THEN b.reference END "
        "FROM windows w CROSS JOIN LATERAL placement(w.id) p JOIN saunas s ON s.id = p.sauna_id "
        # a whole_bookings row exists only while its Booking is active (migration 0013): no status filter is needed
        "LEFT JOIN whole_bookings wb ON wb.window_id = w.id AND wb.sauna_id = p.sauna_id "
        "LEFT JOIN bookings b ON b.id = wb.booking_id "
        "WHERE venue_date(w.id) = %s ORDER BY lower(w.during), s.fill_order", (date,)).fetchall()


def bookings_on(c: psycopg.Connection, date: dt.date) -> list[tuple]:
    """(id, window_id, reference, name, email, seats, total_ore, created_at, status, cancelled_at, cancel_cause,
    cancel_remedy, kind, sauna_id, sauna name) of every Booking in a Window of a
    Venue date, active and cancelled, oldest first (`created_at`, then `id`). A cancelled Booking takes no Seats; the
    figures come from the store functions alone. Name and email are masked when the Booking is due. The Sauna id and
    name are NULL for a Seat booking (AD-23)."""
    return c.execute(
        "SELECT b.id, b.window_id, b.reference, "
        "       CASE WHEN retention_due(b.id) THEN %(name)s ELSE b.name END, "
        "       CASE WHEN retention_due(b.id) THEN %(email)s ELSE b.email END, "
        "       b.seats, b.total_ore, b.created_at, b.status, b.cancelled_at, b.cancel_cause, b.cancel_remedy, "
        "       b.kind, s.id, s.name "
        "FROM bookings b JOIN windows w ON w.id = b.window_id LEFT JOIN saunas s ON s.id = b.sauna_id "
        "WHERE venue_date(w.id) = %(date)s "
        "ORDER BY b.created_at, b.id",
        {"date": date, "name": ANONYMISED_NAME, "email": ANONYMISED_EMAIL}).fetchall()
