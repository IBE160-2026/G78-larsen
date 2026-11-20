"""Whole-sauna bookings (FR-29). The store judges whether the Sauna can be booked whole."""

from __future__ import annotations

from .. import db
from ..db import venue_admin as q
from .windows import ensure_open_for_booking


def book_whole(window_id: int, sauna_id: int) -> int:
    def work(c):
        db.lock_windows(c, [window_id])
        ensure_open_for_booking(c, window_id)
        return q.insert_whole_booking(c, window_id, sauna_id)

    return db.run(work)
