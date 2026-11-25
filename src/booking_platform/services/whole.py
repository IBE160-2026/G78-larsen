"""Whole-sauna bookings (FR-29, FR-30, AD-23, AD-24), shown to Guests as "Private sauna".

Story 5.1 holds the listing: for a Venue date, the Saunas a Guest may book whole and their free Windows. The store
judges FR-29 (`whole_bookable`, the only statement of the rule); the time rules are the SQL predicates of AD-4. The
booking itself is Story 5.2.
"""

from __future__ import annotations

import datetime as dt
from itertools import groupby
from zoneinfo import ZoneInfo

from .. import db
from ..db import whole as q
from ..db import windows as wq
from .errors import Refused
from .windows import ensure_generated


def listing(date: dt.date) -> dict:
    """`GET /api/private-saunas?date=`: `{saunas: [{id, name, capacity, whole_price_ore, windows: [{id, start, end,
    already_started}]}], horizon_end, horizon_days}`. Saunas in Fill order, each with its free Windows in time order;
    a Sauna with no free Window is left out. A date outside `today..horizon_end` is `409 outside_horizon`, judged
    before anything is written, as `GET /api/windows`. Takes no lock; the only write is `ensure_generated()`."""
    today, horizon_end, _, _ = db.run(wq.horizon)
    if not today <= date <= horizon_end:
        raise Refused("outside_horizon", today=today.isoformat(), horizon_end=horizon_end.isoformat())
    ensure_generated()

    def work(c):
        _, horizon_end, days, tz_name = wq.horizon(c)
        return horizon_end, days, ZoneInfo(tz_name), q.pairs_on(c, date)

    horizon_end, days, tz, rows = db.run(work)
    saunas = []
    for (sid, name, capacity, price), pairs in groupby(rows, key=lambda r: r[:4]):
        saunas.append({
            "id": sid, "name": name, "capacity": capacity, "whole_price_ore": price,
            "windows": [{"id": wid, "start": start.astimezone(tz).isoformat(), "end": end.astimezone(tz).isoformat(),
                         "already_started": started} for *_, wid, start, end, started in pairs],
        })
    return {"saunas": saunas, "horizon_end": horizon_end.isoformat(), "horizon_days": days}
