"""Vouchers (FR-27, FR-28, AD-30). `issue` and `spend` are the only writers of `vouchers`.

A code is 16 upper-case Crockford base32 characters from `secrets` (80 bits), shown as `XXXX-XXXX-XXXX-XXXX`. Only the
unkeyed SHA-256 hash of the 16 characters (no hyphens) is stored in `vouchers`, never any part of the code. The code
is returned only to build the email of the Change that issued it: it is written only into that email's body (the Outbox
row, and the email as the Change response returns it), never into another column, a log or any other response field
(AD-19, AD-29). A new Voucher is valid through the Venue date of app_now() plus one year; `expires_at` is 00:00 Venue time on
the day after (computed in SQL, AD-4).

Paying with a Voucher (FR-28): a typed code is normalised by `normalise` (the one place) and hashed; `quote` reads the
balance without a lock and writes nothing, `spend` takes the Voucher part in one conditional UPDATE after the action's
`lock_windows`. Every unusable code (malformed, unknown, used up, expired, or not enough left) is the same
`409 voucher_invalid` with no facts; no response, log line or table holds the code, a balance or an expiry.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import secrets

import psycopg

from .. import db
from ..db import seats as sq
from ..db import venue as vq
from ..db import vouchers as q
from .errors import Refused

CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
LENGTH = 16
MAX_INPUT = 32  # longer typed input is never a code
_LOOKALIKES = str.maketrans({"I": "1", "L": "1", "O": "0"})


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


# ------------------------------------------------------------------ paying with a Voucher (FR-28)


def normalise(text: object) -> str | None:
    """The 16 Crockford characters a typed code stands for, or None. Input of at most 32 characters is upper-cased,
    hyphens and spaces are removed, `I` and `L` become `1` and `O` becomes `0` (AD-30)."""
    if not isinstance(text, str) or len(text) > MAX_INPUT:
        return None
    code = text.upper().replace("-", "").replace(" ", "").translate(_LOOKALIKES)
    if len(code) != LENGTH or any(ch not in CROCKFORD for ch in code):
        return None
    return code


def quote(window_id: int, seats: int, code: object) -> dict:
    """`{voucher_part_ore, card_part_ore}` for `seats` Seats in the Window at the price in Settings: the Voucher part is
    the lesser of the balance and the total. Takes no lock and writes nothing. An unknown Window is `404 not_found`;
    any unusable code is `409 voucher_invalid` with no facts."""
    normalised = normalise(code)

    def work(c):
        if sq.get_window(c, window_id) is None:
            raise Refused("not_found")
        total = seats * vq.venue_facts(c)[7]
        balance = None if normalised is None else q.valid_balance(c, code_hash(normalised))
        if balance is None:
            raise Refused("voucher_invalid")
        part = min(balance, total)
        return {"voucher_part_ore": part, "card_part_ore": total - part}

    return db.run(work)


def spend(c: psycopg.Connection, code: object, part_ore: int) -> int:
    """Take `part_ore` from the Voucher in the caller's transaction, after its `lock_windows` (AD-30); returns its id.
    No usable Voucher with that much left is `409 voucher_invalid`, and the caller's transaction rolls back."""
    normalised = normalise(code)
    voucher_id = None if normalised is None else q.spend(c, code_hash(normalised), part_ore)
    if voucher_id is None:
        raise Refused("voucher_invalid")
    return voucher_id
