"""Venue Settings (FR-39). A Release time later than the Booking deadline of a Window with an unreleased
Whole-booking-only Sauna is refused, and the message names the Windows (checked per Window)."""

from __future__ import annotations

import datetime as dt

from .. import db
from ..db import venue_admin as q
from .errors import Refused


def put(release_on: bool, release_time: dt.time, booking_deadline_minutes: int) -> None:
    def work(c):
        ids = q.window_ids(c)
        db.lock_windows(c, ids)
        for i in ids:  # bring every release that is already due up to date, under the old setting
            q.recompute_window(c, i)
        bad = q.windows_breaking_release_limit(c, release_on, release_time, booking_deadline_minutes)
        if bad:
            raise Refused("release_after_deadline", message="Windows: " + ", ".join(str(b) for b in bad))
        q.update_settings(c, release_on, release_time, booking_deadline_minutes)

    db.run(work)
