"""Changes of a Seat booking through its Manage link (FR-26, AD-9, AD-28, AD-29). Story 4.2: the Seat move.

`move` is one `db.run`, in the order of AD-29:

1. read the Booking's `window_id` without a lock; `lock_windows` with it and the target Window (in id order, AD-3);
   re-read the Booking `FOR NO KEY UPDATE`; when `window_id` moved in between, `db.Retry` runs the whole unit again
   with the new pair of Windows locked;
2. re-check the grant by join (`404 not_found`, never 401), then read the key: a known key from the same session with
   the same request returns the first outcome and writes nothing; any other known key is `409 invalid_key`;
3. refuse, in this order: `booking_cancelled`; `booking_changed` (another `version`; fact: the Booking now);
   `change_invalid` (`reason` `seats_exceed` or `same_target`); `outside_horizon` and `deadline_passed` for the target;
   `cutoff_passed` (fact `cutoff_at`); `no_seat_free` (fact: the target's `seats_left`), with the store's
   `booked_within_capacity` as the backstop (FR-10);
4. a full move is one UPDATE of `window_id` with `entry_time = app_now()` and `version + 1`. A partial move (a split)
   takes the Seats off the original (its total follows its price per Seat, `version + 1`) and creates a new Booking
   in the target through `services.reference`, with the original's name, email, price per Seat and Cutoff, the acting
   session, its own Manage token (`services.manage.issue`) and a grant for the acting session, and no `payments` row
   (AD-31);
5. one history row (`services.history.record`), the emails through `outbox.send` with the Change's id, and last the
   key row (`change_id` set). Only a success stores a key.

The response is the one Change serializer: `{booking, new_booking?, emails: [{id, subject, body}]}`, each Booking in
the Manage read's shape. It holds no name, email, token or Sauna; the emails are what the Guest was sent. No email of a
Change carries the original's Manage link, and none names a Sauna (FR-4).
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
from .errors import Refused
from .windows import ensure_open_for_booking

MOVE_ENDPOINT = "POST /api/manage/seats/move"
MANAGE_LINK_STILL_WORKS = "The Manage link in your booking confirmation email still works."
OWN_CONFIRMATION = "The moved seats have their own confirmation email."


def move_hash(reference_: str, window_id: int, seats: int, version: int) -> bytes:
    """SHA-256 of the canonical outcome-defining fields of a move (AD-9)."""
    canonical = json.dumps({"action": "move", "reference": reference_, "seats": seats, "version": version,
                            "window_id": window_id}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).digest()


# ------------------------------------------------------------------ the response (one serializer)


def outcome(c: psycopg.Connection, change_id: int) -> dict:
    """The Change serializer: the Booking (and the split-off Booking) as they are now, and the emails the Change sent,
    read by the Change's id (AD-9)."""
    booking_id, new_booking_id = q.change(c, change_id)
    out = {"booking": manage.booking_now(c, booking_id)}
    if new_booking_id is not None:
        out["new_booking"] = manage.booking_now(c, new_booking_id)
    out["emails"] = outbox.of_change(c, change_id)
    return out


# ------------------------------------------------------------------ the Change email (Lisa, 2026-11-24)


def change_email(booking: dict, venue: tuple, moved: int | None = None, new_reference: str | None = None
                 ) -> tuple[str, str]:
    """(subject, body) of the Change confirmation: the Venue block and the Booking as it is now; for a split also the
    Seats moved and the new reference. No Manage link and no Sauna (AD-29, FR-4)."""
    venue_name, address_lines, phone, venue_email = venue[0], venue[1], venue[2], venue[3]
    start, end = booking["start"][11:16], booking["end"][11:16]
    lines = [
        "Booking changed",
        "",
        venue_name,
        ", ".join(address_lines),
        phone,
        venue_email,
        "",
        f"Booking reference: {booking['reference']}",
        f"Date: {booking_service.long_date(dt.date.fromisoformat(booking['date']))}",
        f"Session: {start}–{end}",
        f"Seats: {booking['seats']}",
        f"Total: {booking_service.nok(booking['total_ore'])} incl. VAT",
        "",
    ]
    if new_reference is not None:
        lines += [f"Seats moved: {moved}", f"New booking reference: {new_reference}", OWN_CONFIRMATION, ""]
    lines.append(MANAGE_LINK_STILL_WORKS)
    return f"Booking changed: {booking['reference']}", "\n".join(lines)


# ------------------------------------------------------------------ the move


def _refuse_unless_changeable(c: psycopg.Connection, b: q.Locked, booking_id: int, window_id: int, seats: int,
                              version: int) -> None:
    """The refusals of AD-29 in their order, up to and including the Cutoff."""
    if b.status == "cancelled":
        raise Refused("booking_cancelled")
    if b.version != version:
        raise Refused("booking_changed", booking=manage.booking_now(c, booking_id))
    if not 1 <= seats <= b.seats:
        raise Refused("change_invalid", reason="seats_exceed")
    if window_id == b.window_id:
        raise Refused("change_invalid", reason="same_target")
    ensure_open_for_booking(c, window_id)  # outside_horizon, then deadline_passed (an unknown Window: not_found)
    if not b.change_allowed:
        raise Refused("cutoff_passed", cutoff_at=b.cutoff_at.astimezone(ZoneInfo(q.venue_tz(c))).isoformat())


def move(session_id: int, booking_id: int, reference_: str, window_id: int, seats: int, version: int,
         key: uuid.UUID) -> dict:
    """Move `seats` Seats of the Booking to the Window `window_id` (all of them: the same Booking moves; fewer: a
    split). Returns the Change serializer; a repeat of a known key returns the first outcome and writes nothing."""
    h = move_hash(reference_, window_id, seats, version)

    def work(c):
        current = q.window_of(c, booking_id)  # unlocked (AD-29)
        if current is None:
            raise Refused("not_found")
        db.lock_windows(c, [current, window_id])
        b = q.lock_booking(c, booking_id)
        if b is None:
            raise Refused("not_found")
        if b.window_id != current:
            raise db.Retry()  # moved in between: lock the new pair of Windows
        if not q.grant_valid(c, session_id, booking_id):
            raise Refused("not_found")
        known = bq.key(c, key)
        if known is not None:
            k_session, k_endpoint, k_hash, _k_booking, k_change = known
            if (k_session == session_id and k_endpoint == MOVE_ENDPOINT and bytes(k_hash) == h
                    and k_change is not None):
                return outcome(c, k_change)
            raise Refused("invalid_key")
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
