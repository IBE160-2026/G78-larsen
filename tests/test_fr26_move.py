"""FR-26 / AD-29 / AD-9 / AD-2 (Story 4.2): move all or some Seats to another session through the Manage link.

`POST /api/manage/{reference}/seats/move {window_id, seats, version}` with an `Idempotency-Key`. A full move changes the
Booking's Window in one UPDATE (`entry_time = app_now()`, `version + 1`); a partial move splits it: the original keeps
its reference, link, price per Seat and Cutoff with fewer Seats, and the moved Seats become a new Booking with its own
reference, Manage token and a grant for the acting session, and no `payments` row. Every Change writes one history row
(`booking_changes`) and sends its emails with its `change_id`. Refusals come in the AD-29 order; the store's
`booked_within_capacity` is the backstop (the bypass test fails under `BP_TEST_MUTATE=nocheck`). A repeat of the key
returns the first outcome; any other use of it is `409 invalid_key`. The two races run 100 times each.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import uuid

import psycopg
import pytest

from client import api_client
from conftest import clear, raw_booking, set_clock, state, win_start
from test_fr10_through_the_api import guests, parallel
from test_fr25_manage_link import BEFORE, NOT_FOUND, SAUNA_NAMES, TOKEN, book, open_link, rows

ROUNDS = 100  # FR-11 repetitions
DAY = "2026-12-01"
MANAGE_LINK_STILL_WORKS = "The Manage link in your booking confirmation email still works."


def move(client, ref: str, window_id: int, seats: int, version: int = 0, key: str | None = None):
    return client.post(f"/api/manage/{ref}/seats/move", json={"window_id": window_id, "seats": seats,
                                                              "version": version},
                       headers={"Idempotency-Key": key or str(uuid.uuid4())})


def opened(api, window_id: int = 1, seats: int = 2) -> tuple[str, str]:
    """A Booking paid by `api` whose Manage link `api` has opened; returns (reference, token)."""
    ref, token, _ = book(api, window_id, seats)
    assert open_link(api, token).status_code == 200
    return ref, token


def everything(pg) -> tuple:
    """Every row a refused or repeated Change must leave alone."""
    return rows(pg, "SELECT (SELECT array_agg(b::text ORDER BY b.id) FROM bookings b), "
                    "(SELECT array_agg(t::text ORDER BY t.id) FROM access_tokens t), "
                    "(SELECT array_agg(o::text ORDER BY o.id) FROM outbox_emails o), "
                    "(SELECT array_agg(p::text ORDER BY p.id) FROM payments p), "
                    "(SELECT array_agg(k::text ORDER BY k.id) FROM idempotency_keys k), "
                    "(SELECT array_agg(h::text ORDER BY h.id) FROM booking_changes h), "
                    "(SELECT array_agg((w.id, w.booked)::text ORDER BY w.id) FROM windows w), "
                    "(SELECT array_agg((g.id, g.session_id, g.token_id)::text ORDER BY g.id) FROM manage_grants g)")[0]


def left_in(api, window_id: int) -> int:
    return api.get(f"/api/windows/{window_id}").json()["seats_left"]


def listing_left(api) -> dict[int, int]:
    """Seats left in `world`'s three Windows as a Guest lists the date (FR-3)."""
    r = api.get("/api/windows", params={"date": DAY})
    assert r.status_code == 200, r.text
    return {w["id"]: w["seats_left"] for w in r.json()["windows"] if w["id"] in (1, 2, 3)}


def fill(pg, window_id: int, seats: int) -> None:
    """Seats booked straight in the store (AD-21), at most 44 per row."""
    pg.execute(raw_booking(window_id, seats))
    pg.commit()


def refused(r, code: str, **facts) -> None:
    assert r.status_code == 409, r.text
    assert r.json() == {"detail": {"error": code, **facts}}, r.text


@pytest.fixture
def before_cutoff(world, pg):
    set_clock(pg, BEFORE)
    return world


@pytest.fixture
def guest(before_cutoff):
    with api_client(before_cutoff) as c:
        yield c


# ------------------------------------------------------------------ the store (migration 0011)


def test_the_history_shape_and_the_key_check_are_in_the_store(before_cutoff, pg):
    fill(pg, 1, 1)
    bid = rows(pg, "SELECT id FROM bookings")[0][0]
    bad = [
        "INSERT INTO booking_changes (booking_id, action, seats, from_window_id, to_window_id) VALUES (%s, 'move', 1, 1, NULL)",
        "INSERT INTO booking_changes (booking_id, action, seats, from_window_id, to_window_id) VALUES (%s, 'move', NULL, 1, 2)",
        "INSERT INTO booking_changes (booking_id, action, seats, from_window_id, to_window_id) VALUES (%s, 'move', 1, 1, 1)",
        "INSERT INTO booking_changes (booking_id, action, seats, from_window_id, to_window_id, from_sauna_id) "
        "VALUES (%s, 'move', 1, 1, 2, 1)",
        "INSERT INTO booking_changes (booking_id, action, seats, from_window_id, to_window_id) VALUES (%s, 'cancel', 1, 1, 2)",
    ]
    for sql in bad:
        with pytest.raises(psycopg.errors.CheckViolation):
            pg.execute(sql, (bid,))
        pg.rollback()
    cid = pg.execute("INSERT INTO booking_changes (booking_id, action, seats, from_window_id, to_window_id) "
                     "VALUES (%s, 'move', 1, 1, 2) RETURNING id", (bid,)).fetchone()[0]
    pg.commit()
    for booking_id, change_id in ((None, None), (bid, cid)):
        with pytest.raises(psycopg.errors.CheckViolation) as e:
            pg.execute("INSERT INTO idempotency_keys (key, endpoint, request_hash, booking_id, change_id) "
                       "VALUES (gen_random_uuid(), 'x', %s, %s, %s)", (b"x" * 32, booking_id, change_id))
        assert e.value.diag.constraint_name == "idempotency_keys_one_target"
        pg.rollback()
    # no trigger writes the history: a raw move leaves none
    pg.execute("UPDATE bookings SET window_id = 2 WHERE id = %s", (bid,))
    pg.commit()
    assert rows(pg, "SELECT count(*) FROM booking_changes") == [(1,)]
    triggers = rows(pg, "SELECT count(*) FROM pg_trigger WHERE tgrelid = 'booking_changes'::regclass "
                        "AND NOT tgisinternal")
    assert triggers == [(0,)]


def test_the_store_refuses_a_move_into_a_full_window_written_around_the_api_bypass(before_cutoff, pg):
    """AD-2: an UPDATE of `bookings.window_id` into a full Window, around the API, is refused by
    `booked_within_capacity`. Fails under `BP_TEST_MUTATE=nocheck`."""
    fill(pg, 2, 42)
    fill(pg, 1, 3)
    with pytest.raises(psycopg.errors.CheckViolation) as e:
        pg.execute("UPDATE bookings SET window_id = 2 WHERE window_id = 1")
        pg.commit()
    assert e.value.diag.constraint_name == "booked_within_capacity"
    pg.rollback()
    assert state(pg, 1)["real_booked"] == 3 and state(pg, 2)["real_booked"] == 42


# ------------------------------------------------------------------ a full move


def test_a_full_move_changes_the_window_of_the_same_booking(guest, admin, pg):
    ref, token = opened(guest, 1, 2)
    before = rows(pg, "SELECT id, reference, total_ore, price_per_seat_ore, cutoff, created_at, entry_time "
                      "FROM bookings")[0]
    assert listing_left(guest)[1] == 42
    r = move(guest, ref, 2, 2)
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"booking", "emails"}
    b = body["booking"]
    assert (b["reference"], b["seats"], b["total_ore"], b["version"], b["status"]) == (ref, 2, 50000, 1, "active")
    assert b["window"] == {"id": 2, "date": DAY, "start": "2026-12-01T11:30:00+01:00",
                           "end": "2026-12-01T13:00:00+01:00"}
    assert b == guest.get(f"/api/manage/{ref}").json()  # the Manage read's shape
    # the same row: window, entry time and version change; reference, value, Cutoff and time of booking stay
    after = rows(pg, "SELECT id, reference, total_ore, price_per_seat_ore, cutoff, created_at, entry_time, window_id, "
                     "version FROM bookings")
    assert len(after) == 1
    assert after[0][:6] == before[:6] and after[0][6] > before[6] and after[0][7:] == (2, 1)
    # one history row, one email with the Change's id, one key that points at the Change
    [(cid, bid, action, seats, fw, tw, fs, ts, nb)] = rows(
        pg, "SELECT id, booking_id, action, seats, from_window_id, to_window_id, from_sauna_id, to_sauna_id, "
            "new_booking_id FROM booking_changes")
    assert (bid, action, seats, fw, tw, fs, ts, nb) == (before[0], "move", 2, 1, 2, None, None, None)
    assert rows(pg, "SELECT booking_id, change_id FROM outbox_emails ORDER BY id") == [(before[0], None),
                                                                                       (before[0], cid)]
    assert rows(pg, "SELECT booking_id, change_id, endpoint FROM idempotency_keys ORDER BY id") == [
        (before[0], None, "POST /api/bookings"), (None, cid, "POST /api/manage/seats/move")]
    # the Manage link stays: one token, unrevoked, and it still opens the Booking
    assert rows(pg, "SELECT count(*), bool_and(revoked_at IS NULL) FROM access_tokens") == [(1, True)]
    assert open_link(guest, token).json() == {"reference": ref}
    # the freed Seats count at once in Window 1, the moved ones in Window 2
    assert listing_left(guest)[1] == 44 and listing_left(guest)[2] == 42
    # the email
    [email] = body["emails"]
    stored_id, subject, text = rows(pg, "SELECT id, subject, body FROM outbox_emails WHERE change_id = %s", (cid,))[0]
    assert email == {"id": stored_id, "subject": subject, "body": text}
    assert subject == f"Booking changed: {ref}"
    lines = text.split("\n")
    assert lines[0] == "Booking changed" and lines[2] == "Saunalöyly"
    assert f"Booking reference: {ref}" in lines and "Date: Tuesday 1 December 2026" in lines
    assert "Session: 11:30–13:00" in lines and "Seats: 2" in lines and "Total: NOK 500 incl. VAT" in lines
    assert lines[-1] == MANAGE_LINK_STILL_WORKS
    assert "http" not in text and "#t=" not in text and token not in text and "Seats moved" not in text
    assert not any(name in text for name in SAUNA_NAMES)
    # the history in the Manage read and in the Booking list
    entry = {"action": "move", "at": guest.get(f"/api/manage/{ref}").json()["history"][0]["at"], "seats": 2,
             "from_window": {"id": 1, "start": "2026-12-01T10:00:00+01:00", "end": "2026-12-01T11:30:00+01:00"},
             "to_window": {"id": 2, "start": "2026-12-01T11:30:00+01:00", "end": "2026-12-01T13:00:00+01:00"},
             "new_reference": None}
    assert guest.get(f"/api/manage/{ref}").json()["history"] == [entry]
    assert entry["at"].startswith("2026-11-30T21:0") and entry["at"].endswith("+01:00")
    ws = {w["id"]: w for w in admin.get("/api/admin/bookings", params={"date": DAY}).json()["windows"]}
    assert ws[1]["bookings"] == [] and ws[1]["seats_left"] == 44
    [listed] = ws[2]["bookings"]
    assert (listed["reference"], listed["status"], listed["history"]) == (ref, "active", [entry])
    assert (ws[2]["seats_booked"], ws[2]["seats_left"]) == (2, 42)


# ------------------------------------------------------------------ a partial move (a split)


def test_a_partial_move_splits_the_booking(before_cutoff, guest, admin, pg):
    ref, token = opened(guest, 1, 3)
    pg.execute("UPDATE bookings SET cutoff = interval '3 hours'")  # the split keeps the original's own Cutoff
    pg.commit()
    original = rows(pg, "SELECT id, name, email, price_per_seat_ore FROM bookings")[0]
    r = move(guest, ref, 2, 1)
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"booking", "new_booking", "emails"}
    b, n = body["booking"], body["new_booking"]
    new_ref = n["reference"]
    assert new_ref != ref
    assert (b["reference"], b["seats"], b["total_ore"], b["version"], b["window"]["id"]) == (ref, 2, 50000, 1, 1)
    assert (n["seats"], n["total_ore"], n["version"], n["window"]["id"], n["status"]) == (1, 25000, 0, 2, "active")
    assert n["history"] == [] and len(b["history"]) == 1 and b["history"][0]["new_reference"] == new_ref
    got = rows(pg, "SELECT reference, seats, total_ore, price_per_seat_ore, cutoff, version, window_id, name, email, "
                   "session_id, status, created_at = entry_time FROM bookings ORDER BY id")
    assert got == [
        (ref, 2, 50000, 25000, dt.timedelta(hours=3), 1, 1, original[1], original[2], guest.session_id, "active",
         True),
        (new_ref, 1, 25000, 25000, dt.timedelta(hours=3), 0, 2, original[1], original[2], guest.session_id,
         "active", True)]
    new_id = rows(pg, "SELECT id FROM bookings WHERE reference = %s", (new_ref,))[0][0]
    # no payments row for the split; the original's charge stays
    assert rows(pg, "SELECT booking_id, direction, method, amount_ore FROM payments") == [
        (original[0], "charge", "card", 75000)]
    # history
    [(cid, bid, seats, fw, tw, nb)] = rows(pg, "SELECT id, booking_id, seats, from_window_id, to_window_id, "
                                               "new_booking_id FROM booking_changes")
    assert (bid, seats, fw, tw, nb) == (original[0], 1, 1, 2, new_id)
    # two tokens, both unrevoked: the original's is the same, the new one is its own; the acting session has a grant
    tokens = rows(pg, "SELECT booking_id, token_hash, revoked_at FROM access_tokens ORDER BY id")
    assert [(t[0], t[2]) for t in tokens] == [(original[0], None), (new_id, None)]
    assert bytes(tokens[0][1]) == hashlib.sha256(token.encode()).digest()
    assert guest.get(f"/api/manage/{new_ref}").json() == n
    # the emails: the Change confirmation on the original, then the new Booking's own confirmation
    e1, e2 = body["emails"]
    assert rows(pg, "SELECT id, booking_id, change_id, subject FROM outbox_emails WHERE change_id IS NOT NULL "
                    "ORDER BY id") == [(e1["id"], original[0], cid, f"Booking changed: {ref}"),
                                       (e2["id"], new_id, cid, f"Booking confirmed: {new_ref}")]
    lines = e1["body"].split("\n")
    assert "Seats: 2" in lines and "Total: NOK 500 incl. VAT" in lines and "Session: 10:00–11:30" in lines
    assert lines[-5:] == ["Seats moved: 1", f"New booking reference: {new_ref}",
                          "The moved seats have their own confirmation email.", "", MANAGE_LINK_STILL_WORKS]
    assert "http" not in e1["body"]
    m = TOKEN.search(e2["body"])
    assert m and hashlib.sha256(m.group(1).encode()).digest() == bytes(tokens[1][1])
    assert "Seats: 1" in e2["body"] and "Session: 11:30–13:00" in e2["body"]
    for e in (e1, e2):
        assert token not in e["body"] and not any(name in e["body"] for name in SAUNA_NAMES)
    # the new link opens the new Booking in another browser
    with api_client(before_cutoff, session=False) as other:
        assert open_link(other, m.group(1)).json() == {"reference": new_ref}
    # Seats left in both Windows, and the Booking list
    assert listing_left(guest)[1] == 42 and listing_left(guest)[2] == 43
    ws = {w["id"]: w for w in admin.get("/api/admin/bookings", params={"date": DAY}).json()["windows"]}
    assert [(x["reference"], x["seats"], x["status"]) for x in ws[1]["bookings"]] == [(ref, 2, "active")]
    assert ws[1]["bookings"][0]["history"][0]["new_reference"] == new_ref
    assert [(x["reference"], x["seats"], x["history"]) for x in ws[2]["bookings"]] == [(new_ref, 1, [])]
    # the confirmation read of the original shows only its payment's email
    conf = guest.get(f"/api/bookings/{ref}/confirmation").json()
    assert [e["subject"] for e in conf["emails"]] == [f"Booking confirmed: {ref}"]
    assert [e["subject"] for e in guest.get(f"/api/bookings/{new_ref}/confirmation").json()["emails"]] == [
        f"Booking confirmed: {new_ref}"]


def test_moved_seats_can_move_on_and_both_bookings_change_separately(guest, pg):
    ref, _ = opened(guest, 1, 3)
    split = move(guest, ref, 2, 1).json()
    new_ref = split["new_booking"]["reference"]
    r = move(guest, new_ref, 3, 1)  # the split-off Booking, through the grant the split gave
    assert r.status_code == 200 and r.json()["booking"]["window"]["id"] == 3
    r = move(guest, ref, 3, 2, version=1)
    assert r.status_code == 200 and r.json()["booking"]["version"] == 2
    assert listing_left(guest) == {1: 44, 2: 44, 3: 41}
    assert rows(pg, "SELECT count(*) FROM booking_changes") == [(3,)]


# ------------------------------------------------------------------ refusals, in the AD-29 order


def test_e5_three_seats_to_a_window_with_two_left_change_nothing(guest, pg):
    ref, _ = opened(guest, 1, 3)
    fill(pg, 2, 42)
    lefts = listing_left(guest)  # generates the rest of the horizon first
    before = everything(pg)
    refused(move(guest, ref, 2, 3), "no_seat_free", seats_left=2)
    refused(move(guest, ref, 2, 3, key=str(uuid.uuid4())), "no_seat_free", seats_left=2)
    assert everything(pg) == before and listing_left(guest) == lefts == {1: 41, 2: 2, 3: 44}
    assert rows(pg, "SELECT seats FROM bookings WHERE reference = %s", (ref,)) == [(3,)]
    assert move(guest, ref, 2, 2).status_code == 200  # two of them fit


def test_a_stale_version_is_booking_changed_with_the_booking_now(guest, pg):
    ref, _ = opened(guest, 1, 2)
    assert move(guest, ref, 2, 1).status_code == 200  # version 0 -> 1
    before = everything(pg)
    r = move(guest, ref, 3, 1, version=0)
    refused(r, "booking_changed", booking=guest.get(f"/api/manage/{ref}").json())
    assert r.json()["detail"]["booking"]["version"] == 1
    assert everything(pg) == before


@pytest.mark.parametrize("seats", [0, -1, 3, 2_147_483_647])
def test_seats_outside_one_to_the_bookings_seats_are_change_invalid(guest, pg, seats):
    ref, _ = opened(guest, 1, 2)
    before = everything(pg)
    refused(move(guest, ref, 2, seats), "change_invalid", reason="seats_exceed")
    assert everything(pg) == before


def test_the_current_window_is_change_invalid_same_target(guest, pg):
    ref, _ = opened(guest, 1, 2)
    before = everything(pg)
    refused(move(guest, ref, 1, 2), "change_invalid", reason="same_target")
    refused(move(guest, ref, 1, 1), "change_invalid", reason="same_target")
    assert everything(pg) == before


def test_targets_outside_the_horizon_or_past_their_deadline_are_refused(guest, pg):
    ref, _ = opened(guest, 1, 2)
    late = pg.execute("INSERT INTO windows (during) VALUES (tstzrange('2027-03-01 09:00Z', '2027-03-01 10:30Z')) "
                      "RETURNING id").fetchone()[0]
    started = pg.execute("INSERT INTO windows (during) VALUES (tstzrange(%s, %s)) RETURNING id",
                         (BEFORE - dt.timedelta(minutes=30), BEFORE + dt.timedelta(minutes=60))).fetchone()[0]
    pg.commit()
    before = everything(pg)
    refused(move(guest, ref, late, 1), "outside_horizon", message="the Window starts after the end of the Booking horizon")
    refused(move(guest, ref, started, 1), "deadline_passed", message="the Booking deadline has passed")
    assert move(guest, ref, 999999, 1).json() == NOT_FOUND  # an unknown Window
    assert everything(pg) == before


def test_after_the_cutoff_a_move_is_cutoff_passed(guest, pg):
    ref, token = opened(guest, 1, 2)
    fill(pg, 2, 44)  # a full target: the Cutoff comes before capacity
    set_clock(pg, win_start(0) - dt.timedelta(hours=12))  # Window 1's Cutoff, 2026-11-30 21:00Z
    assert open_link(guest, token).status_code == 200  # the grant was idle for an hour
    before = everything(pg)
    refused(move(guest, ref, 2, 1), "cutoff_passed", cutoff_at="2026-11-30T22:00:00+01:00")
    refused(move(guest, ref, 3, 2), "cutoff_passed", cutoff_at="2026-11-30T22:00:00+01:00")
    assert everything(pg) == before
    assert guest.get(f"/api/manage/{ref}").json()["change_allowed"] is False


def test_the_refusal_order(guest, pg):
    ref, token = opened(guest, 1, 2)
    late = pg.execute("INSERT INTO windows (during) VALUES (tstzrange('2027-03-01 09:00Z', '2027-03-01 10:30Z')) "
                      "RETURNING id").fetchone()[0]
    pg.commit()
    fill(pg, 2, 44)
    set_clock(pg, win_start(0) - dt.timedelta(hours=11))  # past the Cutoff
    assert open_link(guest, token).status_code == 200
    # outside_horizon before cutoff_passed; same_target and seats_exceed before both; booking_changed before them
    assert move(guest, ref, late, 1).json()["detail"]["error"] == "outside_horizon"
    refused(move(guest, ref, 1, 1), "change_invalid", reason="same_target")
    refused(move(guest, ref, late, 5), "change_invalid", reason="seats_exceed")
    assert move(guest, ref, late, 5, version=7).json()["detail"]["error"] == "booking_changed"
    assert move(guest, ref, 2, 2).json()["detail"]["error"] == "cutoff_passed"
    # a cancelled Booking comes first of all
    pg.execute("UPDATE bookings SET status = 'cancelled' WHERE reference = %s", (ref,))
    pg.commit()
    before = everything(pg)
    refused(move(guest, ref, late, 5, version=7), "booking_cancelled")
    assert everything(pg) == before


# ------------------------------------------------------------------ repeats and keys (AD-9)


def test_a_repeat_returns_the_first_outcome_and_writes_nothing(guest, pg):
    ref, _ = opened(guest, 1, 3)
    key = str(uuid.uuid4())
    first = move(guest, ref, 2, 1, key=key)
    assert first.status_code == 200, first.text
    before = everything(pg)
    again = move(guest, ref, 2, 1, key=key)
    assert again.status_code == 200 and again.json() == first.json()
    assert everything(pg) == before
    # the Booking as it is now: after a later Change the repeat shows it, with the same emails
    assert move(guest, ref, 3, 1, version=1).status_code == 200
    later = move(guest, ref, 2, 1, key=key).json()
    assert later["emails"] == first.json()["emails"]
    assert later["booking"]["version"] == 2 and later["booking"]["seats"] == 1
    assert later["new_booking"]["reference"] == first.json()["new_booking"]["reference"]


def test_a_known_key_with_another_request_or_session_is_invalid_key(before_cutoff, guest, pg):
    ref, token = opened(guest, 1, 3)
    key = str(uuid.uuid4())
    assert move(guest, ref, 2, 1, key=key).status_code == 200
    with api_client(before_cutoff, session=False) as other:
        assert open_link(other, token).status_code == 200
        before = everything(pg)
        refused(move(other, ref, 2, 1, key=key), "invalid_key")  # another session
        refused(move(guest, ref, 2, 1, version=1, key=key), "invalid_key")  # another request
        refused(move(guest, ref, 3, 1, key=key), "invalid_key")
        assert everything(pg) == before
    # a payment's key is not a move's, nor the other way round
    paid_key = rows(pg, "SELECT key FROM idempotency_keys WHERE booking_id IS NOT NULL")[0][0]
    refused(move(guest, ref, 2, 1, version=1, key=str(paid_key)), "invalid_key")
    refused(guest.book(3, 1, key=key), "invalid_key")


def test_a_refusal_stores_no_key(guest, pg):
    ref, _ = opened(guest, 1, 2)
    key = str(uuid.uuid4())
    refused(move(guest, ref, 1, 2, key=key), "change_invalid", reason="same_target")
    assert move(guest, ref, 2, 2, key=key).status_code == 200  # the same key may then succeed


# ------------------------------------------------------------------ access (AD-28)


def test_without_a_valid_grant_it_is_404_and_writes_nothing(guest, before_cutoff, pg):
    ref, token = opened(guest, 1, 2)
    other_ref, _ = opened(guest, 2, 1)
    before = everything(pg)
    with api_client(before_cutoff, session=False) as anon, api_client(before_cutoff) as stranger:
        answers = [move(anon, ref, 2, 1), move(stranger, ref, 2, 1), move(guest, "ZZZZZZZZ", 2, 1),
                   move(guest, ref.lower(), 2, 1)]
        with api_client(before_cutoff, session=False) as holder:
            assert open_link(holder, token).status_code == 200
            answers.append(move(holder, other_ref, 3, 1))  # a grant for another Booking
    for r in answers:
        assert r.status_code == 404 and r.json() == NOT_FOUND, r.text
    set_clock(pg, BEFORE + dt.timedelta(minutes=31))  # the grant has been idle too long
    assert move(guest, ref, 2, 1).json() == NOT_FOUND
    assert everything(pg)[:7] == before[:7]  # only grant touches differ


def test_a_body_or_key_of_the_wrong_shape_is_422(guest, pg):
    ref, _ = opened(guest, 1, 2)
    before = everything(pg)
    url = f"/api/manage/{ref}/seats/move"
    for kwargs in ({"json": {"window_id": 2, "seats": 1, "version": 0}},  # no key
                   {"json": {"window_id": 2, "seats": 1, "version": 0}, "headers": {"Idempotency-Key": "x"}},
                   {"json": {"window_id": 2, "seats": "one", "version": 0}, "headers": {"Idempotency-Key": str(uuid.uuid4())}},
                   {"json": {"window_id": 2, "seats": 1}, "headers": {"Idempotency-Key": str(uuid.uuid4())}},
                   {"json": {"window_id": 2, "seats": 1, "version": 0, "sauna_id": 1},
                    "headers": {"Idempotency-Key": str(uuid.uuid4())}}):
        r = guest.post(url, **kwargs)
        assert r.status_code == 422 and r.json()["detail"]["error"] == "invalid_input", r.text
    assert everything(pg)[:7] == before[:7]


def test_another_origin_is_403(guest, pg):
    ref, _ = opened(guest, 1, 2)
    r = guest.post(f"/api/manage/{ref}/seats/move", json={"window_id": 2, "seats": 1, "version": 0},
                   headers={"Idempotency-Key": str(uuid.uuid4()), "Origin": "https://evil.example"})
    assert r.status_code == 403
    assert rows(pg, "SELECT count(*) FROM booking_changes") == [(0,)]


# ------------------------------------------------------------------ races (FR-10, FR-32, AD-3), 100 times each


def _cross_window_setup(pg, world) -> tuple[list, list]:
    clear(pg)
    clients = guests(world, 2)
    refs = []
    for c, wid in zip(clients, (1, 2)):
        ref, _ = opened(c, wid, 5)
        refs.append(ref)
    fill(pg, 1, 34)  # each Window 39 of 44: room for the other's 5
    fill(pg, 2, 34)
    return clients, refs


def test_opposite_moves_in_parallel_never_deadlock_or_oversell(before_cutoff, pg):
    for r in range(ROUNDS):
        (ca, cb), (ra, rb) = _cross_window_setup(pg, before_cutoff)
        a, b = parallel([lambda: move(ca, ra, 2, 5), lambda: move(cb, rb, 1, 5)])
        ca.close(), cb.close()
        assert (a.status_code, b.status_code) == (200, 200), (r, a.text, b.text)
        s1, s2 = state(pg, 1), state(pg, 2)
        assert s1["booked"] == s1["real_booked"] == 39 and s2["booked"] == s2["real_booked"] == 39, (r, s1, s2)
        assert rows(pg, "SELECT window_id FROM bookings WHERE reference IN (%s, %s) ORDER BY reference = %s",
                    (ra, rb, rb)) == [(2,), (1,)]


def test_opposite_moves_where_one_fits_only_after_the_other(before_cutoff, pg):
    for r in range(ROUNDS):
        (ca, cb), (ra, rb) = _cross_window_setup(pg, before_cutoff)
        fill(pg, 1, 2)  # Window 1: 41 of 44 (3 left); Window 2: 39 (5 left)
        # A moves 5 into Window 2 (always fits); B moves 5 into Window 1 (fits only once A has left it)
        a, b = parallel([lambda: move(ca, ra, 2, 5), lambda: move(cb, rb, 1, 5)])
        ca.close(), cb.close()
        assert a.status_code == 200, (r, a.text)
        assert b.status_code == 200 or (b.status_code == 409 and b.json() == {
            "detail": {"error": "no_seat_free", "seats_left": 3}}), (r, b.text)
        s1, s2 = state(pg, 1), state(pg, 2)
        assert s1["real_booked"] + s2["real_booked"] == 80, (r, s1, s2)  # the total is kept
        assert s1["booked"] == s1["real_booked"] <= 44 and s2["booked"] == s2["real_booked"] <= 44, (r, s1, s2)
        assert s1["real_booked"] == (41 if b.status_code == 200 else 36), (r, s1)


def test_a_move_races_a_new_booking_for_the_last_seats(before_cutoff, pg):
    for r in range(ROUNDS):
        clear(pg)
        mover, booker = guests(before_cutoff, 2)
        ref, _ = opened(mover, 1, 2)
        fill(pg, 2, 42)  # Window 2 has room for 2: one of the two requests
        a, b = parallel([lambda: move(mover, ref, 2, 2), lambda: booker.book(2, 2)])
        mover.close(), booker.close()
        won = sorted([a.status_code == 200, b.status_code == 201])
        assert won == [False, True], (r, a.text, b.text)
        loser = b if a.status_code == 200 else a
        assert loser.status_code == 409 and loser.json()["detail"]["error"] == "no_seat_free", (r, loser.text)
        s1, s2 = state(pg, 1), state(pg, 2)
        assert s2["booked"] == s2["real_booked"] == 44 and s2["left"] == 0, (r, s2)
        assert s1["real_booked"] == (0 if a.status_code == 200 else 2), (r, s1)
        assert rows(pg, "SELECT count(*) FROM booking_changes") == [(1 if a.status_code == 200 else 0,)], r



def test_two_moves_of_one_booking_to_different_windows_retry_and_one_wins(before_cutoff, pg):
    """AD-29: the loser read `window_id` unlocked before the winner moved the Booking; its locked re-read sees another
    Window, so `db.Retry` runs it again with the new pair locked, and it is refused as `booking_changed`."""
    for r in range(ROUNDS):
        clear(pg)
        [g] = guests(before_cutoff, 1)
        ref, _ = opened(g, 1, 2)
        a, b = parallel([lambda: move(g, ref, 2, 2), lambda: move(g, ref, 3, 2)])
        g.close()
        codes = sorted([a.status_code, b.status_code])
        assert codes == [200, 409], (r, a.text, b.text)
        loser = a if a.status_code == 409 else b
        assert loser.json()["detail"]["error"] == "booking_changed", (r, loser.text)
        winner = b if loser is a else a
        assert loser.json()["detail"]["booking"]["window"]["id"] == winner.json()["booking"]["window"]["id"], r
        for wid in (1, 2, 3):
            s = state(pg, wid)
            assert s["booked"] == s["real_booked"], (r, wid, s)
        assert state(pg, 1)["real_booked"] == 0 and state(pg, 2)["real_booked"] + state(pg, 3)["real_booked"] == 2
        assert rows(pg, "SELECT count(*) FROM booking_changes") == [(1,)], r
