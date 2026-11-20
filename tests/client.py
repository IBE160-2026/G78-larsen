"""The one way tests talk to the API (Conventions: Tests). Every request carries the base URL's `Origin`, so it
passes the same-origin rule (AD-8); `test_fr18_csrf.py` sends other origins on purpose.
"""

from __future__ import annotations

import hashlib
import secrets
import ssl
import uuid

import httpx
import psycopg

from booking_platform.db.sessions import lifetime

COOKIE = "bp_session"
ADMIN = "'admin'"  # the role as an SQL literal, for lifetime()
GUEST = {"name": "Test Guest", "email": "guest@example.com"}  # the Guest's details in every test booking

# One TLS context for every client: building one per client costs tens of milliseconds, and the races create
# many clients (one per Guest session).
_TLS = ssl.create_default_context()

# Set by conftest: the test database, used to look up a client's session id by its token hash.
DATABASE_URL: str | None = None


def token_hash(token: str) -> bytes:
    return hashlib.sha256(token.encode("utf-8")).digest()


def new_key() -> dict[str, str]:
    """A fresh `Idempotency-Key` header (AD-9)."""
    return {"Idempotency-Key": str(uuid.uuid4())}


def booking_body(window_id, seats, **fields) -> dict:
    """The body of `POST /api/bookings`: the Window, the Seats and the Guest's name and email (Story 1.5)."""
    return {"window_id": window_id, "seats": seats, **GUEST, **fields}


class ApiClient(httpx.Client):
    _session_id: int | None = None

    def __enter__(self):
        """Usable in `with` also after its first request (the session is opened before it is handed out)."""
        return self

    @property
    def token(self) -> str | None:
        return self.cookies.get(COOKIE)

    @property
    def session_id(self) -> int | None:
        """The `sessions.id` behind this client's cookie (looked up once, straight in the store)."""
        if self._session_id is None and self.token is not None:
            with psycopg.connect(DATABASE_URL) as c:
                row = c.execute("SELECT id FROM sessions WHERE token_hash = %s", (token_hash(self.token),)).fetchone()
            self._session_id = row[0] if row else None
        return self._session_id

    def book(self, window_id, seats, *, key: str | None = None, **fields) -> httpx.Response:
        """`POST /api/bookings` in the request shape of Story 1.5: `{window_id, seats, name, email}` plus an
        `Idempotency-Key` (a new one unless `key` is given). `fields` replace or add body fields."""
        headers = {"Idempotency-Key": key} if key is not None else new_key()
        return self.post("/api/bookings", json=booking_body(window_id, seats, **fields), headers=headers)


def api_client(base: str, *, session: bool = True, origin: str | None = None, timeout: float = 60) -> ApiClient:
    """A client for the API at `base`. With `session`, it opens an anonymous session first (`POST /api/session`)."""
    c = ApiClient(base_url=base, timeout=timeout, headers={"Origin": origin or base}, verify=_TLS)
    if session:
        r = c.post("/api/session", json={})
        assert r.status_code == 200 and r.json() == {"role": "guest"}, r.text
    return c


def admin_client(base: str, pg: psycopg.Connection) -> ApiClient:
    """A client with an Administrator session, inserted straight into the store until sign-in exists (Story 2.1)."""
    token = secrets.token_urlsafe(32)
    sid = pg.execute("INSERT INTO sessions (token_hash, role, created_at, expires_at) "
                     f"SELECT %s, 'admin', n, n + {lifetime(ADMIN)} FROM (SELECT app_now() AS n) x RETURNING id",
                     (token_hash(token),)).fetchone()[0]
    pg.commit()
    c = ApiClient(base_url=base, timeout=60, headers={"Origin": base}, verify=_TLS)
    c.cookies.set(COOKIE, token, domain=httpx.URL(base).host)
    c._session_id = sid
    return c
