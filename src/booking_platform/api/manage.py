"""The Manage routes (FR-25, AD-28).

- `open_router`: `POST /api/manage/open {token}` exchanges the token from the link's fragment for a grant on the
  caller's session and returns `{reference}`. It creates or reuses the session (AD-8) and sets the cookie only when it
  created one. It passes the same-origin check like every POST (the app's RequestGuard).
- `router`: every route reached through a grant lives under `/api/manage/{reference}`, behind the one dependency
  `require_grant`. No grant, no session, another Booking and an unknown reference are all `404 not_found`; a Manage
  route never answers `401`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response

from ..services import manage, sessions
from .deps import COOKIE, current_session, set_session_cookie
from .schemas import ManageOpenIn

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
