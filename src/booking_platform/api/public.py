"""The public `/api` router: health, the Venue facts, Windows, the Private sauna listing, the session, Holds, Seat
bookings and the confirmation read."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request, Response

from ..services import booking, holds, sessions, venue, voucher, whole, windows
from .deps import COOKIE, current_session, require_session, set_session_cookie
from .schemas import (BookingIn, BookingResult, HoldIn, PrivateSaunasQuery, SessionIn, VenueOut, VoucherQuoteIn,
                      VoucherQuoteOut, WindowsQuery)

router = APIRouter(prefix="/api", redirect_slashes=False)


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/venue", response_model=VenueOut)
def venue_facts():
    """The Venue facts Landing shows (FR-1, AD-16). Needs no session, writes nothing and sets no cookie."""
    return venue.facts()


@router.get("/windows")
def list_windows(query: Annotated[WindowsQuery, Query()]):
    """The dated Window listing (FR-2, FR-3, AD-16). Needs no session and sets no cookie. The only write is
    `windows.ensure_generated()`; a refused listing (422, 409 `outside_horizon`) writes nothing."""
    return windows.listing(query.date, query.seats)


@router.get("/private-saunas")
def private_saunas(query: Annotated[PrivateSaunasQuery, Query()]):
    """The Private sauna listing of one Venue date (FR-29, FR-30, AD-24): the Saunas that can be booked whole, in
    Fill order, each with its free Windows. Needs no session, sets no cookie and takes no lock. The only write is
    `windows.ensure_generated()`; a refused listing (422, 409 `outside_horizon`) writes nothing."""
    return whole.listing(query.date)


@router.get("/windows/{window_id}")
def get_window(window_id: int):
    return windows.get_window(window_id)


@router.post("/session")
def open_session(_: SessionIn, request: Request, response: Response):
    """Create an anonymous session, or return the caller's existing one while it is still valid (AD-8)."""
    s, token = sessions.open_session(request.cookies.get(COOKIE))
    if token is not None:
        set_session_cookie(response, token)
    return {"role": s.role}


@router.post("/holds")
def hold(body: HoldIn, s: sessions.Session = Depends(require_session)):
    return {"hold_id": holds.hold(s.id, body.window_id, body.seats)}


@router.delete("/holds")
def release_hold(window_id: int, s: sessions.Session = Depends(require_session)):
    return {"released": holds.release(s.id, window_id)}


@router.post("/bookings", status_code=201, response_model=BookingResult)
def book(body: BookingIn, idempotency_key: Annotated[uuid.UUID, Header(alias="Idempotency-Key")],
         s: sessions.Session = Depends(require_session)):
    """Pay and create a Seat booking (FR-5, FR-6, FR-9). The `Idempotency-Key` UUID is required (AD-9): a repeat from
    the same session with the same Window and Seats returns the first outcome (201 again) and writes nothing."""
    return booking.create(s.id, body.window_id, body.seats, body.name, body.email, idempotency_key,
                          voucher_code=body.voucher_code, voucher_part=body.voucher_part_ore)


@router.post("/vouchers/quote", response_model=VoucherQuoteOut)
def quote_voucher(body: VoucherQuoteIn, _s: sessions.Session = Depends(require_session)):
    """What a Voucher would pay of a Seat booking (FR-28, AD-30): `{voucher_part_ore, card_part_ore}`. Takes no lock and
    writes nothing. Any unusable code is `409 voucher_invalid` with no facts; an unknown Window is `404 not_found`."""
    return voucher.quote(body.window_id, body.seats, body.code)


@router.get("/bookings/{reference}/confirmation", response_model=BookingResult)
def confirmation(reference: str, s: sessions.Session | None = Depends(current_session)):
    """The Booking and the email as sent, for the paying session only (FR-8, AD-12). Any other session, no session,
    and an unknown or malformed reference get the same `404 not_found` (FR-20 RB-4)."""
    return booking.confirmation(s.id if s else None, reference)

