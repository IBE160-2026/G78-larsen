"""Request shapes (Conventions: Input), the Venue facts response and the Booking response. Every request model forbids unknown fields;
Seats are 1 to 10 (FR-2)."""

from __future__ import annotations

import datetime as dt
import re
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictStr, ValidationInfo, field_validator

INT4_MAX = 2_147_483_647
Seats = Annotated[int, Field(ge=1, le=10)]
Id = Annotated[int, Field(ge=1, le=INT4_MAX)]  # store ids are int4: anything outside is a shape error


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


class DateQuery(Strict):
    """An optional `date` query field: a Venue date written yyyy-mm-dd, and only that form is accepted."""

    date: dt.date | None = None

    @field_validator("date", mode="before")
    @classmethod
    def _iso_date(cls, value: object) -> object:
        if value is not None and not (isinstance(value, str) and _ISO_DATE.fullmatch(value)):
            raise ValueError("not a yyyy-mm-dd date")
        return value


class WindowsQuery(DateQuery):
    """`GET /api/windows?date=&seats=` (AD-16): both optional, but a value that is present must be valid."""

    seats: Seats | None = None


class BookingListQuery(DateQuery):
    """`GET /api/admin/bookings?date=` (FR-16): the date is optional (the API's today); any calendar date is
    allowed. No other field."""


class OutboxQuery(Strict):
    """`GET /api/admin/outbox` (FR-17) takes no query field: any field is an unknown field."""


class SessionIn(Strict):
    """`POST /api/session` takes an empty JSON object."""


class SignInIn(Strict):
    """`POST /api/admin/sign-in` (FR-15): the email and the password, as typed. No shape rule beyond the caps and no
    U+0000 (which the store cannot hold), so a short or odd value is an ordinary refused sign-in, never a different
    answer (PW-5)."""

    email: Annotated[str, Field(max_length=254, pattern=r"^[^\x00]*$")]  # the store refuses U+0000: a shape error
    password: Annotated[str, Field(max_length=1024, pattern=r"^[^\x00]*$")]


class ManageOpenIn(Strict):
    """`POST /api/manage/open` (AD-28): the token from the Manage link's fragment. Any JSON string is accepted here; a
    token that opens nothing (too long, malformed, unknown, revoked, its Window ended) is `404 not_found`, never a
    shape error."""

    token: StrictStr


class HoldIn(Strict):
    window_id: Id
    seats: Seats


class BookingIn(Strict):
    """`POST /api/bookings` (FR-5, FR-9): one Window, 1 to 10 Seats, the Guest's name and email and nothing else. A
    second Window (`window_ids`, any other field) is an unknown field. Leading and trailing spaces are not part of a
    name or an email, and neither may hold a control character (U+0000 to U+001F, U+007F)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    window_id: Id
    seats: Seats
    name: Annotated[str, Field(min_length=1, max_length=100, pattern=r"^[^\x00-\x1f\x7f]+$")]
    email: Annotated[str, Field(min_length=3, max_length=254,
                                pattern=r"^[^@\s\x00-\x1f\x7f]+@[^@\s\x00-\x1f\x7f]+\.[^@\s\x00-\x1f\x7f]+$")]


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


class BookingOut(BaseModel):
    """A Seat booking as every page shows it (FR-8): the stored price and total in øre, the Venue date and the
    Window's start and end in Venue time. No Sauna (FR-4) and no internal id."""

    reference: str
    date: str
    start: str
    end: str
    seats: int
    price_per_seat_ore: int
    total_ore: int
    name: str
    email: str
    status: str


class EmailOut(BaseModel):
    subject: str
    body: str


class BookingResult(BaseModel):
    """`POST /api/bookings` (also a repeat) and `GET /api/bookings/{reference}/confirmation`: the Booking as it is now
    and the emails its action sent."""

    booking: BookingOut
    emails: list[EmailOut]
