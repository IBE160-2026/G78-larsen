"""The booking platform API: a thin Core slice built to run the FR-10 tests against a real stack.

Scope of this slice (everything else in the PRD is not built yet):
- Seats left, Holds (FR-35), Bookings that consume a Hold (FR-6/FR-36), Whole-sauna bookings (FR-29),
  Blocks (FR-40), Whole-booking-only marks and the Release time (FR-41), the Booking deadline and the
  Release time Settings (FR-39), bounded retry of temporary conflicts (FR-14).
- No sign-in: the Administrator endpoints are open (FR-15/FR-20 are not built). No payment, no email,
  no Booking horizon or Cutoffs, no Guest-facing text.

The application checks what it can, but the data store is the last word: every capacity rule is also
enforced by PostgreSQL itself (addendum A), so a bug or a bypass here cannot oversell a Window.
"""

from __future__ import annotations

import datetime as dt
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from psycopg import errors
from pydantic import BaseModel, Field

from . import db


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.migrate()
    db.open_pool()
    try:
        yield
    finally:
        db.close_pool()


app = FastAPI(title="Saunalöyly booking platform (Core slice)", lifespan=lifespan)


def conflict(code: str, message: str = "") -> HTTPException:
    return HTTPException(status_code=409, detail={"error": code, "message": message})


@app.exception_handler(db.TryAgain)
def _try_again(_, __):
    # FR-14: retries used up. A different message from "no Seat free"; nothing was written.
    return JSONResponse(status_code=503, content={"detail": {"error": "try_again"}})


def refusal(e: psycopg.Error) -> HTTPException:
    """Map a refusal by the data store to a Guest-facing code. 'no_seat_free' is a definite loss."""
    if isinstance(e, errors.CheckViolation):
        if e.diag.constraint_name == "booked_within_capacity":
            return conflict("no_seat_free", "not enough Seats left")
        return conflict("rule_refused", e.diag.message_primary or "")
    if isinstance(e, errors.UniqueViolation):
        return conflict("already_exists", e.diag.message_primary or "")
    return conflict("refused", str(e))


def guard(work):
    """Run a unit of work with the bounded retry, turning the store's refusals into 409."""
    try:
        return db.run(work)
    except (errors.CheckViolation, errors.UniqueViolation) as e:
        raise refusal(e) from e


def _open_for_booking(c: psycopg.Connection, window_id: int) -> None:
    """Window exists and its Booking deadline has not passed (FR-39). Call after the Window is locked."""
    row = c.execute("SELECT app_now() < booking_deadline(id) FROM windows WHERE id = %s", (window_id,)).fetchone()
    if row is None:
        raise HTTPException(404, {"error": "no_such_window"})
    if not row[0]:
        raise conflict("deadline_passed", "the Booking deadline has passed")


# ---------------------------------------------------------------- reading

@app.get("/health")
def health():
    return {"ok": True}


@app.get("/windows")
def windows():
    def work(c):
        return c.execute("SELECT id, lower(during), upper(during), seats_left(id) FROM windows ORDER BY id").fetchall()

    return [{"id": i, "start": s, "end": e, "seats_left": left} for i, s, e, left in db.run(work)]


@app.get("/windows/{window_id}")
def window(window_id: int):
    row = db.run(lambda c: c.execute(
        "SELECT id, lower(during), upper(during), seats_left(id) FROM windows WHERE id = %s", (window_id,)).fetchone())
    if row is None:
        raise HTTPException(404, {"error": "no_such_window"})
    return {"id": row[0], "start": row[1], "end": row[2], "seats_left": row[3]}


# ---------------------------------------------------------------- Holds and Bookings

class HoldIn(BaseModel):
    window_id: int
    seats: int = Field(ge=1, le=44)
    session_id: str = Field(min_length=1, max_length=100)


@app.post("/holds")
def hold(body: HoldIn):
    """FR-35. One Hold per session and Window: a second request resizes it, and the old Hold stays if the
    extra Seats are not free. A Hold ends at the earlier of 10 minutes and the Booking deadline."""

    def work(c):
        db.lock_windows(c, [body.window_id])
        _open_for_booking(c, body.window_id)
        live = c.execute(
            "SELECT id FROM holds WHERE session_id = %s AND window_id = %s AND expires_at > app_now()",
            (body.session_id, body.window_id)).fetchone()
        if live:
            c.execute("UPDATE holds SET seats = %s WHERE id = %s", (body.seats, live[0]))
            return live[0]
        c.execute("DELETE FROM holds WHERE session_id = %s AND window_id = %s", (body.session_id, body.window_id))
        return c.execute(
            "INSERT INTO holds (window_id, seats, session_id, created_at, expires_at) "
            "SELECT %s, %s, %s, n, LEAST(n + interval '10 minutes', booking_deadline(%s)) FROM (SELECT app_now() AS n) x "
            "RETURNING id", (body.window_id, body.seats, body.session_id, body.window_id)).fetchone()[0]

    return {"hold_id": guard(work)}


@app.delete("/holds")
def cancel_hold(window_id: int, session_id: str):
    """The Guest pressing Cancel releases the Hold at once (FR-35)."""
    n = db.run(lambda c: c.execute(
        "DELETE FROM holds WHERE window_id = %s AND session_id = %s", (window_id, session_id)).rowcount)
    return {"released": n}


class BookingIn(BaseModel):
    window_id: int
    seats: int = Field(ge=1, le=44)
    session_id: str = Field(min_length=1, max_length=100)
    guest: str = Field(default="", max_length=200)


@app.post("/bookings", status_code=201)
def book(body: BookingIn):
    """FR-6/FR-36: the Booking is created when the (simulated) payment completes. The session's Hold is
    released first, in the same transaction, so the Guest's own Seats are not counted twice. After a Hold
    expired, the Booking is made only if the Seats are still free (the store decides)."""

    def work(c):
        db.lock_windows(c, [body.window_id])
        _open_for_booking(c, body.window_id)
        c.execute("DELETE FROM holds WHERE session_id = %s AND window_id = %s", (body.session_id, body.window_id))
        return c.execute("INSERT INTO bookings (window_id, seats, guest) VALUES (%s, %s, %s) RETURNING id",
                         (body.window_id, body.seats, body.guest)).fetchone()[0]

    return {"booking_id": guard(work)}


# ---------------------------------------------------------------- Whole-sauna bookings, Blocks, marks

class WholeIn(BaseModel):
    window_id: int
    sauna_id: int


@app.post("/whole-bookings", status_code=201)
def book_whole(body: WholeIn):
    def work(c):
        db.lock_windows(c, [body.window_id])
        _open_for_booking(c, body.window_id)
        return c.execute("INSERT INTO whole_bookings (window_id, sauna_id) VALUES (%s, %s) RETURNING id",
                         (body.window_id, body.sauna_id)).fetchone()[0]

    return {"whole_booking_id": guard(work)}


class BlockIn(BaseModel):
    sauna_id: int
    start: dt.datetime
    end: dt.datetime


@app.post("/blocks", status_code=201)
def block(body: BlockIn):
    """FR-40. The store refuses a Block that would leave less Seat capacity than the Seats booked and held."""
    if body.end <= body.start:
        raise HTTPException(422, {"error": "empty_period"})
    return {"block_id": guard(lambda c: c.execute(
        "INSERT INTO blocks (sauna_id, during) VALUES (%s, tstzrange(%s, %s, '[)')) RETURNING id",
        (body.sauna_id, body.start, body.end)).fetchone()[0])}


@app.delete("/blocks/{block_id}")
def lift_block(block_id: int):
    n = guard(lambda c: c.execute("DELETE FROM blocks WHERE id = %s", (block_id,)).rowcount)
    return {"lifted": n}


class MarkIn(BaseModel):
    window_id: int
    sauna_id: int


@app.post("/marks", status_code=201)
def mark(body: MarkIn):
    """FR-41. Refused while Seats are placed in the Sauna (the store checks), and when the Release time
    (when on) is later than the Window's Booking deadline (an application rule)."""

    def work(c):
        db.lock_windows(c, [body.window_id])
        row = c.execute("SELECT release_on AND release_due(id) > booking_deadline(id) FROM windows, settings WHERE id = %s",
                        (body.window_id,)).fetchone()
        if row is None:
            raise HTTPException(404, {"error": "no_such_window"})
        if row[0]:
            raise conflict("release_after_deadline", "the Release time is later than the Booking deadline of this Window")
        return c.execute("INSERT INTO marks (window_id, sauna_id) VALUES (%s, %s) RETURNING id",
                         (body.window_id, body.sauna_id)).fetchone()[0]

    return {"mark_id": guard(work)}


@app.delete("/marks")
def unmark(window_id: int, sauna_id: int):
    n = guard(lambda c: c.execute("DELETE FROM marks WHERE window_id = %s AND sauna_id = %s",
                                  (window_id, sauna_id)).rowcount)
    return {"removed": n}


# ---------------------------------------------------------------- Settings

class SettingsIn(BaseModel):
    release_on: bool
    release_time: dt.time
    booking_deadline_minutes: int = Field(le=45)


@app.put("/settings")
def put_settings(body: SettingsIn):
    """FR-39. A Release time later than the Booking deadline of a Window with an unreleased
    Whole-booking-only Sauna is refused and the message names the Windows (checked per Window)."""

    def work(c):
        ids = [r[0] for r in c.execute("SELECT id FROM windows ORDER BY id").fetchall()]
        db.lock_windows(c, ids)
        for i in ids:  # bring every release that is already due up to date, under the old setting
            c.execute("SELECT recompute_window(%s)", (i,))
        bad = c.execute(
            "SELECT w.id FROM windows w, settings st WHERE %s AND EXISTS ("
            "  SELECT 1 FROM marks m WHERE m.window_id = w.id "
            "  AND NOT EXISTS (SELECT 1 FROM releases r WHERE r.window_id = m.window_id AND r.sauna_id = m.sauna_id)) "
            "AND ((lower(w.during) AT TIME ZONE st.venue_tz)::date + %s::time) AT TIME ZONE st.venue_tz "
            "    > lower(w.during) + make_interval(mins => %s) ORDER BY w.id",
            (body.release_on, body.release_time, body.booking_deadline_minutes)).fetchall()
        if bad:
            raise conflict("release_after_deadline", "Windows: " + ", ".join(str(b[0]) for b in bad))
        c.execute("UPDATE settings SET release_on = %s, release_time = %s, booking_deadline_minutes = %s",
                  (body.release_on, body.release_time, body.booking_deadline_minutes))
        return True

    return {"ok": guard(work)}


def main() -> None:
    import uvicorn

    uvicorn.run("booking_platform.app:app", host="127.0.0.1", port=8000)
