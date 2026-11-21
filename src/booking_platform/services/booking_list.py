"""The Administrator's Booking list for one Venue date (FR-16, FR-21, AD-4, AD-5): `GET /api/admin/bookings`.

`ensure_generated()` runs first (the only write); then one `db.run` of SELECTs reads `today`, every Window of the date
(bookable or not, past dates and dates after the horizon included) and its active Bookings. No Window is locked. A
Booking due for retention reads with the anonymised name and email (`db.booking_list`); nothing is written for it.
"""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

from .. import db
from ..db import booking_list as q
from ..db import windows as wq
from .windows import ensure_generated


def day(date: dt.date | None = None) -> dict:
    """`{"today", "date", "windows"}`: without a date, the Venue date of app_now(). Each Window has `id`, `start`,
    `end` (Venue time), `seat_capacity`, `seats_booked`, `seats_left` and `bookings` (oldest first)."""
    ensure_generated()

    def work(c):
        today, _, _, tz_name = wq.horizon(c)
        tz = ZoneInfo(tz_name)
        chosen = today if date is None else date
        per_window: dict[int, list[dict]] = {}
        for wid, reference, name, email, seats, total_ore, created_at in q.bookings_on(c, chosen):
            per_window.setdefault(wid, []).append(
                {"reference": reference, "name": name, "email": email, "seats": seats, "total_ore": total_ore,
                 "created_at": created_at.astimezone(tz).isoformat()})
        windows = [
            {"id": wid, "start": start.astimezone(tz).isoformat(), "end": end.astimezone(tz).isoformat(),
             "seat_capacity": capacity, "seats_booked": booked, "seats_left": left,
             "bookings": per_window.get(wid, [])}
            for wid, start, end, capacity, booked, left in q.windows_on(c, chosen)]
        return {"today": today.isoformat(), "date": chosen.isoformat(), "windows": windows}

    return db.run(work)
