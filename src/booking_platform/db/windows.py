"""SQL for the Window schedule, Window generation and the dated Window listing (FR-2, FR-3, FR-13, AD-4).

Every time rule is one SQL function of `0005_windows_horizon.sql` (`venue_today`, `horizon_end`, `venue_date`,
`within_horizon`, `window_started`) or of 0001 (`booking_deadline`), judged on app_now(). Seats left comes only from
`seats_left()` (AD-5). Every function takes the connection of the caller's transaction (`db.run`).
"""

from __future__ import annotations

import datetime as dt

import psycopg

_GENERATE_LOCK = 7816202  # the advisory lock that serialises `ensure_generated` (transaction-scoped)

# A Window a Guest may still book: inside the Booking horizon and before its Booking deadline.
_BOOKABLE = "within_horizon(w.id) AND app_now() < booking_deadline(w.id)"
_ROW = "w.id, lower(w.during), upper(w.during), seats_left(w.id), window_started(w.id), venue_date(w.id)"


def horizon(c: psycopg.Connection) -> tuple[dt.date, dt.date, int, str]:
    """(today, horizon_end, horizon_days, venue_tz): the Venue date of app_now(), the last Venue date inside the
    Booking horizon, the horizon in days and the Venue time zone."""
    return c.execute("SELECT venue_today(), horizon_end(), booking_horizon_days, venue_tz FROM settings").fetchone()


def generate(c: psycopg.Connection) -> int:
    """Insert the scheduled Windows of every Venue date after the high-water mark (and from today) up to the end of
    the Booking horizon, then move the mark. Under a transaction-scoped advisory lock, so two callers never insert
    the same dates. An existing Window that overlaps a new one wins (`ON CONFLICT DO NOTHING`), and no existing
    Window row is locked. With an empty schedule nothing is inserted and the mark stays. Returns the rows
    inserted."""
    c.execute("SELECT pg_advisory_xact_lock(%s)", (_GENERATE_LOCK,))
    # read the dates once, so the INSERT and the mark agree even if Venue midnight passes in between
    today, end = c.execute("SELECT venue_today(), horizon_end()").fetchone()
    inserted = c.execute(
        "INSERT INTO windows (during) "
        "SELECT tstzrange((g.day::date + s.start_time) AT TIME ZONE st.venue_tz, "
        "                 (g.day::date + s.end_time) AT TIME ZONE st.venue_tz, '[)') "
        "FROM settings st "
        "CROSS JOIN LATERAL generate_series("
        "  GREATEST(st.windows_generated_through + 1, %(today)s::date)::timestamp, %(end)s::date::timestamp, "
        "  interval '1 day') AS g(day) "
        "CROSS JOIN window_schedule s "
        "ORDER BY g.day, s.start_time "
        "ON CONFLICT DO NOTHING", {"today": today, "end": end}).rowcount
    c.execute("UPDATE settings SET windows_generated_through = %(end)s "
              "WHERE (windows_generated_through IS NULL OR windows_generated_through < %(end)s) "
              "AND EXISTS (SELECT 1 FROM window_schedule)", {"end": end})
    return inserted


def bookable_dates(c: psycopg.Connection) -> list[dt.date]:
    """The Venue dates with at least one Window inside the Booking horizon and before its Booking deadline."""
    return [r[0] for r in c.execute(
        f"SELECT DISTINCT venue_date(w.id) AS d FROM windows w WHERE {_BOOKABLE} ORDER BY d").fetchall()]


def windows_on(c: psycopg.Connection, date: dt.date) -> list[tuple]:
    """(id, start, end, seats_left, already_started, venue_date) of every bookable Window of a Venue date, in time
    order. Windows past their Booking deadline are left out."""
    return c.execute(f"SELECT {_ROW} FROM windows w WHERE venue_date(w.id) = %s AND {_BOOKABLE} "
                     "ORDER BY lower(w.during)", (date,)).fetchall()


def nearest(c: psycopg.Connection, date: dt.date, seats: int, limit: int = 3) -> list[tuple]:
    """Up to `limit` bookable Windows with room for `seats`, from `date` on: the same day first, then the following
    days inside the Booking horizon, in time order."""
    return c.execute(f"SELECT {_ROW} FROM windows w WHERE venue_date(w.id) >= %s AND {_BOOKABLE} "
                     "AND seats_left(w.id) >= %s ORDER BY lower(w.during) LIMIT %s", (date, seats, limit)).fetchall()


def schedule(c: psycopg.Connection) -> list[tuple[dt.time, dt.time]]:
    return c.execute("SELECT start_time, end_time FROM window_schedule ORDER BY start_time").fetchall()


def venue_tz(c: psycopg.Connection) -> str:
    return c.execute("SELECT venue_tz FROM settings").fetchone()[0]


def seed_schedule(c: psycopg.Connection, rows: list[tuple[dt.time, dt.time]]) -> int:
    """Insert the seed's schedule only when `window_schedule` is empty (AD-18: never overwrite). Returns the rows
    inserted."""
    if c.execute("SELECT EXISTS (SELECT 1 FROM window_schedule)").fetchone()[0]:
        return 0
    for start, end in rows:
        c.execute("INSERT INTO window_schedule (start_time, end_time) VALUES (%s, %s)", (start, end))
    return len(rows)
