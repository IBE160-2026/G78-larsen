"""The Venue facts (FR-1, AD-16): what Landing shows about the Venue, read from the `settings` row and the Saunas.

The Pydantic models here are the one validation of Venue facts and Saunas. The seed goes through them (AD-18,
IV-6), and the Administrator endpoints that change these values will reuse them.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from .. import db
from ..db import venue as q
from .windows import DEFAULT_TZ, ScheduleRow, check_schedule

INT4_MAX = 2_147_483_647
Text = Annotated[str, Field(min_length=1, max_length=100)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class VenueFacts(_Strict):
    """The Venue's name, address and contact, opening hours, Session length and price per Seat."""

    name: Text
    address_lines: list[Text] = Field(min_length=1, max_length=4)
    phone: Annotated[str, Field(min_length=1, max_length=40)]
    email: Annotated[str, Field(min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]
    opening_time: dt.time
    closing_time: dt.time
    session_minutes: int = Field(gt=0, le=24 * 60)
    price_per_seat_ore: int = Field(ge=0, le=INT4_MAX)

    @model_validator(mode="after")
    def _closes_after_opening(self) -> VenueFacts:
        if self.closing_time <= self.opening_time:
            raise ValueError("closing_time must be later than opening_time")
        return self

    def row(self) -> tuple:
        """The values in `db.venue.VENUE_COLUMNS` order."""
        return (self.name, self.address_lines, self.phone, self.email, self.opening_time, self.closing_time,
                self.session_minutes, self.price_per_seat_ore)


class Sauna(_Strict):
    id: int = Field(ge=1, le=INT4_MAX)
    name: Annotated[str, Field(min_length=1, max_length=60)]
    capacity: int = Field(gt=0, le=1000)
    fill_order: int = Field(ge=1, le=INT4_MAX)
    # The Whole-sauna price (AD-23): absent or null means the Sauna is not offered whole.
    whole_price_ore: int | None = Field(default=None, gt=0, le=INT4_MAX)


class VenueSeed(_Strict):
    """The shape of `seeds/venue.json`. The schedule is checked against the Venue time zone given as validation
    context `tz` (default: the `settings.venue_tz` default)."""

    venue: VenueFacts
    saunas: list[Sauna] = Field(min_length=1)
    schedule: list[ScheduleRow] = Field(min_length=1, max_length=48)

    @field_validator("schedule")
    @classmethod
    def _schedule(cls, rows: list[ScheduleRow], info: ValidationInfo) -> list[ScheduleRow]:
        check_schedule(rows, (info.context or {}).get("tz", DEFAULT_TZ))
        return rows

    @model_validator(mode="after")
    def _unique(self) -> VenueSeed:
        for key in ("id", "fill_order"):
            values = [getattr(s, key) for s in self.saunas]
            if len(values) != len(set(values)):
                raise ValueError(f"two saunas share one {key}")
        return self


def _hhmm(t: dt.time) -> str:
    return t.strftime("%H:%M")


def facts() -> dict:
    """The Venue facts for `GET /api/venue`, with the Saunas in Fill order and each one's Whole-sauna price (null when
    it is not offered whole). Reads only."""

    def work(c):
        return q.venue_facts(c), q.saunas(c)

    venue, saunas = db.run(work)
    name, address_lines, phone, email, opening, closing, session_minutes, price = venue
    return {
        "name": name,
        "address_lines": list(address_lines),
        "phone": phone,
        "email": email,
        "opening_time": _hhmm(opening),
        "closing_time": _hhmm(closing),
        "session_minutes": session_minutes,
        "price_per_seat_ore": price,
        "saunas": [{"id": i, "name": n, "capacity": cap, "whole_price_ore": price} for i, n, cap, price in saunas],
    }
