"""Request shapes (Conventions: Input), the Venue facts response and the Booking response. Every request model forbids unknown fields;
Seats are 1 to 10 (FR-2)."""

from __future__ import annotations

import datetime as dt
import re
from typing import Annotated, Literal

from pydantic import (AwareDatetime, BaseModel, ConfigDict, Discriminator, Field, StrictStr, StringConstraints, Tag,
                      ValidationInfo, field_validator, model_validator)

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


class PrivateSaunasQuery(DateQuery):
    """`GET /api/private-saunas?date=` (FR-30, AD-24): the Venue date is required. No other field."""

    date: dt.date


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


Int4 = Annotated[int, Field(ge=-INT4_MAX - 1, le=INT4_MAX)]


class MoveIn(Strict):
    """`POST /api/manage/{reference}/seats/move` (FR-26, AD-29): the target Window, the Seats to move and the Booking's
    `version` as the page read it. Any whole number of Seats and any version is accepted here: Seats outside 1 to the
    Booking's Seats are `409 change_invalid`, another version `409 booking_changed`, never a shape error."""

    window_id: Id
    seats: Int4
    version: Int4


class VoucherIn(Strict):
    """`POST /api/manage/{reference}/seats/voucher` (FR-27, AD-29): the Seats to give up and the Booking's `version` as
    the page read it. Any whole number is accepted here, as in `MoveIn`: Seats outside 1 to the Booking's Seats are
    `409 change_invalid`, another version `409 booking_changed`, never a shape error."""

    seats: Int4
    version: Int4


# A typed Voucher code: any JSON string up to 1024 characters for the shape; whether it is a code is
# `services.voucher`'s question (`409 voucher_invalid`), never a shape error (AD-30). It is never stripped (also
# inside `BookingIn`), so input longer than 32 characters stays too long however much of it is spaces.
VoucherCode = Annotated[StrictStr, StringConstraints(max_length=1024, strip_whitespace=False)]


class HoldIn(Strict):
    window_id: Id
    seats: Seats


# A request that comes in two kinds (`POST /api/bookings`, `POST /api/vouchers/quote`) is a union chosen by `kind`
# (AD-23). Its tags start with `kind=`, and `api/errors.py` leaves them out of a shape error's `fields`, so a field is
# named as in a one-kind request ("window_id", never "kind=seats.window_id"). Anything that is not `kind: 'whole'`
# goes to the Seat shape, whose own `kind` field then reports a wrong value.
KIND_TAG = "kind="


def _kind_of(value: object) -> str:
    kind = value.get("kind") if isinstance(value, dict) else getattr(value, "kind", None)
    return KIND_TAG + ("whole" if kind == "whole" else "seats")


class _BookingFields(Strict):
    """The fields every Booking request has: the Window, the Guest's name and email and an optional Voucher. Leading
    and trailing spaces are not part of a name or an email, and neither may hold a control character (U+0000 to
    U+001F, U+007F)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    window_id: Id
    name: Annotated[str, Field(min_length=1, max_length=100, pattern=r"^[^\x00-\x1f\x7f]+$")]
    email: Annotated[str, Field(min_length=3, max_length=254,
                                pattern=r"^[^@\s\x00-\x1f\x7f]+@[^@\s\x00-\x1f\x7f]+\.[^@\s\x00-\x1f\x7f]+$")]
    # A Voucher (FR-28, AD-30): one code and the quoted Voucher part, both or neither. Any string up to the shape cap is
    # accepted here; a code that is not usable is `409 voucher_invalid`, never a shape error.
    voucher_code: VoucherCode | None = None
    voucher_part_ore: Annotated[int, Field(ge=1, le=INT4_MAX)] | None = None

    @model_validator(mode="after")
    def _voucher_both_or_neither(self):
        if (self.voucher_code is None) != (self.voucher_part_ore is None):
            raise ValueError("voucher_code and voucher_part_ore go together")
        return self


class SeatBookingIn(_BookingFields):
    """`POST /api/bookings` for Seats (FR-5, FR-9): one Window, 1 to 10 Seats, the Guest's name and email and nothing
    else. `kind` may be left out (every Seat request before Story 5.2 is unchanged). A second Window (`window_ids`, any
    other field) is an unknown field, and so is a `sauna_id`."""

    kind: Literal["seats"] = "seats"
    seats: Seats


class WholeBookingIn(_BookingFields):
    """`POST /api/bookings` for a Whole-sauna booking (FR-29, Story 5.2): `kind: 'whole'`, one Window and one Sauna, the
    Guest's name and email. A `seats` field is an unknown field."""

    kind: Literal["whole"]
    sauna_id: Id


BookingIn = Annotated[Annotated[SeatBookingIn, Tag(KIND_TAG + "seats")] | Annotated[WholeBookingIn, Tag(KIND_TAG + "whole")],
                      Discriminator(_kind_of)]


class SeatQuoteIn(Strict):
    """`POST /api/vouchers/quote` for Seats (FR-28, AD-30): what a Voucher would pay of `seats` Seats in the Window."""

    code: VoucherCode
    kind: Literal["seats"]
    window_id: Id
    seats: Seats


class WholeQuoteIn(Strict):
    """`POST /api/vouchers/quote` for a Whole-sauna booking (Story 5.2): what a Voucher would pay of the Sauna's
    `whole_price_ore`."""

    code: VoucherCode
    kind: Literal["whole"]
    window_id: Id
    sauna_id: Id


VoucherQuoteIn = Annotated[Annotated[SeatQuoteIn, Tag(KIND_TAG + "seats")] | Annotated[WholeQuoteIn, Tag(KIND_TAG + "whole")],
                           Discriminator(_kind_of)]


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
    """A Sauna of the Venue facts; `whole_price_ore` is null for a Sauna that is not offered whole (AD-23)."""

    id: int
    name: str
    capacity: int
    whole_price_ore: int | None


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


class PaidOut(BaseModel):
    """How a Booking was paid (FR-28, AD-31): its `charge` rows summed by method, in øre."""

    voucher_ore: int
    card_ore: int


class VoucherQuoteOut(BaseModel):
    """What a Voucher would pay (FR-28): never its balance or expiry."""

    voucher_part_ore: int
    card_part_ore: int


class SaunaRef(BaseModel):
    """The Sauna of a Whole-sauna booking: its id and name, never its Capacity (AD-23)."""

    id: int
    name: str


class BookingOut(BaseModel):
    """A Booking as every page shows it (FR-8), from the one serializer (AD-23): `kind`, the stored price and total in
    øre, the Venue date and the Window's start and end in Venue time. A Seat booking has `seats` and
    `price_per_seat_ore` and `sauna` null (FR-4, AD-25); a Whole-sauna booking has `sauna` and `seats` and
    `price_per_seat_ore` null. No internal Booking id."""

    reference: str
    kind: Literal["seats", "whole"]
    date: str
    start: str
    end: str
    seats: int | None
    price_per_seat_ore: int | None
    sauna: SaunaRef | None
    total_ore: int
    name: str
    email: str
    status: str
    paid: PaidOut


class EmailOut(BaseModel):
    subject: str
    body: str


class BookingResult(BaseModel):
    """`POST /api/bookings` (also a repeat) and `GET /api/bookings/{reference}/confirmation`: the Booking as it is now
    and the emails its action sent."""

    booking: BookingOut
    emails: list[EmailOut]
