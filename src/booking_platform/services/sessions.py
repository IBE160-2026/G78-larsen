"""Server-side sessions (AD-8). The cookie holds a 256-bit random token; the store keeps only its SHA-256 hash."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass

from .. import db
from ..db import sessions as q


@dataclass(frozen=True)
class Session:
    id: int
    role: str
    account_id: int | None = None  # set only by sign-in; a Guest's booking session has none (RB-1)


def token_hash(token: str) -> bytes:
    return hashlib.sha256(token.encode("utf-8")).digest()


def resolve(token: str | None) -> Session | None:
    """The still-valid session of a cookie token, its sliding expiry touched in one autocommit statement outside
    every action transaction (AD-4). None when there is no token, or it is unknown or expired."""
    if not token or len(token) > 200:
        return None
    row = db.statement(lambda c: q.resolve_and_touch(c, token_hash(token)))
    return None if row is None else Session(id=row[0], role=row[1], account_id=row[2])


def new_token() -> str:
    """A fresh cookie token: 256 random bits, URL-safe."""
    return secrets.token_urlsafe(32)


def open_session(token: str | None) -> tuple[Session, str | None]:
    """Return the caller's still-valid session, or create an anonymous one. The second value is the new token for
    the cookie, or None when the existing session was returned."""
    current = resolve(token)
    if current is not None:
        return current, None
    token = new_token()
    sid = db.run(lambda c: q.create(c, token_hash(token), "guest"))
    return Session(id=sid, role="guest"), token


def purge_expired() -> int:
    """Startup: delete the expired sessions."""
    return db.statement(q.purge_expired)
