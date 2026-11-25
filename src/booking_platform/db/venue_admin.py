"""SQL for the Administrator's slice actions: Blocks, Whole-booking-only marks and Settings."""

from __future__ import annotations

import datetime as dt

import psycopg


def insert_block(c: psycopg.Connection, sauna_id: int, start: dt.datetime, end: dt.datetime) -> int:
    return c.execute("INSERT INTO blocks (sauna_id, during) VALUES (%s, tstzrange(%s, %s, '[)')) RETURNING id",
                     (sauna_id, start, end)).fetchone()[0]


def delete_block(c: psycopg.Connection, block_id: int) -> int:
    return c.execute("DELETE FROM blocks WHERE id = %s", (block_id,)).rowcount


def release_after_deadline(c: psycopg.Connection, window_id: int) -> bool | None:
    """True when the Release time is on and later than the Window's Booking deadline; None for an unknown Window."""
    row = c.execute("SELECT release_on AND release_due(id) > booking_deadline(id) FROM windows, settings WHERE id = %s",
                    (window_id,)).fetchone()
    return None if row is None else row[0]


def insert_mark(c: psycopg.Connection, window_id: int, sauna_id: int) -> int:
    return c.execute("INSERT INTO marks (window_id, sauna_id) VALUES (%s, %s) RETURNING id",
                     (window_id, sauna_id)).fetchone()[0]


def delete_mark(c: psycopg.Connection, window_id: int, sauna_id: int) -> int:
    return c.execute("DELETE FROM marks WHERE window_id = %s AND sauna_id = %s", (window_id, sauna_id)).rowcount


def window_ids(c: psycopg.Connection) -> list[int]:
    return [r[0] for r in c.execute("SELECT id FROM windows ORDER BY id").fetchall()]


def recompute_window(c: psycopg.Connection, window_id: int) -> None:
    c.execute("SELECT recompute_window(%s)", (window_id,))


def windows_breaking_release_limit(c: psycopg.Connection, release_on: bool, release_time: dt.time,
                                   booking_deadline_minutes: int) -> list[int]:
    """Windows with an unreleased Whole-booking-only Sauna whose Release time under the proposed Settings would be
    later than their Booking deadline (FR-39)."""
    return [r[0] for r in c.execute(
        "SELECT w.id FROM windows w, settings st WHERE %s AND EXISTS ("
        "  SELECT 1 FROM marks m WHERE m.window_id = w.id "
        "  AND NOT EXISTS (SELECT 1 FROM releases r WHERE r.window_id = m.window_id AND r.sauna_id = m.sauna_id)) "
        "AND ((lower(w.during) AT TIME ZONE st.venue_tz)::date + %s::time) AT TIME ZONE st.venue_tz "
        "    > lower(w.during) + make_interval(mins => %s) ORDER BY w.id",
        (release_on, release_time, booking_deadline_minutes)).fetchall()]


def update_settings(c: psycopg.Connection, release_on: bool, release_time: dt.time,
                    booking_deadline_minutes: int) -> None:
    c.execute("UPDATE settings SET release_on = %s, release_time = %s, booking_deadline_minutes = %s",
              (release_on, release_time, booking_deadline_minutes))
