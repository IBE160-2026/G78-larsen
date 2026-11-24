"""SQL for Vouchers (FR-27, AD-30). Only `services.voucher` calls `insert`, the one writer of `vouchers`. The code is
never passed here: only its SHA-256 hash. Dates come from `app_now()` in Venue time, computed in SQL (AD-4). Every
function takes the connection of the caller's transaction (`db.run`)."""

from __future__ import annotations

import datetime as dt

import psycopg

# The last valid date: the given one, or the Venue date of app_now() plus one year (29 February -> 28 February).
# `expires_at` is 00:00 Venue time on the day after it.
_INSERT = (
    "WITH d AS (SELECT st.venue_tz AS tz, COALESCE(%(last)s::date, "
    "                  ((app_now() AT TIME ZONE st.venue_tz)::date + interval '1 year')::date) AS last "
    "           FROM settings st) "
    "INSERT INTO vouchers (code_hash, value_ore, balance_ore, issued_at, expires_at, booking_id) "
    "SELECT %(h)s, %(v)s, %(v)s, app_now(), (d.last + 1)::timestamp AT TIME ZONE d.tz, %(b)s FROM d "
    "RETURNING id, (expires_at AT TIME ZONE (SELECT venue_tz FROM settings))::date - 1")


def insert(c: psycopg.Connection, code_hash: bytes, value_ore: int, booking_id: int | None,
           last_valid_date: dt.date | None = None) -> tuple[int, dt.date]:
    """Insert one Voucher with `balance_ore = value_ore`, issued at app_now(); returns (id, last valid date)."""
    row = c.execute(_INSERT, {"h": code_hash, "v": value_ore, "b": booking_id, "last": last_valid_date}).fetchone()
    return row[0], row[1]


def read(c: psycopg.Connection, voucher_id: int) -> tuple[int, dt.date] | None:
    """(value_ore, last valid date) of a Voucher, or None. Never its hash or balance."""
    return c.execute(
        "SELECT v.value_ore, (v.expires_at AT TIME ZONE st.venue_tz)::date - 1 FROM vouchers v CROSS JOIN settings st "
        "WHERE v.id = %s", (voucher_id,)).fetchone()
