"""The Manage routes (FR-25, AD-28).

- `open_router`: `POST /api/manage/open {token}` exchanges the token from the link's fragment for a grant on the
  caller's session and returns `{reference}`. It creates or reuses the session (AD-8) and sets the cookie only when it
  created one. It passes the same-origin check like every POST (the app's RequestGuard).
- `router`: every route reached through a grant lives under `/api/manage/{reference}`, behind the one dependency
  `require_grant`. No grant, no session, another Booking and an unknown reference are all `404 not_found`; a Manage
  route never answers `401`. `POST …/seats/move` is the Seat move (FR-26, AD-29) and `POST …/seats/voucher` the
  Voucher instead of Seats (FR-27, AD-29, AD-30); `POST …/whole/cancel` cancels a Whole-sauna booking for a refund
  or a Voucher (FR-33, AD-31). Each needs an `Idempotency-Key` (AD-9); a route of the other kind of Booking is `404
  not_found` (AD-28).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, Response

from ..services import change, manage, sessions
from .deps import COOKIE, current_session, set_session_cookie
from .schemas import ManageOpenIn, MoveIn, VoucherIn, WholeCancelIn

open_router = APIRouter(prefix="/api/manage", redirect_slashes=False)


@open_router.post("/open")
def open_link(body: ManageOpenIn, request: Request, response: Response):
    reference, new_cookie = manage.open(request.cookies.get(COOKIE), body.token)
    if new_cookie is not None:
        set_session_cookie(response, new_cookie)
    return {"reference": reference}


def require_grant(reference: str, s: sessions.Session | None = Depends(current_session)) -> int:
    """The Booking id behind `reference` when the caller's session holds a valid grant for it (checked and touched in
    one autocommit statement); `404 not_found` otherwise."""
    return manage.grant(s, reference)


router = APIRouter(prefix="/api/manage/{reference}", dependencies=[Depends(require_grant)], redirect_slashes=False)


@router.get("")
def read(booking_id: int = Depends(require_grant)):
    """The Booking as the Manage page shows it. Writes nothing apart from the grant and session touch."""
    return manage.read(booking_id)


@router.post("/seats/move")
def move_seats(reference: str, body: MoveIn, idempotency_key: Annotated[uuid.UUID, Header(alias="Idempotency-Key")],
               booking_id: int = Depends(require_grant), s: sessions.Session | None = Depends(current_session)):
    """Move all or some Seats to another Window (FR-26). The grant was checked by the router's dependency (so the
    session exists) and is checked again inside the transaction. A repeat with the same key from the same session
    returns the first outcome."""
    return change.move(s.id, booking_id, reference, body.window_id, body.seats, body.version, idempotency_key)


@router.post("/seats/voucher")
def give_up_seats(reference: str, body: VoucherIn,
                  idempotency_key: Annotated[uuid.UUID, Header(alias="Idempotency-Key")],
                  booking_id: int = Depends(require_grant), s: sessions.Session | None = Depends(current_session)):
    """Give up some or all Seats for a Voucher (FR-27); all Seats cancel the Booking. The grant is checked again inside
    the transaction. A repeat with the same key from the same session returns the first outcome (no second Voucher)."""
    return change.voucher(s.id, booking_id, reference, body.seats, body.version, idempotency_key)


@router.post("/whole/cancel")
def cancel_whole(reference: str, body: WholeCancelIn,
                 idempotency_key: Annotated[uuid.UUID, Header(alias="Idempotency-Key")],
                 booking_id: int = Depends(require_grant), s: sessions.Session | None = Depends(current_session)):
    """Cancel a Whole-sauna booking for a refund or a Voucher (FR-33). The grant is checked again inside the
    transaction. A repeat with the same key from the same session returns the first outcome (no second refund or
    Voucher)."""
    return change.whole_cancel(s.id, booking_id, reference, body.remedy, body.version, idempotency_key)
