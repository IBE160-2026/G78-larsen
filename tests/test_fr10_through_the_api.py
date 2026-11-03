"""FR-10, FR-11, FR-12 against the real stack: real HTTP, the real API process, the real connection pool and PostgreSQL.

Parallel requests are real threads sending real HTTP requests. Every response must be a definite answer
(200/201 or 409): a 5xx would be a deadlock or error that leaked out (FR-14).
"""

from __future__ import annotations

import datetime as dt
import random
import threading
from concurrent.futures import ThreadPoolExecutor

import httpx
import psycopg

from conftest import EARLY, clear, set_clock, state, win_start

ROUNDS = 100  # FR-11: 100 repetitions per run


def parallel(fns):
    """Start all calls at (nearly) the same moment and return their results in order."""
    barrier = threading.Barrier(len(fns))

    def go(fn):
        barrier.wait()
        return fn()

    with ThreadPoolExecutor(len(fns)) as ex:
        return [f.result() for f in [ex.submit(go, fn) for fn in fns]]


def book(base, seats, sid, wid=1):
    with httpx.Client(base_url=base, timeout=30) as c:
        return c.post("/bookings", json=dict(window_id=wid, seats=seats, session_id=sid, guest=sid))


def hold(base, seats, sid, wid=1):
    with httpx.Client(base_url=base, timeout=30) as c:
        return c.post("/holds", json=dict(window_id=wid, seats=seats, session_id=sid))


def fill(api, n, wid=1):
    """Book n Seats in Bookings of at most 10."""
    todo, k = n, 0
    while todo:
        part = min(10, todo)
        assert api.post("/bookings", json=dict(window_id=wid, seats=part, session_id=f"fill{k}")).status_code == 201
        todo -= part
        k += 1


def left(api, wid=1):
    return api.get(f"/windows/{wid}").json()["seats_left"]


def test_seats_left_is_capacity_at_start(api):
    assert left(api) == 44


def test_parallel_requests_never_book_more_than_is_left(api, world, pg):
    """FR-10 bullet 1: many requests together ask for more than is left; the Seats accepted never exceed it."""
    for r in range(20):
        clear(pg)
        res = parallel([lambda i=i: book(world, 5, f"s{r}-{i}") for i in range(12)])  # 60 Seats asked, 44 exist
        odd = [x.text for x in res if x.status_code not in (201, 409)]
        assert not odd, f"round {r}: {odd}"
        accepted = sum(5 for x in res if x.status_code == 201)
        assert accepted == 40, f"round {r}: accepted {accepted}"  # eight fit, a ninth would make 45
        assert all(x.json()["detail"]["error"] == "no_seat_free" for x in res if x.status_code == 409)
        s = state(pg)
        assert s["booked"] == s["real_booked"] == accepted and s["left"] == 44 - accepted >= 0


def test_the_last_seat_has_exactly_one_winner(api, world, pg):
    """FR-11: two parallel requests for the one remaining Seat create exactly one Booking. 100 repetitions."""
    for r in range(ROUNDS):
        clear(pg)
        fill(api, 43)
        assert left(api) == 1
        a, b = parallel([lambda: book(world, 1, f"A{r}"), lambda: book(world, 1, f"B{r}")])
        assert sorted([a.status_code, b.status_code]) == [201, 409], (r, a.text, b.text)
        assert left(api) == 0
        assert state(pg)["booked"] == 44


def test_a_request_for_more_than_is_left_is_rejected_as_a_whole(api, pg):
    """FR-12: 42 of 44 booked, a request for 3 is rejected and nothing changes; with all 44 booked, 1 is rejected."""
    fill(api, 42)
    r = api.post("/bookings", json=dict(window_id=1, seats=3, session_id="x"))
    assert r.status_code == 409 and r.json()["detail"]["error"] == "no_seat_free"
    assert left(api) == 2 and state(pg)["real_booked"] == 42
    assert api.post("/bookings", json=dict(window_id=1, seats=2, session_id="y")).status_code == 201
    r = api.post("/bookings", json=dict(window_id=1, seats=1, session_id="z"))
    assert r.status_code == 409 and left(api) == 0


def test_two_guests_holding_the_last_seat_one_hold_succeeds(api, world, pg):
    """FR-35 / CT-1."""
    for r in range(50):
        clear(pg)
        fill(api, 43)
        a, b = parallel([lambda: hold(world, 1, f"A{r}"), lambda: hold(world, 1, f"B{r}")])
        assert sorted([a.status_code, b.status_code]) == [200, 409], (r, a.text, b.text)
        assert left(api) == 0 and state(pg)["real_held"] == 1


def test_late_payment_races_another_guests_hold_for_the_last_seat(api, world, pg):
    """FR-36: a payment after its Hold expired, in parallel with another Guest's Hold for the same last Seat:
    exactly one of them gets the Seat."""
    for r in range(50):
        clear(pg)
        set_clock(pg, EARLY)
        fill(api, 43)
        assert hold(world, 1, "A").status_code == 200  # A holds the last Seat
        set_clock(pg, EARLY + dt.timedelta(minutes=11))  # A's Hold has expired; no cleanup has run
        assert left(api) == 1
        pay, other = parallel([lambda: book(world, 1, "A"), lambda: hold(world, 1, "B")])
        won = sorted([pay.status_code in (200, 201), other.status_code in (200, 201)])
        assert won == [False, True], (r, pay.text, other.text)
        s = state(pg)
        assert s["real_booked"] + s["real_held"] == 44 and s["left"] == 0, s


def test_a_hold_expires_without_any_cleanup(api, pg):
    """FR-35: after expiry, other Guests can book those Seats, and Seats left shows them again."""
    for k in range(4):
        n = 10 if k < 3 else 14
        assert api.post("/holds", json=dict(window_id=1, seats=n, session_id=f"h{k}")).status_code == 200
    assert left(api) == 0
    assert api.post("/bookings", json=dict(window_id=1, seats=1, session_id="late")).status_code == 409
    set_clock(pg, EARLY + dt.timedelta(minutes=10, seconds=5))
    assert left(api) == 44
    assert pg.execute("SELECT count(*) FROM holds").fetchone()[0] == 4  # the rows are still there
    assert api.post("/bookings", json=dict(window_id=1, seats=44, session_id="late")).status_code == 201


def test_mixed_load_keeps_every_window_consistent(api, world, pg, database):
    """A random mix of Seat bookings, Holds, Whole-sauna bookings, Blocks, marks and a moving clock, sent in
    parallel over HTTP. No 5xx, and after every round the store's numbers equal the numbers derived from the rows.
    A monitor reads in a repeatable-read snapshot throughout and must never see a Window over capacity."""
    clear(pg)
    dsn = database
    bad_snapshots: list = []
    looks = [0]
    crashed: list = []
    stop = threading.Event()

    def monitor():
        try:
            with psycopg.connect(dsn) as mc:
                mc.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
                while not stop.is_set():
                    rows = mc.execute(
                        "SELECT id, window_booked_seats(id), window_open_capacity(id) FROM windows").fetchall()
                    mc.rollback()
                    looks[0] += 1
                    bad_snapshots.extend((wid, bk, cap) for wid, bk, cap in rows if bk > cap)
        except Exception as e:  # noqa - a dead monitor must fail the test, not pass it silently
            crashed.append(e)

    mt = threading.Thread(target=monitor)
    mt.start()
    statuses: list[int] = []
    lock = threading.Lock()

    def one(i):
        r = random.Random(i)
        with httpx.Client(base_url=world, timeout=60) as c:
            for _ in range(25):
                w = r.randint(1, 3)
                kind = r.choice(["book", "book", "hold", "hold", "whole", "block", "unmark", "mark", "lift", "cancel"])
                s = f"w{i}-{r.randint(0, 3)}"
                if kind == "book":
                    x = c.post("/bookings", json=dict(window_id=w, seats=r.randint(1, 6), session_id=s))
                elif kind == "hold":
                    x = c.post("/holds", json=dict(window_id=w, seats=r.randint(1, 6), session_id=s))
                elif kind == "cancel":
                    x = c.delete("/holds", params=dict(window_id=w, session_id=s))
                elif kind == "whole":
                    x = c.post("/whole-bookings", json=dict(window_id=w, sauna_id=r.randint(1, 4)))
                elif kind == "block":
                    st = win_start(r.randint(0, 2))
                    x = c.post("/blocks", json=dict(sauna_id=r.randint(1, 4), start=st.isoformat(),
                                                    end=(st + dt.timedelta(minutes=90)).isoformat()))
                elif kind == "lift":
                    x = c.delete(f"/blocks/{r.randint(1, 30)}")
                elif kind == "mark":
                    x = c.post("/marks", json=dict(window_id=w, sauna_id=r.randint(1, 4)))
                else:
                    x = c.delete("/marks", params=dict(window_id=w, sauna_id=r.randint(1, 4)))
                with lock:
                    statuses.append(x.status_code)

    try:
        for rnd_i in range(4):
            with ThreadPoolExecutor(8) as ex:
                list(ex.map(one, range(rnd_i * 8, rnd_i * 8 + 8)))
            set_clock(pg, EARLY + dt.timedelta(minutes=20 * (rnd_i + 1)))
            for wid in (1, 2, 3):
                s = state(pg, wid)
                assert s["booked"] == s["real_booked"], (wid, s)
                assert s["held"] >= s["real_held"], (wid, s)
                assert s["booked"] + s["held"] <= s["cap"], (wid, s)
                assert s["left"] >= 0, (wid, s)
    finally:
        stop.set()
        mt.join()
    bad = sorted({c for c in statuses if c >= 500 or c not in (200, 201, 409, 404, 422)})
    assert not bad, f"unexpected statuses: {bad}"
    assert not crashed, crashed
    assert looks[0] > 20, f"the monitor only looked {looks[0]} times"
    assert not bad_snapshots, bad_snapshots[:5]
    assert 201 in statuses and 409 in statuses  # the load really did both accept and refuse
