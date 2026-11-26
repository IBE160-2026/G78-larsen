"""Manage links (FR-25, AD-28): the token in the email link's fragment, exchanged for a grant on the browser's session,
and the read of the Booking it opens.

- `issue` is the only writer of `access_tokens`. Only Booking creators call it, inside their own transaction: the Seat
  flow (`services.booking.create`), the Whole-sauna flow (`services.whole.create`), a split (`services.change.move`) and the seed. It locks the Booking `FOR NO KEY UPDATE`, revokes any unrevoked
  Manage token of it, then stores the SHA-256 hash of a new 256-bit token. The raw token is returned only to build
  the email link and is never stored, logged or put in a path or query (AD-19).
- `open` checks the token, creates or reuses the session (AD-8) and upserts the grant. Every bad token (unknown,
  malformed, too long, revoked, its Window ended) is the same `404 not_found`, and a session is created only on
  success.
- `grant` is the one check of every route under `/api/manage/{reference}/`: one autocommit statement that judges
  `manage_grant_valid` and touches `last_used_at` (AD-4). No session, no grant, another Booking's reference and an
  unknown reference are all `404 not_found`, never `401`.
- `read` writes nothing. Its Booking JSON never holds a name, an email, an Outbox body or a token (FR-17), and names a
  Sauna only for a Whole-sauna booking (`kind = 'whole'`, FR-4, AD-25).
"""

from __future__ import annotations

import secrets
from zoneinfo import ZoneInfo

import psycopg

from .. import config, db
from ..db import bookings as bq
from ..db import manage as q
from ..db import vouchers as vq
from . import content, history, outbox, reference, sessions, voucher
from .errors import Refused

MAX_TOKEN = 200  # a longer token is not one of ours; it is never hashed


def new_token() -> str:
    """A fresh link token: 256 random bits, URL-safe (43 characters)."""
    return secrets.token_urlsafe(32)


def issue(c: psycopg.Connection, booking_id: int, *, grant_to: int | None = None) -> str:
    """Give the Booking a new Manage token in the caller's transaction and return the raw token (for the email link
    only). Any earlier unrevoked Manage token of the Booking is revoked. With `grant_to` (a split, AD-29), that session
    also gets a grant through the new token, so the Guest who split the Booking can open it at once."""
    q.lock_booking(c, booking_id)
    q.revoke(c, booking_id)
    token = new_token()
    token_id = q.insert_token(c, booking_id, sessions.token_hash(token))
    if grant_to is not None:
        q.upsert_grant(c, grant_to, token_id)
    return token


def link(token: str) -> str:
    """The email link: `<BP_BASE_URL>/manage#t=<token>`. The token is in the fragment, so it never reaches a server
    log, a referrer or a query."""
    return outbox.link(config.links.manage) + "#t=" + token


def change_statement() -> str:
    """The approved change statement (CAP-9): the second paragraph of the Seat booking terms."""
    return content.paragraphs(content.TERMS_SEATS)[1]


def open(session_cookie: str | None, token: str) -> tuple[str, str | None]:  # noqa: A001 - the spec's name
    """Exchange a Manage token for a grant on the caller's session. Returns (reference, new session token for the
    cookie or None when the existing session was reused). Any token that does not open a Booking is `404
    not_found`, and then no session is created."""
    if not token or len(token) > MAX_TOKEN:
        raise Refused("not_found")
    found = db.run(lambda c: q.valid_token(c, sessions.token_hash(token)))
    if found is None:
        raise Refused("not_found")
    token_id, _booking_id, ref = found
    s, new_cookie = sessions.open_session(session_cookie)
    if not db.run(lambda c: q.upsert_grant(c, s.id, token_id)):
        raise Refused("not_found")  # the token stopped being valid in between
    return ref, new_cookie


def grant(session: sessions.Session | None, ref: str) -> int:
    """The id of the Booking `ref` when the session holds a valid grant for it, touching the grant; otherwise `404
    not_found` (with or without a session)."""
    if session is None or not reference.is_reference(ref):
        raise Refused("not_found")
    booking_id = db.statement(lambda c: q.check_and_touch(c, session.id, ref))
    if booking_id is None:
        raise Refused("not_found")
    return booking_id


def booking_now(c: psycopg.Connection, booking_id: int) -> dict:
    """The Booking as the Manage page shows it, in the caller's transaction (the Manage read, and every Change
    response and `booking_changed` fact, AD-29)."""
    row = q.booking(c, booking_id)
    if row is None:
        raise Refused("not_found")
    (ref, seats, window_id, date, start, end, total, status, version, allowed, cutoff_at, cancelled_at, tz_name, kind,
     sauna_id, sauna_name, cancel_remedy) = row
    tz = ZoneInfo(tz_name)
    whole = kind == "whole"
    out = {
        "reference": ref,
        "kind": kind,
        "seats": seats,
        "sauna": None if sauna_id is None else {"id": sauna_id, "name": sauna_name},
        "window": {"id": window_id, "date": date.isoformat(), "start": start.astimezone(tz).isoformat(),
                   "end": end.astimezone(tz).isoformat()},
        "total_ore": total,
        "status": status,
        "version": version,
        "change_allowed": allowed,
        "cutoff_at": cutoff_at.astimezone(tz).isoformat(),
        "cancelled_at": None if cancelled_at is None else cancelled_at.astimezone(tz).isoformat(),
        "cancel_remedy": cancel_remedy,
        "history": history.of_booking(c, booking_id, tz),
        # what a Voucher issued from the Booking now would be valid through (the give-up step and the Whole-sauna
        # cancel step state it): a Whole-sauna booking's Voucher remedy is always one year (AD-31)
        "voucher_last_valid_date": (vq.a_year_ahead(c) if whole
                                    else voucher.next_last_valid_date(c, booking_id)).isoformat(),
    }
    if whole and status == "active":
        out["refund_split"] = refund_split(c, booking_id)
    return out


def refund_split(c: psycopg.Connection, booking_id: int) -> dict:
    """What a refund of the active Whole-sauna booking would return now (AD-31), computed here so no browser clock
    decides it: `{card_ore, voucher_ore, voucher_last_valid_date}` (the date null without a Voucher part). No code."""
    voucher_ore, card_ore = bq.charges(c, booking_id)
    last = vq.refund_last_valid_date(c, booking_id) if voucher_ore > 0 else None
    return {"card_ore": card_ore, "voucher_ore": voucher_ore,
            "voucher_last_valid_date": None if last is None else last.isoformat()}


def read(booking_id: int) -> dict:
    """The Booking as the Manage page shows it: the AD-23 serializer (`kind`, `seats`, `sauna`, `window`,
    `total_ore`, `status`) plus `reference`, `version`, `change_allowed` (the SQL predicate), `cutoff_at`,
    `cancelled_at` (null while active, Story 4.3), `cancel_remedy` (Story 5.3), `history` (`services.history`) and
    `voucher_last_valid_date` (what a Voucher issued from it now would be valid through,
    `services.voucher.next_last_valid_date`; one year for a Whole-sauna booking); an active Whole-sauna booking also
    has `refund_split` (Story 5.3). A cancelled Booking
    still reads; its page offers no Change. Times are ISO strings in Venue time. Reads only."""
    return db.run(lambda c: booking_now(c, booking_id))


def purge() -> int:
    """Startup: delete the grants of expired sessions and of tokens whose Window has ended."""
    return db.statement(q.purge)
