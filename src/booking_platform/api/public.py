"""The public `/api` router: health, the Venue facts, Windows, the session, Holds and Seat bookings."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response

from .. import config
from ..services import booking, holds, sessions, venue, windows
from .deps import COOKIE, require_session
from .schemas import BookingIn, HoldIn, SessionIn, VenueOut, WindowsQuery

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


@router.get("/windows/{window_id}")
def get_window(window_id: int):
    return windows.get_window(window_id)


@router.post("/session")
def open_session(_: SessionIn, request: Request, response: Response):
    """Create an anonymous session, or return the caller's existing one while it is still valid (AD-8)."""
    s, token = sessions.open_session(request.cookies.get(COOKIE))
    if token is not None:
        response.set_cookie(COOKIE, token, httponly=True, samesite="strict", path="/",
                            secure=config.settings().https)
    return {"role": s.role}


@router.post("/holds")
def hold(body: HoldIn, s: sessions.Session = Depends(require_session)):
    return {"hold_id": holds.hold(s.id, body.window_id, body.seats)}


@router.delete("/holds")
def release_hold(window_id: int, s: sessions.Session = Depends(require_session)):
    return {"released": holds.release(s.id, window_id)}


@router.post("/bookings", status_code=201)
def book(body: BookingIn, s: sessions.Session = Depends(require_session)):
    return {"booking_id": booking.book(s.id, body.window_id, body.seats, body.guest)}

