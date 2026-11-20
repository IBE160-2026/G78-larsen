"""The Simulated payment (FR-6, FR-7, AD-13, AD-14). No payment credential and no external service.

`charge()` decides the card part's outcome before the action locks anything; `record()` writes its `payments` row
after the lock, in the action's transaction. The test switch `payment` is read here only, and only for runs made
for an HTTP request, so the seed always charges `ok`."""

from __future__ import annotations

from dataclasses import dataclass

import psycopg

from .. import config
from ..db import bookings as q
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
