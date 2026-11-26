"""FR-33 / AD-23 / AD-28 / AD-29 / AD-31 / AD-9 (Story 5.3, part 1): cancel a Private sauna through its Manage link.

`POST /api/manage/{reference}/whole/cancel {remedy, version}` with an `Idempotency-Key` runs
`services.change.whole_cancel` in one `db.run`, in AD-23's write order: the Booking becomes `cancelled` (`guest`, the remedy, `version + 1`), its
capacity row is deleted (Seats left rises by the Sauna's Capacity at once), one `cancel` history row, the `payments`
rows and one cancellation email. Remedy `refund` calls `services.payment.refund`: the card part is one `refund`/`card`
row, a Voucher part one new Voucher of that sum (valid through the earliest last valid date of the Vouchers used, never
less than 30 days ahead) with a `refund`/`voucher` row; the history row has no Voucher. Remedy `voucher`: one Voucher of
the full total, valid one year, a `refund`/`voucher` row and no card row; the history row points to the Voucher.
Refusals in AD-29's order: `booking_cancelled`, `booking_changed`, `cutoff_passed` (72 hours, tested on both sides).
A repeat returns the first outcome; the routes of the other kind of Booking are `404 not_found`. The ledger (charges
minus returns) is the total while active and 0 once cancelled.

The clock is `FAR` (2026-11-27 10:00 Venue time), more than 72 hours before `world`'s Windows of 1 December, so the
Whole-sauna Cutoff has not passed (`BEFORE` of the Seat tests is past it).
"""

from __future__ import annotations

import datetime as dt
import json
import uuid

import psycopg
import pytest

from booking_platform import db
from booking_platform.services import payment
from booking_platform.services.errors import Refused
from client import admin_client, api_client
from conftest import raw_booking, set_clock, win_start
from test_fr25_manage_link import NOT_FOUND, TOKEN, open_link, rows
from test_fr26_move import DAY, MANAGE_LINK_STILL_WORKS, everything, left_in, move, refused
from test_fr27_voucher_for_seats import NEVER_PAID_OUT, _refused_by, code_of, give_up, ledger, not_in_store, walk
from test_fr27_voucher_for_seats import opened as opened_seats
from test_fr28_voucher import balance, payments_of, voucher_id
from test_fr29_whole_booking import KAJO, SIMULATED, book_whole

FAR = win_start(0) - dt.timedelta(days=4)  # 2026-11-27 09:00Z (10:00 Venue time): before every Whole-sauna Cutoff
CUTOFF_1 = win_start(0) - dt.timedelta(hours=72)  # Window 1's Whole-sauna Cutoff
CUTOFF_AT_1 = "2026-11-28T10:00:00+01:00"
A_YEAR = "2027-11-27"  # a Voucher issued at FAR is valid one year
IN_30_DAYS = "2026-12-27"  # the shortest validity of a returned Voucher at FAR
KAJO_ORE = 315000


def cancel(client, ref: str, remedy: str = "refund", version: int = 0, key: str | None = None):
    return client.post(f"/api/manage/{ref}/whole/cancel", json={"remedy": remedy, "version": version},
                       headers={"Idempotency-Key": key or str(uuid.uuid4())})


@pytest.fixture
def far(world, pg):
    set_clock(pg, FAR)
    return world


@pytest.fixture
def group(far):
    with api_client(far) as c:
        yield c


def whole_opened(client, window_id: int = 1, sauna_id: int = KAJO, **fields) -> tuple[str, str]:
    """A Private sauna paid by `client`, whose Manage link `client` has opened; returns (reference, token)."""
    r = book_whole(client, window_id, sauna_id, **fields)
    assert r.status_code == 201, r.text
    body = r.json()
    ref = body["booking"]["reference"]
    token = TOKEN.search(body["emails"][0]["body"]).group(1)
    assert open_link(client, token).status_code == 200
    return ref, token


def seat_voucher(client, seats: int = 1) -> str:
    """A Voucher worth `seats` x NOK 250 from a give-up of Seats in Window 2; its displayed code."""
    ref, _ = opened_seats(client, 2, seats + 1)
    r = give_up(client, ref, seats)
    assert r.status_code == 200, r.text
    return code_of(r.json()["emails"][0]["body"])


def booking_row(pg, ref: str) -> tuple:
    return rows(pg, "SELECT id, status, cancel_cause, cancel_remedy, version, cancelled_at IS NOT NULL, sauna_id, "
                    "total_ore FROM bookings WHERE reference = %s", (ref,))[0]


def history_rows(pg, bid: int) -> list:
    return rows(pg, "SELECT action, seats, from_window_id, to_window_id, from_sauna_id, to_sauna_id, new_booking_id, "
                    "voucher_id FROM booking_changes WHERE booking_id = %s ORDER BY id", (bid,))


def returned_vouchers(pg, bid: int) -> list:
    return rows(pg, "SELECT id, value_ore, balance_ore, (expires_at AT TIME ZONE 'Europe/Oslo')::date - 1 "
                    "FROM vouchers WHERE booking_id = %s ORDER BY id", (bid,))


def body_from_reference(body: str, ref: str) -> list[str]:
    lines = body.split("\n")
    return lines[lines.index(f"Booking reference: {ref}"):]


# ------------------------------------------------------------------ the store (migration 0014)


def test_the_cancel_history_shape_is_in_the_store(far, pg):
    pg.execute(raw_booking(1, 1))
    pg.commit()
    bid = rows(pg, "SELECT id FROM bookings")[0][0]
    other = pg.execute(raw_booking(1, 1) + " RETURNING id").fetchone()[0]
    vid = pg.execute("INSERT INTO vouchers (code_hash, value_ore, balance_ore, expires_at, booking_id) "
                     "VALUES (%s, 100, 100, app_now() + interval '1 year', %s) RETURNING id",
                     (b"c" * 32, bid)).fetchone()[0]
    pg.commit()
    ins = ("INSERT INTO booking_changes (booking_id, action, seats, from_window_id, to_window_id, from_sauna_id, "
           "to_sauna_id, new_booking_id, voucher_id) VALUES (%s, 'cancel', %s, %s, %s, %s, %s, %s, %s)")
    for shape in ((1, None, None, None, None, None, None), (None, 1, None, None, None, None, None),
                  (None, None, 2, None, None, None, None), (None, None, None, 1, None, None, None),
                  (None, None, None, None, 1, None, None), (None, None, None, None, None, other, vid)):
        _refused_by(pg, "booking_changes_cancel_shape", ins, (bid, *shape))
    _refused_by(pg, "booking_changes_action_known",
                ins.replace("'cancel'", "'refund'"), (bid, None, None, None, None, None, None, None))
    pg.execute(ins, (bid, None, None, None, None, None, None, None))  # a refund: no Voucher
    pg.execute(ins, (bid, None, None, None, None, None, None, vid))  # a Voucher remedy
    pg.commit()
    assert rows(pg, "SELECT count(*) FROM booking_changes WHERE action = 'cancel'") == [(2,)]


def test_a_seat_booking_is_never_cancelled_for_a_refund(far, pg):
    pg.execute(raw_booking(1, 2))
    pg.commit()
    bid = rows(pg, "SELECT id FROM bookings")[0][0]
    _refused_by(pg, "seat_guest_refund_forbidden",
                "UPDATE bookings SET status = 'cancelled', cancelled_at = app_now(), cancel_cause = 'guest', "
                "cancel_remedy = 'refund' WHERE id = %s", (bid,))
    assert rows(pg, "SELECT status FROM bookings WHERE id = %s", (bid,)) == [("active",)]


@pytest.fixture
def pool(world, database):
    db.open_pool(database, max_size=2)
    yield
    db.close_pool()


def test_refund_of_a_booking_with_a_split_is_an_internal_error(group, pg, pool):
    ref, _ = opened_seats(group, 1, 3)
    r = move(group, ref, 2, 1)  # a split: 1 Seat moves to a new Booking
    assert r.status_code == 200, r.text
    new_ref = r.json()["new_booking"]["reference"]
    before = everything(pg)
    for reference in (ref, new_ref):
        bid = rows(pg, "SELECT id FROM bookings WHERE reference = %s", (reference,))[0][0]
        with pytest.raises(payment.SplitRefund):
            db.run(lambda c, b=bid: payment.refund(c, b))
    assert not issubclass(payment.SplitRefund, Refused)  # unmapped: the API answers 500 internal_error (AD-1)
    assert everything(pg) == before  # rolled back: no refund row, no Voucher
    assert rows(pg, "SELECT count(*) FROM vouchers") == [(0,)]


# ------------------------------------------------------------------ the Manage read (AD-28)


def test_the_read_offers_the_refund_split_and_no_code_or_email(group, pg):
    ref, token = whole_opened(group)
    read = group.get(f"/api/manage/{ref}").json()
    assert (read["kind"], read["sauna"], read["status"], read["change_allowed"], read["cutoff_at"]) == (
        "whole", {"id": KAJO, "name": "Kajo"}, "active", True, CUTOFF_AT_1)
    assert read["cancel_remedy"] is None
    assert read["refund_split"] == {"card_ore": KAJO_ORE, "voucher_ore": 0, "voucher_last_valid_date": None}
    assert read["voucher_last_valid_date"] == A_YEAR  # the Voucher remedy: one year
    text = json.dumps(read)
    assert token not in text and "@" not in text and "manage#t=" not in text


def test_a_seat_booking_read_has_no_refund_split(group):
    ref, _ = opened_seats(group, 1, 2)
    read = group.get(f"/api/manage/{ref}").json()
    assert "refund_split" not in read and read["cancel_remedy"] is None


# ------------------------------------------------------------------ cancel for a refund, paid by card


def test_cancel_for_a_refund_returns_the_card_payment(group, pg):
    ref, token = whole_opened(group)
    bid = booking_row(pg, ref)[0]
    assert left_in(group, 1) == 32
    assert ledger(pg, ref) == KAJO_ORE  # active: the charges add up to the total
    r = cancel(group, ref, "refund")
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"booking", "refund", "emails"}
    assert body["refund"] == {"card_ore": KAJO_ORE}
    b = body["booking"]
    assert (b["status"], b["cancel_remedy"], b["version"], b["kind"], b["sauna"]) == (
        "cancelled", "refund", 1, "whole", {"id": KAJO, "name": "Kajo"})
    assert b["cancelled_at"].startswith("2026-11-27T10:0") and "refund_split" not in b
    # AD-23's write order in one transaction: cancelled, no capacity row, one history row, the ledger rows
    assert booking_row(pg, ref)[1:] == ("cancelled", "guest", "refund", 1, True, KAJO, KAJO_ORE)
    assert rows(pg, "SELECT count(*) FROM whole_bookings") == [(0,)]
    assert history_rows(pg, bid) == [("cancel", None, None, None, None, None, None, None)]
    assert payments_of(pg, ref) == [("charge", "card", KAJO_ORE, None), ("refund", "card", KAJO_ORE, None)]
    assert rows(pg, "SELECT count(*) FROM vouchers") == [(0,)]
    assert ledger(pg, ref) == 0
    assert left_in(group, 1) == 44  # Kajo's 12 Seats are back at once
    # the email
    [sent] = body["emails"]
    assert sent["subject"] == f"Booking cancelled: {ref}"
    lines = sent["body"].split("\n")
    assert lines[:3] == ["Booking cancelled", "", "Saunalöyly"]
    assert body_from_reference(sent["body"], ref) == [
        f"Booking reference: {ref}", "Date: Tuesday 1 December 2026", "Session: 10:00–11:30", "Sauna: Kajo", "",
        "Refunded to card: NOK 3150", SIMULATED, "", MANAGE_LINK_STILL_WORKS]
    assert "http" not in sent["body"] and "Code:" not in sent["body"]
    assert rows(pg, "SELECT count(*) FROM outbox_emails o JOIN booking_changes h ON h.id = o.change_id "
                    "WHERE h.booking_id = %s", (bid,)) == [(1,)]
    # the Manage link still opens it, cancelled
    assert open_link(group, token).json() == {"reference": ref}
    read = group.get(f"/api/manage/{ref}").json()
    assert (read["status"], read["cancel_remedy"], read["cancelled_at"]) == ("cancelled", "refund", b["cancelled_at"])
    assert read["history"] == [{"action": "cancel", "at": read["history"][0]["at"], "seats": None,
                                "from_window": None, "to_window": None, "new_reference": None,
                                "voucher_value_ore": None}]


def test_the_booking_list_shows_it_cancelled_and_does_not_count_it(group, far, pg):
    ref, _ = whole_opened(group)
    seat_ref, _ = opened_seats(group, 1, 2)
    b = cancel(group, ref, "refund").json()["booking"]
    with admin_client(far, pg) as admin:
        w1 = {w["id"]: w for w in admin.get("/api/admin/bookings", params={"date": DAY}).json()["windows"]}[1]
    listed = {x["reference"]: x for x in w1["bookings"]}
    row = listed[ref]
    assert (row["kind"], row["sauna"], row["status"], row["cancelled_at"], row["cancel_cause"],
            row["cancel_remedy"]) == ("whole", {"id": KAJO, "name": "Kajo"}, "cancelled", b["cancelled_at"], "guest",
                                      "refund")
    assert [h["action"] for h in row["history"]] == ["cancel"] and row["history"][0]["voucher_value_ore"] is None
    assert listed[seat_ref]["status"] == "active"
    assert (w1["seat_capacity"], w1["seats_booked"], w1["seats_left"]) == (44, 2, 42)


# ------------------------------------------------------------------ cancel for a refund, paid partly by a Voucher


def test_a_partial_voucher_comes_back_as_a_new_voucher_and_the_rest_to_the_card(group, pg):
    code = seat_voucher(group)  # NOK 250, valid one year
    used = voucher_id(pg, code)
    ref, _ = whole_opened(group, voucher_code=code, voucher_part_ore=25000)
    bid = booking_row(pg, ref)[0]
    assert group.get(f"/api/manage/{ref}").json()["refund_split"] == {
        "card_ore": 290000, "voucher_ore": 25000, "voucher_last_valid_date": A_YEAR}
    assert ledger(pg, ref) == KAJO_ORE
    r = cancel(group, ref, "refund")
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"booking", "refund", "voucher", "emails"}
    assert body["refund"] == {"card_ore": 290000}
    assert body["voucher"] == {"value_ore": 25000, "last_valid_date": A_YEAR}  # the earliest used: one year
    [(new_id, value, bal, last)] = returned_vouchers(pg, bid)
    assert (value, bal, last.isoformat()) == (25000, 25000, A_YEAR) and new_id != used
    assert balance(pg, code) == 0  # the spent Voucher is not refilled
    assert payments_of(pg, ref) == [("charge", "voucher", 25000, used), ("charge", "card", 290000, None),
                                    ("refund", "card", 290000, None), ("refund", "voucher", 25000, new_id)]
    assert history_rows(pg, bid) == [("cancel", None, None, None, None, None, None, None)]  # a refund: no Voucher
    assert ledger(pg, ref) == 0
    [sent] = body["emails"]
    new_code = code_of(sent["body"])
    assert new_code != code
    assert body_from_reference(sent["body"], ref) == [
        f"Booking reference: {ref}", "Date: Tuesday 1 December 2026", "Session: 10:00–11:30", "Sauna: Kajo", "",
        "Refunded to card: NOK 2900", SIMULATED, "",
        "Voucher", f"Code: {new_code}", "Value: NOK 250", "Valid until: Saturday 27 November 2027", NEVER_PAID_OUT, "",
        MANAGE_LINK_STILL_WORKS]
    # the code is only in the email: never in the response or another table
    assert new_code not in json.dumps(body["booking"]) and new_code not in json.dumps(body.get("voucher"))
    not_in_store(pg, new_code, new_code.replace("-", ""))


def test_a_returned_voucher_is_valid_at_least_30_days(group, pg):
    code = seat_voucher(group)
    ref, _ = whole_opened(group, voucher_code=code, voucher_part_ore=25000)
    bid = booking_row(pg, ref)[0]
    # the Voucher that paid it ends in 5 days
    pg.execute("UPDATE vouchers SET expires_at = app_now() + interval '5 days' WHERE id = %s", (voucher_id(pg, code),))
    pg.commit()
    assert group.get(f"/api/manage/{ref}").json()["refund_split"]["voucher_last_valid_date"] == IN_30_DAYS
    body = cancel(group, ref, "refund").json()
    assert body["voucher"] == {"value_ore": 25000, "last_valid_date": IN_30_DAYS}
    assert returned_vouchers(pg, bid)[0][3].isoformat() == IN_30_DAYS
    assert "Valid until: Sunday 27 December 2026" in body["emails"][0]["body"]


def test_a_voucher_that_paid_all_comes_back_whole_with_no_card_row(group, pg):
    code = seat_voucher(group, 8)  # NOK 2000, more than Rauha's NOK 1850
    ref, _ = whole_opened(group, 1, 1, voucher_code=code, voucher_part_ore=185000)
    body = cancel(group, ref, "refund").json()
    assert body["refund"] == {"card_ore": 0}
    assert body["voucher"] == {"value_ore": 185000, "last_valid_date": A_YEAR}
    assert [p[:3] for p in payments_of(pg, ref)] == [("charge", "voucher", 185000), ("refund", "voucher", 185000)]
    lines = body_from_reference(body["emails"][0]["body"], ref)
    assert "Refunded to card" not in "\n".join(lines) and SIMULATED not in lines  # no card part, no payment note
    assert lines[4:6] == ["", "Voucher"]
    assert ledger(pg, ref) == 0


# ------------------------------------------------------------------ cancel for a Voucher


@pytest.mark.parametrize("partial", [False, True])
def test_cancel_for_a_voucher_issues_one_voucher_of_the_full_total(group, pg, partial):
    fields = {}
    if partial:
        code = seat_voucher(group)
        fields = dict(voucher_code=code, voucher_part_ore=25000)
    ref, _ = whole_opened(group, **fields)
    bid = booking_row(pg, ref)[0]
    r = cancel(group, ref, "voucher")
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"booking", "voucher", "emails"}  # no refund
    assert body["voucher"] == {"value_ore": KAJO_ORE, "last_valid_date": A_YEAR}
    assert booking_row(pg, ref)[1:4] == ("cancelled", "guest", "voucher")
    [(vid, value, bal, last)] = returned_vouchers(pg, bid)
    assert (value, bal, last.isoformat()) == (KAJO_ORE, KAJO_ORE, A_YEAR)
    assert history_rows(pg, bid) == [("cancel", None, None, None, None, None, None, vid)]  # the remedy's Voucher
    assert [p for p in payments_of(pg, ref) if p[0] == "refund"] == [("refund", "voucher", KAJO_ORE, vid)]
    assert rows(pg, "SELECT count(*) FROM payments WHERE direction = 'refund' AND method = 'card'") == [(0,)]
    assert ledger(pg, ref) == 0
    assert rows(pg, "SELECT count(*) FROM whole_bookings") == [(0,)] and left_in(group, 1) == 44
    [sent] = body["emails"]
    new_code = code_of(sent["body"])
    assert body_from_reference(sent["body"], ref) == [
        f"Booking reference: {ref}", "Date: Tuesday 1 December 2026", "Session: 10:00–11:30", "Sauna: Kajo", "",
        "Voucher", f"Code: {new_code}", "Value: NOK 3150", "Valid until: Saturday 27 November 2027", NEVER_PAID_OUT,
        "", MANAGE_LINK_STILL_WORKS]
    assert SIMULATED not in sent["body"]
    assert all(new_code not in s for s in walk({k: v for k, v in body.items() if k != "emails"}))
    read = group.get(f"/api/manage/{ref}").json()
    assert read["cancel_remedy"] == "voucher" and read["history"][0]["voucher_value_ore"] == KAJO_ORE
    assert new_code not in json.dumps(read)


# ------------------------------------------------------------------ refusals (AD-29)


def test_the_cutoff_edge_on_both_sides(group, pg):
    ref, token = whole_opened(group)
    set_clock(pg, CUTOFF_1)
    assert open_link(group, token).status_code == 200
    before = everything(pg)
    for remedy in ("refund", "voucher"):
        refused(cancel(group, ref, remedy), "cutoff_passed", cutoff_at=CUTOFF_AT_1)
    assert everything(pg) == before and rows(pg, "SELECT count(*) FROM vouchers") == [(0,)]
    read = group.get(f"/api/manage/{ref}").json()
    assert (read["status"], read["change_allowed"], read["cutoff_at"]) == ("active", False, CUTOFF_AT_1)
    set_clock(pg, CUTOFF_1 - dt.timedelta(seconds=1))
    assert group.get(f"/api/manage/{ref}").json()["change_allowed"] is True
    r = cancel(group, ref, "refund")
    assert r.status_code == 200, r.text


def test_a_stale_version_is_booking_changed_and_a_cancelled_booking_is_booking_cancelled(group, pg):
    ref, _ = whole_opened(group)
    pg.execute("UPDATE bookings SET version = version + 1 WHERE reference = %s", (ref,))
    pg.commit()
    before = everything(pg)
    refused(cancel(group, ref, "refund", version=0), "booking_changed", booking=group.get(f"/api/manage/{ref}").json())
    assert everything(pg) == before
    assert cancel(group, ref, "refund", version=1).status_code == 200
    before = everything(pg)
    for remedy, version in (("refund", 2), ("voucher", 2), ("refund", 0)):  # booking_cancelled comes first
        refused(cancel(group, ref, remedy, version=version), "booking_cancelled")
    assert everything(pg) == before
    assert rows(pg, "SELECT count(*) FROM payments WHERE direction = 'refund'") == [(1,)]


def test_the_refusal_order(group, pg):
    ref, token = whole_opened(group)
    set_clock(pg, CUTOFF_1 + dt.timedelta(hours=1))
    assert open_link(group, token).status_code == 200
    refused(cancel(group, ref, version=3), "booking_changed", booking=group.get(f"/api/manage/{ref}").json())
    refused(cancel(group, ref), "cutoff_passed", cutoff_at=CUTOFF_AT_1)
    pg.execute("UPDATE bookings SET status = 'cancelled', cancelled_at = app_now(), cancel_cause = 'block' "
               "WHERE reference = %s", (ref,))
    pg.execute("DELETE FROM whole_bookings")
    pg.commit()
    refused(cancel(group, ref, version=3), "booking_cancelled")


# ------------------------------------------------------------------ repeats and keys (AD-9)


def test_a_repeat_returns_the_first_outcome_with_one_refund_and_one_voucher(group, pg):
    code = seat_voucher(group)
    ref, _ = whole_opened(group, voucher_code=code, voucher_part_ore=25000)
    key = str(uuid.uuid4())
    first = cancel(group, ref, "refund", key=key)
    assert first.status_code == 200, first.text
    before = everything(pg)
    vouchers_before = rows(pg, "SELECT count(*) FROM vouchers")
    again = cancel(group, ref, "refund", key=key)
    assert again.status_code == 200 and again.json() == first.json()  # `refund` rebuilt from the ledger
    assert everything(pg) == before and rows(pg, "SELECT count(*) FROM vouchers") == vouchers_before
    assert [p[:2] for p in payments_of(pg, ref)].count(("refund", "card")) == 1


def test_a_repeat_of_the_voucher_remedy_issues_no_second_voucher(group, pg):
    ref, _ = whole_opened(group)
    key = str(uuid.uuid4())
    first = cancel(group, ref, "voucher", key=key).json()
    again = cancel(group, ref, "voucher", key=key).json()
    assert again == first and rows(pg, "SELECT count(*) FROM vouchers") == [(1,)]


def test_a_known_key_with_another_request_or_session_is_invalid_key(far, group, pg):
    ref, token = whole_opened(group)
    key = str(uuid.uuid4())
    assert cancel(group, ref, "voucher", key=key).status_code == 200
    with api_client(far, session=False) as other:
        assert open_link(other, token).status_code == 200
        before = everything(pg)
        refused(cancel(other, ref, "voucher", key=key), "invalid_key")  # another session
        refused(cancel(group, ref, "refund", key=key), "invalid_key")  # another body
        refused(cancel(group, ref, "voucher", version=1, key=key), "invalid_key")
        assert everything(pg) == before


def test_a_refusal_stores_no_key(group, pg):
    ref, _ = whole_opened(group)
    key = str(uuid.uuid4())
    refused(cancel(group, ref, version=5, key=key), "booking_changed", booking=group.get(f"/api/manage/{ref}").json())
    assert cancel(group, ref, key=key).status_code == 200


# ------------------------------------------------------------------ the other kind (AD-28), access and shape


def test_the_routes_of_the_other_kind_are_404(group, pg):
    whole_ref, _ = whole_opened(group)
    seat_ref, _ = opened_seats(group, 2, 2)
    before = everything(pg)
    answers = [
        group.post(f"/api/manage/{whole_ref}/seats/move", json={"window_id": 3, "seats": 1, "version": 0},
                   headers={"Idempotency-Key": str(uuid.uuid4())}),
        give_up(group, whole_ref, 1),
        cancel(group, seat_ref, "refund"),
        cancel(group, seat_ref, "voucher"),
    ]
    for r in answers:
        assert r.status_code == 404 and r.json() == NOT_FOUND, r.text
    assert everything(pg) == before


def test_without_a_valid_grant_it_is_404_and_writes_nothing(far, group, pg):
    ref, _ = whole_opened(group)
    before = everything(pg)
    with api_client(far, session=False) as anon, api_client(far) as stranger:
        for r in (cancel(anon, ref), cancel(stranger, ref), cancel(group, "ZZZZZZZZ")):
            assert r.status_code == 404 and r.json() == NOT_FOUND, r.text
    assert everything(pg)[:7] == before[:7]


def test_a_body_or_key_of_the_wrong_shape_is_422(group, pg):
    ref, _ = whole_opened(group)
    before = everything(pg)
    url = f"/api/manage/{ref}/whole/cancel"
    key = {"Idempotency-Key": str(uuid.uuid4())}
    for kwargs in ({"json": {"remedy": "refund", "version": 0}},  # no key
                   {"json": {"remedy": "refund", "version": 0}, "headers": {"Idempotency-Key": "x"}},
                   {"json": {"version": 0}, "headers": key},
                   {"json": {"remedy": "cash", "version": 0}, "headers": key},
                   {"json": {"remedy": None, "version": 0}, "headers": key},
                   {"json": {"remedy": "refund"}, "headers": key},
                   {"json": {"remedy": "refund", "version": 0, "sauna_id": 3}, "headers": key}):
        r = group.post(url, **kwargs)
        assert r.status_code == 422 and r.json()["detail"]["error"] == "invalid_input", (kwargs, r.text)
    assert everything(pg)[:7] == before[:7]


def test_another_origin_is_403(group, pg):
    ref, _ = whole_opened(group)
    r = group.post(f"/api/manage/{ref}/whole/cancel", json={"remedy": "refund", "version": 0},
                   headers={"Idempotency-Key": str(uuid.uuid4()), "Origin": "https://evil.example"})
    assert r.status_code == 403
    assert booking_row(pg, ref)[1] == "active"


# ------------------------------------------------------------------ the ledger (AD-31)


def test_the_ledger_holds_for_every_whole_sauna_booking(group, pg):
    code = seat_voucher(group, 4)  # NOK 1000
    paid = [whole_opened(group, 1, KAJO)[0], whole_opened(group, 2, KAJO, voucher_code=code,
                                                           voucher_part_ore=100000)[0], whole_opened(group, 3, 1)[0]]
    for ref, total in zip(paid, (KAJO_ORE, KAJO_ORE, 185000)):
        assert ledger(pg, ref) == total
    for ref, remedy in zip(paid, ("refund", "refund", "voucher")):
        assert cancel(group, ref, remedy).status_code == 200
        assert ledger(pg, ref) == 0
    assert rows(pg, "SELECT count(*) FROM whole_bookings") == [(0,)]
    assert rows(pg, "SELECT bool_and(status = 'cancelled') FROM bookings WHERE kind = 'whole'") == [(True,)]
    with pytest.raises(psycopg.errors.CheckViolation):  # the store still refuses a refund of Seats
        pg.execute("UPDATE bookings SET status = 'cancelled', cancelled_at = app_now(), cancel_cause = 'guest', "
                   "cancel_remedy = 'refund' WHERE kind = 'seats'")
    pg.rollback()
