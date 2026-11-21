"""The one way tests talk to the API (Conventions: Tests). Every request carries the base URL's `Origin`, so it
passes the same-origin rule (AD-8); `test_fr18_csrf.py` sends other origins on purpose.
"""

from __future__ import annotations

import hashlib
import json
import ssl
import uuid
from pathlib import Path

import httpx
import psycopg

COOKIE = "bp_session"
# The seeded Administrator (`seeds/admin.json`, Story 2.1): the fixture signs in with it for real (AD-21).
ADMIN_LOGIN = json.loads((Path(__file__).resolve().parents[1] / "seeds" / "admin.json").read_text(encoding="utf-8"))
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


def sign_in(c: ApiClient, email: str | None = None, password: str | None = None) -> httpx.Response:
    """`POST /api/admin/sign-in`, by default with the seeded Administrator's login."""
    body = {"email": ADMIN_LOGIN["email"] if email is None else email,
            "password": ADMIN_LOGIN["password"] if password is None else password}
    return c.post("/api/admin/sign-in", json=body)


def admin_client(base: str, pg: psycopg.Connection | None = None) -> ApiClient:
    """A client with an Administrator session made by a real sign-in with the seeded account (AD-21): an anonymous
    session first, then `POST /api/admin/sign-in`. (`pg` is no longer needed; it stays for the existing callers.)"""
    c = api_client(base)
    r = sign_in(c)
    assert r.status_code == 200 and r.json() == {"role": "admin"}, r.text
    c._session_id = None  # the token changed (the row is the same); look it up again when asked
    return c
