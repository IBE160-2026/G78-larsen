"""FR-21 / AD-8: server-side sessions with hashed tokens, set only by `POST /api/session`.

The cookie holds a 256-bit random token (HttpOnly, SameSite=Strict, Path=/, Secure only with BP_HTTPS); the store
keeps only its SHA-256 hash. Anonymous sessions last 24 h and Administrator sessions 8 h, both sliding, judged on
app_now(). Expired rows are purged at startup. Nothing secret reaches the backend log (AD-19).
"""

from __future__ import annotations

import datetime as dt

import httpx

from client import COOKIE, _TLS, admin_client, api_client, token_hash
from conftest import EARLY, set_clock, start_backend


def rows(pg, sql, params=()):
    pg.rollback()
    out = pg.execute(sql, params).fetchall()
    pg.rollback()
    return out


def test_a_guest_write_without_a_session_is_401_and_writes_nothing(world, pg):
    with api_client(world, session=False) as anon:
        for r in [anon.post("/api/holds", json=dict(window_id=1, seats=1)),
                  anon.post("/api/bookings", json=dict(window_id=1, seats=1)),
                  anon.delete("/api/holds", params=dict(window_id=1))]:
            assert r.status_code == 401 and r.json() == {"detail": {"error": "no_session"}}, r.text
        anon.cookies.set(COOKIE, "not-a-real-token", domain="127.0.0.1")
        r = anon.post("/api/holds", json=dict(window_id=1, seats=1))
        assert r.status_code == 401 and r.json()["detail"]["error"] == "no_session"
    assert rows(pg, "SELECT count(*) FROM holds") == [(0,)]
    assert rows(pg, "SELECT count(*) FROM bookings") == [(0,)]
    assert rows(pg, "SELECT count(*) FROM sessions") == [(0,)]  # no request but POST /api/session creates one


def test_the_cookie_flags_and_only_a_hash_in_the_store(world, pg):
    with httpx.Client(base_url=world, headers={"Origin": world}, verify=_TLS) as c:
        r = c.post("/api/session", json={})
    assert r.status_code == 200 and r.json() == {"role": "guest"}
    cookie = r.headers["set-cookie"]
    attrs = [a.strip().lower() for a in cookie.split(";")]
    name, token = cookie.split(";")[0].split("=", 1)
    assert name == COOKIE
    assert "httponly" in attrs and "samesite=strict" in attrs and "path=/" in attrs
    assert "secure" not in attrs  # BP_HTTPS is off in the API test layer
    assert not any(a.startswith(("domain=", "max-age=", "expires=")) for a in attrs)
    assert len(token) >= 43  # 256 random bits, URL-safe base64
    stored = rows(pg, "SELECT token_hash, role FROM sessions")
    assert stored == [(token_hash(token), "guest")]  # the SHA-256 hash, never the token itself


def test_a_still_valid_session_is_returned_instead_of_a_new_one(api, pg):
    first = api.token
    r = api.post("/api/session", json={})
    assert r.status_code == 200 and r.json() == {"role": "guest"}
    assert "set-cookie" not in r.headers
    assert api.token == first
    assert rows(pg, "SELECT count(*) FROM sessions") == [(1,)]


def test_the_anonymous_lifetime_is_24_hours_judged_on_the_store_clock(api, pg):
    (life,) = rows(pg, "SELECT expires_at - created_at FROM sessions")[0]
    assert life == dt.timedelta(hours=24)
    set_clock(pg, EARLY + dt.timedelta(hours=23, minutes=59))
    assert api.delete("/api/holds", params=dict(window_id=1)).status_code == 200
    set_clock(pg, EARLY + dt.timedelta(hours=23, minutes=59) + dt.timedelta(hours=24, minutes=1))
    r = api.delete("/api/holds", params=dict(window_id=1))
    assert r.status_code == 401 and r.json()["detail"]["error"] == "no_session"
    # an expired session is replaced by a new one
    old = api.token
    r = api.post("/api/session", json={})
    assert r.status_code == 200 and api.token != old


def test_the_lifetime_slides_with_use(api, pg):
    for hours in (20, 40, 60):  # each use moves the expiry to 24 h after it
        set_clock(pg, EARLY + dt.timedelta(hours=hours))
        assert api.delete("/api/holds", params=dict(window_id=1)).status_code == 200, hours
    set_clock(pg, EARLY + dt.timedelta(hours=60 + 24, minutes=1))
    assert api.delete("/api/holds", params=dict(window_id=1)).status_code == 401


def test_an_administrator_session_lasts_8_hours_sliding(world, pg):
    with admin_client(world, pg) as admin:
        set_clock(pg, EARLY + dt.timedelta(hours=7))
        assert admin.delete("/api/admin/marks", params=dict(window_id=1, sauna_id=1)).status_code == 200
        set_clock(pg, EARLY + dt.timedelta(hours=7 + 8, minutes=1))
        r = admin.delete("/api/admin/marks", params=dict(window_id=1, sauna_id=1))
        assert r.status_code == 401 and r.json()["detail"]["error"] == "not_signed_in"


def test_holds_reference_the_server_session(api, pg):
    assert api.post("/api/holds", json=dict(window_id=1, seats=3)).status_code == 200
    assert rows(pg, "SELECT session_id, seats FROM holds") == [(api.session_id, 3)]


def test_expired_sessions_are_purged_at_startup(api, world, pg, database, tmp_path):
    pg.execute("INSERT INTO sessions (token_hash, role, created_at, expires_at) "
               "VALUES (sha256('expired'), 'guest', app_now() - interval '2 days', app_now() - interval '1 day')")
    pg.execute("INSERT INTO holds (window_id, seats, session_id, created_at, expires_at) "
               "SELECT 1, 2, id, n, n + interval '10 minutes' FROM sessions, (SELECT app_now() AS n) x "
               "WHERE token_hash = sha256('expired')")
    pg.commit()
    second = start_backend(database, tmp_path, name="purge")
    try:
        assert rows(pg, "SELECT count(*) FROM sessions WHERE token_hash = sha256('expired')") == [(0,)]
        assert rows(pg, "SELECT session_id FROM holds") == [(None,)]  # ON DELETE SET NULL
        assert rows(pg, "SELECT count(*) FROM sessions WHERE id = %s", (api.session_id,)) == [(1,)]  # still valid
    finally:
        second.stop()


def test_no_token_cookie_or_body_reaches_the_backend_log(api, backend):
    marker = "Body-Marker-Ada-Lovelace-7d1f"
    assert api.post("/api/bookings", json=dict(window_id=1, seats=1, guest=marker)).status_code == 201
    assert api.post("/api/holds", json=dict(window_id=2, seats=1)).status_code == 200
    log = backend.output()
    assert "POST /api/bookings" in log  # the access log is on, and it is the right file
    assert api.token not in log
    assert COOKIE not in log
    assert marker not in log


def test_the_cookie_is_secure_when_https_is_on(database, tmp_path):
    origin = "https://localhost:8443"
    b = start_backend(database, tmp_path, name="https", env={"BP_HTTPS": "on", "BP_BASE_URL": origin})
    try:
        with httpx.Client(base_url=b.base, headers={"Origin": origin}, verify=_TLS) as c:
            r = c.post("/api/session", json={})
    finally:
        b.stop()
    assert r.status_code == 200, r.text
    attrs = [a.strip().lower() for a in r.headers["set-cookie"].split(";")]
    assert "secure" in attrs and "httponly" in attrs and "samesite=strict" in attrs
