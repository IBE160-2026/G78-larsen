"""Seat bookings (FR-5, FR-6, FR-8, FR-9, FR-36): pay and create a Booking, its repeat (AD-9), and the confirmation
read (AD-12).

`create` is one `db.run`: the charge is decided before `lock_windows` (AD-13); after the lock the key is read first
(AD-9), then the Window rules (`ensure_open_for_booking`: `outside_horizon`, then `deadline_passed`), the session's
Hold on the Window is released (so its Seats are not counted twice), Seats left is read and a request for more is
`409 no_seat_free` with the fact `seats_left` (FR-12, AD-16), the Booking is inserted through `services.reference`
(AD-20) with its own copy of the Seat Cutoff (AD-4), the `payments` row is written, the Booking gets its Manage link
(`services.manage.issue`, AD-28), the confirmation goes through `outbox.send` (AD-12), and last the key row. Only
a success stores a key; a refusal raises, so `db.run` rolls back everything, the deleted Hold included. The store's
`booked_within_capacity` stays the backstop for capacity (FR-10).

The Booking's value is stored (`price_per_seat_ore`, `total_ore`) and every response and email shows the stored
values, never a recomputation (AD-13). No Sauna name or id appears in anything here (FR-4).

A Voucher (FR-28, AD-30, AD-31) pays all or part: the request carries the code and the quoted Voucher part. Before the
lock the card part is the Seats times the price in Settings minus that part (an unlocked read), and `charge()` runs only
when it is above 0; nothing before the lock refuses on the Voucher. After the Booking insert the part is checked
against the stored total, then `services.voucher.spend` takes it in one conditional UPDATE (`voucher_invalid` rolls
back everything), and the `payments` rows are `charge`/`voucher` (with the Voucher id) plus `charge`/`card` for any card
part. The request hash holds the Voucher part, never the code.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import uuid
from zoneinfo import ZoneInfo

import psycopg

from .. import config, db
from ..db import bookings as q
from ..db import seats as sq
from ..db import venue as vq
from . import content, manage, outbox, payment, reference, voucher
from .errors import Refused
from .windows import ensure_open_for_booking

ENDPOINT = "POST /api/bookings"
SIMULATED = "Simulated payment: no money moves"

_MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
           "November", "December")
_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def request_hash(window_id: int, seats: int, voucher_part: int | None = None) -> bytes:
    """SHA-256 of the canonical outcome-defining fields (AD-9). Never the name, the email or a Voucher code; the Voucher
    part only when a Voucher is sent, so a hash without one is the same as before Story 4.4."""
    fields = {"endpoint": ENDPOINT, "seats": seats, "window_id": window_id}
    if voucher_part is not None:
        fields["voucher_part_ore"] = voucher_part
    canonical = json.dumps(fields, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).digest()


# ------------------------------------------------------------------ the Booking as it is now


def facts(c: psycopg.Connection, booking_id: int) -> dict:
    """The one Booking serializer (AD-23): the Booking as it is now, as every booking page and the confirmation email
    show it (with name and email), with `paid`: its `charge` rows summed by method (FR-28, AD-31). `kind` is `seats` or
    `whole`; a Seat booking has `seats` and `price_per_seat_ore` and `sauna` null, a Whole-sauna booking has `sauna`
    (`{id, name}`) and `seats` and `price_per_seat_ore` null. Never a Sauna's Capacity, and never a Sauna for a Seat
    booking (AD-25)."""
    (ref, date, start, end, seats, price, total, name, email, status, tz_name, kind, sauna_id,
     sauna_name) = q.booking(c, booking_id)
    voucher_ore, card_ore = q.charges(c, booking_id)
    tz = ZoneInfo(tz_name)
    return {"reference": ref, "kind": kind, "date": date.isoformat(), "start": start.astimezone(tz).isoformat(),
            "end": end.astimezone(tz).isoformat(), "seats": seats, "price_per_seat_ore": price,
            "sauna": None if sauna_id is None else {"id": sauna_id, "name": sauna_name}, "total_ore": total,
            "name": name, "email": email, "status": status,
            "paid": {"voucher_ore": voucher_ore, "card_ore": card_ore}}


def _outcome(c: psycopg.Connection, booking_id: int) -> dict:
    """The Booking as it is now, plus the emails its action sent, read by Booking id (AD-9, AD-12)."""
    return {"booking": facts(c, booking_id), "emails": outbox.of_booking(c, booking_id)}


# ------------------------------------------------------------------ the confirmation email (FR-8, UX-DR38)


def nok(ore: int) -> str:
    """"NOK 500" from 50000 øre; "NOK 250,50" when øre are left over (the frontend writes amounts the same way)."""
    kroner, rest = divmod(ore, 100)
    return f"NOK {kroner}" + (f",{rest:02d}" if rest else "")


def long_date(date: dt.date) -> str:
    """"Saturday 14 November 2026"."""
    return f"{_WEEKDAYS[date.weekday()]} {date.day} {_MONTHS[date.month - 1]} {date.year}"


def confirmation_email(booking: dict, venue: tuple, manage_link: str) -> tuple[str, str]:
    """(subject, body) in the line layout of `mockups/key-confirmation.html`. Built from the stored Booking facts and
    the Venue facts; the booking terms (with the change statement) and the reception sentence come from `content/`.
    The Manage link (`services.manage.link`, AD-28) stands just before "Before you come". A Seat booking's email names
    no Sauna (FR-4); a Whole-sauna booking's says "Sauna: {name}" where a Seat booking's says "Seats: N", never the
    Sauna's Capacity, and its terms are `content/terms-whole.json` (AD-12, AD-23).
    A Booking paid with a Voucher shows "Paid with voucher" and "Paid by card" after the total (a zero part left out),
    and the payment note only when a card part was paid; without a Voucher the email is as before (FR-28)."""
    venue_name, address_lines, phone, venue_email = venue[0], venue[1], venue[2], venue[3]
    start, end = booking["start"][11:16], booking["end"][11:16]
    paid = booking.get("paid") or {"voucher_ore": 0, "card_ore": 0}
    payment_lines = []
    if paid["voucher_ore"] > 0:
        payment_lines.append(f"Paid with voucher: {nok(paid['voucher_ore'])}")
        if paid["card_ore"] > 0:
            payment_lines.append(f"Paid by card: {nok(paid['card_ore'])}")
    card_paid = paid["voucher_ore"] == 0 or paid["card_ore"] > 0
    whole = booking.get("kind") == "whole"
    lines = [
        "Booking confirmed",
        "",
        venue_name,
        ", ".join(address_lines),
        phone,
        venue_email,
        "",
        f"Booking reference: {booking['reference']}",
        f"Date: {long_date(dt.date.fromisoformat(booking['date']))}",
        f"Session: {start}–{end}",
        f"Sauna: {booking['sauna']['name']}" if whole else f"Seats: {booking['seats']}",
        f"Total: {nok(booking['total_ore'])} incl. VAT",
        *payment_lines,
        f"Email: {booking['email']}",
        "",
        *content.paragraphs(content.RECEPTION),
        "",
        "Booking terms",
        *content.paragraphs(content.TERMS_WHOLE if whole else content.TERMS_SEATS),
        "",
        "Manage your booking",
        manage_link,
        "",
        "Before you come",
        outbox.link(config.links.before_you_come),
        *(["", SIMULATED] if card_paid else []),
    ]
    return f"Booking confirmed: {booking['reference']}", "\n".join(lines)


# ------------------------------------------------------------------ create, and its repeat (AD-9)


def _price(c: psycopg.Connection) -> int:
    return vq.venue_facts(c)[7]


def create(session_id: int, window_id: int, seats: int, name: str, email: str, key: uuid.UUID,
           voucher_code: str | None = None, voucher_part: int | None = None) -> dict:
    """Pay for `seats` Seats in one Window and create the Booking. Returns `{booking, emails}`; a repeat of a known
    key from the same session with the same request returns the first outcome and writes nothing. Any other known
    key is `409 invalid_key`. With a Voucher (`voucher_code` and the quoted `voucher_part`, FR-28) that part is spent
    after the Booking insert and the card pays the rest; an unusable Voucher is `409 voucher_invalid`."""
    h = request_hash(window_id, seats, voucher_part)
    with_voucher = voucher_part is not None
    # Before the lock (AD-13): a failed or held payment writes nothing. With a Voucher the card part comes from an
    # unlocked read of the price, and no card part means no charge() at all; nothing here refuses on the Voucher.
    card_part = seats * db.run(_price) - voucher_part if with_voucher else None
    decided = payment.charge() if not with_voucher or card_part > 0 else None

    def work(c):
        db.lock_windows(c, [window_id])
        known = q.key(c, key)  # the first statement after the lock (AD-9)
        if known is not None:
            k_session, k_endpoint, k_hash, k_booking, _k_change = known
            if k_session == session_id and k_endpoint == ENDPOINT and bytes(k_hash) == h:
                return _outcome(c, k_booking)
            raise Refused("invalid_key")
        ensure_open_for_booking(c, window_id)
        sq.delete_holds(c, session_id, window_id)
        left = sq.seats_left(c, window_id)  # after the lock and without this session's Hold (FR-12, AD-16)
        if left < seats:
            raise Refused("no_seat_free", seats_left=max(left, 0))
        venue = vq.venue_facts(c)
        price = venue[7]
        booking_id, _ = reference.claim(
            lambda ref: sq.insert_booking(c, ref, window_id, seats, name, email, price, session_id))
        total = facts(c, booking_id)["total_ore"]
        if with_voucher:
            if voucher_part > total or total - voucher_part != card_part:
                raise Refused("voucher_invalid")  # a part that does not fit the stored total: nothing is written
            voucher_id = voucher.spend(c, voucher_code, voucher_part)  # last before the ledger rows (AD-30)
            q.insert_payment(c, booking_id, "charge", "voucher", voucher_part, voucher_id)
            if decided is not None:
                payment.record(c, decided, booking_id, card_part)
        else:
            payment.record(c, decided, booking_id, total)
        booking = facts(c, booking_id)
        token = manage.issue(c, booking_id)  # after the insert, in the same transaction (AD-28)
        subject, body = confirmation_email(booking, venue, manage.link(token))
        outbox.send(c, booking["email"], subject, body, booking_id=booking_id)
        q.insert_key(c, key, session_id, ENDPOINT, h, booking_id)
        return {"booking": booking, "emails": outbox.of_booking(c, booking_id)}

    return db.run(work)


# ------------------------------------------------------------------ the confirmation read (FR-8, AD-12)


def confirmation(session_id: int | None, ref: str) -> dict:
    """`{booking, emails}` of a Booking paid by this session. No session, another session's Booking, and an unknown
    or malformed reference are all the same `404 not_found` (FR-20 RB-4). Reads only."""
    if session_id is None or not reference.is_reference(ref):
        raise Refused("not_found")

    def work(c):
        booking_id = q.paid_by_session(c, ref, session_id)
        if booking_id is None:
            raise Refused("not_found")
        return _outcome(c, booking_id)

    return db.run(work)
