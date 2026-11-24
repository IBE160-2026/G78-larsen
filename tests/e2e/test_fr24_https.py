"""HTTPS only (FR-24, AD-27): plain HTTP is only redirected (HT-1), every HTTPS response carries HSTS and the Core
headers (HT-2), every session cookie is `Secure` and plain HTTP never touches the session (HT-3), and every Outbox
link starts with the HTTPS base URL (HT-4). Every URL is built from `base_url` and the stack's HTTP port."""

from __future__ import annotations

import hashlib
import json
import re
import ssl
import uuid
from pathlib import Path

import httpx
import psycopg
import pytest

from .admin import LOGIN, db_url, no_throttle  # noqa: F401 (fixture)
from .guest import free_windows

HSTS = "max-age=3600"  # the Caddyfile's default; the e2e env file sets no HSTS_MAX_AGE
SITE_HEADERS = ("strict-transport-security", "referrer-policy", "cache-control", "x-robots-tag")
NOT_FOUND = {"detail": {"error": "not_found"}}
PUBLIC = Path(__file__).resolve().parents[2] / "frontend" / "public"


def http_url(stack, base_url: str, path_and_query: str) -> str:
    """The same address over plain HTTP on the stack's HTTP port."""
    return str(httpx.URL(base_url).copy_with(scheme="http", port=stack.http_port)).rstrip("/") + path_and_query


def https_client(base_url: str, tls: ssl.SSLContext) -> httpx.Client:
    """One browser-like caller over HTTPS: verifies Caddy's certificate and keeps the cookies it is given."""
    return httpx.Client(base_url=base_url, verify=tls, follow_redirects=False, timeout=30)


def open_session(client: httpx.Client, base_url: str) -> str:
    r = client.post("/api/session", json={}, headers=unsafe(base_url))
    assert r.status_code == 200, r.text
    return assert_secure_cookie(r)


def sign_in(client: httpx.Client, base_url: str) -> str:
    """Sign the client's session in as the seeded Administrator; returns the rotated token."""
    r = client.post("/api/admin/sign-in", headers=unsafe(base_url),
                    json={"email": LOGIN["email"], "password": LOGIN["password"]})
    assert r.status_code == 200, r.text
    return assert_secure_cookie(r)


def unsafe(base_url: str) -> dict:
    """The headers of a same-origin write (AD-8)."""
    return {"Origin": base_url, "Content-Type": "application/json"}


def snapshot(stack) -> dict:
    """Every table's row count and every session row (id, token hash, expiry): what a request could change."""
    with psycopg.connect(db_url(stack)) as c:
        tables = [r[0] for r in c.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name")]
        counts = {t: c.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0] for t in tables}
        rows = c.execute("SELECT id, token_hash, expires_at::text FROM sessions ORDER BY id").fetchall()
    return {"counts": counts, "sessions": rows}


def session_row(stack, token: str):
    with psycopg.connect(db_url(stack)) as c:
        return c.execute("SELECT id, token_hash, expires_at::text FROM sessions WHERE token_hash = %s",
                         (hashlib.sha256(token.encode("utf-8")).digest(),)).fetchone()


def cookie_attributes(set_cookie: str) -> tuple[str, str, dict[str, str]]:
    """`name=value; Attr; Attr=x` as (name, value, {attr lower-cased: value})."""
    first, *attrs = [p.strip() for p in set_cookie.split(";")]
    name, _, value = first.partition("=")
    parsed = {}
    for a in attrs:
        k, _, v = a.partition("=")
        parsed[k.strip().lower()] = v.strip()
    return name, value, parsed


def assert_secure_cookie(response: httpx.Response) -> str:
    """Every `Set-Cookie` of the response has Secure, HttpOnly, SameSite=Strict and Path=/; returns the token."""
    cookies = response.headers.get_list("set-cookie")
    assert cookies, "no Set-Cookie"
    token = None
    for raw in cookies:
        name, value, attrs = cookie_attributes(raw)
        assert name == "bp_session", raw
        assert "secure" in attrs, raw
        assert "httponly" in attrs, raw
        assert attrs.get("samesite", "").lower() == "strict", raw
        assert attrs.get("path") == "/", raw
        token = value
    return token


def assert_only_the_redirect(r: httpx.Response, base_url: str, path_and_query: str) -> None:
    assert r.status_code == 308, (r.status_code, r.text[:200])
    assert r.headers["location"] == base_url + path_and_query
    for h in SITE_HEADERS:
        assert h not in r.headers, (h, r.headers)
    assert "set-cookie" not in r.headers


# ------------------------------------------------------------------ HT-1: plain HTTP is only redirected


@pytest.mark.parametrize("path_and_query", ["/book-seats?date=2030-01-01&seats=2", "/api/windows?date=2030-01-01"])
def test_plain_http_gets_only_the_redirect_and_changes_nothing(stack, base_url, path_and_query):
    marker = uuid.uuid4().hex
    path_and_query += f"&ht1={marker}"
    before = snapshot(stack)
    # a fresh client: no HSTS state, no cookies, redirects not followed
    with httpx.Client(follow_redirects=False, timeout=30) as plain:
        r = plain.get(http_url(stack, base_url, path_and_query))
        posted = plain.post(http_url(stack, base_url, "/api/session"), json={}, headers=unsafe(base_url))
    assert_only_the_redirect(r, base_url, path_and_query)
    assert_only_the_redirect(posted, base_url, "/api/session")
    assert snapshot(stack) == before
    logs = stack.compose("logs", "--no-color", "backend", "frontend").stdout
    assert marker not in logs  # no request reached the backend (its access log has every request line and query)


# ------------------------------------------------------------------ HT-2: HSTS and the Core headers on HTTPS


def _proxy_environment(stack, env: dict[str, str]) -> dict:
    return json.loads(stack.compose("config", "--format", "json", env=env).stdout)["services"]["proxy"]["environment"]


def test_hsts_max_age_reaches_the_proxy_only_when_set(stack):
    unset = stack.compose_env()
    # compose renders an unset bare key as null and gives the container no such variable: the Caddyfile's 3600 applies
    assert _proxy_environment(stack, unset).get("HSTS_MAX_AGE") is None
    assert "HSTS_MAX_AGE=" not in stack.compose("exec", "-T", "proxy", "env").stdout
    assert _proxy_environment(stack, {**unset, "HSTS_MAX_AGE": "60"})["HSTS_MAX_AGE"] == "60"


def _static_asset() -> str:
    return "/" + next(p for p in sorted(PUBLIC.rglob("*")) if p.is_file()).relative_to(PUBLIC).as_posix()


def assert_hsts(r: httpx.Response) -> None:
    assert r.headers.get_list("strict-transport-security") == [HSTS], r.headers  # no includeSubDomains, no preload
    assert r.headers.get("referrer-policy") == "no-referrer"


def test_every_https_response_carries_hsts_and_the_core_headers(base_url, tls):
    with https_client(base_url, tls) as client:
        page = client.get("/")
        assert page.status_code == 200 and "text/html" in page.headers["content-type"]
        assert_hsts(page)
        assert "cache-control" not in page.headers  # Caddy drops the frontend's own (AD-27)

        api = client.get("/api/nope")
        assert api.status_code == 404 and api.json() == NOT_FOUND
        assert_hsts(api)
        assert api.headers["cache-control"] == "no-store"

        asset = client.get(_static_asset())
        assert asset.status_code == 200 and asset.content
        assert_hsts(asset)
        assert "cache-control" not in asset.headers


def test_caddys_own_502_carries_hsts(stack, base_url, tls):
    stack.compose("stop", "frontend")
    try:
        with https_client(base_url, tls) as client:
            r = client.get("/")
        assert r.status_code == 502
        assert_hsts(r)
    finally:
        stack.compose("up", "--wait")
    with https_client(base_url, tls) as client:
        assert client.get("/").status_code == 200


# ------------------------------------------------------------------ HT-3: Secure cookies; plain HTTP never touches one


def test_guest_and_administrator_cookies_are_secure_and_plain_http_leaves_the_session_alone(stack, base_url, tls):
    with https_client(base_url, tls) as client:
        guest = open_session(client, base_url)  # the Guest's cookie
        admin = sign_in(client, base_url)  # the Administrator's cookie, on the same session row
        assert admin != guest  # rotated at sign-in

        row = session_row(stack, admin)
        assert row is not None
        before = snapshot(stack)
        # the cookie sent over plain HTTP, as a browser does to plain-HTTP `localhost` (a Known limit in the README)
        with httpx.Client(follow_redirects=False, timeout=30, cookies={"bp_session": admin}) as plain:
            for method, path in (("POST", "/api/session"), ("GET", "/api/admin/me"), ("POST", "/api/admin/sign-out")):
                body = {"json": {}} if method == "POST" else {}
                r = plain.request(method, http_url(stack, base_url, path), headers=unsafe(base_url), **body)
                assert_only_the_redirect(r, base_url, path)
        assert session_row(stack, admin) == row  # token hash and expiry unchanged
        assert snapshot(stack) == before

        assert client.get("/api/admin/me").status_code == 200  # still signed in: the HTTP sign-out never ran


# ------------------------------------------------------------------ HT-4: every Outbox link is the HTTPS base URL


def test_every_outbox_link_starts_with_the_https_base_url(base_url, tls):
    window = free_windows(base_url)[3]
    with https_client(base_url, tls) as guest:
        open_session(guest, base_url)
        booked = guest.post("/api/bookings", headers={**unsafe(base_url), "Idempotency-Key": str(uuid.uuid4())},
                            json={"window_id": window["id"], "seats": 1, "name": "Ingrid Hansen",
                                  "email": "ingrid@example.com"})
        assert booked.status_code == 201, booked.text
    with https_client(base_url, tls) as admin:
        open_session(admin, base_url)
        sign_in(admin, base_url)
        emails = admin.get("/api/admin/outbox").json()["emails"]

    assert emails
    links = [u for e in emails for u in re.findall(r"[a-zA-Z][a-zA-Z0-9+.-]*://\S+", e["body"])]
    assert links, "no link in any Outbox email"
    for u in links:
        assert u.startswith(base_url + "/"), u
    assert any(booked.json()["booking"]["reference"] in e["subject"] for e in emails)
