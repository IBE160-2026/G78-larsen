"""Whole-sauna bookings (FR-29, FR-30, AD-23, AD-24), shown to Guests as "Private sauna".

Story 5.1 holds the listing: for a Venue date, the Saunas a Guest may book whole and their free Windows. The store
judges FR-29 (`whole_bookable`, the only statement of the rule); the time rules are the SQL predicates of AD-4.

Story 5.2 holds the booking, `create`, in the order of `services.booking.create` (AD-3, AD-9, AD-13): the request hash
(endpoint, `kind`, `window_id`, `sauna_id`, and the Voucher part when one is sent); with a Voucher, the card part from
an unlocked read of the Sauna's price; `payment.charge()` unless a Voucher covers the total; then one `db.run`:
`lock_windows`, the key read (a repeat returns the first outcome, any other known key is `invalid_key`),
`ensure_open_for_booking` (`outside_horizon`, then `deadline_passed`), the price read again (NULL: `sauna_unavailable`),
the Booking through `services.reference` (`kind = 'whole'`, `total_ore` = the price, `price_per_seat_ore` NULL, the
Whole-sauna Cutoff), its `whole_bookings` row, the Voucher spend and the `payments` rows as Story 4.4, the Manage
token, the confirmation email and last the key row. No Hold is read, released or written: the Sauna is not held while
the Guest pays (FR-29).

FR-29 is judged again by the store at the capacity row: in this action only, `db.run` maps `whole_bookable`,
`booked_within_capacity` and the `(window_id, sauna_id)` key to `409 sauna_unavailable` (AD-24), so nothing is charged,
written or emailed. The global refusal table is unchanged, so the Seat flow keeps `no_seat_free`.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import uuid
from itertools import groupby
from zoneinfo import ZoneInfo

import psycopg

from .. import db
from ..db import bookings as bq
from ..db import venue as vq
from ..db import whole as q
from ..db import windows as wq
from . import booking, manage, outbox, payment, reference, voucher
from .errors import Refused
from .windows import ensure_generated, ensure_open_for_booking

ENDPOINT = booking.ENDPOINT  # one endpoint, `POST /api/bookings`; the hash holds `kind`

# The store's FR-29 refusals in a Whole-sauna action (AD-24), passed to `db.run`.
REFUSALS = {
    "whole_bookable": "sauna_unavailable",
    "booked_within_capacity": "sauna_unavailable",
    "whole_bookings_window_id_sauna_id_key": "sauna_unavailable",
}


def listing(date: dt.date) -> dict:
    """`GET /api/private-saunas?date=`: `{saunas: [{id, name, capacity, whole_price_ore, windows: [{id, start, end,
    already_started}]}], horizon_end, horizon_days}`. Saunas in Fill order, each with its free Windows in time order;
    a Sauna with no free Window is left out. A date outside `today..horizon_end` is `409 outside_horizon`, judged
    before anything is written, as `GET /api/windows`. Takes no lock; the only write is `ensure_generated()`."""
    today, horizon_end, _, _ = db.run(wq.horizon)
    if not today <= date <= horizon_end:
        raise Refused("outside_horizon", today=today.isoformat(), horizon_end=horizon_end.isoformat())
    ensure_generated()

    def work(c):
        _, horizon_end, days, tz_name = wq.horizon(c)
        return horizon_end, days, ZoneInfo(tz_name), q.pairs_on(c, date)

    horizon_end, days, tz, rows = db.run(work)
    saunas = []
    for (sid, name, capacity, price), pairs in groupby(rows, key=lambda r: r[:4]):
        saunas.append({
            "id": sid, "name": name, "capacity": capacity, "whole_price_ore": price,
            "windows": [{"id": wid, "start": start.astimezone(tz).isoformat(), "end": end.astimezone(tz).isoformat(),
                         "already_started": started} for *_, wid, start, end, started in pairs],
        })
    return {"saunas": saunas, "horizon_end": horizon_end.isoformat(), "horizon_days": days}


# ------------------------------------------------------------------ the booking (Story 5.2)


def request_hash(window_id: int, sauna_id: int, voucher_part: int | None = None) -> bytes:
    """SHA-256 of the canonical outcome-defining fields of a Whole-sauna booking (AD-9): the endpoint, `kind`, the
    Window and the Sauna, and the Voucher part when a Voucher is sent. Never the name, the email or a Voucher code.
    A key first used for one Sauna (or for Seats) therefore cannot book another."""
    fields = {"endpoint": ENDPOINT, "kind": "whole", "sauna_id": sauna_id, "window_id": window_id}
    if voucher_part is not None:
        fields["voucher_part_ore"] = voucher_part
    canonical = json.dumps(fields, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).digest()


def total(c: psycopg.Connection, sauna_id: int) -> int:
    """The total of a Whole-sauna booking of the Sauna now: its `whole_price_ore` (AD-23). An unknown Sauna is
    `404 not_found`; one that is not offered whole (no price, or not bookable whole) is `409 sauna_unavailable`."""
    row = q.price(c, sauna_id)
    if row is None:
        raise Refused("not_found")
    if row[0] is None:
        raise Refused("sauna_unavailable")
    return row[0]


def create(session_id: int, window_id: int, sauna_id: int, name: str, email: str, key: uuid.UUID,
           voucher_code: str | None = None, voucher_part: int | None = None) -> dict:
    """Pay for the Sauna `sauna_id` whole in the Window `window_id` and create the Booking. Returns `{booking,
    emails}` in the shape of `services.booking.create`; a repeat of a known key from the same session with the same
    request returns the first outcome and writes nothing, any other known key is `409 invalid_key`. Refusals after the
    lock, in this order: `not_found` (unknown Window), `outside_horizon`, `deadline_passed`, `not_found` (unknown
    Sauna), `sauna_unavailable` (no price, or FR-29 judged by the store); then `voucher_invalid` with a Voucher."""
    h = request_hash(window_id, sauna_id, voucher_part)
    with_voucher = voucher_part is not None
    # Before the lock (AD-13): a failed or held payment writes nothing. With a Voucher the card part comes from an
    # unlocked read of the price, and no card part means no charge() at all; nothing here refuses on the Sauna or the
    # Voucher (an unknown or unpriced Sauna is refused after the lock, in the order above).
    card_part = None
    if with_voucher:
        row = db.run(lambda c: q.price(c, sauna_id))
        card_part = None if row is None or row[0] is None else row[0] - voucher_part
    decided = payment.charge() if not with_voucher or card_part is None or card_part > 0 else None

    def work(c):
        db.lock_windows(c, [window_id])
        known = bq.key(c, key)  # the first statement after the lock (AD-9)
        if known is not None:
            k_session, k_endpoint, k_hash, k_booking, _k_change = known
            if k_session == session_id and k_endpoint == ENDPOINT and bytes(k_hash) == h and k_booking is not None:
                return {"booking": booking.facts(c, k_booking), "emails": outbox.of_booking(c, k_booking)}
            raise Refused("invalid_key")
        ensure_open_for_booking(c, window_id)  # not_found, outside_horizon, then deadline_passed
        price = total(c, sauna_id)  # read again after the lock: NULL is sauna_unavailable
        booking_id, _ = reference.claim(
            lambda ref: q.insert_booking(c, ref, window_id, sauna_id, name, email, price, session_id))
        q.insert_capacity(c, booking_id, window_id, sauna_id)  # FR-29 judged by the store (AD-24)
        if with_voucher:
            if voucher_part > price or card_part is None or price - voucher_part != card_part:
                raise Refused("voucher_invalid")  # a part that does not fit the stored total: nothing is written
            voucher_id = voucher.spend(c, voucher_code, voucher_part)  # last before the ledger rows (AD-30)
            bq.insert_payment(c, booking_id, "charge", "voucher", voucher_part, voucher_id)
            if decided is not None:
                payment.record(c, decided, booking_id, card_part)
        else:
            payment.record(c, decided, booking_id, price)
        facts = booking.facts(c, booking_id)
        token = manage.issue(c, booking_id)  # after the insert, in the same transaction (AD-28)
        subject, body = booking.confirmation_email(facts, vq.venue_facts(c), manage.link(token))
        outbox.send(c, facts["email"], subject, body, booking_id=booking_id)
        bq.insert_key(c, key, session_id, ENDPOINT, h, booking_id)
        return {"booking": facts, "emails": outbox.of_booking(c, booking_id)}

    return db.run(work, refusals=REFUSALS)
