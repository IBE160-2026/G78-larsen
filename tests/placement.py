"""FR-31 / AD-6 / AD-25: the brute-force reference Placement and the INV-1 to INV-5 checker (Story 5.4), shared with
Story 5.5.

The store's `placement(wid)` is the only computation of Placement in the product. This module is the one other: a
plain Python Placement worked out from the raw store rows (the Saunas, the active Seat bookings, the Whole-sauna
capacity rows, the Blocks and, through `mark_closed`, the marks, releases and clock), used only as the reference the
tests compare `placement(wid)` with.

- `raw(pg, wid)` reads those rows in one REPEATABLE READ snapshot; `brute_force(r)` places the booked Seats (never Holds) greedily in
  Fill order over the open Saunas; `violations(rows, r)` lists every broken invariant of a Placement.
- `assert_invariants(pg, wid)` reads `placement(wid)` and the raw rows in one snapshot and asserts that INV-1 to INV-5
  hold, that `placement(wid)` equals the brute force, and that `seats_left(wid)` equals the open Capacity minus the
  booked and held Seats.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import psycopg

OPEN, WHOLE, BLOCKED, MARKED = "open", "whole", "blocked", "marked"


@dataclass
class Raw:
    """The raw rows of one Window that Placement is derived from."""
    saunas: list[tuple[int, int]]  # (sauna_id, capacity) in Fill order
    booked: int  # Seats of the active Seat bookings
    held: int  # Seats of the unexpired Holds
    whole: set[int] = field(default_factory=set)  # Saunas with a `whole_bookings` row
    blocked: set[int] = field(default_factory=set)  # Saunas with a Block overlapping the Window
    marked: set[int] = field(default_factory=set)  # Saunas with `mark_closed(wid, sid)`

    def state(self, sid: int) -> str:
        if sid in self.whole:
            return WHOLE
        if sid in self.blocked:
            return BLOCKED
        if sid in self.marked:
            return MARKED
        return OPEN


def _read_raw(pg: psycopg.Connection, wid: int) -> Raw:
    saunas = pg.execute("SELECT id, capacity FROM saunas ORDER BY fill_order").fetchall()
    booked = pg.execute("SELECT COALESCE(SUM(seats), 0) FROM bookings WHERE window_id = %s AND kind = 'seats' "
                        "AND status = 'active'", (wid,)).fetchone()[0]
    held = pg.execute("SELECT COALESCE(SUM(seats), 0) FROM holds WHERE window_id = %s AND expires_at > app_now()",
                      (wid,)).fetchone()[0]
    whole = {r[0] for r in pg.execute("SELECT sauna_id FROM whole_bookings WHERE window_id = %s", (wid,))}
    w_lo, w_hi = pg.execute("SELECT lower(during), upper(during) FROM windows WHERE id = %s", (wid,)).fetchone()
    # Both are '[)' ranges: they overlap when each starts before the other ends.
    blocked = {sid for sid, lo, hi in pg.execute("SELECT sauna_id, lower(during), upper(during) FROM blocks")
               if (lo is None or lo < w_hi) and (hi is None or w_lo < hi)}
    marked = {sid for (sid,) in pg.execute("SELECT sauna_id FROM marks WHERE window_id = %s AND mark_closed(%s, sauna_id)",
                                           (wid, wid))}
    return Raw(saunas=[(s, c) for s, c in saunas], booked=int(booked), held=int(held), whole=whole, blocked=blocked,
               marked=marked)


def raw(pg: psycopg.Connection, wid: int) -> Raw:
    """The raw rows of Window `wid`, read in one snapshot (the caller's open transaction is rolled back first)."""
    pg.rollback()
    pg.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")  # one snapshot for every statement
    try:
        return _read_raw(pg, wid)
    finally:
        pg.rollback()


def brute_force(r: Raw) -> list[tuple[int, str, int]]:
    """(sauna_id, state, seats) per Sauna in Fill order: the booked Seats fill the open Saunas one by one."""
    left = r.booked
    out = []
    for sid, cap in r.saunas:
        state = r.state(sid)
        seats = 0
        if state == OPEN:
            seats = min(cap, left)
            left -= seats
        out.append((sid, state, seats))
    return out


def violations(rows: list[tuple[int, str, int]], r: Raw) -> list[str]:
    """Every invariant the Placement `rows` breaks against the raw rows `r` (empty when all hold)."""
    out = []
    caps = dict(r.saunas)
    if [sid for sid, _, _ in rows] != [sid for sid, _ in r.saunas]:
        out.append(f"not one row per Sauna in Fill order: {rows}")
        return out
    for sid, state, seats in rows:
        if state != r.state(sid):
            out.append(f"Sauna {sid} is {state}, its rows say {r.state(sid)}")
        if not 0 <= seats <= caps[sid]:
            out.append(f"INV-1: Sauna {sid} holds {seats} of {caps[sid]}")
        if sid in r.whole and seats:
            out.append(f"INV-3: Sauna {sid} is booked whole and holds {seats}")
        if sid in r.blocked and seats:
            out.append(f"INV-4: Sauna {sid} is Blocked and holds {seats}")
        if state != OPEN and seats:
            out.append(f"Sauna {sid} is {state} and holds {seats}")
    placed = sum(seats for _, _, seats in rows)
    if placed != r.booked:
        out.append(f"INV-2: {placed} Seats placed, {r.booked} booked")
    open_rows = [(sid, seats) for sid, state, seats in rows if state == OPEN]
    for i, (sid, seats) in enumerate(open_rows):
        if seats < caps[sid]:
            later = [(s, n) for s, n in open_rows[i + 1:] if n]
            if later:
                out.append(f"INV-5: Sauna {sid} has room ({seats} of {caps[sid]}) while later Saunas hold {later}")
    return out


def placement(pg: psycopg.Connection, wid: int) -> list[tuple[int, str, int]]:
    """`placement(wid)` as the store returns it."""
    pg.rollback()
    pg.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")  # one snapshot for every statement
    try:
        return [tuple(row) for row in pg.execute("SELECT sauna_id, state, seats FROM placement(%s)", (wid,))]
    finally:
        pg.rollback()


def seats_of(rows: list[tuple[int, str, int]]) -> list[int | None]:
    """`[a, b, c, d]` as the catalogue writes it: the Seats per Sauna, None for a Sauna booked whole."""
    return [None if state == WHOLE else seats for _, state, seats in rows]


def assert_invariants(pg: psycopg.Connection, wid: int) -> list[tuple[int, str, int]]:
    """INV-1 to INV-5 on `placement(wid)` against the raw rows, `placement(wid) == brute_force`, and Seats left; all
    read in one snapshot. Returns the Placement."""
    pg.rollback()
    pg.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")  # one snapshot for every statement
    try:
        rows = [tuple(row) for row in pg.execute("SELECT sauna_id, state, seats FROM placement(%s)", (wid,))]
        r = _read_raw(pg, wid)
        left = pg.execute("SELECT seats_left(%s)", (wid,)).fetchone()[0]
    finally:
        pg.rollback()
    problems = violations(rows, r)
    assert not problems, problems
    assert rows == brute_force(r), (rows, brute_force(r))
    open_capacity = sum(cap for sid, cap in r.saunas if r.state(sid) == OPEN)
    assert left == open_capacity - r.booked - r.held, (left, open_capacity, r.booked, r.held)
    return rows
