"""FR-31 / AD-6 / AD-10 / AD-25 (Story 5.4): the Administrator sees where Seats are counted.

`placement(wid)` (migration 0016) is the only computation of Placement: one row per Sauna in Fill order,
`(sauna_id, state, seats)`, placing booked Seats only. The FR-31 catalogue examples are named by ID; each is set up
through the API (Seats given up through FR-27's Voucher, a Private sauna cancelled through FR-33) or raw rows, and
after every step `tests/placement.assert_invariants` checks INV-1 to INV-5, `placement(wid)` against the brute force
and Seats left, and the Booking list's `placement` must equal `placement(wid)` (its open Seats summing to
`seats_booked`). The test Saunas are Rauha 7, Loyly 10, Kajo 12 and Lumo 15 (`world`); `[a, b, c, d]` are the Seats per
Sauna, None for a Sauna booked whole. The clock is `FAR`, before every Cutoff, unless a test says otherwise.
"""

from __future__ import annotations

import datetime as dt

import pytest

from client import api_client
from conftest import SAUNAS, raw_booking, raw_whole, set_clock, state
from placement import BLOCKED, MARKED, OPEN, WHOLE, Raw, assert_invariants, brute_force, placement, seats_of, violations
from test_fr16_booking_list import DAY, NOT_SIGNED_IN, booking_list
from test_fr25_manage_link import rows
from test_fr27_voucher_for_seats import give_up, opened
from test_fr29_whole_booking import KAJO, LUMO, RAUHA, book_whole
from test_fr29_whole_sauna import listed
from test_fr33_whole_change import LOYLY, cancel, far, group, whole_opened  # noqa: F401

NAMES = {i: n for i, n, _ in SAUNAS}
CAPACITY = {i: c for i, _, c in SAUNAS}


def check(pg, admin, expect: list, left: int | None = None, wid: int = 1) -> list:
    """INV-1..INV-5, the brute force and Seats left; the catalogue's `[a, b, c, d]`; the Booking list equals
    `placement(wid)`."""
    got = assert_invariants(pg, wid)
    assert seats_of(got) == expect, got
    if left is not None:
        assert state(pg, wid)["left"] == left
    windows = booking_list(admin, date=DAY)["windows"]
    for other in windows:  # every Window of the day carries its own placement(wid)
        assert [(p["sauna"]["id"], p["state"], p["seats"]) for p in other["placement"]] == placement(pg, other["id"])
    [w] = [w for w in windows if w["id"] == wid]
    assert [(p["sauna"]["id"], p["state"], p["seats"]) for p in w["placement"]] == got
    assert sum(p["seats"] for p in w["placement"] if p["state"] == OPEN) == w["seats_booked"]
    whole = dict(rows(pg, "SELECT wb.sauna_id, b.reference FROM whole_bookings wb JOIN bookings b "
                          "ON b.id = wb.booking_id WHERE wb.window_id = %s", (wid,)))
    for p in w["placement"]:
        sid = p["sauna"]["id"]
        assert (p["sauna"]["name"], p["capacity"]) == (NAMES[sid], CAPACITY[sid])
        assert p["reference"] == (whole[sid] if p["state"] == WHOLE else None)
    return got


def seats(client, n: int, wid: int = 1) -> None:
    """Book `n` Seats through the Guest flow, at most 10 per Booking."""
    while n:
        k = min(n, 10)
        r = client.book(wid, k)
        assert r.status_code == 201, r.text
        n -= k


# ------------------------------------------------------------------ the reference and the checker bite


def test_the_checker_finds_every_broken_invariant():
    r = Raw(saunas=[(1, 7), (2, 10), (3, 12), (4, 15)], booked=9, held=0, whole={2}, blocked={3})
    good = brute_force(r)
    assert good == [(1, OPEN, 7), (2, WHOLE, 0), (3, BLOCKED, 0), (4, OPEN, 2)]
    assert violations(good, r) == []
    bad = {
        "INV-1": [(1, OPEN, 8), (2, WHOLE, 0), (3, BLOCKED, 0), (4, OPEN, 1)],
        "INV-2": [(1, OPEN, 7), (2, WHOLE, 0), (3, BLOCKED, 0), (4, OPEN, 3)],
        "INV-3": [(1, OPEN, 7), (2, WHOLE, 2), (3, BLOCKED, 0), (4, OPEN, 0)],
        "INV-4": [(1, OPEN, 7), (2, WHOLE, 0), (3, BLOCKED, 2), (4, OPEN, 0)],
        "INV-5": [(1, OPEN, 6), (2, WHOLE, 0), (3, BLOCKED, 0), (4, OPEN, 3)],
    }
    for inv, placed in bad.items():
        found = violations(placed, r)
        assert any(v.startswith(inv) for v in found), (inv, found)
    assert violations([(2, WHOLE, 0), (1, OPEN, 7), (3, BLOCKED, 0), (4, OPEN, 2)], r)  # not in Fill order
    assert violations([(1, OPEN, 7), (2, OPEN, 0), (3, BLOCKED, 0), (4, OPEN, 2)], r)  # wrong state
    marked = Raw(saunas=[(1, 7), (2, 10)], booked=3, held=0, marked={1})
    assert brute_force(marked) == [(1, MARKED, 0), (2, OPEN, 3)]
    assert violations([(1, MARKED, 3), (2, OPEN, 0)], marked)


def test_placement_is_read_only_and_one_row_per_sauna_in_fill_order(world, pg):
    assert placement(pg, 1) == [(1, OPEN, 0), (2, OPEN, 0), (3, OPEN, 0), (4, OPEN, 0)]
    assert placement(pg, 999) == []
    volatility = rows(pg, "SELECT provolatile FROM pg_proc WHERE proname = 'placement'")
    assert volatility == [("v",)]


# ------------------------------------------------------------------ FR-31 catalogue, group A


def test_a1(far, group, admin, pg):
    seats(group, 5)
    check(pg, admin, [5, 0, 0, 0], 39)
    seats(group, 4)
    check(pg, admin, [7, 2, 0, 0], 35)


def a2(group, admin, pg) -> str:
    seats(group, 17)
    ref, _ = opened(group, 1, 5)
    check(pg, admin, [7, 10, 5, 0], 22)
    assert give_up(group, ref, 3).status_code == 200
    check(pg, admin, [7, 10, 2, 0], 25)
    return ref


def test_a2(far, group, admin, pg):
    a2(group, admin, pg)


def test_a3(far, group, admin, pg):
    ref = a2(group, admin, pg)
    assert "Kajo" not in listed(group, 1)
    assert give_up(group, ref, 2, version=1).status_code == 200  # the rest of the Booking, cancelled for a Voucher
    check(pg, admin, [7, 10, 0, 0], 27)
    assert "Kajo" in listed(group, 1)


def test_a4(far, group, admin, pg):
    seats(group, 17)
    ref, _ = opened(group, 1, 5)
    check(pg, admin, [7, 10, 5, 0])
    assert give_up(group, ref, 2).status_code == 200
    check(pg, admin, [7, 10, 3, 0], 24)


def test_a5(far, group, admin, pg):
    seats(group, 27)
    ref, _ = opened(group, 1, 5)
    check(pg, admin, [7, 10, 12, 3], 12)
    assert give_up(group, ref, 5).status_code == 200  # Lumo empties first, then Kajo gives up 2
    check(pg, admin, [7, 10, 10, 0], 17)


def test_a8(far, group, admin, pg):
    seats(group, 18)
    ref, _ = opened(group, 1, 4)
    check(pg, admin, [7, 10, 5, 0])
    assert give_up(group, ref, 1).status_code == 200
    check(pg, admin, [7, 10, 4, 0], 23)


# ------------------------------------------------------------------ FR-31 catalogue, group B


def test_b4(far, group, admin, pg):
    assert book_whole(group, 1, RAUHA).status_code == 201
    check(pg, admin, [None, 0, 0, 0], 37)
    for n, expect in ((10, [None, 10, 0, 0]), (10, [None, 10, 10, 0]), (10, [None, 10, 12, 8]),
                      (7, [None, 10, 12, 15])):
        seats(group, n)
        check(pg, admin, expect)
    assert state(pg)["left"] == 0
    r = group.book(1, 1)
    assert r.status_code == 409 and r.json()["detail"]["error"] == "no_seat_free", r.text
    got = check(pg, admin, [None, 10, 12, 15], 0)
    assert got[0] == (RAUHA, WHOLE, 0)


def test_b5(far, group, admin, pg):
    assert book_whole(group, 1, LOYLY).status_code == 201
    check(pg, admin, [0, None, 0, 0], 34)
    seats(group, 9)
    check(pg, admin, [7, None, 2, 0], 25)


def test_b6(far, group, admin, pg):
    ref, _ = whole_opened(group, 1, LOYLY)
    seats(group, 23)
    check(pg, admin, [7, None, 12, 4], 11)
    r = cancel(group, ref, "refund")
    assert r.status_code == 200, r.text
    check(pg, admin, [7, 10, 6, 0], 21)


# ------------------------------------------------------------------ states, Holds and access


def test_blocked_and_marked_saunas_count_none_and_a_released_mark_is_open(admin, pg):
    """Raw rows (AD-21) at `EARLY`, before the 06:00 Release time: a Block on Kajo, a mark on Lumo."""
    pg.execute(raw_booking(1, 12))
    pg.execute("INSERT INTO blocks (sauna_id, during) SELECT %s, during FROM windows WHERE id = 1", (KAJO,))
    pg.execute("INSERT INTO marks (window_id, sauna_id) VALUES (1, %s)", (LUMO,))
    pg.commit()
    got = check(pg, admin, [7, 5, 0, 0], 5)
    assert [s for _, s, _ in got] == [OPEN, OPEN, BLOCKED, MARKED]
    set_clock(pg, dt.datetime(2026, 12, 1, 5, 30, tzinfo=dt.timezone.utc))  # 06:30 Oslo: the mark is released
    got = check(pg, admin, [7, 5, 0, 0], 20)
    assert [s for _, s, _ in got] == [OPEN, OPEN, BLOCKED, OPEN]


def test_seats_fill_past_a_blocked_sauna(admin, pg):
    pg.execute("INSERT INTO blocks (sauna_id, during) SELECT %s, during FROM windows WHERE id = 1", (LOYLY,))
    pg.execute(raw_booking(1, 20))
    pg.commit()
    check(pg, admin, [7, 0, 12, 1], 14)


def test_a_block_over_a_whole_sauna_booking_still_shows_the_booking(admin, pg):
    bid = raw_whole(pg, 1, KAJO)
    pg.execute("INSERT INTO blocks (sauna_id, during) SELECT %s, during FROM windows WHERE id = 1", (KAJO,))
    pg.commit()
    got = check(pg, admin, [0, 0, None, 0], 32)
    assert got[2] == (KAJO, WHOLE, 0)
    [w] = [w for w in booking_list(admin, date=DAY)["windows"] if w["id"] == 1]
    assert w["placement"][2]["reference"] == rows(pg, "SELECT reference FROM bookings WHERE id = %s", (bid,))[0][0]


def test_holds_are_not_placed(api, admin, pg):
    assert api.post("/api/holds", json={"window_id": 1, "seats": 3}).status_code == 200
    check(pg, admin, [0, 0, 0, 0], 41)


def test_every_window_of_the_date_carries_placement(admin, pg):
    ws = booking_list(admin, date=DAY)["windows"]
    assert ws and all([p["sauna"]["name"] for p in w["placement"]] == [n for _, n, _ in SAUNAS] for w in ws)


@pytest.mark.parametrize("who", ["anonymous", "guest"])
def test_anonymous_and_guest_callers_get_401_and_no_placement(world, pg, who):
    pg.execute(raw_booking(1, 5))
    pg.commit()
    with api_client(world, session=who == "guest") as c:
        r = c.get("/api/admin/bookings", params={"date": DAY})
    assert r.status_code == 401 and r.json() == NOT_SIGNED_IN
    assert "placement" not in r.text
