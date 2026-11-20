"""Windows: the daily schedule and its validation, generation up to the Booking horizon, the dated listing with the
nearest Windows (FR-2, FR-3, FR-13, NFR-3, AD-4, AD-5), and the Booking-deadline rule shared by every booking action
(FR-39).

Every time rule is judged in SQL on app_now() (`db.windows`); nothing here reads a clock for a rule. The one Python
date check is the seed's daylight-saving check, which looks at the tz database, not at the time of a booking.
"""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import psycopg
from pydantic import BaseModel, ConfigDict, model_validator

from .. import db
from ..db import seats as q
from ..db import windows as wq
from .errors import Refused

DEFAULT_TZ = "Europe/Oslo"  # the `settings.venue_tz` default; the seed file is checked against it before startup
DST_YEARS = 10  # the daylight-saving check looks this far ahead
NEAREST = 3


# ------------------------------------------------------------------ the schedule (FR-13, NFR-3)


class ScheduleRow(BaseModel):
    """One daily Window of the schedule, in Venue time."""

    model_config = ConfigDict(extra="forbid")

    start: dt.time
    end: dt.time

    @model_validator(mode="after")
    def _ends_after_start(self) -> ScheduleRow:
        if self.start.tzinfo is not None or self.end.tzinfo is not None:
            raise ValueError("times are Venue clock times, without an offset")
        if self.end <= self.start:
            raise ValueError("end must be later than start")
        return self


def _hhmm(t: dt.time) -> str:
    return t.strftime("%H:%M")


def _label(row: ScheduleRow) -> str:
    return f"{_hhmm(row.start)}–{_hhmm(row.end)}"


def _transition_days(tz: ZoneInfo, first: dt.date, years: int) -> list[dt.date]:
    """The dates around every UTC-offset change of `tz` from `first` on, `years` ahead (each change day and the
    day after, so a change at midnight is covered too)."""
    days = []
    try:
        last = first.replace(year=first.year + years)
    except ValueError:  # 29 February in a year that has none
        last = first.replace(year=first.year + years, day=28)
    d = first
    offset = dt.datetime.combine(d, dt.time(0), tzinfo=tz).utcoffset()
    while d <= last:
        nxt = d + dt.timedelta(days=1)
        nxt_offset = dt.datetime.combine(nxt, dt.time(0), tzinfo=tz).utcoffset()
        if nxt_offset != offset:
            days += [d, nxt]
        d, offset = nxt, nxt_offset
    return days


def _skipped_or_repeated(t: dt.time, day: dt.date, tz: ZoneInfo) -> bool:
    """A wall-clock time that does not exist (skipped) or exists twice (repeated) on `day`: the two folds
    disagree."""
    a = dt.datetime.combine(day, t, tzinfo=tz)
    return a.utcoffset() != a.replace(fold=1).utcoffset()


def check_schedule(rows: list[ScheduleRow], tz_name: str = DEFAULT_TZ, today: dt.date | None = None) -> None:
    """Refuse a schedule whose rows overlap partly, are identical or nested (back-to-back is fine, FR-13 E1, E2),
    and a row that starts or ends in a time skipped or repeated on a daylight-saving change day of the Venue time
    zone in the next ten years (NFR-3). Raises ValueError with a one-line message."""
    try:
        tz = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError(f"the Venue time zone {tz_name!r} is unknown") from None
    ordered = sorted(rows, key=lambda r: (r.start, r.end))
    for a, b in zip(ordered, ordered[1:]):
        if b.start < a.end:
            raise ValueError(f"rows {_label(a)} and {_label(b)} overlap")
    days = _transition_days(tz, today or dt.date.today(), DST_YEARS)
    for row in ordered:
        for t in (row.start, row.end):
            bad = next((d for d in days if _skipped_or_repeated(t, d, tz)), None)
            if bad is not None:
                raise ValueError(f"row {_label(row)}: {_hhmm(t)} is skipped or repeated on {bad.isoformat()} "
                                 f"in {tz_name} (daylight saving)")


# ------------------------------------------------------------------ generation (FR-13, AD-4)


def ensure_generated() -> int:
    """Insert the scheduled Windows after `windows_generated_through` up to the end of the Booking horizon, in one
    unit of work under an advisory lock. A second call creates nothing. Returns the Windows inserted."""
    return db.run(wq.generate)


# ------------------------------------------------------------------ the dated listing (FR-2, FR-3)


def _shape(row: tuple, tz: ZoneInfo, with_date: bool = False) -> dict:
    wid, start, end, left, started, date = row
    out = {"id": wid, "start": start.astimezone(tz).isoformat(), "end": end.astimezone(tz).isoformat(),
           "seats_left": left, "already_started": started}
    if with_date:
        out = {"id": wid, "date": date.isoformat(), **{k: v for k, v in out.items() if k != "id"}}
    return out


def listing(date: dt.date | None = None, seats: int | None = None) -> dict:
    """`GET /api/windows`. Always `today`, `horizon_end`, `horizon_days` and `dates`; with a date, its Windows; with
    a date and Seats, the nearest Windows with room when none of the date's has room. A date outside
    `today..horizon_end` is `409 outside_horizon`, judged before anything is written. The only write is
    `ensure_generated()`."""
    today, horizon_end, _, _ = db.run(wq.horizon)
    if date is not None and not today <= date <= horizon_end:
        raise Refused("outside_horizon", today=today.isoformat(), horizon_end=horizon_end.isoformat())
    ensure_generated()

    def work(c):
        today, horizon_end, days, tz_name = wq.horizon(c)
        tz = ZoneInfo(tz_name)
        out = {"today": today.isoformat(), "horizon_end": horizon_end.isoformat(), "horizon_days": days,
               "dates": [d.isoformat() for d in wq.bookable_dates(c)]}
        if date is not None:
            rows = wq.windows_on(c, date)
            out["windows"] = [_shape(r, tz) for r in rows]
            if seats is not None and not any(r[3] >= seats for r in rows):
                out["nearest"] = [_shape(r, tz, with_date=True) for r in wq.nearest(c, date, seats, NEAREST)]
        return out

    return db.run(work)


# ------------------------------------------------------------------ one Window, and the Booking deadline


def _one(row: tuple) -> dict:
    return {"id": row[0], "start": row[1], "end": row[2], "seats_left": row[3]}


def get_window(window_id: int) -> dict:
    row = db.run(lambda c: q.get_window(c, window_id))
    if row is None:
        raise Refused("not_found")
    return _one(row)


def ensure_open_for_booking(c: psycopg.Connection, window_id: int) -> None:
    """The Window exists and its Booking deadline has not passed. Call after the Window is locked (AD-4)."""
    is_open = q.before_booking_deadline(c, window_id)
    if is_open is None:
        raise Refused("not_found")
    if not is_open:
        raise Refused("deadline_passed", message="the Booking deadline has passed")
