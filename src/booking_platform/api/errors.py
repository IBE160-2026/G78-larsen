"""The one code -> status table (AD-16) and the exception handlers that turn every failure into the envelope
`{"detail": {"error": "<code>", "message"?: "<dev text>", ...facts}}`. Store text never reaches a response."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..services.errors import Refused, StoreError

log = logging.getLogger("booking_platform.api")

STATUS: dict[str, int] = {
    "no_session": 401,  # a Guest write without a session (AD-8)
    "not_signed_in": 401,  # anonymous caller on /api/admin/ (AD-10)
    "sign_in_refused": 401,  # every failed sign-in: wrong password, unknown email or throttled email (FR-15, PW-5)
    "cross_origin": 403,  # a state-changing request that is not same-origin (AD-8)
    "not_allowed": 403,  # a session without the Administrator role on /api/admin/ (AD-10)
    "not_found": 404,  # unknown path, 405, unknown or not yours (AD-10)
    "no_seat_free": 409,  # the store's capacity CHECK (FR-10, FR-12)
    "rule_refused": 409,  # a named store rule (FR-29, FR-41)
    "already_exists": 409,  # one of the slice's UNIQUE keys
    "deadline_passed": 409,  # past the Window's Booking deadline (FR-39)
    "outside_horizon": 409,  # a date before today or after the end of the Booking horizon (FR-2), or a Window
    # that starts after it, on a booking, Hold or Whole-sauna booking (FR-18 IV-2, AD-4)
    "release_after_deadline": 409,  # the Release time is later than a Booking deadline (FR-39, FR-41)
    "cutoff_passed": 409,  # a Change after the Booking's Cutoff (AD-4, AD-16); fact `cutoff_at`
    "invalid_key": 409,  # an Idempotency-Key already used by another session or for another request (AD-9)
    "payment_pending": 409,  # the payment is held (test switch `payment = "hold"`, AD-14); nothing written
    "payment_failed": 409,  # the payment failed (test switch `payment = "fail"`, FR-7); nothing written
    "invalid_input": 422,  # a shape error from Pydantic, with `fields`
    "internal_error": 500,  # an unmapped store error or a bug; never carries store text
    "try_again": 503,  # retries used up (FR-14)
}


def envelope(code: str, **facts) -> JSONResponse:
    return JSONResponse(status_code=STATUS[code], content={"detail": {"error": code, **facts}})


def _field(loc: tuple) -> str:
    parts = loc[1:] if loc and loc[0] in ("body", "query", "path", "header", "cookie") else loc
    return ".".join(str(p) for p in parts) or str(loc[0])


async def _refused(_: Request, exc: Refused) -> JSONResponse:
    if exc.code not in STATUS:
        log.error("undeclared refusal code %s", exc.code)
        return envelope("internal_error")
    return envelope(exc.code, **exc.facts)


async def _invalid(_: Request, exc: RequestValidationError) -> JSONResponse:
    fields = sorted({_field(tuple(e.get("loc", ()))) for e in exc.errors()})
    return envelope("invalid_input", fields=fields)


async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code in (404, 405):
        return envelope("not_found")
    if 400 <= exc.status_code < 500:  # e.g. FastAPI's 400 for a body it cannot decode: a shape error
        return envelope("invalid_input", fields=[])
    log.error("http error status=%s", exc.status_code)
    return envelope("internal_error")


async def _store(request: Request, exc: StoreError) -> JSONResponse:
    log.error("store error sqlstate=%s constraint=%s on %s %s", exc.sqlstate, exc.constraint,
              request.method, request.url.path)
    return envelope("internal_error")


def install(app: FastAPI) -> None:
    app.add_exception_handler(Refused, _refused)
    app.add_exception_handler(RequestValidationError, _invalid)
    app.add_exception_handler(StarletteHTTPException, _http)
    app.add_exception_handler(StoreError, _store)
