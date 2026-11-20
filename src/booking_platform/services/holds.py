"""Holds (FR-35): one per session and Window. A second request resizes it, and the old Hold stays if the extra
Seats are not free. A Hold ends at the earlier of 10 minutes and the Booking deadline."""

from __future__ import annotations

from .. import db
from ..db import seats as q
from .windows import ensure_open_for_booking


def hold(session_id: int, window_id: int, seats: int) -> int:
    def work(c):
        db.lock_windows(c, [window_id])
        ensure_open_for_booking(c, window_id)
        live = q.live_hold(c, session_id, window_id)
        if live:
            q.resize_hold(c, live, seats)
            return live
        q.delete_holds(c, session_id, window_id)
        return q.insert_hold(c, session_id, window_id, seats)

    return db.run(work)


def release(session_id: int, window_id: int) -> int:
    """The Guest pressing Cancel releases the Hold at once (FR-35)."""
    return db.run(lambda c: q.delete_holds(c, session_id, window_id))
