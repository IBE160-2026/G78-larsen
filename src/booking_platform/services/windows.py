"""Windows and Seats left (AD-5), and the Booking-deadline rule shared by every booking action (FR-39)."""

from __future__ import annotations

import psycopg

from .. import db
from ..db import seats as q
from .errors import Refused


def _shape(row: tuple) -> dict:
    return {"id": row[0], "start": row[1], "end": row[2], "seats_left": row[3]}


def list_windows() -> list[dict]:
    return [_shape(r) for r in db.run(q.list_windows)]


def get_window(window_id: int) -> dict:
    row = db.run(lambda c: q.get_window(c, window_id))
    if row is None:
        raise Refused("not_found")
    return _shape(row)


def ensure_open_for_booking(c: psycopg.Connection, window_id: int) -> None:
    """The Window exists and its Booking deadline has not passed. Call after the Window is locked (AD-4)."""
    is_open = q.before_booking_deadline(c, window_id)
    if is_open is None:
        raise Refused("not_found")
    if not is_open:
        raise Refused("deadline_passed", message="the Booking deadline has passed")
