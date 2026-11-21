"""The `/api/admin` routers (AD-10).

`router` carries the one dependency that requires an Administrator: anonymous callers (no session, or a session with
no account) get 401 `not_signed_in`, other accounts 403 `not_allowed`, and neither changes anything. Every
Administrator endpoint is on it, sign-out and `me` included. `sign_in_router` holds only `POST /api/admin/sign-in`,
which has no dependency because the caller is not signed in yet (FR-15)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response

from ..services import auth, blocks, booking_list, marks, outbox, sessions, settings, whole
from .deps import clear_session_cookie, current_session, require_admin, set_session_cookie
from .schemas import BlockIn, BookingListQuery, MarkIn, OutboxQuery, SettingsIn, SignInIn, WholeIn

router = APIRouter(prefix="/api/admin", redirect_slashes=False, dependencies=[Depends(require_admin)])
sign_in_router = APIRouter(prefix="/api/admin", redirect_slashes=False)


@sign_in_router.post("/sign-in")
def sign_in(body: SignInIn, request: Request, response: Response):
    """Sign the caller's browser session in (FR-15, AD-8, AD-11). Without a valid session `401 no_session` (the page
    opens one and retries); every refusal is the same `401 sign_in_refused`. On success the same session row gets a
    new token, so the old one names nothing, and the cookie is set as by `POST /api/session`."""
    token = auth.sign_in(current_session(request), body.email, body.password)
    set_session_cookie(response, token)
    return {"role": "admin"}


@router.post("/sign-out")
def sign_out(response: Response, s: sessions.Session = Depends(require_admin)):
    """Delete the session row and clear the cookie (FR-15); the old token then gets 401 everywhere."""
    auth.sign_out(s)
    clear_session_cookie(response)
    return {"ok": True}


@router.get("/me")
def me():
    """The Administrator page guard's check: 200 for a signed-in Administrator, 401 otherwise."""
    return {"role": "admin"}


@router.get("/bookings")
def bookings(query: Annotated[BookingListQuery, Query()]):
    """The Booking list of one Venue date (FR-16, AD-4, AD-5): every Window of the date in time order with its
    figures and active Bookings, oldest first. Without `date`, the API's today. Takes no lock; the only write is
    `windows.ensure_generated()`, and a refused request (422) writes nothing. Name and email of a Booking due for
    retention are masked (FR-21)."""
    return booking_list.day(query.date)


@router.get("/outbox")
def outbox_emails(query: Annotated[OutboxQuery, Query()]):
    """Every simulated email, newest first (FR-17, AD-12), with time, recipient, subject and body exactly as stored.
    One SELECT (the Venue time zone included): no lock, no write. Recipient and body of an email whose Booking is due for retention
    read as '' (FR-21). Any query field is `422 invalid_input`."""
    return outbox.listing()


@router.post("/whole-bookings", status_code=201)
def book_whole(body: WholeIn):
    return {"whole_booking_id": whole.book_whole(body.window_id, body.sauna_id)}


@router.post("/blocks", status_code=201)
def block(body: BlockIn):
    return {"block_id": blocks.block(body.sauna_id, body.start, body.end)}


@router.delete("/blocks/{block_id}")
def lift_block(block_id: int):
    return {"lifted": blocks.lift(block_id)}


@router.post("/marks", status_code=201)
def mark(body: MarkIn):
    return {"mark_id": marks.mark(body.window_id, body.sauna_id)}


@router.delete("/marks")
def unmark(window_id: int, sauna_id: int):
    return {"removed": marks.unmark(window_id, sauna_id)}


@router.put("/settings")
def put_settings(body: SettingsIn):
    settings.put(body.release_on, body.release_time, body.booking_deadline_minutes)
    return {"ok": True}
