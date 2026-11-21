"""Request dependencies: the caller's session (AD-8) and the Administrator role (AD-10), plus the same-origin
check that every state-changing request passes (AD-8)."""

from __future__ import annotations

from fastapi import Depends, Request, Response

from .. import config
from ..services import sessions
from ..services.errors import Refused

COOKIE = "bp_session"
UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def same_origin(origin: str | None, sec_fetch_site: str | None) -> bool:
    """`Origin` equals the base URL's origin, or, without `Origin`, `Sec-Fetch-Site: same-origin`.
    Never compared with `Host`, and no switch turns it off."""
    if origin is not None:
        return origin.strip().lower() == config.settings().base_origin
    return (sec_fetch_site or "").strip().lower() == "same-origin"


def set_session_cookie(response: Response, token: str) -> None:
    """The one shape of the session cookie (AD-8): HttpOnly, SameSite=Strict, Path=/, Secure with BP_HTTPS."""
    response.set_cookie(COOKIE, token, httponly=True, samesite="strict", path="/", secure=config.settings().https)


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE, httponly=True, samesite="strict", path="/", secure=config.settings().https)


def current_session(request: Request) -> sessions.Session | None:
    return sessions.resolve(request.cookies.get(COOKIE))


def require_session(s: sessions.Session | None = Depends(current_session)) -> sessions.Session:
    if s is None:
        raise Refused("no_session")
    return s


def require_admin(s: sessions.Session | None = Depends(current_session)) -> sessions.Session:
    """The caller resolved from the session's account and role (AD-10). No session, or a session with no account
    (a Guest's booking session, RB-1), is anonymous: `401 not_signed_in`. An account without the Administrator role
    is `403 not_allowed` (unreachable in the Core, which has only Administrators)."""
    if s is None or s.account_id is None:
        raise Refused("not_signed_in")
    if s.role != "admin":
        raise Refused("not_allowed")
    return s
