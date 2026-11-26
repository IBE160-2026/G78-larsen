"""The Simulated payment (FR-6, FR-7, AD-13, AD-14). No payment credential and no external service.

`charge()` decides the card part's outcome before the action locks anything; `record()` writes its `payments` row
after the lock, in the action's transaction. The test switch `payment` is read here only, and only for runs made
for an HTTP request, so the seed always charges `ok`.

`refund()` is the only refund (AD-31): each part of a Booking goes back the way it was paid. The card part is one
`refund`/`card` row (simulated: it cannot fail and reads no switch); the Voucher part becomes one new Voucher of that
sum, recorded as a `refund`/`voucher` row. No path turns a Voucher balance into a card refund (AD-30)."""

from __future__ import annotations

from dataclasses import dataclass

import psycopg

from .. import config
from ..db import bookings as q
from ..db import changes as cq
from ..db import vouchers as vq
from . import voucher
from .errors import Refused


@dataclass(frozen=True)
class Charge:
    """A charge that has been decided and is written by `record`."""

    method: str = "card"


def charge() -> Charge:
    """Decide the outcome. `fail` is `409 payment_failed`, `hold` is `409 payment_pending`; both are raised before
    anything is written, so nothing is stored under the key and a retry runs again (AD-9)."""
    outcome = config.switches().payment if config.in_request.get() else "ok"
    if outcome == "fail":
        raise Refused("payment_failed")
    if outcome == "hold":
        raise Refused("payment_pending")
    return Charge()


def record(c: psycopg.Connection, decided: Charge, booking_id: int, amount_ore: int) -> None:
    """Write the charge as a `payments` row. A total of 0 (a free price) is no charge, so no row (`amount_ore > 0`)."""
    if amount_ore > 0:
        q.insert_payment(c, booking_id, "charge", decided.method, amount_ore)


class SplitRefund(RuntimeError):
    """`refund()` of a Booking with a split in its history: not decided until If-time 7 (AD-31, Deferred). Unmapped,
    so the request is a `500 internal_error`."""


def refund(c: psycopg.Connection, booking_id: int) -> dict:
    """Return what the Booking was paid, in the caller's transaction (after its lock): its card charges as one
    `refund`/`card` row, its Voucher charges as one new Voucher of their sum (valid through the earliest last valid
    date of the Vouchers used, but never less than 30 days after app_now()) with a `refund`/`voucher` row. Returns
    `{card_ore, voucher: {id, code, value_ore, last_valid_date} | None}`; the code is for the email only. A Booking
    with a split in its history raises `SplitRefund` (a 500)."""
    if cq.has_split(c, booking_id):
        raise SplitRefund(f"Booking {booking_id} has a split in its history")
    voucher_ore, card_ore = q.charges(c, booking_id)
    if card_ore > 0:
        q.insert_payment(c, booking_id, "refund", "card", card_ore)
    returned = None
    if voucher_ore > 0:
        voucher_id, code, last = voucher.issue(c, booking_id, voucher_ore,
                                               last_valid_date=vq.refund_last_valid_date(c, booking_id))
        q.insert_payment(c, booking_id, "refund", "voucher", voucher_ore, voucher_id)
        returned = {"id": voucher_id, "code": code, "value_ore": voucher_ore, "last_valid_date": last}
    return {"card_ore": card_ore, "voucher": returned}
