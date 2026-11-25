"""Changes of a Seat booking through its Manage link (FR-26, FR-27, AD-9, AD-28, AD-29, AD-30, AD-31). Story 4.2: the
Seat move; Story 4.3: the Voucher instead of Seats.

Both Changes start with one shared prologue (`_locked`), in the order of AD-29:

1. read the Booking's `window_id` without a lock; `lock_windows` with it and the move's target Window (in id order,
   AD-3; the Voucher Change has no target); re-read the Booking `FOR NO KEY UPDATE`; when `window_id` moved in between,
   `db.Retry` runs the whole unit again with the new Windows locked;
2. re-check the grant by join (`404 not_found`, never 401), then read the key: a known key from the same session with
   the same request returns the first outcome and writes nothing; any other known key is `409 invalid_key`.

`move` is one `db.run`:

1. refuse, in this order: `booking_cancelled`; `booking_changed` (another `version`; fact: the Booking now);
   `change_invalid` (`reason` `seats_exceed` or `same_target`); `outside_horizon` and `deadline_passed` for the target;
   `cutoff_passed` (fact `cutoff_at`); `no_seat_free` (fact: the target's `seats_left`), with the store's
   `booked_within_capacity` as the backstop (FR-10);
2. a full move is one UPDATE of `window_id` with `entry_time = app_now()` and `version + 1`. A partial move (a split)
   takes the Seats off the original (its total follows its price per Seat, `version + 1`) and creates a new Booking
   in the target through `services.reference`, with the original's name, email, price per Seat and Cutoff, the acting
   session, its own Manage token (`services.manage.issue`) and a grant for the acting session, and no `payments` row
   (AD-31);
3. one history row (`services.history.record`), the emails through `outbox.send` with the Change's id, and last the
   key row (`change_id` set). Only a success stores a key.

`voucher` is one `db.run`:

1. refuse, in this order: `booking_cancelled`; `booking_changed`; `change_invalid` (`seats_exceed`); `cutoff_passed`.
   There is no target Window, so no `same_target`, horizon, deadline or capacity refusal;
2. some Seats: one UPDATE takes them off (`total_ore` follows the stored price per Seat, `version + 1`). All Seats:
   one UPDATE cancels the Booking (`cancelled_at = app_now()`, `guest`, `voucher`, `version + 1`; Seats and total stay);
3. `services.voucher.issue` (value = Seats given up x the Booking's `price_per_seat_ore`; valid through
   `services.voucher.next_last_valid_date`: a Voucher that paid the Booking keeps its date, so giving up never renews
   a Voucher; otherwise one year), one `voucher` history row
   with `seats` and `voucher_id`, one `payments` row `refund`/`voucher` of the value with its `voucher_id` (AD-31; no
   `card` row), one email with the Voucher code through `outbox.send` with the Change's id, and last the key row.

The response is the one Change serializer: `{booking, new_booking?, voucher?: {value_ore, last_valid_date}, emails:
[{id, subject, body}]}`, each Booking in the Manage read's shape. It holds no name, email, token, Voucher code or
Sauna; the emails are what the Guest was sent, and the Voucher code is only in an email body. No email of a Change
carries the original's Manage link, and none names a Sauna (FR-4).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import uuid
from zoneinfo import ZoneInfo

import psycopg

from .. import db
from ..db import bookings as bq
from ..db import changes as q
from ..db import seats as sq
from ..db import venue as vq
from . import booking as booking_service
from . import history, manage, outbox, reference
from . import voucher as vouchers
from .errors import Refused
from .windows import ensure_open_for_booking

MOVE_ENDPOINT = "POST /api/manage/seats/move"
VOUCHER_ENDPOINT = "POST /api/manage/seats/voucher"
MANAGE_LINK_STILL_WORKS = "The Manage link in your booking confirmation email still works."
OWN_CONFIRMATION = "The moved seats have their own confirmation email."
NEVER_PAID_OUT = "Use the code when you pay for a new booking. A voucher is never paid out in money."


def move_hash(reference_: str, window_id: int, seats: int, version: int) -> bytes:
    """SHA-256 of the canonical outcome-defining fields of a move (AD-9)."""
    canonical = json.dumps({"action": "move", "reference": reference_, "seats": seats, "version": version,
                            "window_id": window_id}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).digest()


def voucher_hash(reference_: str, seats: int, version: int) -> bytes:
    """SHA-256 of the canonical outcome-defining fields of a Voucher Change (AD-9)."""
    canonical = json.dumps({"action": "voucher", "reference": reference_, "seats": seats, "version": version},
                           sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).digest()


# ------------------------------------------------------------------ the response (one serializer)


def outcome(c: psycopg.Connection, change_id: int) -> dict:
    """The Change serializer: the Booking (and the split-off Booking) as they are now, the Voucher the Change issued
    (value and last valid date, never the code) and the emails the Change sent, read by the Change's id (AD-9)."""
    booking_id, new_booking_id, voucher_id = q.change(c, change_id)
    out = {"booking": manage.booking_now(c, booking_id)}
    if new_booking_id is not None:
        out["new_booking"] = manage.booking_now(c, new_booking_id)
    if voucher_id is not None:
        out["voucher"] = vouchers.facts(c, voucher_id)
    out["emails"] = outbox.of_change(c, change_id)
    return out


# ------------------------------------------------------------------ the Change email (Lisa, 2026-11-24)


def _head(title: str, booking: dict, venue: tuple) -> list[str]:
    """The title, the Venue block, the reference, date and session of a Change email."""
    venue_name, address_lines, phone, venue_email = venue[0], venue[1], venue[2], venue[3]
    start, end = booking["start"][11:16], booking["end"][11:16]
    return [
        title,
        "",
        venue_name,
        ", ".join(address_lines),
        phone,
        venue_email,
        "",
        f"Booking reference: {booking['reference']}",
        f"Date: {booking_service.long_date(dt.date.fromisoformat(booking['date']))}",
        f"Session: {start}–{end}",
    ]


def change_email(booking: dict, venue: tuple, moved: int | None = None, new_reference: str | None = None,
                 extra: list[str] | None = None) -> tuple[str, str]:
    """(subject, body) of the Change confirmation: the Venue block and the Booking as it is now; for a split also the
    Seats moved and the new reference; `extra` lines (a Voucher block) before the last line. No Manage link and no
    Sauna (AD-29, FR-4)."""
    lines = [
        *_head("Booking changed", booking, venue),
        f"Seats: {booking['seats']}",
        f"Total: {booking_service.nok(booking['total_ore'])} incl. VAT",
        "",
    ]
    if new_reference is not None:
        lines += [f"Seats moved: {moved}", f"New booking reference: {new_reference}", OWN_CONFIRMATION, ""]
    lines += extra or []
    lines.append(MANAGE_LINK_STILL_WORKS)
    return f"Booking changed: {booking['reference']}", "\n".join(lines)


def voucher_block(code: str, value_ore: int, last_valid_date: dt.date) -> list[str]:
    """The Voucher block of a Voucher Change email (Lisa, 2026-11-24): the only place the code is ever written."""
    return [
        "Voucher",
        f"Code: {vouchers.display(code)}",
        f"Value: {booking_service.nok(value_ore)}",
        f"Valid until: {booking_service.long_date(last_valid_date)}",
        NEVER_PAID_OUT,
        "",
    ]


def voucher_email(booking: dict, venue: tuple, given_up: int, code: str, value_ore: int, last_valid_date: dt.date
                  ) -> tuple[str, str]:
    """(subject, body) of a Voucher Change (Lisa, 2026-11-24). Some Seats: the Change confirmation (the Booking as it
    is now) with the Voucher block. All Seats (the Booking is cancelled): "Booking cancelled", the Venue block,
    reference, date, session and the Seats given up, then the Voucher block. Both end with the Manage link line."""
    block = voucher_block(code, value_ore, last_valid_date)
    if booking["status"] != "cancelled":
        return change_email(booking, venue, extra=block)
    lines = [*_head("Booking cancelled", booking, venue), f"Seats given up: {given_up}", "", *block,
             MANAGE_LINK_STILL_WORKS]
    return f"Booking cancelled: {booking['reference']}", "\n".join(lines)


# ------------------------------------------------------------------ the shared prologue and refusals (AD-29)


def _locked(c: psycopg.Connection, session_id: int, booking_id: int, extra_windows: list[int], key: uuid.UUID,
            endpoint: str, h: bytes) -> q.Locked | dict:
    """The prologue of every Change: the unlocked read of `window_id`, `lock_windows` with it and `extra_windows`, the
    locked re-read (`db.Retry` when `window_id` moved), the grant re-check by join and the key read. Returns the locked
    Booking, or the first outcome (a dict) when the key is a repeat of this request from this session."""
    current = q.window_of(c, booking_id)  # unlocked (AD-29)
    if current is None:
        raise Refused("not_found")
    db.lock_windows(c, [current, *extra_windows])
    b = q.lock_booking(c, booking_id)
    if b is None:
        raise Refused("not_found")
    if b.window_id != current:
        raise db.Retry()  # moved in between: lock the new Windows
    if not q.grant_valid(c, session_id, booking_id):
        raise Refused("not_found")
    known = bq.key(c, key)
    if known is not None:
        k_session, k_endpoint, k_hash, _k_booking, k_change = known
        if k_session == session_id and k_endpoint == endpoint and bytes(k_hash) == h and k_change is not None:
            return outcome(c, k_change)
        raise Refused("invalid_key")
    return b


def _refuse_unless_current(c: psycopg.Connection, b: q.Locked, booking_id: int, seats: int, version: int) -> None:
    """The first refusals of AD-29: `booking_cancelled`, `booking_changed`, `change_invalid` `seats_exceed`."""
    if b.status == "cancelled":
        raise Refused("booking_cancelled")
    if b.version != version:
        raise Refused("booking_changed", booking=manage.booking_now(c, booking_id))
    if not 1 <= seats <= b.seats:
        raise Refused("change_invalid", reason="seats_exceed")


def _refuse_after_cutoff(c: psycopg.Connection, b: q.Locked) -> None:
    """`cutoff_passed` with the Booking's `cutoff_at` in Venue time (AD-4)."""
    if not b.change_allowed:
        raise Refused("cutoff_passed", cutoff_at=b.cutoff_at.astimezone(ZoneInfo(q.venue_tz(c))).isoformat())


# ------------------------------------------------------------------ the move


def _refuse_unless_changeable(c: psycopg.Connection, b: q.Locked, booking_id: int, window_id: int, seats: int,
                              version: int) -> None:
    """The refusals of AD-29 for a move in their order, up to and including the Cutoff."""
    _refuse_unless_current(c, b, booking_id, seats, version)
    if window_id == b.window_id:
        raise Refused("change_invalid", reason="same_target")
    ensure_open_for_booking(c, window_id)  # outside_horizon, then deadline_passed (an unknown Window: not_found)
    _refuse_after_cutoff(c, b)


def move(session_id: int, booking_id: int, reference_: str, window_id: int, seats: int, version: int,
         key: uuid.UUID) -> dict:
    """Move `seats` Seats of the Booking to the Window `window_id` (all of them: the same Booking moves; fewer: a
    split). Returns the Change serializer; a repeat of a known key returns the first outcome and writes nothing."""
    h = move_hash(reference_, window_id, seats, version)

    def work(c):
        b = _locked(c, session_id, booking_id, [window_id], key, MOVE_ENDPOINT, h)
        if isinstance(b, dict):
            return b  # a repeat: the first outcome
        _refuse_unless_changeable(c, b, booking_id, window_id, seats, version)
        left = sq.seats_left(c, window_id)  # after the lock (FR-12); the store stays the backstop
        if left < seats:
            raise Refused("no_seat_free", seats_left=max(left, 0))

        venue = vq.venue_facts(c)
        if seats == b.seats:
            q.move_all(c, booking_id, window_id)
            change_id = history.record(c, booking_id, "move", seats=seats, from_window_id=b.window_id,
                                       to_window_id=window_id)
            subject, body = change_email(booking_service.facts(c, booking_id), venue)
            outbox.send(c, b.email, subject, body, booking_id=booking_id, change_id=change_id)
        else:
            q.give_up_seats(c, booking_id, seats)
            new_id, new_reference = reference.claim(
                lambda ref: sq.insert_booking(c, ref, window_id, seats, b.name, b.email, b.price_per_seat_ore,
                                              session_id, cutoff=b.cutoff))
            token = manage.issue(c, new_id, grant_to=session_id)  # its own link (AD-28), no payments row (AD-31)
            change_id = history.record(c, booking_id, "move", seats=seats, from_window_id=b.window_id,
                                       to_window_id=window_id, new_booking_id=new_id)
            subject, body = change_email(booking_service.facts(c, booking_id), venue, seats, new_reference)
            outbox.send(c, b.email, subject, body, booking_id=booking_id, change_id=change_id)
            new_facts = booking_service.facts(c, new_id)
            subject, body = booking_service.confirmation_email(new_facts, venue, manage.link(token))
            outbox.send(c, new_facts["email"], subject, body, booking_id=new_id, change_id=change_id)
        q.insert_key(c, key, session_id, MOVE_ENDPOINT, h, change_id)
        return outcome(c, change_id)

    return db.run(work)


# ------------------------------------------------------------------ the Voucher instead of Seats (FR-27)


def voucher(session_id: int, booking_id: int, reference_: str, seats: int, version: int, key: uuid.UUID) -> dict:
    """Give up `seats` Seats of the Booking for one Voucher worth `seats x price_per_seat_ore` (all of them: the Booking
    is cancelled). Returns the Change serializer with `voucher`; a repeat of a known key returns the first outcome and
    writes nothing (no second Voucher)."""
    h = voucher_hash(reference_, seats, version)

    def work(c):
        b = _locked(c, session_id, booking_id, [], key, VOUCHER_ENDPOINT, h)
        if isinstance(b, dict):
            return b  # a repeat: the first outcome
        _refuse_unless_current(c, b, booking_id, seats, version)
        _refuse_after_cutoff(c, b)

        value_ore = seats * b.price_per_seat_ore  # the price paid, never the current setting (AD-13)
        if seats == b.seats:
            q.cancel_for_voucher(c, booking_id)
        else:
            q.give_up_for_voucher(c, booking_id, seats)
        voucher_id, code, last_valid_date = vouchers.issue(
            c, booking_id, value_ore, last_valid_date=vouchers.next_last_valid_date(c, booking_id))
        change_id = history.record(c, booking_id, "voucher", seats=seats, voucher_id=voucher_id)
        bq.insert_payment(c, booking_id, "refund", "voucher", value_ore, voucher_id)  # AD-31: no card row
        subject, body = voucher_email(booking_service.facts(c, booking_id), vq.venue_facts(c), seats, code, value_ore,
                                      last_valid_date)
        outbox.send(c, b.email, subject, body, booking_id=booking_id, change_id=change_id)
        q.insert_key(c, key, session_id, VOUCHER_ENDPOINT, h, change_id)
        return outcome(c, change_id)

    return db.run(work)
