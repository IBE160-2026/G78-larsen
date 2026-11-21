"""FR-15 / PW-5 / PW-6 / AD-8 / AD-11: the Administrator signs in and out.

- A correct sign-in (the seeded email in any case) answers `{"role": "admin"}`, rotates the token on the same
  `sessions` row (the old token names nothing), gives the row the account, the Administrator role and 8 h, and resets
  the throttle.
- A wrong password, an unknown email and a throttled email all get the byte-identical `401 sign_in_refused`, and every
  refusal adds 1 to the email's `failures`. After 5 in a row the email is refused for 15 minutes even with the right
  password; a locked attempt never extends the lock; once the clock (`clock.off`) has moved past it, the right
  password signs in and `failures` is 0 again. Parallel wrong attempts are all counted.
- Without a session the answer is `401 no_session` and no throttle row is touched; a foreign `Origin` is
  `403 cross_origin` and nothing is written.
- Sign-out deletes the row and clears the cookie; the old token then gets 401 on `/api/admin/`.
"""

from __future__ import annotations

import datetime as dt
import unicodedata
from concurrent.futures import ThreadPoolExecutor

import httpx
import psycopg
import pytest
from argon2 import PasswordHasher

from booking_platform import db
from booking_platform.services import auth, sessions
from client import ADMIN_LOGIN, COOKIE, _TLS, api_client, sign_in, token_hash
from conftest import EARLY, set_clock

EMAIL, PASSWORD = ADMIN_LOGIN["email"], ADMIN_LOGIN["password"]
REFUSED = {"detail": {"error": "sign_in_refused"}}
NOT_SIGNED_IN = {"detail": {"error": "not_signed_in"}}


def one(pg, sql, params=()):
    pg.rollback()
    row = pg.execute(sql, params).fetchone()
    pg.rollback()
    return row


def throttle(pg, email=EMAIL) -> tuple | None:
    """(failures, locked_until) of the email's throttle row, or None."""
    return one(pg, "SELECT failures, locked_until FROM sign_in_throttle WHERE email_lower = lower(%s)", (email,))


def session_row(pg, token: str) -> tuple | None:
    return one(pg, "SELECT id, role, account_id, expires_at - app_now() FROM sessions WHERE token_hash = %s",
               (token_hash(token),))


# ------------------------------------------------------------------ the correct password


@pytest.mark.parametrize("email", [EMAIL, EMAIL.upper(), "Admin@SaunaLoyly.Example"], ids=["lower", "upper", "mixed"])
def test_the_right_password_signs_in_and_rotates_the_token_on_the_same_row(world, pg, email):
    with api_client(world) as c:
        old = c.token
        sid = session_row(pg, old)[0]
        assert c.get("/api/admin/me").status_code == 401  # a Guest's session is anonymous here
        r = sign_in(c, email)
        assert r.status_code == 200 and r.json() == {"role": "admin"}, r.text
        new = c.token
        assert new != old and len(new) >= 43
        attrs = [a.strip().lower() for a in r.headers["set-cookie"].split(";")]
        assert attrs[0].startswith(f"{COOKIE}=") and "httponly" in attrs and "samesite=strict" in attrs
        assert "path=/" in attrs and "secure" not in attrs
        assert "password" not in r.text and "argon2" not in r.text
        account = one(pg, "SELECT id FROM accounts WHERE email = %s", (EMAIL,))[0]
        row = session_row(pg, new)
        assert row[:3] == (sid, "admin", account)  # the same row, now the Administrator's
        assert dt.timedelta(hours=7, minutes=59) < row[3] <= dt.timedelta(hours=8)
        assert session_row(pg, old) is None
        assert c.get("/api/admin/me").json() == {"role": "admin"}
    with httpx.Client(base_url=world, verify=_TLS) as stale:
        stale.cookies.set(COOKIE, old, domain=httpx.URL(world).host)
        r = stale.get("/api/admin/me")
        assert r.status_code == 401 and r.json() == NOT_SIGNED_IN
    assert throttle(pg) == (0, None)


def test_a_success_resets_the_failures(world, pg):
    with api_client(world) as c:
        for _ in range(3):
            assert sign_in(c, password="not the password at all").status_code == 401
        assert throttle(pg)[0] == 3
        assert sign_in(c).status_code == 200
    assert throttle(pg) == (0, None)


def test_a_stale_hash_is_rehashed_at_sign_in(world, pg):
    weak = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1).hash(PASSWORD)
    (before,) = one(pg, "SELECT password_hash FROM accounts WHERE email = %s", (EMAIL,))
    pg.execute("UPDATE accounts SET password_hash = %s WHERE email = %s", (weak, EMAIL))
    pg.commit()
    try:
        with api_client(world) as c:
            assert sign_in(c).status_code == 200
        (after,) = one(pg, "SELECT password_hash FROM accounts WHERE email = %s", (EMAIL,))
        assert after != weak and after.startswith("$argon2id$v=19$m=65536,t=3,p=4$")
    finally:
        pg.execute("UPDATE accounts SET password_hash = %s WHERE email = %s", (before, EMAIL))
        pg.commit()


# ------------------------------------------------------------------ refusals


def test_a_wrong_password_and_an_unknown_email_get_the_same_answer(world, pg):
    with api_client(world) as c:
        wrong = sign_in(c, password="not the password at all")
        unknown = sign_in(c, email="nobody@saunaloyly.example", password=PASSWORD)
        token = c.token
    for r in (wrong, unknown):
        assert r.status_code == 401 and r.json() == REFUSED, r.text
        assert "set-cookie" not in r.headers
    assert wrong.content == unknown.content
    assert {k: v for k, v in wrong.headers.items() if k != "date"} == \
           {k: v for k, v in unknown.headers.items() if k != "date"}
    assert throttle(pg) == (1, None)
    assert throttle(pg, "nobody@saunaloyly.example") == (1, None)  # known or not, every email is counted
    assert session_row(pg, token)[1:3] == ("guest", None)  # nothing changed on the session


def test_five_failures_lock_the_email_for_15_minutes_even_with_the_right_password(world, pg):
    with api_client(world) as c:
        for i in range(1, 6):
            wrong = sign_in(c, password=f"wrong password number {i}")
            assert wrong.json() == REFUSED
        failures, locked_until = throttle(pg)
        assert failures == 5 and locked_until is not None
        (now,) = one(pg, "SELECT app_now()")
        assert dt.timedelta(minutes=14, seconds=59) < locked_until - now <= dt.timedelta(minutes=15)

        set_clock(pg, EARLY + dt.timedelta(minutes=10))
        r = sign_in(c)
        assert r.status_code == 401 and r.json() == REFUSED  # the right password, but locked
        assert r.content == wrong.content  # byte-identical to a wrong password
        assert {k: v for k, v in r.headers.items() if k != "date"} == \
               {k: v for k, v in wrong.headers.items() if k != "date"}
        assert throttle(pg) == (6, locked_until)  # counted, and the lock is not extended

        set_clock(pg, EARLY + dt.timedelta(minutes=15, seconds=1))
        r = sign_in(c)
        assert r.status_code == 200 and r.json() == {"role": "admin"}, r.text
    assert throttle(pg) == (0, None)


def test_a_wrong_password_after_the_lock_locks_again_at_once(world, pg):
    """The failures are still 5 or more after the lock ends; one more wrong attempt locks the email again."""
    with api_client(world) as c:
        for i in range(5):
            sign_in(c, password=f"wrong password number {i}")
        set_clock(pg, EARLY + dt.timedelta(minutes=16))
        assert sign_in(c, password="still not the password").json() == REFUSED
        failures, locked_until = throttle(pg)
        (now,) = one(pg, "SELECT app_now()")
        assert failures == 6 and locked_until - now > dt.timedelta(minutes=14)


def test_an_unknown_email_is_throttled_too(world, pg):
    with api_client(world) as c:
        for _ in range(6):
            assert sign_in(c, email="Someone@Elsewhere.example").json() == REFUSED
    failures, locked_until = throttle(pg, "someone@elsewhere.example")
    assert failures == 6 and locked_until is not None


def test_ten_parallel_wrong_attempts_are_all_counted(world, pg):
    clients = [api_client(world) for _ in range(10)]
    try:
        with ThreadPoolExecutor(10) as ex:
            answers = list(ex.map(lambda c: sign_in(c, password="a parallel wrong password"), clients))
    finally:
        for c in clients:
            c.close()
    assert [r.status_code for r in answers] == [401] * 10
    assert throttle(pg)[0] == 10


@pytest.mark.parametrize("cookie", [None, "not-a-real-token"], ids=["no-cookie", "unknown-token"])
def test_without_a_session_sign_in_is_no_session_and_touches_no_throttle_row(world, pg, cookie):
    with api_client(world, session=False) as c:
        if cookie:
            c.cookies.set(COOKIE, cookie, domain=httpx.URL(world).host)
        for password in (PASSWORD, "a wrong password here"):
            r = sign_in(c, password=password)
            assert r.status_code == 401 and r.json() == {"detail": {"error": "no_session"}}, r.text
    assert one(pg, "SELECT count(*) FROM sign_in_throttle") == (0,)
    assert one(pg, "SELECT count(*) FROM sessions") == (0,)


@pytest.mark.parametrize("body", [
    {"email": EMAIL},
    {"email": EMAIL, "password": PASSWORD, "role": "admin"},
    {"email": "x" * 255, "password": PASSWORD},
    {"email": EMAIL, "password": "p" * 1025},
    {"email": EMAIL + "\u0000", "password": PASSWORD},
    {"email": EMAIL, "password": PASSWORD + "\u0000"},
], ids=["no-password", "extra-field", "long-email", "long-password", "nul-email", "nul-password"])
def test_a_malformed_body_is_invalid_input_and_writes_nothing(api, pg, body):
    r = api.post("/api/admin/sign-in", json=body)
    assert r.status_code == 422 and r.json()["detail"]["error"] == "invalid_input", r.text
    assert one(pg, "SELECT count(*) FROM sign_in_throttle") == (0,)


def test_a_password_of_1024_characters_is_an_ordinary_refusal(api):
    r = sign_in(api, password="p" * 1024)
    assert r.status_code == 401 and r.json() == REFUSED


@pytest.mark.parametrize("headers", [{"Origin": "http://evil.example"}, {}], ids=["evil", "none"])
def test_cross_origin_sign_in_and_sign_out_are_refused_and_write_nothing(admin, api, world, pg, headers):
    before = one(pg, "SELECT (SELECT count(*) FROM sessions), (SELECT array_agg((failures, locked_until)::text) "
                     "FROM sign_in_throttle)")
    for token, path, body in [(api.token, "/api/admin/sign-in", {"email": EMAIL, "password": PASSWORD}),
                              (api.token, "/api/admin/sign-in", {"email": EMAIL, "password": "wrong password!!"}),
                              (admin.token, "/api/admin/sign-out", None)]:
        with httpx.Client(base_url=world, headers=headers, verify=_TLS) as c:
            c.cookies.set(COOKIE, token, domain=httpx.URL(world).host)
            r = c.post(path, json=body)
        assert r.status_code == 403 and r.json() == {"detail": {"error": "cross_origin"}}, r.text
    assert one(pg, "SELECT (SELECT count(*) FROM sessions), (SELECT array_agg((failures, locked_until)::text) "
                   "FROM sign_in_throttle)") == before
    assert session_row(pg, api.token)[1] == "guest"
    assert admin.get("/api/admin/me").status_code == 200


# ------------------------------------------------------------------ sign-out and the guard


def test_sign_out_deletes_the_row_and_clears_the_cookie(admin, world, pg):
    token = admin.token
    sid = session_row(pg, token)[0]
    r = admin.post("/api/admin/sign-out")
    assert r.status_code == 200 and r.json() == {"ok": True}, r.text
    attrs = [a.strip().lower() for a in r.headers["set-cookie"].split(";")]
    assert attrs[0] in (f"{COOKIE}=", f'{COOKIE}=""') and "max-age=0" in attrs
    assert one(pg, "SELECT count(*) FROM sessions WHERE id = %s", (sid,)) == (0,)
    with httpx.Client(base_url=world, headers={"Origin": world}, verify=_TLS) as stale:
        stale.cookies.set(COOKIE, token, domain=httpx.URL(world).host)
        for method, path in [("GET", "/api/admin/me"), ("POST", "/api/admin/sign-out"),
                             ("POST", "/api/admin/marks")]:
            r = stale.request(method, path, json={"window_id": 1, "sauna_id": 1} if path.endswith("marks") else None)
            assert r.status_code == 401 and r.json() == NOT_SIGNED_IN, (path, r.text)
    assert one(pg, "SELECT count(*) FROM marks") == (0,)


@pytest.mark.parametrize("method,path", [("GET", "/api/admin/me"), ("POST", "/api/admin/sign-out")])
def test_me_and_sign_out_need_a_signed_in_administrator(world, api, pg, method, path):
    with api_client(world, session=False) as anon:
        r = anon.request(method, path)
        assert r.status_code == 401 and r.json() == NOT_SIGNED_IN
    r = api.request(method, path)  # a Guest's session has no account
    assert r.status_code == 401 and r.json() == NOT_SIGNED_IN
    assert session_row(pg, api.token) is not None  # sign-out by a Guest deleted nothing


def test_an_expired_administrator_is_not_signed_in(admin, pg):
    set_clock(pg, EARLY + dt.timedelta(hours=8, minutes=1))
    r = admin.get("/api/admin/me")
    assert r.status_code == 401 and r.json() == NOT_SIGNED_IN


def test_no_password_or_token_reaches_the_backend_log(world, backend):
    with api_client(world) as c:
        sign_in(c, password="Marker-Wrong-Password-5c1e")
        assert sign_in(c).status_code == 200
        token = c.token
        assert c.post("/api/admin/sign-out").status_code == 200
    log = backend.output()
    assert "POST /api/admin/sign-in" in log
    for secret in ("Marker-Wrong-Password-5c1e", PASSWORD, token, "$argon2"):
        assert secret not in log


# ------------------------------------------------------------------ services.auth, in process


@pytest.fixture
def pool(world, database):
    db.open_pool(database, max_size=2)
    yield
    db.close_pool()


def test_verify_runs_for_an_unknown_email_against_the_dummy_hash(pool, pg, monkeypatch):
    seen = []
    real = auth._verify

    def spy(password_hash, password):
        seen.append(password_hash)
        return real(password_hash, password)

    monkeypatch.setattr(auth, "_verify", spy)
    s, _token = sessions.open_session(None)
    with pytest.raises(auth.Refused) as e:
        auth.sign_in(s, "nobody@saunaloyly.example", PASSWORD)
    assert e.value.code == "sign_in_refused"
    assert seen == [auth._DUMMY_HASH]
    (known,) = one(pg, "SELECT password_hash FROM accounts WHERE email = %s", (EMAIL,))
    with pytest.raises(auth.Refused):
        auth.sign_in(s, EMAIL, "a wrong password, verified")
    assert seen[1] == known
    # a locked attempt verifies too
    for _ in range(5):
        with pytest.raises(auth.Refused):
            auth.sign_in(s, EMAIL, "a wrong password, verified")
    seen.clear()
    with pytest.raises(auth.Refused):
        auth.sign_in(s, EMAIL, PASSWORD)
    assert seen == [known]
    with pytest.raises(auth.Refused) as e:
        auth.sign_in(None, EMAIL, PASSWORD)
    assert e.value.code == "no_session"


def test_a_session_gone_before_the_rotation_is_no_session_and_changes_no_count(pool, pg):
    s, _token = sessions.open_session(None)
    for _ in range(2):
        with pytest.raises(auth.Refused):
            auth.sign_in(s, EMAIL, "a wrong password, counted")
    assert throttle(pg)[0] == 2
    pg.execute("DELETE FROM sessions WHERE id = %s", (s.id,))
    pg.commit()
    with pytest.raises(auth.Refused) as e:
        auth.sign_in(sessions.Session(id=s.id, role="guest"), EMAIL, PASSWORD)
    assert e.value.code == "no_session"
    assert throttle(pg)[0] == 2  # the right password, but nothing was written


NFC_EMAIL = "nfc.staff@saunaloyly.example"
NFC_PASSWORD = unicodedata.normalize("NFC", "Kåre på lørdagskveld i badstuen")


@pytest.fixture
def nfc_account(database, pg):
    with psycopg.connect(database) as c:
        auth.set_account(c, NFC_EMAIL, NFC_PASSWORD, overwrite=True)
    yield
    pg.rollback()
    pg.execute("DELETE FROM accounts WHERE email = %s", (NFC_EMAIL,))
    pg.commit()


def test_a_password_typed_in_nfd_signs_in(nfc_account, api):
    nfd = unicodedata.normalize("NFD", NFC_PASSWORD)
    assert nfd != NFC_PASSWORD
    r = sign_in(api, NFC_EMAIL, nfd)
    assert r.status_code == 200 and r.json() == {"role": "admin"}, r.text
