"""The FastAPI app: factory, lifespan and middleware only. Routes live in `api/`, rules in `services/`, SQL in `db/`.

Startup: read the configuration (AD-14, AD-22), create `booking_dev` when the default URL is used, apply the
migrations (AD-15), open the pool, apply the seed (AD-18), generate the Windows up to the Booking horizon (FR-13),
create the sample Bookings that do not exist yet (AD-18), run the retention catch-up (FR-21: anonymise the Bookings
due for retention and clear their Outbox emails) and purge expired sessions (AD-8). The seed file is also checked
before uvicorn starts (`booking_platform.main`), so an invalid seed stops startup with one line.
"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import config, db
from .api import admin, errors, public
from .api.deps import UNSAFE_METHODS, same_origin
from .db import migrate
from .services import catchup, seed, sessions, windows

log = logging.getLogger("booking_platform")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings, _switches = config.load()
    migrate.ensure_database(settings.database_url)
    migrate.migrate(settings.database_url)
    db.open_pool(settings.database_url)
    try:
        seed.apply()
        log.info("generated %d windows", windows.ensure_generated())
        seed.apply_bookings()  # the sample Bookings need their Windows (AD-18)
        caught_up = catchup.run()  # counts only, never a name or an email (AD-19)
        log.info("retention catch-up: %d bookings anonymised, %d emails cleared",
                 caught_up["bookings_anonymised"], caught_up["emails_cleared"])
        purged = sessions.purge_expired()
        log.info("purged %d expired sessions", purged)
        yield
    finally:
        db.close_pool()


def _json(status: int, code: str) -> tuple[dict, dict]:
    body = json.dumps({"detail": {"error": code}}, separators=(",", ":")).encode()
    start = {"type": "http.response.start", "status": status,
             "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]}
    return start, {"type": "http.response.body", "body": body}


class RequestGuard:
    """Pure ASGI middleware around every HTTP request:

    - the same-origin rule for POST, PUT, PATCH and DELETE (AD-8): anything else is `403 cross_origin` and nothing
      runs;
    - `config.in_request` is true while the request runs, so the `force_conflict` seam applies to it (AD-14);
    - an unexpected exception becomes `500 internal_error`, logged by type only (AD-19: no bodies, headers or
      cookies, and no store text)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if scope["method"] in UNSAFE_METHODS:
            headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope["headers"]}
            if not same_origin(headers.get("origin"), headers.get("sec-fetch-site")):
                start, body = _json(403, "cross_origin")
                await send(start)
                await send(body)
                return
        started = False

        async def tracked_send(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        token = config.in_request.set(True)
        try:
            await self.app(scope, receive, tracked_send)
        except Exception as e:  # noqa: BLE001 - the last line of defence; see the docstring
            log.error("unhandled %s on %s %s", type(e).__name__, scope["method"], scope["path"])
            if started:
                raise
            start, body = _json(500, "internal_error")
            await send(start)
            await send(body)
        finally:
            config.in_request.reset(token)


def create_app() -> FastAPI:
    app = FastAPI(title="Saunalöyly booking platform", lifespan=lifespan, redirect_slashes=False,
                  docs_url=None, redoc_url=None, openapi_url=None)
    errors.install(app)
    app.include_router(public.router)
    app.include_router(admin.sign_in_router)
    app.include_router(admin.router)
    app.add_middleware(RequestGuard)
    return app


app = create_app()
