"""FR-27 / AD-29 / AD-30 / AD-31 / AD-9 (Story 4.3): give up some or all Seats for a Voucher through the Manage link.

`POST /api/manage/{reference}/seats/voucher {seats, version}` with an `Idempotency-Key`. Some Seats: the Booking keeps
the rest (`total_ore = seats x price_per_seat_ore`, `version + 1`). All Seats: one UPDATE cancels it (`guest`,
`voucher`, `cancelled_at = app_now()`), Seats and total kept on the row. Either way one Voucher worth the Seats given up
x the Booking's own price per Seat is issued through `services.voucher.issue` (16 Crockford characters, only the
SHA-256 stored, valid through the Venue date of app_now() plus one year), with one `voucher` history row, one
`payments` row `refund`/`voucher` and one email that is the only place the code is written. Refusals in the AD-29
order: `booking_cancelled`, `booking_changed`, `change_invalid` (`seats_exceed`), `cutoff_passed`. A repeat returns the
first outcome and issues no second Voucher. The store refuses every cancellation and history shape the rules forbid,
and `retention_due` waits for the latest Voucher expiry.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import uuid

import psycopg
import pytest

from booking_platform.services import voucher as voucher_service
from client import admin_client, api_client
from conftest import raw_booking, set_clock, win_start
from test_fr25_manage_link import BEFORE, NOT_FOUND, SAUNA_NAMES, book, open_link, rows
from test_fr26_move import DAY, MANAGE_LINK_STILL_WORKS, everything, guest, before_cutoff, left_in, move  # noqa: F401
from test_fr26_move import refused

CODE = re.compile(r"(?m)^Code: ([0-9A-HJKMNP-TV-Z]{4}(?:-[0-9A-HJKMNP-TV-Z]{4}){3})$")
CODE_FORMAT = re.compile(r"^[0-9A-HJKMNP-TV-Z]{4}(-[0-9A-HJKMNP-TV-Z]{4}){3}$")
# BEFORE is 2026-11-30 21:00 Venue time: a Voucher issued then is valid through 30 November 2027.
LAST_VALID = "2027-11-30"
NEVER_PAID_OUT = "Use the code when you pay for a new booking. A voucher is never paid out in money."


def give_up(client, ref: str, seats: int, version: int = 0, key: str | None = None):
    return client.post(f"/api/manage/{ref}/seats/voucher", json={"seats": seats, "version": version},
                       headers={"Idempotency-Key": key or str(uuid.uuid4())})


def opened(api, window_id: int = 1, seats: int = 2) -> tuple[str, str]:
    ref, token, _ = book(api, window_id, seats)
    assert open_link(api, token).status_code == 200
    return ref, token


def code_of(body: str) -> str:
    m = CODE.search(body)
    assert m, body
    return m.group(1)


def ledger(pg, ref: str) -> int:
    """Charges minus returns of a Booking (AD-31)."""
    return rows(pg, "SELECT COALESCE(SUM(CASE WHEN p.direction = 'charge' THEN p.amount_ore ELSE -p.amount_ore END), 0) "
                    "FROM payments p JOIN bookings b ON b.id = p.booking_id WHERE b.reference = %s", (ref,))[0][0]


def not_in_store(pg, *secrets: str) -> None:
    """No table but the Outbox holds any of these strings (AD-30)."""
    for table in ("bookings", "vouchers", "booking_changes", "payments", "idempotency_keys", "access_tokens",
                  "manage_grants", "sessions"):
        text = rows(pg, f"SELECT COALESCE(string_agg(t::text, ' '), '') FROM {table} t")[0][0]
        for s in secrets:
            assert s not in text, (table, s)


def walk(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from walk(v)
    elif isinstance(value, str):
        yield value


# ------------------------------------------------------------------ the store (migration 0012)


def _booking(pg, seats: int = 2) -> int:
    pg.execute(raw_booking(1, seats))
    pg.commit()
    return rows(pg, "SELECT max(id) FROM bookings")[0][0]


def _refused_by(pg, constraint: str, sql: str, params=()) -> None:
    with pytest.raises(psycopg.errors.CheckViolation) as e:
        pg.execute(sql, params)
        pg.commit()
    assert e.value.diag.constraint_name == constraint, (sql, e.value.diag.constraint_name)
    pg.rollback()


def test_the_voucher_table_keeps_value_and_balance_in_range_and_only_a_hash(before_cutoff, pg):
    bid = _booking(pg)
    insert = ("INSERT INTO vouchers (code_hash, value_ore, balance_ore, expires_at, booking_id) "
              "VALUES (%s, %s, %s, app_now() + interval '1 year', %s)")
    for value, balance in ((0, 0), (-1, -1), (100, 101), (100, -1)):
        _refused_by(pg, "vouchers_balance_within_value", insert, (b"h" * 32, value, balance, bid))
    _refused_by(pg, "vouchers_code_hash_length", insert, (b"short", 100, 100, bid))
    pg.execute(insert, (b"h" * 32, 100, 0, bid))  # a used-up Voucher is allowed
    pg.commit()
    with pytest.raises(psycopg.errors.UniqueViolation) as e:
        pg.execute(insert, (b"h" * 32, 100, 100, bid))
    assert e.value.diag.constraint_name == "vouchers_code_hash_key"
    pg.rollback()
    columns = rows(pg, "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'vouchers' "
                       "ORDER BY ordinal_position")
    assert columns == [("id", "bigint"), ("code_hash", "bytea"), ("value_ore", "integer"),
                       ("balance_ore", "integer"), ("issued_at", "timestamp with time zone"),
                       ("expires_at", "timestamp with time zone"), ("booking_id", "bigint")]


def test_the_cancellation_columns_are_checked_by_the_store(before_cutoff, pg):
    bid = _booking(pg)
    upd = "UPDATE bookings SET {} WHERE id = %s"
    _refused_by(pg, "bookings_active_not_cancelled", upd.format("cancelled_at = app_now()"), (bid,))
    _refused_by(pg, "bookings_active_not_cancelled", upd.format("cancel_cause = 'block'"), (bid,))
    _refused_by(pg, "bookings_cancelled_has_time_and_cause", upd.format("status = 'cancelled'"), (bid,))
    _refused_by(pg, "bookings_cancelled_has_time_and_cause",
                upd.format("status = 'cancelled', cancelled_at = app_now()"), (bid,))
    _refused_by(pg, "bookings_guest_cancel_has_remedy",
                upd.format("status = 'cancelled', cancelled_at = app_now(), cancel_cause = 'guest'"), (bid,))
    # a Seat booking is never refunded in money at the Guest's request
    _refused_by(pg, "seat_guest_refund_forbidden",
                upd.format("status = 'cancelled', cancelled_at = app_now(), cancel_cause = 'guest', "
                           "cancel_remedy = 'refund'"), (bid,))
    _refused_by(pg, "bookings_cancel_cause_known",
                upd.format("status = 'cancelled', cancelled_at = app_now(), cancel_cause = 'whim'"), (bid,))
    _refused_by(pg, "bookings_cancel_remedy_known",
                upd.format("status = 'cancelled', cancelled_at = app_now(), cancel_cause = 'block', "
                           "cancel_remedy = 'cash'"), (bid,))
    # a Block's cancellation without a remedy yet is allowed (FR-42)
    pg.execute(upd.format("status = 'cancelled', cancelled_at = app_now(), cancel_cause = 'block'"), (bid,))
    pg.commit()
    assert rows(pg, "SELECT status, cancel_cause, cancel_remedy FROM bookings WHERE id = %s", (bid,)) == [
        ("cancelled", "block", None)]


def test_a_cancelled_booking_is_frozen_by_the_store(before_cutoff, pg):
    bid = _booking(pg, 2)
    pg.execute("UPDATE bookings SET status = 'cancelled', cancelled_at = app_now(), cancel_cause = 'guest', "
               "cancel_remedy = 'voucher' WHERE id = %s", (bid,))
    pg.commit()
    upd = "UPDATE bookings SET {} WHERE id = %s"
    _refused_by(pg, "booking_cancelled_frozen", upd.format("status = 'active'"), (bid,))
    _refused_by(pg, "booking_cancelled_frozen",
                upd.format("status = 'active', cancelled_at = NULL, cancel_cause = NULL, cancel_remedy = NULL"), (bid,))
    _refused_by(pg, "booking_cancelled_frozen", upd.format("seats = 1, total_ore = 25000"), (bid,))
    _refused_by(pg, "booking_cancelled_frozen", upd.format("window_id = 2"), (bid,))
    # the retention catch-up still anonymises a cancelled row
    pg.execute(upd.format("name = 'Anonymised', email = 'anonymised@example.invalid'"), (bid,))
    pg.commit()
    assert rows(pg, "SELECT status, seats, window_id FROM bookings WHERE id = %s", (bid,)) == [("cancelled", 2, 1)]
    triggers = rows(pg, "SELECT tgname FROM pg_trigger WHERE tgrelid = 'bookings'::regclass AND NOT tgisinternal "
                        "ORDER BY tgname")
    assert triggers == [("a_lock_bookings",), ("b_cancelled_frozen",), ("t_bookings",)]


def test_the_history_and_payment_shapes_of_a_voucher(before_cutoff, pg):
    bid = _booking(pg)
    vid = pg.execute("INSERT INTO vouchers (code_hash, value_ore, balance_ore, expires_at, booking_id) "
                     "VALUES (%s, 100, 100, app_now() + interval '1 year', %s) RETURNING id",
                     (b"v" * 32, bid)).fetchone()[0]
    pg.commit()
    ins = "INSERT INTO booking_changes (booking_id, action, seats, from_window_id, to_window_id, voucher_id, " \
          "new_booking_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    other = _booking(pg)
    for shape in ((1, None, None, None, None), (None, None, None, vid, None), (1, 1, None, vid, None),
                  (1, None, 2, vid, None), (1, None, None, vid, other)):
        _refused_by(pg, "booking_changes_voucher_shape", ins, (bid, "voucher", *shape))
    _refused_by(pg, "booking_changes_move_shape", ins, (bid, "move", 1, 1, 2, vid, None))
    _refused_by(pg, "booking_changes_action_known", ins, (bid, "cancel", None, None, None, vid, None))
    pg.execute(ins, (bid, "voucher", 1, None, None, vid, None))
    pg.execute(ins, (bid, "move", 1, 1, 2, None, None))
    pg.commit()
    pay = "INSERT INTO payments (booking_id, direction, method, amount_ore, voucher_id) VALUES (%s, %s, %s, 100, %s)"
    _refused_by(pg, "payments_voucher_id_matches_method", pay, (bid, "refund", "voucher", None))
    _refused_by(pg, "payments_voucher_id_matches_method", pay, (bid, "charge", "card", vid))
    pg.execute(pay, (bid, "refund", "voucher", vid))
    pg.execute(pay, (bid, "charge", "card", None))
    pg.commit()


# ------------------------------------------------------------------ issue: code, hash and expiry (AD-30)


def test_a_code_is_sixteen_crockford_characters_and_only_its_hash_is_stored(before_cutoff, pg):
    codes = {voucher_service.new_code() for _ in range(200)}
    assert len(codes) == 200
    for code in codes:
        assert re.fullmatch(r"[0-9A-HJKMNP-TV-Z]{16}", code)
        assert CODE_FORMAT.match(voucher_service.display(code))
        assert voucher_service.code_hash(code) == hashlib.sha256(code.encode()).digest()
    assert set("".join(codes)) <= set(voucher_service.CROCKFORD) and len(voucher_service.CROCKFORD) == 32


@pytest.mark.parametrize(("clock", "last"), [
    (dt.datetime(2026, 11, 30, 20, 0, tzinfo=dt.timezone.utc), dt.date(2027, 11, 30)),  # 21:00 Venue time
    (dt.datetime(2026, 11, 30, 23, 30, tzinfo=dt.timezone.utc), dt.date(2027, 12, 1)),  # already 1 Dec in Oslo
    (dt.datetime(2028, 2, 29, 12, 0, tzinfo=dt.timezone.utc), dt.date(2029, 2, 28)),  # 29 February -> 28 February
    (dt.datetime(2028, 2, 28, 23, 30, tzinfo=dt.timezone.utc), dt.date(2029, 2, 28)),  # 29 Feb in Oslo
])
def test_the_expiry_is_midnight_venue_time_after_one_year(world, pg, clock, last):
    bid = _booking(pg)
    set_clock(pg, clock)
    vid, code, got = voucher_service.issue(pg, bid, 25000)
    pg.commit()
    assert got == last
    expires, issued, value, balance, stored_hash = rows(
        pg, "SELECT expires_at, issued_at, value_ore, balance_ore, code_hash FROM vouchers WHERE id = %s", (vid,))[0]
    oslo = dt.timezone(dt.timedelta(hours=1))  # no summer time in these months
    assert expires == dt.datetime.combine(last + dt.timedelta(days=1), dt.time(0, 0), oslo)
    assert abs(issued - clock) < dt.timedelta(minutes=1)
    assert (value, balance, bytes(stored_hash)) == (25000, 25000, hashlib.sha256(code.encode()).digest())
    assert voucher_service.facts(pg, vid) == {"value_ore": 25000, "last_valid_date": last.isoformat()}
    pg.rollback()


# ------------------------------------------------------------------ some Seats


def test_giving_up_one_of_four_seats_issues_a_voucher_and_keeps_three(guest, admin, pg, backend):
    ref, token = opened(guest, 1, 4)
    assert left_in(guest, 1) == 40
    bid, email = rows(pg, "SELECT id, email FROM bookings WHERE reference = %s", (ref,))[0]
    r = give_up(guest, ref, 1)
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"booking", "voucher", "emails"}
    assert body["voucher"] == {"value_ore": 25000, "last_valid_date": LAST_VALID}
    b = body["booking"]
    assert (b["reference"], b["seats"], b["total_ore"], b["version"], b["status"], b["cancelled_at"]) == (
        ref, 3, 75000, 1, "active", None)
    assert b == guest.get(f"/api/manage/{ref}").json()  # the Manage read's shape
    # the row: 3 Seats, the total follows the stored price, version + 1; the freed Seat counts at once
    assert rows(pg, "SELECT seats, total_ore, version, status, cancelled_at, cancel_cause, cancel_remedy FROM bookings "
                    "WHERE id = %s", (bid,)) == [(3, 75000, 1, "active", None, None, None)]
    assert left_in(guest, 1) == 41
    # one Voucher, one history row, one refund/voucher row, no card refund, one email, one key
    [(vid, v_value, v_balance, v_booking, v_hash)] = rows(
        pg, "SELECT id, value_ore, balance_ore, booking_id, code_hash FROM vouchers")
    assert (v_value, v_balance, v_booking) == (25000, 25000, bid)
    [(cid, action, seats, fw, tw, nb, h_voucher)] = rows(
        pg, "SELECT id, action, seats, from_window_id, to_window_id, new_booking_id, voucher_id FROM booking_changes")
    assert (action, seats, fw, tw, nb, h_voucher) == ("voucher", 1, None, None, None, vid)
    assert rows(pg, "SELECT direction, method, amount_ore, voucher_id FROM payments ORDER BY id") == [
        ("charge", "card", 100000, None), ("refund", "voucher", 25000, vid)]
    assert ledger(pg, ref) == 75000 == b["total_ore"]  # AD-31 while active
    assert rows(pg, "SELECT booking_id, change_id, endpoint FROM idempotency_keys ORDER BY id") == [
        (bid, None, "POST /api/bookings"), (None, cid, "POST /api/manage/seats/voucher")]
    # the email: the Booking now, then the Voucher block; the code only there
    [sent] = body["emails"]
    assert rows(pg, "SELECT id, recipient, subject, body, booking_id, change_id FROM outbox_emails "
                    "WHERE change_id IS NOT NULL") == [(sent["id"], email, sent["subject"], sent["body"], bid, cid)]
    assert sent["subject"] == f"Booking changed: {ref}"
    lines = sent["body"].split("\n")
    code = code_of(sent["body"])
    assert CODE_FORMAT.match(code)
    assert lines[0] == "Booking changed" and lines[2] == "Saunalöyly"
    assert f"Booking reference: {ref}" in lines and "Date: Tuesday 1 December 2026" in lines
    assert "Session: 10:00–11:30" in lines and "Seats: 3" in lines and "Total: NOK 750 incl. VAT" in lines
    assert lines[-8:] == ["", "Voucher", f"Code: {code}", "Value: NOK 250", "Valid until: Tuesday 30 November 2027",
                          NEVER_PAID_OUT, "", MANAGE_LINK_STILL_WORKS]
    assert "http" not in sent["body"] and token not in sent["body"]
    assert not any(name in sent["body"] for name in SAUNA_NAMES)
    # only the hash is stored, of the 16 characters
    raw = code.replace("-", "")
    assert bytes(v_hash) == hashlib.sha256(raw.encode()).digest()
    not_in_store(pg, code, raw)
    # the code is in no response but inside the email body, not in the Manage read, history, Booking list or log
    without_emails = {k: v for k, v in body.items() if k != "emails"}
    for text in walk(without_emails):
        assert raw not in text.replace("-", "")
    manage_read = guest.get(f"/api/manage/{ref}").json()
    listing = admin.get("/api/admin/bookings", params={"date": DAY}).json()
    for doc in (manage_read, listing):
        assert code not in json.dumps(doc) and raw not in json.dumps(doc)
    assert code not in backend.output() and raw not in backend.output()
    # the history entry, in the Manage read and the Booking list
    entry = manage_read["history"][0]
    assert entry == {"action": "voucher", "at": entry["at"], "seats": 1, "from_window": None, "to_window": None,
                     "new_reference": None, "voucher_value_ore": 25000}
    assert entry["at"].startswith("2026-11-30T21:0") and entry["at"].endswith("+01:00")
    w1 = {w["id"]: w for w in listing["windows"]}[1]
    [listed] = w1["bookings"]
    assert (listed["reference"], listed["seats"], listed["status"], listed["cancelled_at"], listed["history"]) == (
        ref, 3, "active", None, [entry])
    assert (w1["seats_booked"], w1["seats_left"]) == (3, 41)


def test_the_value_is_the_bookings_own_price_per_seat(guest, pg):
    ref, _ = opened(guest, 1, 3)
    pg.execute("UPDATE bookings SET price_per_seat_ore = 19950, total_ore = 3 * 19950 WHERE reference = %s", (ref,))
    pg.commit()  # the setting stays at 25000; the Booking's stored price decides (AD-13)
    r = give_up(guest, ref, 2)
    assert r.status_code == 200, r.text
    assert r.json()["voucher"]["value_ore"] == 39900
    assert r.json()["booking"]["total_ore"] == 19950
    assert "Value: NOK 399" in r.json()["emails"][0]["body"]
    assert rows(pg, "SELECT value_ore, balance_ore FROM vouchers") == [(39900, 39900)]


# ------------------------------------------------------------------ all Seats: the Booking is cancelled


def test_giving_up_all_seats_cancels_the_booking(guest, admin, pg):
    ref, token = opened(guest, 1, 2)
    other, _ = opened(guest, 1, 3)
    assert left_in(guest, 1) == 39
    bid, created, entry_time = rows(pg, "SELECT id, created_at, entry_time FROM bookings WHERE reference = %s",
                                    (ref,))[0]
    r = give_up(guest, ref, 2)
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"booking", "voucher", "emails"}
    assert body["voucher"] == {"value_ore": 50000, "last_valid_date": LAST_VALID}
    b = body["booking"]
    assert (b["seats"], b["total_ore"], b["version"], b["status"]) == (2, 50000, 1, "cancelled")
    assert b["cancelled_at"].startswith("2026-11-30T21:0") and b["cancelled_at"].endswith("+01:00")
    # one UPDATE: cancelled by the Guest with a Voucher; Seats and total stay; it counts no more
    [(status, seats, total, version, cancelled_at, cause, remedy, c2, e2)] = rows(
        pg, "SELECT status, seats, total_ore, version, cancelled_at, cancel_cause, cancel_remedy, created_at, "
            "entry_time FROM bookings WHERE id = %s", (bid,))
    assert (status, seats, total, version, cause, remedy, c2, e2) == (
        "cancelled", 2, 50000, 1, "guest", "voucher", created, entry_time)
    assert abs(cancelled_at - BEFORE) < dt.timedelta(minutes=1)
    assert left_in(guest, 1) == 41
    assert rows(pg, "SELECT value_ore, balance_ore, booking_id FROM vouchers") == [(50000, 50000, bid)]
    assert rows(pg, "SELECT action, seats FROM booking_changes") == [("voucher", 2)]
    assert ledger(pg, ref) == 0  # AD-31 once cancelled
    assert rows(pg, "SELECT count(*) FROM payments WHERE direction = 'refund' AND method = 'card'") == [(0,)]
    # the email
    [sent] = body["emails"]
    assert sent["subject"] == f"Booking cancelled: {ref}"
    lines = sent["body"].split("\n")
    code = code_of(sent["body"])
    assert lines[:3] == ["Booking cancelled", "", "Saunalöyly"]
    assert lines[7:12] == [f"Booking reference: {ref}", "Date: Tuesday 1 December 2026", "Session: 10:00–11:30",
                           "Seats given up: 2", ""]
    assert lines[12:] == ["Voucher", f"Code: {code}", "Value: NOK 500", "Valid until: Tuesday 30 November 2027",
                          NEVER_PAID_OUT, "", MANAGE_LINK_STILL_WORKS]
    assert "Total:" not in sent["body"] and "http" not in sent["body"]
    # the Manage link still opens it: cancelled, with its time, Seats given up and history
    assert open_link(guest, token).json() == {"reference": ref}
    read = guest.get(f"/api/manage/{ref}").json()
    assert (read["status"], read["seats"], read["cancelled_at"]) == ("cancelled", 2, b["cancelled_at"])
    assert code not in json.dumps(read)
    # the Booking list: still listed, with its time, cause and remedy, outside Seats booked
    w1 = {w["id"]: w for w in admin.get("/api/admin/bookings", params={"date": DAY}).json()["windows"]}[1]
    listed = {x["reference"]: x for x in w1["bookings"]}
    assert (listed[ref]["status"], listed[ref]["cancelled_at"], listed[ref]["cancel_cause"],
            listed[ref]["cancel_remedy"]) == ("cancelled", b["cancelled_at"], "guest", "voucher")
    assert listed[ref]["history"][0]["voucher_value_ore"] == 50000
    assert listed[other]["status"] == "active"
    assert (w1["seats_booked"], w1["seats_left"]) == (3, 41)


def test_a_cancelled_booking_refuses_every_change(guest, pg):
    ref, _ = opened(guest, 1, 2)
    assert give_up(guest, ref, 2).status_code == 200
    before = everything(pg)
    vouchers_before = rows(pg, "SELECT count(*) FROM vouchers")
    refused(give_up(guest, ref, 1, version=1), "booking_cancelled")
    refused(give_up(guest, ref, 5, version=0), "booking_cancelled")  # before booking_changed and seats_exceed
    refused(move(guest, ref, 2, 1, version=1), "booking_cancelled")
    assert everything(pg) == before and rows(pg, "SELECT count(*) FROM vouchers") == vouchers_before


def test_a_one_seat_booking_is_cancelled_whole(guest, pg):
    ref, _ = opened(guest, 2, 1)
    r = give_up(guest, ref, 1)
    assert r.status_code == 200, r.text
    assert r.json()["booking"]["status"] == "cancelled"
    assert r.json()["emails"][0]["subject"] == f"Booking cancelled: {ref}"
    assert left_in(guest, 2) == 44


# ------------------------------------------------------------------ the ledger across Changes (AD-31)


def test_the_ledger_holds_after_partial_and_full_voucher_changes(guest, pg):
    ref, _ = opened(guest, 1, 4)
    assert ledger(pg, ref) == 100000
    for version, seats, total in ((0, 1, 75000), (1, 2, 25000)):
        r = give_up(guest, ref, seats, version=version)
        assert r.status_code == 200, r.text
        assert ledger(pg, ref) == total == r.json()["booking"]["total_ore"]
    assert give_up(guest, ref, 1, version=2).json()["booking"]["status"] == "cancelled"
    assert ledger(pg, ref) == 0
    assert rows(pg, "SELECT count(*), sum(value_ore) FROM vouchers") == [(3, 100000)]
    assert rows(pg, "SELECT count(*) FROM booking_changes WHERE action = 'voucher'") == [(3,)]
    assert left_in(guest, 1) == 44


# ------------------------------------------------------------------ refusals, in the AD-29 order


def test_a_stale_version_is_booking_changed_with_the_booking_now(guest, pg):
    ref, _ = opened(guest, 1, 3)
    assert give_up(guest, ref, 1).status_code == 200  # version 0 -> 1
    before = everything(pg)
    r = give_up(guest, ref, 1, version=0)
    refused(r, "booking_changed", booking=guest.get(f"/api/manage/{ref}").json())
    assert everything(pg) == before and rows(pg, "SELECT count(*) FROM vouchers") == [(1,)]


@pytest.mark.parametrize("seats", [0, -1, 3, 2_147_483_647])
def test_seats_outside_one_to_the_bookings_seats_are_change_invalid(guest, pg, seats):
    ref, _ = opened(guest, 1, 2)
    before = everything(pg)
    refused(give_up(guest, ref, seats), "change_invalid", reason="seats_exceed")
    assert everything(pg) == before and rows(pg, "SELECT count(*) FROM vouchers") == [(0,)]


def test_after_the_cutoff_it_is_cutoff_passed(guest, pg):
    ref, token = opened(guest, 1, 2)
    set_clock(pg, win_start(0) - dt.timedelta(hours=12))  # Window 1's Cutoff
    assert open_link(guest, token).status_code == 200
    before = everything(pg)
    refused(give_up(guest, ref, 1), "cutoff_passed", cutoff_at="2026-11-30T22:00:00+01:00")
    refused(give_up(guest, ref, 2), "cutoff_passed", cutoff_at="2026-11-30T22:00:00+01:00")
    assert everything(pg) == before and rows(pg, "SELECT count(*) FROM vouchers") == [(0,)]


def test_the_refusal_order(guest, pg):
    ref, token = opened(guest, 1, 2)
    set_clock(pg, win_start(0) - dt.timedelta(hours=11))  # past the Cutoff
    assert open_link(guest, token).status_code == 200
    # seats_exceed before cutoff_passed; booking_changed before seats_exceed
    refused(give_up(guest, ref, 5), "change_invalid", reason="seats_exceed")
    assert give_up(guest, ref, 5, version=7).json()["detail"]["error"] == "booking_changed"
    assert give_up(guest, ref, 1).json()["detail"]["error"] == "cutoff_passed"
    # a cancelled Booking comes first of all
    pg.execute("UPDATE bookings SET status = 'cancelled', cancelled_at = app_now(), cancel_cause = 'guest', "
               "cancel_remedy = 'voucher' WHERE reference = %s", (ref,))
    pg.commit()
    refused(give_up(guest, ref, 5, version=7), "booking_cancelled")


# ------------------------------------------------------------------ repeats and keys (AD-9)


def test_a_repeat_returns_the_first_outcome_and_issues_no_second_voucher(guest, pg):
    ref, _ = opened(guest, 1, 3)
    key = str(uuid.uuid4())
    first = give_up(guest, ref, 1, key=key)
    assert first.status_code == 200, first.text
    before = everything(pg)
    again = give_up(guest, ref, 1, key=key)
    assert again.status_code == 200 and again.json() == first.json()
    assert everything(pg) == before and rows(pg, "SELECT count(*) FROM vouchers") == [(1,)]
    # after a later Change the repeat shows the Booking now, with the same email and Voucher
    assert give_up(guest, ref, 2, version=1).status_code == 200
    later = give_up(guest, ref, 1, key=key).json()
    assert later["emails"] == first.json()["emails"] and later["voucher"] == first.json()["voucher"]
    assert later["booking"]["status"] == "cancelled"
    assert rows(pg, "SELECT count(*) FROM vouchers") == [(2,)]


def test_a_known_key_with_another_request_or_session_is_invalid_key(before_cutoff, guest, pg):
    ref, token = opened(guest, 1, 3)
    key = str(uuid.uuid4())
    assert give_up(guest, ref, 1, key=key).status_code == 200
    with api_client(before_cutoff, session=False) as other:
        assert open_link(other, token).status_code == 200
        before = everything(pg)
        refused(give_up(other, ref, 1, key=key), "invalid_key")  # another session
        refused(give_up(guest, ref, 2, key=key), "invalid_key")  # another body
        refused(give_up(guest, ref, 1, version=1, key=key), "invalid_key")
        refused(move(guest, ref, 2, 1, key=key), "invalid_key")  # a Voucher key is not a move's
        assert everything(pg) == before
    assert rows(pg, "SELECT count(*) FROM vouchers") == [(1,)]
    move_key = str(uuid.uuid4())
    assert move(guest, ref, 2, 1, version=1, key=move_key).status_code == 200
    refused(give_up(guest, ref, 1, version=2, key=move_key), "invalid_key")  # nor the other way round


def test_a_refusal_stores_no_key(guest, pg):
    ref, _ = opened(guest, 1, 2)
    key = str(uuid.uuid4())
    refused(give_up(guest, ref, 3, key=key), "change_invalid", reason="seats_exceed")
    assert give_up(guest, ref, 1, key=key).status_code == 200


# ------------------------------------------------------------------ access (AD-28) and shape


def test_without_a_valid_grant_it_is_404_and_writes_nothing(guest, before_cutoff, pg):
    ref, token = opened(guest, 1, 2)
    other_ref, _ = opened(guest, 2, 1)
    before = everything(pg)
    with api_client(before_cutoff, session=False) as anon, api_client(before_cutoff) as stranger:
        answers = [give_up(anon, ref, 1), give_up(stranger, ref, 1), give_up(guest, "ZZZZZZZZ", 1),
                   give_up(guest, ref.lower(), 1)]
        with api_client(before_cutoff, session=False) as holder:
            assert open_link(holder, token).status_code == 200
            answers.append(give_up(holder, other_ref, 1))  # a grant for another Booking
    for r in answers:
        assert r.status_code == 404 and r.json() == NOT_FOUND, r.text
    set_clock(pg, BEFORE + dt.timedelta(minutes=31))  # the grant has been idle too long
    assert give_up(guest, ref, 1).json() == NOT_FOUND
    assert everything(pg)[:7] == before[:7]
    assert rows(pg, "SELECT count(*) FROM vouchers") == [(0,)]


def test_a_body_or_key_of_the_wrong_shape_is_422(guest, pg):
    ref, _ = opened(guest, 1, 2)
    before = everything(pg)
    url = f"/api/manage/{ref}/seats/voucher"
    for kwargs in ({"json": {"seats": 1, "version": 0}},  # no key
                   {"json": {"seats": 1, "version": 0}, "headers": {"Idempotency-Key": "x"}},
                   {"json": {"seats": "one", "version": 0}, "headers": {"Idempotency-Key": str(uuid.uuid4())}},
                   {"json": {"seats": 1}, "headers": {"Idempotency-Key": str(uuid.uuid4())}},
                   {"json": {"seats": 1, "version": 0, "window_id": 2},
                    "headers": {"Idempotency-Key": str(uuid.uuid4())}}):
        r = guest.post(url, **kwargs)
        assert r.status_code == 422 and r.json()["detail"]["error"] == "invalid_input", r.text
    assert everything(pg)[:7] == before[:7]


def test_another_origin_is_403(guest, pg):
    ref, _ = opened(guest, 1, 2)
    r = guest.post(f"/api/manage/{ref}/seats/voucher", json={"seats": 1, "version": 0},
                   headers={"Idempotency-Key": str(uuid.uuid4()), "Origin": "https://evil.example"})
    assert r.status_code == 403
    assert rows(pg, "SELECT count(*) FROM vouchers") == [(0,)]


# ------------------------------------------------------------------ retention (FR-21, AD-30)


def test_retention_waits_for_the_latest_voucher_expiry(world, pg):
    bid = _booking(pg)
    other = _booking(pg)
    pg.execute("UPDATE bookings SET name = 'Kari Voucher' WHERE id = %s", (bid,))
    pg.commit()
    # Window 1 ends 2026-12-01 10:30Z, so 12 months after it is 2027-12-01 10:30Z. A Voucher issued at EARLY (Venue
    # date 1 Dec 2026) expires 2027-12-01 23:00Z; a second one, valid through 15 Jan 2028, at 2028-01-15 23:00Z.
    voucher_service.issue(pg, bid, 25000)
    voucher_service.issue(pg, bid, 25000, last_valid_date=dt.date(2028, 1, 15))
    pg.commit()

    def due(ts):
        set_clock(pg, ts)
        return rows(pg, "SELECT retention_due(%s), retention_due(%s)", (bid, other))[0]

    assert due(dt.datetime(2027, 12, 1, 12, 0, tzinfo=dt.timezone.utc)) == (False, True)
    assert due(dt.datetime(2027, 12, 2, 12, 0, tzinfo=dt.timezone.utc)) == (False, True)  # the later one counts
    assert due(dt.datetime(2028, 1, 15, 22, 59, tzinfo=dt.timezone.utc)) == (False, True)
    assert due(dt.datetime(2028, 1, 15, 23, 1, tzinfo=dt.timezone.utc)) == (True, True)
    # the Booking list masks by the same predicate
    set_clock(pg, dt.datetime(2027, 12, 2, 12, 0, tzinfo=dt.timezone.utc))
    with admin_client(world) as admin:
        listed = admin.get("/api/admin/bookings", params={"date": DAY}).json()
    names = {b["reference"]: b["name"] for w in listed["windows"] for b in w["bookings"]}
    by_id = dict(rows(pg, "SELECT id, reference FROM bookings"))
    assert names[by_id[bid]] == "Kari Voucher" and names[by_id[other]] == "Anonymised"
