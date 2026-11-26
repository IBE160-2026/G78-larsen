"""SQL for Vouchers (FR-27, FR-28, AD-30). Only `services.voucher` calls `insert` and `spend`, the writers of
`vouchers`. The code is never passed here: only its SHA-256 hash. Dates come from `app_now()` in Venue time, computed
in SQL (AD-4). Every function takes the connection of the caller's transaction (`db.run`)."""

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


def valid_balance(c: psycopg.Connection, code_hash: bytes) -> int | None:
    """The balance of a valid Voucher (it exists, `balance_ore > 0`, `expires_at > app_now()`), or None. Unlocked and
    read-only: for the quote (FR-28). The balance never leaves `services.voucher`."""
    row = c.execute("SELECT balance_ore FROM vouchers WHERE code_hash = %s AND balance_ore > 0 "
                    "AND expires_at > app_now()", (code_hash,)).fetchone()
    return None if row is None else row[0]


def spend(c: psycopg.Connection, code_hash: bytes, part_ore: int) -> int | None:
    """Take `part_ore` from a valid Voucher in one conditional statement (AD-30); its id, or None when no Voucher with
    this hash has that much left before its expiry. Called only by `services.voucher.spend`, after `lock_windows`."""
    row = c.execute("UPDATE vouchers SET balance_ore = balance_ore - %(part)s WHERE code_hash = %(h)s "
                    "AND balance_ore >= %(part)s AND expires_at > app_now() RETURNING id",
                    {"h": code_hash, "part": part_ore}).fetchone()
    return None if row is None else row[0]


# The last valid date of a Voucher issued from this Booking (Lisa, 2026-11-24): the earliest last valid date of a
# Voucher that paid the Booking or the Booking it was split from (`booking_changes.new_booking_id`, followed back to the
# Booking that was paid), so giving up Seats never renews a Voucher; otherwise the Venue date of app_now() plus one year.
_NEXT_LAST_VALID = (
    "WITH RECURSIVE line(id) AS (SELECT %(b)s::bigint UNION "
    "                            SELECT h.booking_id FROM booking_changes h JOIN line ON h.new_booking_id = line.id) "
    "SELECT COALESCE((SELECT MIN((v.expires_at AT TIME ZONE st.venue_tz)::date - 1) "
    "                 FROM payments p JOIN line ON p.booking_id = line.id JOIN vouchers v ON v.id = p.voucher_id "
    "                 WHERE p.direction = 'charge' AND p.method = 'voucher'), "
    "                ((app_now() AT TIME ZONE st.venue_tz)::date + interval '1 year')::date) "
    "FROM settings st")


def next_last_valid_date(c: psycopg.Connection, booking_id: int) -> dt.date:
    """The last valid date a Voucher issued from the Booking now gets: the spent Voucher's, or one year ahead."""
    return c.execute(_NEXT_LAST_VALID, {"b": booking_id}).fetchone()[0]


# The last valid date of a Voucher returned by `services.payment.refund` (AD-31, Lisa 2026-11-19): the earliest last
# valid date of the Vouchers that paid the Booking, but never less than the Venue date of app_now() plus 30 days. NULL
# when no Voucher paid it.
_REFUND_LAST_VALID = (
    "SELECT GREATEST(MIN((v.expires_at AT TIME ZONE st.venue_tz)::date - 1), "
    "                (app_now() AT TIME ZONE st.venue_tz)::date + 30) "
    "FROM payments p JOIN vouchers v ON v.id = p.voucher_id CROSS JOIN settings st "
    "WHERE p.booking_id = %s AND p.direction = 'charge' AND p.method = 'voucher' "
    "GROUP BY st.venue_tz")


def refund_last_valid_date(c: psycopg.Connection, booking_id: int) -> dt.date | None:
    """The last valid date of the Voucher a refund of the Booking returns now, or None when no Voucher paid it."""
    row = c.execute(_REFUND_LAST_VALID, (booking_id,)).fetchone()
    return None if row is None else row[0]


def a_year_ahead(c: psycopg.Connection) -> dt.date:
    """The last valid date of a new Voucher issued now: the Venue date of app_now() plus one year (AD-30)."""
    return c.execute("SELECT ((app_now() AT TIME ZONE venue_tz)::date + interval '1 year')::date FROM settings"
                     ).fetchone()[0]
