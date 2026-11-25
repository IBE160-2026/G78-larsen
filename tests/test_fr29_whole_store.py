"""FR-29 / AD-2 / AD-23 / AD-24 (Story 5.1): the store's own Whole-sauna rules, written around the API.

- Pairing (AD-23): an active Whole-sauna booking has exactly one capacity row with its Window and Sauna, and a capacity
  row's Booking is an active Whole-sauna booking. The deferred triggers refuse the COMMIT with `whole_pairing`.
- Kind (AD-23): a Booking never changes its `kind` (`booking_kind_fixed`).
- FR-29 (AD-24): `trg_check_whole` refuses a capacity row that `whole_bookable` refuses, on INSERT and on a change of
  Window or Sauna, with `whole_bookable`, and nothing is written. The catalogue states are H12 (a started Window with
  29 Seats booked), B2 (Kajo holding Seats, 20 booked) and B3 (Rauha holding the 1 Seat booked).

Each case turns red under its `MUTATIONS` entry in `tests/conftest.py`: `no_pairing_bookings`, `no_pairing_whole`,
`no_kind_fixed`, `no_whole_check` (INSERT) and `no_whole_check_update` (UPDATE). Run one with
`BP_TEST_MUTATE=<name> uv run pytest tests/test_fr29_whole_store.py`.
"""

from __future__ import annotations

import datetime as dt

import pytest
from psycopg import errors

from conftest import raw_booking, raw_whole, set_clock, state, win_start

REF = "upper(substr(md5(random()::text || clock_timestamp()::text), 1, 8))"
WHOLE_BOOKING = ("INSERT INTO bookings (window_id, kind, sauna_id, reference, name, email, total_ore, cutoff) "
                 f"VALUES (%s, 'whole', %s, {REF}, 'Raw Group', 'raw@example.com', 395000, interval '72 hours') "
                 "RETURNING id")


def refused_at_commit(pg, statements, constraint: str) -> None:
    """Run the statements in one transaction; the store refuses it (at a statement or at COMMIT) by `constraint`."""
    with pytest.raises(errors.CheckViolation) as e:
        for sql, params in statements:
            pg.execute(sql, params)
        pg.commit()
    pg.rollback()
    assert e.value.diag.constraint_name == constraint, e.value.diag.constraint_name


def book_raw(pg, wid: int, seats: int) -> None:
    pg.execute(raw_booking(wid, seats))
    pg.commit()


def whole_rows(pg) -> tuple:
    pg.rollback()
    row = pg.execute("SELECT (SELECT count(*) FROM whole_bookings), "
                     "(SELECT count(*) FROM bookings WHERE kind = 'whole')").fetchone()
    pg.rollback()
    return tuple(row)


# ------------------------------------------------------------------ the paired shape (AD-23)


def test_raw_whole_writes_a_paired_whole_sauna_booking(world, pg):
    bid = raw_whole(pg, 1, 4)
    row = pg.execute("SELECT b.kind, b.seats, b.sauna_id, b.price_per_seat_ore, b.total_ore, b.cutoff, b.status, "
                     "wb.window_id, wb.sauna_id FROM bookings b JOIN whole_bookings wb ON wb.booking_id = b.id "
                     "WHERE b.id = %s", (bid,)).fetchone()
    pg.rollback()
    assert row == ("whole", None, 4, None, 395000, dt.timedelta(hours=72), "active", 1, 4)
    assert state(pg)["real_cap"] == 29 and state(pg)["real_booked"] == 0  # a Whole-sauna booking takes no Seats


@pytest.mark.parametrize("columns", [
    "seats = 2",  # a Whole-sauna booking has no Seats
    "sauna_id = NULL",  # and always a Sauna
    "price_per_seat_ore = 25000",  # and no price per Seat
])
def test_one_check_ties_kind_seats_sauna_and_price(world, pg, columns):
    bid = raw_whole(pg, 2, 4)
    refused_at_commit(pg, [(f"UPDATE bookings SET {columns} WHERE id = %s", (bid,))], "bookings_kind_shape")


def test_a_seat_booking_has_1_to_10_seats_and_no_sauna(world, pg):
    for values in ("1, 'seats', 11, NULL, 25000, 275000", "1, 'seats', 2, 4, 25000, 50000",
                   "1, 'seats', 2, NULL, NULL, 50000", "1, 'other', NULL, 4, NULL, 50000"):
        refused_at_commit(pg, [(
            "INSERT INTO bookings (window_id, kind, seats, sauna_id, price_per_seat_ore, total_ore, reference, name, "
            f"email) VALUES ({values}, {REF}, 'Raw', 'raw@example.com')", ())], "bookings_kind_shape")


# ------------------------------------------------------------------ pairing (AD-23); mutations no_pairing_*


def test_an_active_whole_sauna_booking_without_its_capacity_row_is_refused_at_commit(world, pg):
    refused_at_commit(pg, [(WHOLE_BOOKING, (1, 4))], "whole_pairing")  # no_pairing_bookings
    assert whole_rows(pg) == (0, 0)


def test_a_booking_moved_without_its_capacity_row_is_refused_at_commit(world, pg):
    bid = raw_whole(pg, 1, 4)
    refused_at_commit(pg, [("UPDATE bookings SET window_id = 2 WHERE id = %s", (bid,))],
                      "whole_pairing")  # no_pairing_bookings
    refused_at_commit(pg, [("UPDATE bookings SET sauna_id = 3 WHERE id = %s", (bid,))], "whole_pairing")


def test_a_capacity_row_with_another_window_or_sauna_is_refused_at_commit(world, pg):
    bid = raw_whole(pg, 1, 4)
    refused_at_commit(pg, [("UPDATE whole_bookings SET sauna_id = 3 WHERE booking_id = %s", (bid,))],
                      "whole_pairing")  # no_pairing_whole
    refused_at_commit(pg, [("UPDATE whole_bookings SET window_id = 2 WHERE booking_id = %s", (bid,))],
                      "whole_pairing")
    b2 = pg.execute(WHOLE_BOOKING, (2, 3)).fetchone()[0]  # a row for another Window and Sauna than its Booking's
    refused_at_commit(pg, [("INSERT INTO whole_bookings (window_id, sauna_id, booking_id) VALUES (2, 4, %s)", (b2,))],
                      "whole_pairing")
    assert whole_rows(pg) == (1, 1)


def test_a_move_of_booking_and_row_together_is_accepted(world, pg):
    """The write order of AD-23: `bookings` first, then `whole_bookings`, judged at COMMIT."""
    bid = raw_whole(pg, 1, 4)
    pg.execute("UPDATE bookings SET window_id = 2, sauna_id = 3 WHERE id = %s", (bid,))
    pg.execute("UPDATE whole_bookings SET window_id = 2, sauna_id = 3 WHERE booking_id = %s", (bid,))
    pg.commit()
    assert pg.execute("SELECT window_id, sauna_id FROM whole_bookings").fetchall() == [(2, 3)]
    pg.rollback()
    assert state(pg, 1)["real_cap"] == 44 and state(pg, 2)["real_cap"] == 32


def test_a_capacity_row_of_a_cancelled_booking_is_refused_at_commit(world, pg):
    bid = raw_whole(pg, 1, 4)
    cancel = ("UPDATE bookings SET status = 'cancelled', cancelled_at = app_now(), cancel_cause = 'block' "
              "WHERE id = %s")
    refused_at_commit(pg, [(cancel, (bid,))], "whole_pairing")  # no_pairing_bookings
    # the order of AD-23: the status first, then the row goes; the Sauna opens for Seats again
    pg.execute(cancel, (bid,))
    pg.execute("DELETE FROM whole_bookings WHERE booking_id = %s", (bid,))
    pg.commit()
    assert whole_rows(pg) == (0, 1) and state(pg)["real_cap"] == 44


def test_a_whole_sauna_booking_may_be_cancelled_by_the_guest_with_a_refund(world, pg):
    """FR-33, AD-31: 0013 limits 0012's `seat_guest_refund_forbidden` to Seat bookings. In AD-23's order (status, then
    the capacity row) a Guest's cancellation with remedy `refund` commits; a Seat booking with the same values is
    still refused."""
    bid = raw_whole(pg, 1, 4)
    cancel = ("UPDATE bookings SET status = 'cancelled', cancelled_at = app_now(), cancel_cause = 'guest', "
              "cancel_remedy = 'refund' WHERE id = %s")
    pg.execute(cancel, (bid,))
    pg.execute("DELETE FROM whole_bookings WHERE booking_id = %s", (bid,))
    pg.commit()
    assert pg.execute("SELECT status, cancel_cause, cancel_remedy FROM bookings WHERE id = %s", (bid,)).fetchone() == (
        "cancelled", "guest", "refund")
    pg.rollback()
    assert whole_rows(pg) == (0, 1) and state(pg)["real_cap"] == 44
    seat = pg.execute(raw_booking(1, 2) + " RETURNING id").fetchone()[0]
    pg.commit()
    refused_at_commit(pg, [(cancel, (seat,))], "seat_guest_refund_forbidden")


def test_a_capacity_row_of_a_seat_booking_is_refused_at_commit(world, pg):
    sid = pg.execute(raw_booking(2, 1) + " RETURNING id").fetchone()[0]
    pg.commit()
    refused_at_commit(pg, [("INSERT INTO whole_bookings (window_id, sauna_id, booking_id) VALUES (2, 4, %s)", (sid,))],
                      "whole_pairing")  # no_pairing_whole
    assert whole_rows(pg) == (0, 0)


def test_deleting_the_capacity_row_of_an_active_booking_is_refused_at_commit(world, pg):
    bid = raw_whole(pg, 1, 4)
    refused_at_commit(pg, [("DELETE FROM whole_bookings WHERE booking_id = %s", (bid,))],
                      "whole_pairing")  # no_pairing_whole
    assert whole_rows(pg) == (1, 1) and state(pg)["real_cap"] == 29


# ------------------------------------------------------------------ kind (AD-23); mutation no_kind_fixed


def test_a_booking_never_changes_its_kind(world, pg):
    seat = pg.execute(raw_booking(2, 2) + " RETURNING id").fetchone()[0]
    pg.commit()
    refused_at_commit(pg, [("UPDATE bookings SET kind = 'whole', seats = NULL, price_per_seat_ore = NULL, "
                            "sauna_id = 4 WHERE id = %s", (seat,))], "booking_kind_fixed")
    bid = raw_whole(pg, 1, 4)
    # the capacity row goes in the same transaction, so only the kind can be refused
    refused_at_commit(pg, [("DELETE FROM whole_bookings WHERE booking_id = %s", (bid,)),
                           ("UPDATE bookings SET kind = 'seats', seats = 2, price_per_seat_ore = 25000, "
                            "sauna_id = NULL WHERE id = %s", (bid,))], "booking_kind_fixed")
    assert pg.execute("SELECT kind FROM bookings ORDER BY id").fetchall() == [("seats",), ("whole",)]
    pg.rollback()


# ------------------------------------------------------------------ FR-29 on INSERT (AD-24); mutation no_whole_check


def _h12(pg):
    book_raw(pg, 1, 29)  # [7, 10, 12, 0]
    set_clock(pg, win_start(0) + dt.timedelta(minutes=2))  # started, before its Booking deadline
    return 4  # Lumo: Room ahead 29 fits, but the Window has started and has Seat bookings


def _b2(pg):
    book_raw(pg, 1, 20)  # [7, 10, 3, 0]
    return 3  # Kajo holds 3 Seats


def _b3(pg):
    book_raw(pg, 1, 1)
    return 1  # Rauha holds the Seat


def _held(pg):
    pg.execute("INSERT INTO holds (window_id, seats, session_id, expires_at) VALUES (1, 20, NULL, app_now() + interval '5 minutes')")
    pg.commit()
    return 3  # Kajo would take 3 of the 20 held Seats


def _no_price(pg):
    pg.execute("UPDATE saunas SET whole_price_ore = NULL WHERE id = 4")
    pg.commit()
    return 4


def _blocked(pg):
    pg.execute("INSERT INTO blocks (sauna_id, during) SELECT 4, during FROM windows WHERE id = 1")
    pg.commit()
    return 4


@pytest.mark.parametrize("setup", [_h12, _b2, _b3, _held, _no_price, _blocked],
                         ids=["H12", "B2", "B3", "held", "no_price", "blocked"])
def test_the_store_refuses_a_capacity_row_whole_bookable_refuses(world, pg, setup):
    sauna = setup(pg)
    before = state(pg)
    with pytest.raises(errors.CheckViolation) as e:
        raw_whole(pg, 1, sauna)
    assert e.value.diag.constraint_name == "whole_bookable"
    assert whole_rows(pg) == (0, 0) and state(pg) == before


def test_whole_bookable_agrees_with_the_trigger(world, pg):
    book_raw(pg, 1, 20)
    got = [r[0] for r in pg.execute("SELECT whole_bookable(1, s.id) FROM saunas s ORDER BY fill_order").fetchall()]
    pg.rollback()
    assert got == [False, False, False, True]
    bid = raw_whole(pg, 1, 4)
    # booked whole now, except when the judged Booking is the one that holds it (a move keeps its own Sauna)
    assert pg.execute("SELECT whole_bookable(1, 4), whole_bookable(1, 4, %s)", (bid,)).fetchone() == (False, True)
    pg.rollback()


def test_a_marked_unreleased_sauna_skips_the_seat_tests(world, pg):
    """FR-29: a Sauna marked Whole-booking-only and not yet released holds no Seats, so the Seats around it and a
    started Window do not stop it being booked whole."""
    pg.execute("INSERT INTO marks (window_id, sauna_id) VALUES (1, 4)")
    pg.commit()
    book_raw(pg, 1, 29)  # every Seat of the three open Saunas
    pg.execute("UPDATE settings SET release_on = false")  # so the mark stays closed after the clock moves
    pg.commit()
    set_clock(pg, win_start(0) + dt.timedelta(minutes=2))
    raw_whole(pg, 1, 4)
    assert whole_rows(pg) == (1, 1)


def test_a_marked_unreleased_sauna_needs_no_room_ahead(api, pg):
    """FR-29, the `mark_closed` branch of the room clause: Rauha, first in the Fill order, has no Room ahead, yet once
    it is marked and unreleased it holds no Seats, so the 30 Seats booked around it do not stop it. Listed by the API
    and accepted by the store."""
    pg.execute("INSERT INTO marks (window_id, sauna_id) VALUES (1, 1)")  # before 06:00 Oslo: unreleased
    pg.commit()
    book_raw(pg, 1, 30)  # [0, 10, 12, 8]: more than Rauha's Room ahead (0)
    assert pg.execute("SELECT window_booked_seats(1) > room_ahead(1, 1), mark_closed(1, 1)").fetchone() == (True, True)
    pg.rollback()
    r = api.get("/api/private-saunas", params=dict(date="2026-12-01"))
    assert r.status_code == 200, r.text
    assert any(w["id"] == 1 for s in r.json()["saunas"] if s["name"] == "Rauha" for w in s["windows"])
    raw_whole(pg, 1, 1)
    assert whole_rows(pg) == (1, 1)


# ------------------------------------------------------------------ FR-29 on UPDATE (AD-24); mutation no_whole_check_update


def _move(pg, bid: int, wid: int, sid: int) -> list:
    """A move in AD-23's write order: the Booking, then its capacity row with Window and Sauna together."""
    return [("UPDATE bookings SET window_id = %s, sauna_id = %s WHERE id = %s", (wid, sid, bid)),
            ("UPDATE whole_bookings SET window_id = %s, sauna_id = %s WHERE booking_id = %s", (wid, sid, bid))]


def test_the_store_refuses_a_move_into_a_started_window_with_seat_bookings_h12(world, pg):
    bid = raw_whole(pg, 2, 4)  # Lumo in the next Window
    book_raw(pg, 1, 29)
    set_clock(pg, win_start(0) + dt.timedelta(minutes=2))
    refused_at_commit(pg, _move(pg, bid, 1, 4), "whole_bookable")
    assert pg.execute("SELECT window_id, sauna_id FROM whole_bookings").fetchall() == [(2, 4)]
    pg.rollback()


def test_the_store_refuses_a_move_onto_a_sauna_holding_seats_b2_b3(world, pg):
    book_raw(pg, 1, 20)  # [7, 10, 3, 0]
    bid = raw_whole(pg, 1, 4)
    refused_at_commit(pg, _move(pg, bid, 1, 3), "whole_bookable")  # B2: Kajo holds Seats
    refused_at_commit(pg, _move(pg, bid, 1, 1), "whole_bookable")  # B3: Rauha holds Seats
    refused_at_commit(pg, [("UPDATE bookings SET sauna_id = 2 WHERE id = %s", (bid,)),
                           ("UPDATE whole_bookings SET sauna_id = 2 WHERE booking_id = %s", (bid,))],
                      "whole_bookable")  # the Sauna alone
    assert pg.execute("SELECT window_id, sauna_id FROM whole_bookings").fetchall() == [(1, 4)]
    pg.rollback()
    assert state(pg)["real_cap"] == 29


def test_a_move_judges_the_row_without_itself(world, pg):
    """`ignore_booking`: a capacity row is never judged against itself, so a move to another Window that keeps the
    Sauna is accepted when the target allows it."""
    bid = raw_whole(pg, 1, 4)
    for sql, params in _move(pg, bid, 3, 4):
        pg.execute(sql, params)
    pg.commit()
    assert pg.execute("SELECT window_id, sauna_id FROM whole_bookings").fetchall() == [(3, 4)]
    pg.rollback()
