"""Vouchers (FR-27, AD-30). `issue` is the only writer of `vouchers`.

A code is 16 upper-case Crockford base32 characters from `secrets` (80 bits), shown as `XXXX-XXXX-XXXX-XXXX`. Only the
unkeyed SHA-256 hash of the 16 characters (no hyphens) is stored in `vouchers`, never any part of the code. The code
is returned only to build the email of the Change that issued it: it is written only into that email's body (the Outbox
row, and the email as the Change response returns it), never into another column, a log or any other response field
(AD-19, AD-29). A new Voucher is valid through the Venue date of app_now() plus one year; `expires_at` is 00:00 Venue time on
the day after (computed in SQL, AD-4).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import secrets

import psycopg

from ..db import vouchers as q

CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
LENGTH = 16


def new_code() -> str:
    """16 Crockford base32 characters from `secrets` (80 bits)."""
    return "".join(secrets.choice(CROCKFORD) for _ in range(LENGTH))


def display(code: str) -> str:
    """"XXXX-XXXX-XXXX-XXXX"."""
    return "-".join(code[i:i + 4] for i in range(0, LENGTH, 4))


def code_hash(code: str) -> bytes:
    """The unkeyed SHA-256 of the 16 characters (no hyphens)."""
    return hashlib.sha256(code.encode("ascii")).digest()


def issue(c: psycopg.Connection, booking_id: int, value_ore: int, *, last_valid_date: dt.date | None = None
          ) -> tuple[int, str, dt.date]:
    """Issue one Voucher worth `value_ore` from the Booking, in the caller's transaction (after its lock). Returns
    (id, code, last valid date); the code is for the email only."""
    code = new_code()
    voucher_id, last = q.insert(c, code_hash(code), value_ore, booking_id, last_valid_date)
    return voucher_id, code, last


def facts(c: psycopg.Connection, voucher_id: int) -> dict:
    """`{value_ore, last_valid_date}` of a Voucher, as the Change response carries it. Never the code."""
    value_ore, last = q.read(c, voucher_id)
    return {"value_ore": value_ore, "last_valid_date": last.isoformat()}
