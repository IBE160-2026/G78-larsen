"""Seat bookings (FR-6, FR-36). The session's Hold is released first, in the same transaction, so the Guest's
own Seats are not counted twice. After a Hold expired, the Booking is made only if the Seats are still free
(the store decides)."""

from __future__ import annotations

from .. import db
from ..db import seats as q
from .windows import ensure_open_for_booking


def book(session_id: int, window_id: int, seats: int, guest: str) -> int:
    def work(c):
        db.lock_windows(c, [window_id])
        ensure_open_for_booking(c, window_id)
        q.delete_holds(c, session_id, window_id)
        return q.insert_booking(c, window_id, seats, guest)

    return db.run(work)
