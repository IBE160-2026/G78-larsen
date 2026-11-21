"""FR-21 / AD-8: server-side sessions with hashed tokens, set only by `POST /api/session`.

The cookie holds a 256-bit random token (HttpOnly, SameSite=Strict, Path=/, Secure only with BP_HTTPS); the store
keeps only its SHA-256 hash. Anonymous sessions last 24 h and Administrator sessions 8 h, both sliding, judged on
app_now(). Expired rows are purged at startup. Nothing secret reaches the backend log (AD-19).
"""

from __future__ import annotations

import datetime as dt
import uuid

import httpx
import pytest

from client import COOKIE, _TLS, admin_client, api_client, token_hash
from conftest import EARLY, raw_booking, set_clock, start_backend


def rows(pg, sql, params=()):
    pg.rollback()
    out = pg.execute(sql, params).fetchall()
    pg.rollback()
    return out


def test_a_guest_write_without_a_session_is_401_and_writes_nothing(world, pg):
    with api_client(world, session=False) as anon:
        for r in [anon.post("/api/holds", json=dict(window_id=1, seats=1)),
                  anon.book(1, 1),
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
    # the expired session also paid for a Booking under a key (Story 1.5)
    booking_id = pg.execute(raw_booking(2, 3) + " RETURNING id").fetchone()[0]
    pg.execute("UPDATE bookings SET session_id = (SELECT id FROM sessions WHERE token_hash = sha256('expired')) "
               "WHERE id = %s", (booking_id,))
    pg.execute("INSERT INTO idempotency_keys (key, session_id, endpoint, request_hash, booking_id) "
               "SELECT gen_random_uuid(), id, 'POST /api/bookings', sha256('x'), %s FROM sessions "
               "WHERE token_hash = sha256('expired')", (booking_id,))
    pg.commit()
    second = start_backend(database, tmp_path, name="purge")
    try:
        assert rows(pg, "SELECT count(*) FROM sessions WHERE token_hash = sha256('expired')") == [(0,)]
        assert rows(pg, "SELECT session_id FROM holds") == [(None,)]  # ON DELETE SET NULL
        # the Booking stays, without its session, and still takes its Seats; so does its key (0007, AD-9)
        assert rows(pg, "SELECT session_id, status FROM bookings WHERE id = %s", (booking_id,)) == [(None, "active")]
        assert rows(pg, "SELECT window_booked_seats(2)") == [(3,)]
        assert rows(pg, "SELECT session_id FROM idempotency_keys WHERE booking_id = %s", (booking_id,)) == [(None,)]
        assert rows(pg, "SELECT count(*) FROM sessions WHERE id = %s", (api.session_id,)) == [(1,)]  # still valid
    finally:
        second.stop()


def test_a_key_outlives_its_session_so_a_retry_after_a_purge_never_charges_twice(api, world, pg):
    """AD-9 (0007): a paid key whose session is gone (purged, signed out) stays with `session_id` NULL; the same
    request from a new session is `409 invalid_key` and writes nothing: one Booking, one payment."""
    key = str(uuid.uuid4())
    assert api.book(1, 2, key=key).status_code == 201
    pg.execute("DELETE FROM sessions WHERE id = %s", (api.session_id,))  # what the purge does
    pg.commit()
    assert rows(pg, "SELECT session_id FROM idempotency_keys WHERE key = %s", (key,)) == [(None,)]
    assert api.book(1, 2, key=key).status_code == 401  # the old cookie names no session any more
    with api_client(world) as fresh:
        r = fresh.book(1, 2, key=key)
    assert r.status_code == 409 and r.json() == {"detail": {"error": "invalid_key"}}, r.text
    assert rows(pg, "SELECT (SELECT count(*) FROM bookings), (SELECT count(*) FROM payments), "
                    "(SELECT count(*) FROM outbox_emails), (SELECT count(*) FROM idempotency_keys)") == [(1, 1, 1, 1)]


def test_no_token_cookie_or_body_reaches_the_backend_log(api, backend):
    marker = "Body-Marker-Ada-Lovelace-7d1f"
    assert api.book(1, 1, name=marker).status_code == 201
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


@pytest.mark.parametrize("path", ["/api/bookings", "/api/holds"])
def test_a_sign_out_racing_a_write_is_no_session_not_not_found(api, pg, path):
    """The session row is deleted between the request's session check and its insert (a trigger in the test database
    deletes it inside the write, exactly in between). The foreign key refuses the insert, and the answer is
    `401 no_session`, never `404 not_found` (db/refusals.py). Nothing is written."""
    table = "bookings" if path == "/api/bookings" else "holds"
    pg.execute("CREATE OR REPLACE FUNCTION sign_out_now() RETURNS trigger LANGUAGE plpgsql AS $$ "
               "BEGIN DELETE FROM sessions WHERE id = NEW.session_id; RETURN NEW; END $$")
    pg.execute(f"CREATE TRIGGER z_sign_out_now BEFORE INSERT ON {table} FOR EACH ROW EXECUTE FUNCTION sign_out_now()")
    pg.commit()
    try:
        r = api.book(1, 1) if table == "bookings" else api.post(path, json=dict(window_id=1, seats=1))
        assert r.status_code == 401 and r.json() == {"detail": {"error": "no_session"}}, r.text
    finally:
        pg.rollback()
        pg.execute(f"DROP TRIGGER z_sign_out_now ON {table}")
        pg.execute("DROP FUNCTION sign_out_now()")
        pg.commit()
    assert rows(pg, "SELECT (SELECT count(*) FROM bookings), (SELECT count(*) FROM holds), "
                    "(SELECT count(*) FROM idempotency_keys), (SELECT count(*) FROM sessions)") == [(0, 0, 0, 1)]
