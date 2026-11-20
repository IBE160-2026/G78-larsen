"""Request shapes (Conventions: Input) and the Venue facts response. Every request model forbids unknown fields;
Seats are 1 to 10 (FR-2)."""

from __future__ import annotations

import datetime as dt
import re
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, ValidationInfo, field_validator

INT4_MAX = 2_147_483_647
Seats = Annotated[int, Field(ge=1, le=10)]
Id = Annotated[int, Field(ge=1, le=INT4_MAX)]  # store ids are int4: anything outside is a shape error


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


class WindowsQuery(Strict):
    """`GET /api/windows?date=&seats=` (AD-16): both optional, but a value that is present must be valid. The date
    is a Venue date written yyyy-mm-dd, and only that form is accepted."""

    date: dt.date | None = None
    seats: Seats | None = None

    @field_validator("date", mode="before")
    @classmethod
    def _iso_date(cls, value: object) -> object:
        if value is not None and not (isinstance(value, str) and _ISO_DATE.fullmatch(value)):
            raise ValueError("not a yyyy-mm-dd date")
        return value


class SessionIn(Strict):
    """`POST /api/session` takes an empty JSON object."""


class HoldIn(Strict):
    window_id: Id
    seats: Seats


class BookingIn(Strict):
    window_id: Id
    seats: Seats
    guest: str = Field(default="", max_length=200)


class WholeIn(Strict):
    window_id: Id
    sauna_id: Id


class BlockIn(Strict):
    sauna_id: Id
    start: AwareDatetime  # with an offset: a naive time would be read in some zone silently
    end: AwareDatetime

    @field_validator("end")
    @classmethod
    def _not_empty(cls, end: dt.datetime, info: ValidationInfo) -> dt.datetime:
        start = info.data.get("start")
        if start is not None and end <= start:
            raise ValueError("empty_period")
        return end


class MarkIn(Strict):
    window_id: Id
    sauna_id: Id


class SettingsIn(Strict):
    release_on: bool
    release_time: dt.time
    booking_deadline_minutes: int = Field(ge=-INT4_MAX, le=45)


class SaunaOut(BaseModel):
    id: int
    name: str
    capacity: int


class VenueOut(BaseModel):
    """`GET /api/venue` (AD-16): times are "HH:MM" in Venue time, the price is in øre, the Saunas in Fill order."""

    name: str
    address_lines: list[str]
    phone: str
    email: str
    opening_time: str
    closing_time: str
    session_minutes: int
    price_per_seat_ore: int
    saunas: list[SaunaOut]
