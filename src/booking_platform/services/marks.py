"""Whole-booking-only marks (FR-41). Refused while Seats are placed in the Sauna (the store checks), and when the
Release time (when on) is later than the Window's Booking deadline (an application rule)."""

from __future__ import annotations

from .. import db
from ..db import venue_admin as q
from .errors import Refused


def mark(window_id: int, sauna_id: int) -> int:
    def work(c):
        db.lock_windows(c, [window_id])
        late = q.release_after_deadline(c, window_id)
        if late is None:
            raise Refused("not_found")
        if late:
            raise Refused("release_after_deadline",
                          message="the Release time is later than the Booking deadline of this Window")
        return q.insert_mark(c, window_id, sauna_id)

    return db.run(work)


def unmark(window_id: int, sauna_id: int) -> int:
    return db.run(lambda c: q.delete_mark(c, window_id, sauna_id))
