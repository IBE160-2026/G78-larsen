"""FR-25 / AD-28 / AD-4 (Story 4.1): the Manage link opens the Booking.

Paying for a Seat booking issues a Manage token: 256 random bits (`secrets.token_urlsafe(32)`, 43 characters), stored
only as its SHA-256 hash, and emailed as `<BP_BASE_URL>/manage#t=<token>`. `POST /api/manage/open {token}` creates or
reuses the session, upserts one grant and returns `{reference}`; every token that opens nothing (unknown, malformed,
too long, revoked, its Window ended) is the same `404 not_found`, and then no session is created.
`GET /api/manage/{reference}` answers only a session with a valid grant (used in the last 30 minutes, token unrevoked,
before the Window ends); everything else is the same `404 not_found` (RB-4, RB-5). The read returns the AD-23 shape plus
`version`, `change_allowed` (the SQL Cutoff predicate), `cutoff_at` and an empty `history`, and nothing beyond the
Booking. Sign-out ends the grants by cascade; startup purges stale ones; the seed gives every sample Booking a link once.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shutil

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from booking_platform import config, db
from booking_platform.services import manage
from booking_platform.services.booking import nok
from booking_platform.services.seed import manage_email
from client import COOKIE, api_client
from conftest import ADMIN_URL, SAUNAS, TEST_URL, raw_booking, set_clock, start_backend, win_start

NOT_FOUND = {"detail": {"error": "not_found"}}
BEFORE = win_start(1) - dt.timedelta(hours=14, minutes=30)  # 2026-11-30 20:00Z: before Window 2's Cutoff
TOKEN = re.compile(r"(?m)/manage#t=([A-Za-z0-9_-]{43})$")
CHANGE_STATEMENT = ("Up to 12 hours before the session starts, you can move some or all seats to another session, or "
                    "give them up for a voucher. Money is not refunded.")
SAUNA_NAMES = [name for _id, name, _cap in SAUNAS] + ["Löyly"]


def rows(pg, query, params=()):
    pg.rollback()
    out = pg.execute(query, params).fetchall()
    pg.rollback()
    return out


def book(api, window_id: int = 2, seats: int = 2) -> tuple[str, str, dict]:
    """Pay for a Booking; returns (reference, the token of its Manage link, the response body)."""
    r = api.book(window_id, seats)
    assert r.status_code == 201, r.text
    body = r.json()
    [email] = body["emails"]
    m = TOKEN.search(email["body"])
    assert m, email["body"]
    return body["booking"]["reference"], m.group(1), body


def open_link(client, token):
    return client.post("/api/manage/open", json={"token": token})


def counts(pg) -> tuple:
    return rows(pg, "SELECT (SELECT count(*) FROM sessions), (SELECT count(*) FROM manage_grants), "
                    "(SELECT count(*) FROM access_tokens), (SELECT count(*) FROM bookings), "
                    "(SELECT count(*) FROM outbox_emails), (SELECT count(*) FROM payments), "
                    "(SELECT count(*) FROM idempotency_keys)")[0]


def stored(pg) -> list:
    """Every row a read must leave alone (the grant's `last_used_at` and the session's expiry excepted)."""
    return rows(pg, "SELECT (SELECT array_agg(b::text ORDER BY b.id) FROM bookings b), "
                    "(SELECT array_agg(t::text ORDER BY t.id) FROM access_tokens t), "
                    "(SELECT array_agg(o::text ORDER BY o.id) FROM outbox_emails o), "
                    "(SELECT array_agg(p::text ORDER BY p.id) FROM payments p), "
                    "(SELECT array_agg((g.id, g.session_id, g.token_id)::text ORDER BY g.id) FROM manage_grants g)")


@pytest.fixture
def before_cutoff(world, pg):
    set_clock(pg, BEFORE)
    return world


# ------------------------------------------------------------------ the store (migration 0010)


def test_the_cutoff_is_a_setting_copied_into_each_booking(world, pg):
    assert rows(pg, "SELECT cutoff_seats FROM settings") == [(dt.timedelta(hours=12),)]
    with pytest.raises(psycopg.errors.CheckViolation) as e:
        pg.execute("UPDATE settings SET cutoff_seats = interval '1 hour 59 minutes'")
    assert e.value.diag.constraint_name == "cutoff_seats_at_least_2_hours"
    pg.rollback()
    pg.execute(raw_booking(1, 1))  # a Booking written straight to the store gets the setting too
    pg.commit()
    assert rows(pg, "SELECT cutoff, version FROM bookings") == [(dt.timedelta(hours=12), 0)]


def test_the_predicates_are_volatile_sql_functions(world, pg):
    got = rows(pg, "SELECT proname, provolatile FROM pg_proc WHERE proname IN "
                   "('change_allowed', 'manage_grant_valid', 'manage_token_valid') ORDER BY proname")
    assert got == [("change_allowed", "v"), ("manage_grant_valid", "v"), ("manage_token_valid", "v")]
    assert rows(pg, "SELECT change_allowed(-1), manage_grant_valid(-1, -1), manage_token_valid(-1)") == [
        (False, False, False)]


def test_at_most_one_unrevoked_manage_token_per_booking(world, pg):
    pg.execute(raw_booking(1, 1))
    pg.execute("INSERT INTO access_tokens (purpose, booking_id, token_hash) SELECT 'manage', id, %s FROM bookings",
               (hashlib.sha256(b"a").digest(),))
    with pytest.raises(psycopg.errors.UniqueViolation) as e:
        pg.execute("INSERT INTO access_tokens (purpose, booking_id, token_hash) SELECT 'manage', id, %s FROM bookings",
                   (hashlib.sha256(b"b").digest(),))
    assert e.value.diag.constraint_name == "access_tokens_one_manage"
    pg.rollback()


@pytest.fixture
def scratch_db():
    name = "booking_test_scratch_manage"
    with psycopg.connect(ADMIN_URL, autocommit=True) as c:
        c.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))
        c.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    yield make_conninfo(TEST_URL, dbname=name)
    with psycopg.connect(ADMIN_URL, autocommit=True) as c:
        c.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))


def test_0010_fills_the_cutoff_of_existing_bookings_and_issues_no_token(tmp_path, scratch_db):
    from booking_platform.db import migrate as migrations

    before = tmp_path / "before"
    before.mkdir()
    for p in migrations.migration_files():
        if p.name < "0010":
            shutil.copy(p, before / p.name)
    migrations.migrate(scratch_db, before)
    with psycopg.connect(scratch_db) as c:
        c.execute("INSERT INTO saunas (id, name, capacity, fill_order) VALUES (1, 'A', 20, 1)")
        c.execute("INSERT INTO windows (during) VALUES (tstzrange('2026-12-01 09:00Z', '2026-12-01 10:30Z'))")
        c.execute(raw_booking(1, 2))
    upto = tmp_path / "upto-0010"  # later migrations (0011 on) are not this test's
    upto.mkdir()
    for p in migrations.migration_files():
        if p.name < "0011":
            shutil.copy(p, upto / p.name)
    assert migrations.migrate(scratch_db, upto) == ["0010_manage_links.sql"]
    with psycopg.connect(scratch_db) as c:
        assert c.execute("SELECT cutoff, version FROM bookings").fetchall() == [(dt.timedelta(hours=12), 0)]
        assert c.execute("SELECT count(*) FROM access_tokens").fetchone()[0] == 0
        assert c.execute("SELECT attnotnull FROM pg_attribute WHERE attrelid = 'bookings'::regclass "
                         "AND attname = 'cutoff'").fetchone()[0] is True
        triggers = c.execute("SELECT tgname FROM pg_trigger WHERE tgrelid = 'bookings'::regclass "
                             "AND NOT tgisinternal ORDER BY tgname").fetchall()
        assert triggers == [("a_lock_bookings",), ("t_bookings",)]


# ------------------------------------------------------------------ issue and the email link (CAP-2)


def test_paying_issues_one_hashed_token_and_emails_its_link(api, world, pg):
    ref, token, body = book(api)
    assert len(token) == 43
    tokens = rows(pg, "SELECT t.purpose, b.reference, t.token_hash, t.revoked_at FROM access_tokens t "
                      "JOIN bookings b ON b.id = t.booking_id")
    assert tokens == [("manage", ref, hashlib.sha256(token.encode()).digest(), None)]
    lines = body["emails"][0]["body"].split("\n")
    i = lines.index("Manage your booking")
    assert lines[i + 1] == f"{world}/manage#t={token}"
    assert lines[i + 2:i + 4] == ["", "Before you come"]
    assert CHANGE_STATEMENT in lines
    # the token is in the Outbox email alone; every other table holds at most its hash
    for table in ("access_tokens", "manage_grants", "bookings", "sessions", "idempotency_keys", "payments"):
        assert not rows(pg, f"SELECT 1 FROM {table} x WHERE x::text LIKE %s", (f"%{token}%",)), table
    assert rows(pg, "SELECT count(*) FROM outbox_emails WHERE body LIKE %s", (f"%{token}%",)) == [(1,)]
    # the cutoff copied from settings, version 0
    assert rows(pg, "SELECT cutoff, version FROM bookings") == [(dt.timedelta(hours=12), 0)]


def test_a_repeat_of_the_payment_issues_no_second_token(api, pg):
    r1 = api.book(2, 2, key="11111111-1111-4111-8111-111111111111")
    r2 = api.book(2, 2, key="11111111-1111-4111-8111-111111111111")
    assert r1.status_code == r2.status_code == 201 and r1.json() == r2.json()
    assert rows(pg, "SELECT count(*) FROM access_tokens") == [(1,)]


@pytest.fixture
def pool(world, database):
    db.open_pool(database, max_size=2)
    yield
    db.close_pool()


def test_issue_revokes_the_earlier_token(api, pg, pool):
    ref, token, _ = book(api)
    booking_id = rows(pg, "SELECT id FROM bookings")[0][0]
    second = db.run(lambda c: manage.issue(c, booking_id))
    assert second != token and len(second) == 43
    got = rows(pg, "SELECT token_hash, revoked_at IS NOT NULL FROM access_tokens ORDER BY id")
    assert got == [(hashlib.sha256(token.encode()).digest(), True), (hashlib.sha256(second.encode()).digest(), False)]
    assert manage.link(second) == config.settings().base_url + "/manage#t=" + second


# ------------------------------------------------------------------ open (CAP-4, CAP-5)


def test_open_without_a_session_sets_the_cookie_and_returns_the_reference(before_cutoff, pg):
    with api_client(before_cutoff) as payer:
        ref, token, _ = book(payer)
    with api_client(before_cutoff, session=False) as guest:
        r = open_link(guest, token)
        assert r.status_code == 200 and r.json() == {"reference": ref}, r.text
        attrs = [a.strip().lower() for a in r.headers["set-cookie"].split(";")]
        assert attrs[0].startswith(f"{COOKIE}=") and "httponly" in attrs and "samesite=strict" in attrs
        sid = guest.session_id
        assert rows(pg, "SELECT session_id FROM manage_grants") == [(sid,)]
        assert guest.get(f"/api/manage/{ref}").status_code == 200


def test_open_with_a_session_reuses_it_and_again_keeps_one_grant(before_cutoff, api, pg):
    ref, token, _ = book(api)
    sessions_before = rows(pg, "SELECT count(*) FROM sessions")
    r = open_link(api, token)
    assert r.status_code == 200 and r.json() == {"reference": ref}
    assert "set-cookie" not in r.headers
    assert rows(pg, "SELECT count(*) FROM sessions") == sessions_before
    first = rows(pg, "SELECT id, session_id, last_used_at FROM manage_grants")
    assert len(first) == 1 and first[0][1] == api.session_id
    set_clock(pg, BEFORE + dt.timedelta(minutes=5))
    assert open_link(api, token).status_code == 200
    again = rows(pg, "SELECT id, session_id, last_used_at, last_used_at - app_now() FROM manage_grants")
    assert len(again) == 1 and again[0][:2] == first[0][:2]
    assert again[0][2] > first[0][2] + dt.timedelta(minutes=4)  # last_used_at is now


def test_every_bad_token_is_the_same_404_and_creates_nothing(before_cutoff, api, pg):
    ref, token, _ = book(api)
    pg.execute("INSERT INTO access_tokens (purpose, booking_id, token_hash, revoked_at) "
               "SELECT 'manage', id, %s, app_now() FROM bookings", (hashlib.sha256(b"revoked-token").digest(),))
    pg.commit()
    before = counts(pg)
    answers = []
    with api_client(before_cutoff, session=False) as anon:
        for bad in ("", "x", "y" * 500, "z" * 201, token[:-1], token + "A", token.lower() if token.lower() != token
                    else token.upper(), "revoked-token", "../" + token, " " + token, "\u0000"):
            answers.append(open_link(anon, bad))
        assert anon.cookies.get(COOKIE) is None
    for r in answers:
        assert r.status_code == 404 and r.json() == NOT_FOUND, (r.request.content, r.text)
        assert "set-cookie" not in r.headers
    assert len({r.content for r in answers}) == 1
    assert counts(pg) == before  # no session, no grant


def test_a_revoked_token_and_one_whose_window_ended_are_404(before_cutoff, api, pg):
    ref, token, _ = book(api)
    assert open_link(api, token).status_code == 200
    pg.execute("UPDATE access_tokens SET revoked_at = app_now()")
    pg.commit()
    assert open_link(api, token).json() == NOT_FOUND
    assert api.get(f"/api/manage/{ref}").json() == NOT_FOUND  # an open page loses access at once
    pg.execute("UPDATE access_tokens SET revoked_at = NULL")
    pg.commit()
    assert api.get(f"/api/manage/{ref}").status_code == 200
    set_clock(pg, win_start(2))  # Window 2 has just ended
    with api_client(before_cutoff, session=False) as anon:
        r = open_link(anon, token)
        assert r.status_code == 404 and r.json() == NOT_FOUND and "set-cookie" not in r.headers
    assert api.get(f"/api/manage/{ref}").json() == NOT_FOUND
    set_clock(pg, win_start(2) - dt.timedelta(seconds=30))  # just before the end it still opens
    assert open_link(api, token).status_code == 200


@pytest.mark.parametrize("content,kwargs", [
    ("not json", {"headers": {"Content-Type": "application/json"}}),
    (None, {"json": {}}),
    (None, {"json": {"token": 12345}}),
    (None, {"json": {"token": None}}),
    (None, {"json": {"token": "x", "reference": "ABCDEFGH"}}),
    (None, {"json": ["x"]}),
])
def test_a_body_of_the_wrong_shape_is_422(world, pg, content, kwargs):
    before = counts(pg)
    with api_client(world, session=False) as anon:
        r = anon.post("/api/manage/open", content=content, **kwargs)
    assert r.status_code == 422 and r.json()["detail"]["error"] == "invalid_input", r.text
    assert counts(pg) == before


def test_open_from_another_origin_is_403(api, world, pg):
    _ref, token, _ = book(api)
    with api_client(world, session=False, origin="https://evil.example") as other:
        r = open_link(other, token)
    assert r.status_code == 403 and r.json() == {"detail": {"error": "cross_origin"}}
    assert rows(pg, "SELECT count(*) FROM manage_grants") == [(0,)]


def test_get_on_open_and_other_paths_are_the_json_404(api, world):
    ref, token, _ = book(api)
    assert open_link(api, token).status_code == 200
    for method, path in [("GET", "/api/manage/open"), ("GET", f"/api/manage/{ref}/"), ("POST", f"/api/manage/{ref}"),
                         ("GET", "/api/manage"), ("GET", f"/api/manage/{ref}/seats/move")]:
        r = api.request(method, path, json={} if method == "POST" else None)
        assert r.status_code == 404 and r.json() == NOT_FOUND, (method, path, r.text)


# ------------------------------------------------------------------ the read (CAP-6, CAP-8)


def test_the_read_returns_the_booking_and_writes_nothing(before_cutoff, api, pg):
    ref, token, paid = book(api)
    assert open_link(api, token).status_code == 200
    before = stored(pg)
    count = counts(pg)
    for _ in range(2):
        r = api.get(f"/api/manage/{ref}")
        assert r.status_code == 200, r.text
        assert r.json() == {
            "reference": ref, "kind": "seats", "seats": 2, "sauna": None,
            "window": {"id": 2, "date": "2026-12-01", "start": "2026-12-01T11:30:00+01:00",
                       "end": "2026-12-01T13:00:00+01:00"},
            "total_ore": 50000, "status": "active", "version": 0, "change_allowed": True,
            "cutoff_at": "2026-11-30T23:30:00+01:00", "cancelled_at": None, "history": [],
            "voucher_last_valid_date": "2027-11-30",  # one year ahead: no Voucher paid it
        }
        assert "set-cookie" not in r.headers
    assert stored(pg) == before and counts(pg) == count
    # nothing beyond the Booking: no name, email, Outbox body, token, link or Sauna
    forbidden = [token, "@", "manage#t=", paid["emails"][0]["body"], paid["booking"]["name"], *SAUNA_NAMES]

    def walk(value):
        if isinstance(value, dict):
            for k, v in value.items():
                yield k
                yield from walk(v)
        elif isinstance(value, list):
            for v in value:
                yield from walk(v)
        elif isinstance(value, str):
            yield value

    for text in walk(r.json()):
        for bad in forbidden:
            assert bad not in text, (bad, text)
    assert not {"name", "email", "emails", "token", "link", "code"} & set(r.json())
    assert all(bad not in r.text for bad in forbidden)


def test_change_allowed_turns_false_at_the_cutoff(before_cutoff, api, pg):
    ref, token, _ = book(api)
    cutoff = win_start(1) - dt.timedelta(hours=12)
    set_clock(pg, cutoff - dt.timedelta(seconds=30))
    assert open_link(api, token).status_code == 200
    assert api.get(f"/api/manage/{ref}").json()["change_allowed"] is True
    set_clock(pg, cutoff)
    after = api.get(f"/api/manage/{ref}").json()
    assert after["change_allowed"] is False and after["cutoff_at"] == "2026-11-30T23:30:00+01:00"
    assert rows(pg, "SELECT change_allowed(id) FROM bookings") == [(False,)]


def test_a_changed_setting_applies_only_to_new_bookings(before_cutoff, api, pg):
    first, _, _ = book(api, 2, 1)
    pg.execute("UPDATE settings SET cutoff_seats = interval '2 hours'")
    pg.commit()
    try:
        second, _, _ = book(api, 3, 1)
        got = dict(rows(pg, "SELECT reference, cutoff FROM bookings"))
        assert got == {first: dt.timedelta(hours=12), second: dt.timedelta(hours=2)}
    finally:
        pg.execute("UPDATE settings SET cutoff_seats = interval '12 hours'")
        pg.commit()


def test_a_foreign_or_unknown_reference_is_the_same_404_and_writes_nothing(before_cutoff, api, pg):
    ref_a, token_a, _ = book(api, 2, 1)
    ref_b, _token_b, _ = book(api, 3, 1)
    other = "Z" * 8 if "Z" * 8 not in (ref_a, ref_b) else "Y" * 8
    with api_client(before_cutoff, session=False) as holder:
        assert open_link(holder, token_a).status_code == 200
        before, grant = stored(pg), rows(pg, "SELECT last_used_at FROM manage_grants")
        answers = [holder.get(f"/api/manage/{p}") for p in (ref_b, other, ref_a.lower(), ref_a[:7], "IIIIIIII")]
        with api_client(before_cutoff, session=False) as anon, api_client(before_cutoff) as stranger:
            answers += [anon.get(f"/api/manage/{ref_a}"), stranger.get(f"/api/manage/{ref_a}")]
        answers.append(api.get(f"/api/manage/{ref_a}"))  # the paying session has no grant: paying is not opening
        for r in answers:
            assert r.status_code == 404 and r.json() == NOT_FOUND, (r.request.url, r.text)
        assert len({r.content for r in answers}) == 1
        assert stored(pg) == before
        assert rows(pg, "SELECT last_used_at FROM manage_grants") == grant  # a refused read touches no grant
        assert holder.get(f"/api/manage/{ref_a}").status_code == 200


# ------------------------------------------------------------------ the grant's life (CAP-7)


def test_an_idle_grant_ends_after_30_minutes_and_the_link_restores_it(before_cutoff, api, pg):
    ref, token, _ = book(api)
    assert open_link(api, token).status_code == 200
    opened = rows(pg, "SELECT last_used_at FROM manage_grants")[0][0]
    for minutes in (29, 58):  # each read slides the 30 minutes
        set_clock(pg, opened + dt.timedelta(minutes=minutes))
        assert api.get(f"/api/manage/{ref}").status_code == 200, minutes
    set_clock(pg, opened + dt.timedelta(minutes=58 + 31))
    assert api.get(f"/api/manage/{ref}").json() == NOT_FOUND
    assert open_link(api, token).status_code == 200  # opening the email link again restores it
    assert api.get(f"/api/manage/{ref}").status_code == 200
    assert rows(pg, "SELECT count(*) FROM manage_grants") == [(1,)]


def test_sign_out_deletes_the_grants_of_the_browser(before_cutoff, admin, api, pg):
    ref, token, _ = book(api)
    assert open_link(admin, token).status_code == 200  # an Administrator's browser may hold a grant too
    assert admin.get(f"/api/manage/{ref}").status_code == 200
    assert rows(pg, "SELECT session_id FROM manage_grants") == [(admin.session_id,)]
    assert admin.post("/api/admin/sign-out").status_code == 200
    assert rows(pg, "SELECT count(*) FROM manage_grants") == [(0,)]
    assert admin.get(f"/api/manage/{ref}").json() == NOT_FOUND


def test_the_purge_deletes_grants_of_expired_sessions_and_ended_windows(before_cutoff, pg, pool):
    with api_client(before_cutoff) as payer:
        ref2, token2, _ = book(payer, 2, 1)
        ref3, token3, _ = book(payer, 3, 1)
    with api_client(before_cutoff, session=False) as a, api_client(before_cutoff, session=False) as b:
        assert open_link(a, token2).status_code == 200  # Window 2 will have ended
        assert open_link(a, token3).status_code == 200  # Window 3 will not
        assert open_link(b, token3).status_code == 200  # b's session will have expired
        sid_a, sid_b = a.session_id, b.session_id
    pg.execute("UPDATE sessions SET expires_at = app_now() - interval '1 second' WHERE id = %s", (sid_b,))
    pg.commit()
    set_clock(pg, win_start(2) + dt.timedelta(minutes=1))
    assert manage.purge() == 2
    left = rows(pg, "SELECT g.session_id, b.reference FROM manage_grants g JOIN access_tokens t ON t.id = g.token_id "
                    "JOIN bookings b ON b.id = t.booking_id")
    assert left == [(sid_a, ref3)]
    assert manage.purge() == 0


# ------------------------------------------------------------------ the seed (CAP-3)

SEED_DB = "booking_test_seed_manage"


@pytest.fixture
def fresh_db():
    with psycopg.connect(ADMIN_URL, autocommit=True) as c:
        c.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(SEED_DB)))
        c.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(SEED_DB)))
    yield make_conninfo(TEST_URL, dbname=SEED_DB)
    with psycopg.connect(ADMIN_URL, autocommit=True) as c:
        c.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(SEED_DB)))


def seed_state(url: str) -> dict:
    with psycopg.connect(url) as c:
        return {
            "tokens": c.execute("SELECT id, booking_id, token_hash, revoked_at FROM access_tokens ORDER BY id").fetchall(),
            "emails": c.execute("SELECT id, booking_id, subject, body FROM outbox_emails ORDER BY id").fetchall(),
        }


def test_the_seed_gives_every_sample_a_link_once(fresh_db, tmp_path):
    entries = json.loads((config.paths.SEEDS / "bookings.json").read_text(encoding="utf-8"))["bookings"]
    first = start_backend(fresh_db, tmp_path, name="manage-seed-1")
    first.stop()
    assert "purged 0 stale manage grants" in first.output()
    state = seed_state(fresh_db)
    with psycopg.connect(fresh_db) as c:
        samples = c.execute("SELECT id, reference FROM bookings ORDER BY id").fetchall()
    assert len(samples) == len(entries) == 12
    # every sample was created with its link, in its confirmation email; no second email
    assert sorted(t[1] for t in state["tokens"]) == [s[0] for s in samples]
    assert all(t[3] is None for t in state["tokens"])
    assert [e[2] for e in state["emails"]] == [f"Booking confirmed: {ref}" for _id, ref in samples]
    for (_eid, bid, _subject, body), token in zip(state["emails"], state["tokens"], strict=True):
        assert bid == token[1]
        m = TOKEN.search(body)
        assert m and hashlib.sha256(m.group(1).encode()).digest() == bytes(token[2])

    # two samples lose their token (as if made before migration 0010); one of them has ended by the next start
    tomorrow, later = samples[0], samples[-1]  # +1 day 14:30 and +5 days 10:00
    with psycopg.connect(fresh_db) as c:
        c.execute("DELETE FROM access_tokens WHERE booking_id = ANY(%s)", ([tomorrow[0], later[0]],))
        c.execute("UPDATE clock SET off = off + interval '2 days'")
    second = start_backend(fresh_db, tmp_path, name="manage-seed-2")
    second.stop()
    after = seed_state(fresh_db)
    new_tokens = [t for t in after["tokens"] if t not in state["tokens"]]
    new_emails = after["emails"][len(state["emails"]):]
    assert [t[1] for t in new_tokens] == [later[0]] and new_tokens[0][3] is None
    assert len(new_emails) == 1
    _eid, bid, subject, body = new_emails[0]
    assert bid == later[0] and subject == f"Manage your booking: {later[1]}"
    m = TOKEN.search(body)
    assert m and hashlib.sha256(m.group(1).encode()).digest() == bytes(new_tokens[0][2])
    assert f"Booking reference: {later[1]}" in body and re.search(r"(?m)^Session: 10:00–11:30$", body), body
    assert re.search(r"(?m)^Date: \w+day \d{1,2} \w+ \d{4}$", body), body
    with psycopg.connect(fresh_db) as c:
        seats = c.execute("SELECT seats FROM bookings WHERE id = %s", (later[0],)).fetchone()[0]
        total = c.execute("SELECT total_ore FROM bookings WHERE id = %s", (later[0],)).fetchone()[0]
    # a sample is paid by card alone: no voucher line
    assert re.search(rf"(?m)^Session: 10:00–11:30\nSeats: {seats}\nPaid by card: {re.escape(nok(total))}$", body), body
    assert "Paid with voucher" not in body
    assert CHANGE_STATEMENT in body
    assert f"/manage#t={m.group(1)}" in body and body.count("http") == 1
    assert not any(name in body for name in SAUNA_NAMES) and "@" not in body
    assert "1 manage links issued" in second.output()
    with psycopg.connect(fresh_db) as c:
        assert c.execute("SELECT recipient FROM outbox_emails WHERE id = %s", (_eid,)).fetchone()[0] == entries[-1][
            "email"]

    # a third start issues nothing
    third = start_backend(fresh_db, tmp_path, name="manage-seed-3")
    third.stop()
    assert seed_state(fresh_db) == after
    assert "manage links issued" not in third.output()
    for b in (first, second, third):  # no token in the backend's log (AD-19)
        log = b.output()
        assert not TOKEN.search(log) and "#t=" not in log


@pytest.mark.parametrize(("paid", "until", "expected"), [
    ((0, 50000), None, ["Paid by card: NOK 500"]),
    ((50000, 0), dt.date(2027, 3, 1), ["Paid with voucher: NOK 500, valid until Monday 1 March 2027"]),
    ((20000, 30000), dt.date(2027, 3, 1),
     ["Paid with voucher: NOK 200, valid until Monday 1 March 2027", "Paid by card: NOK 300"]),
])
def test_the_sample_email_says_how_the_booking_was_paid(paid, until, expected):
    tz = dt.timezone.utc
    facts = ("ABC123", 2, 1, dt.date(2026, 12, 5), dt.datetime(2026, 12, 5, 14, 30, tzinfo=tz),
             dt.datetime(2026, 12, 5, 16, 0, tzinfo=tz), sum(paid), "confirmed", 0, True, None, None, "UTC")
    _subject, body = manage_email(facts, "https://example.test/manage#t=x", paid, until)
    lines = body.split("\n")
    i = lines.index("Seats: 2")
    assert lines[i + 1:i + 1 + len(expected)] == expected and lines[i + 1 + len(expected)] == ""
