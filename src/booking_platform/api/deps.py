"""Request dependencies: the caller's session (AD-8) and the Administrator role (AD-10), plus the same-origin
check that every state-changing request passes (AD-8)."""

from __future__ import annotations

from fastapi import Depends, Request

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


def current_session(request: Request) -> sessions.Session | None:
    return sessions.resolve(request.cookies.get(COOKIE))


def require_session(s: sessions.Session | None = Depends(current_session)) -> sessions.Session:
    if s is None:
        raise Refused("no_session")
    return s


def require_admin(s: sessions.Session | None = Depends(current_session)) -> sessions.Session:
    if s is None:
        raise Refused("not_signed_in")
    if s.role != "admin":
        raise Refused("not_allowed")
    return s
