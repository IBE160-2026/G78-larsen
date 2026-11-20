---
title: 'Story 1.1: The capacity slice runs on the spine''s backend structure'
type: 'refactor'
created: '2026-11-20'
status: 'done'
baseline_commit: 'a92152ded6462f5e3c2d67935593d5180206e879'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/planning-artifacts/architecture/architecture-booking-platform-2026-11-03/ARCHITECTURE-SPINE.md'
  - '{project-root}/.docs/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The capacity slice (`src/booking_platform/app.py`, `db.py`, `schema.sql`) puts SQL and rules in routes, trusts a client-chosen `session_id`, has no migration runner, no `/api` prefix, open Administrator endpoints and no CSRF check. Every later story needs the spine's structure first.

**Approach:** Reshape the slice onto the spine (AD-1, 3, 4, 8, 10, 14, 15, 16, 21, 22) exactly as Story 1.1 in `.docs/planning-artifacts/epics.md` lists, without loosening any store rule. Keep every slice test as regression proof: change only the setup and transport, never an assertion.

## Boundaries & Constraints

**Always:**
- Dependencies run `api` → `services` → `db`, and `config` is a leaf. SQL text appears only in `db/` and `migrations/`.
- `migrations/0001_core.sql` is byte-identical to today's `schema.sql`. Store changes go in new numbered files.
- Every refusal is `services.errors.Refused(code, **facts)`. Store errors are mapped by constraint name in `db`, including at COMMIT. Unmapped errors are `500 internal_error` with no store text.
- The slice's assertions, `MUTATIONS` and bypass tests stay unchanged in meaning, and each mutation still turns its test red.
- Session expiry is judged on `app_now()`, and the sliding touch is one autocommit statement outside the action transaction.

**Never:**
- Loosen a CHECK, trigger or lock to make a test pass.
- Build the compose stack, seed, Caddy or frontend (Story 1.2 and later), or the `accounts` table and sign-in (Story 2.1).
- Write CSRF tokens, read `X-Forwarded-*` or compare with `Host`.
- Log request bodies, headers or cookies.

**Decisions (made in planning, not by the human):**
- **Migration numbers:** `0002_sessions.sql` and `0003_named_store_refusals.sql`. AD-15 gives each story its number at merge, so AD-7's status migration takes the next free number in Story 1.5.
- **Holds:** `holds.session_id` becomes `bigint NULL REFERENCES sessions ON DELETE SET NULL`. Existing holds are deleted in `0002`; they are 10-minute rows in dev databases only.
- **New codes:** `401 not_signed_in` (anonymous on `/api/admin/`), `403 not_allowed` (non-Administrator), `404 not_found`, `422 invalid_input`, `500 internal_error`. The slice's `empty_period` becomes a Pydantic validator, so it answers `422 invalid_input`. The slice's catch-all `refused` is dropped, because unmapped errors are now 500.
- **Roles:** `sessions.role` is `guest` or `admin`. The test fixture inserts the `admin` row directly until Story 2.1.
- **CSRF:** the Origin rule applies to POST, PUT, PATCH and DELETE. The DELETE endpoints carry no body.
- **Cookie:** the cookie is named `bp_session`. `POST /api/session` answers `{"role": …}`.
- **`force_conflict`:** applies only when `config.in_request` (a ContextVar set by app middleware) is true and the transaction has written (`pg_current_xact_id_if_assigned()` is not null). It then raises a real 40001 before commit.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected |
|---|---|---|
| Last Seat race | 2 parallel `POST /api/bookings` for 1 Seat, 43 booked | one 201, one `409 no_seat_free` (100 rounds) |
| No session | `POST /api/holds` without cookie | `401 no_session`, nothing written |
| Cross-origin | POST with `Origin: http://evil.example` | `403 cross_origin`, nothing written |
| No Origin, same-origin fetch | POST with only `Sec-Fetch-Site: same-origin` | accepted |
| Anonymous admin | `POST /api/admin/marks` without session | `401 not_signed_in`; guest session → `403 not_allowed` |
| Unknown path / 405 | `GET /api/nope`, `GET /api/health/`, `DELETE /api/health` | `404 {"detail":{"error":"not_found"}}` |
| Seats out of range | `seats: 0`, `seats: 11`, extra field | `422 invalid_input` with `fields` |
| Unmapped store error | trigger error with no constraint name | `500 internal_error`, no store text |
| Duplicate migration number | `0002_a.sql` + `0002_b.sql` | startup refuses |
| Legacy database | `windows` exists, no `schema_migrations` | `0001_core.sql` recorded as applied, later files run |
| Switch file broken | invalid TOML at `BP_TEST_SWITCHES` | startup stops with one line naming the file |
| Switch file missing or a directory | — | every switch is off |

</frozen-after-approval>

## Code Map

- `src/booking_platform/app.py` -- slice routes holding SQL and rules; becomes app factory + lifespan + middleware only
- `src/booking_platform/db.py` -- pool, `run` with retry (`RETRIES = 5`), `TryAgain`, `lock_windows`, `raw_connection`; move into `db/__init__.py`, keep retry semantics
- `src/booking_platform/schema.sql` -- move unchanged to `migrations/0001_core.sql`. Unnamed trigger raises live in `trg_check_whole` (L181–201), `trg_check_mark` (L204–216), `trg_check_release` (L222–229) and `verify_window` (L242–252)
- `tests/conftest.py` -- `MUTATIONS` names `lock_windows`, `recompute_window`, `window_held_seats`, `t_verify`, `t_bookings`. `0003` must not rename these
- `tests/test_fr10_through_the_api.py` -- helpers `parallel`, `book`, `hold`, `fill`, `left` are reused by the other files
- `tests/test_application_rules.py`, `tests/test_fr10_bypass.py`, `tests/test_fr14_retry.py` -- the other slice tests. Bodies with `seats` above 10: `/holds` 14 and 36, `/bookings` 40 and 44
- `docker-compose.yml` -- db service only. Add a `pg_isready` healthcheck and bind `127.0.0.1:${DB_PORT:-55432}`
- `README.md` -- "Kom i gang" uses `uv run booking-platform` and the old URL. The status table says epics have not started

## Tasks & Acceptance

**Execution:**
- [x] `migrations/0001_core.sql` -- `git mv` of `schema.sql`, unchanged -- AD-15
- [x] `migrations/0002_sessions.sql` -- `sessions(id bigserial, token_hash bytea UNIQUE NOT NULL, role text CHECK in (guest, admin), created_at, expires_at)`; holds FK change as decided -- AD-8
- [x] `migrations/0003_named_store_refusals.sql` -- `CREATE OR REPLACE` of the four trigger functions with identical logic, adding `CONSTRAINT = 'whole_not_bookable' | 'whole_blocked' | 'whole_seats_placed' | 'whole_window_started' | 'mark_not_bookable' | 'mark_seats_placed' | 'release_not_due' | 'window_out_of_step'` -- AD-1
- [x] `src/booking_platform/config.py` -- frozen settings from the `BP_*` variables with AD-22 defaults, `paths.ROOT`, switches via `tomllib` (`payment`: ok/fail/hold, `force_conflict`: bool), the `in_request` ContextVar, and the HTTPS/base-URL refusal -- AD-14, AD-22
- [x] `src/booking_platform/db/__init__.py` -- pool (READ COMMITTED, `TimeZone=UTC`), `run` (retry, `force_conflict` seam, refusal translation also at COMMIT), `lock_windows`, `StoreError` -- AD-1, AD-3
- [x] `src/booking_platform/db/refusals.py` -- constraint name → code map: `booked_within_capacity` → `no_seat_free`; the eight new names except `window_out_of_step` → `rule_refused`; the slice's UNIQUE keys → `already_exists`; `*_fkey` → `not_found`
- [x] `src/booking_platform/db/migrate.py` -- create `booking_dev` when the URL is the default; advisory-locked runner; legacy rule; duplicate-number refusal -- AD-15, AD-22
- [x] `src/booking_platform/db/{seats,venue_admin,sessions}.py` -- all SQL from today's `app.py`, plus session SQL (create, resolve-and-touch in one `UPDATE … RETURNING`, purge)
- [x] `src/booking_platform/services/{errors,windows,holds,booking,whole,blocks,marks,settings,sessions}.py` -- the slice's rules moved from `app.py`, raising `Refused`
- [x] `src/booking_platform/api/{errors,schemas,public,admin,deps}.py` -- code → status table; `extra="forbid"` models with Seats 1–10; `/api` router; `/api/admin` router with role dependency; session and CSRF dependencies; exception handlers for `Refused`, `RequestValidationError`, Starlette 404/405 and `StoreError` -- AD-10, AD-16
- [x] `src/booking_platform/app.py` -- `docs_url=None`, `openapi_url=None`, `redoc_url=None`, `redirect_slashes=False` everywhere, CSRF and `in_request` middleware, lifespan (ensure db, migrate, purge sessions, open pool)
- [x] `src/booking_platform/__init__.py` -- argparse `dev` (reload) and `serve` → uvicorn on `BP_HOST:BP_PORT` -- AD-22
- [x] `config/test-switches.example.toml`, `.gitignore` -- example with every switch off; ignore `config/test-switches.toml`
- [x] `tests/client.py` -- `api_client(base, *, session=True)` sends `Origin`, optionally opens a session, and exposes `session_id`; `admin_client(base, pg)` inserts an admin session
- [x] `tests/conftest.py` -- `docker compose up -d --wait db`; admin URL from `config`; recreate `booking_test`; migrate; mutate; start `uv run booking-platform serve` with its own port, base URL and switch file; log output to a temp file
- [x] slice test files -- `/api` paths; a session per former `session_id`, created before any barrier; admin calls via `admin_client`; over-10 setups split into ≤10 Bookings or raw inserts; raw hold inserts use `NULL` or a real session id
- [x] `tests/test_fr18_csrf.py`, `tests/test_fr20_access.py`, `tests/test_fr21_sessions.py`, `tests/test_fr2_input.py`, `tests/test_dr4_migrations.py`, `tests/test_fr14_switches.py` -- one test per matrix row, plus cookie flags, the 24 h lifetime, return of a still-valid session, the startup purge, and no token or body in the backend log
- [x] `docker-compose.yml`, `README.md` -- healthcheck and port; dev command `uv run booking-platform dev`, `uv run pytest`, updated status -- DR-2

**Acceptance Criteria:**
- Given the repo, when grepping, then no `api/` module imports `db` or `psycopg`, and no `.py` file outside `db/` contains SQL text.
- Given `BP_TEST_MUTATE=<name>` for each `MUTATIONS` key, when the matching bypass test runs, then it fails, and it passes without the mutation.
- Given a fresh clone, when `uv run pytest` runs, then everything passes, with the same assertions as before.

## Implementation Notes

- `Refused`/`StoreError` are defined in `db/refusals.py` and re-exported by `services/errors.py`, so `db` imports nothing above it.
- `test_a_non_temporary_error_is_not_retried` now forces a 23514 named `booked_within_capacity` (an unnamed 23514 is a 500 under AD-1); a separate test covers the unnamed case.
- The slice's `no_such_window` became `404 not_found`. `POST /api/session` takes `{}`. The cookie has no Max-Age.
- On Windows the test backend is stopped with `taskkill /T /F`, because `uv run` leaves its child running.

## Spec Change Log

## Review Triage Log

Pass 1 (blind-hunter BH, edge-case-hunter EC, verification-gap VG):

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| BH1 | App loggers (`booking_platform.*`) have no handler; info lines lost | medium | uvicorn's default log config covers only `uvicorn.*`; root stays at WARNING | patch |
| BH2/EC1/EC2 | Unbounded ints (`window_id`, `sauna_id`, `booking_deadline_minutes`) reach the store → 500 | medium | `lock_windows(%s)` with an int above 2³¹ adapts to `bigint[]`, no matching function (42883) → `StoreError` | patch |
| BH3 | Empty Block period reports `fields: ["body"]` | low | model-level validator has loc `("body",)` | patch (with EC3) |
| EC3/EC4 | Mixed naive/aware Block datetimes → TypeError → 500; naive read as UTC | medium | Pydantic converts only ValueError/AssertionError; pool TimeZone=UTC | patch |
| EC5 | FastAPI's 400 (undecodable body) becomes 500 | low | `fastapi.routing` raises `HTTPException(400)` for non-JSONDecodeError body errors; `_http` maps non-404/405 to 500 | patch |
| BH8 | Retries used up leave no log line | low | `run` drops the last exception; one log line fixes it | patch |
| BH9/EC16 | README says "uendrede påstander", but an unnamed 23514 is now 500 and some setups changed | low | README L26; `test_fr14_retry.py` forced constraint name | patch |
| VG1 | `Secure` cookie flag with `BP_HTTPS=on` untested | medium | only the negative case is asserted | patch |
| VG2 | Named whole/mark refusals → `rule_refused` not pinned by a test | medium | only status 409 or random mixed load | patch |
| VG3 | `_fkey` → `404 not_found` untested | medium | no test sends an unknown `sauna_id` | patch |
| VG4 | Middleware 500 fallback untested | medium | needs a fault seam that does not exist | defer |
| VG5 | 0002 on a legacy db with data, and concurrent migrate, untested | medium | dev-only data; one process migrates at a time today | defer |
| BH4 | No checksum of applied migrations | low | not required by AD-15; adds a column and checks | reject |
| BH5 | Migration/DB errors at startup print a traceback | low | the one-line rule is AD-14's, for the switch file only | reject |
| BH6 | Sessions purged only at startup; creation unthrottled; no indexes | low | AD-8 specifies startup purge; v1 is local only | reject |
| BH7 | `_fkey` mapping ignores SQLSTATE (23503 on delete) | low | no endpoint deletes a referenced row today | reject |
| BH10/EC7 | Base URL with explicit default port never matches `Origin` | low | defaults and compose use no explicit default port | reject |
| BH11 | README `DB_PORT` advice vs `ensure_database` default-only | false | AD-22 specifies creation for the default URL only | reject |
| BH12a | `window_out_of_step` → 500 untested | low | bypass-only; no API path reaches it | reject |
| BH12b | Admin cookie on `POST /api/session` untested | low | same code path as the guest test | reject |
| BH13 | Some test clients not closed on failure | low | test-only, failure path only | reject |
| EC6 | Empty `loc` → IndexError | false | Pydantic validation errors always carry a loc | reject |
| EC8 | `BP_PORT` range unchecked | low | uvicorn refuses it at bind | reject |
| EC9 | Relative `BP_TEST_SWITCHES` resolves against cwd | low | tests pass absolute paths; AD-14 names a path | reject |
| EC10–EC13 | Missing migrations dir, `.SQL` suffix, renamed applied file, legacy without 0001 | low | each needs a deliberate misconfiguration | reject |
| EC14 | Two processes create `booking_dev` at once | low | dev runs one backend | reject |
| EC15 | Unlisted constraints (`hold_at_most_10_min`, `blocks_during_check` …) now 500 | false | each is guarded upstream (Pydantic, computed expiry, validator); not reachable through the API | reject |
| EC17 | AC "no SQL outside db/" fails for tests | low | fix would edit this spec | reject |

## Design Notes

The `Refused` path in short: `db.run` catches `psycopg.errors.IntegrityError` around the whole `with pool.connection()` block (so deferred `t_verify` at COMMIT is covered), looks up `e.diag.constraint_name` in `refusals.MAP`, and raises `Refused(code)`. When the name is unknown it raises `StoreError(sqlstate, constraint)`. `40001`/`40P01` are retried before that. `try_again` remains a `Refused('try_again')` raised by `run` after `RETRIES`.

## Verification

**Commands:**
- `uv run pytest -q` -- expected: all pass (42 old tests + new)
- `BP_TEST_MUTATE=nocheck uv run pytest -q tests/test_fr10_bypass.py` -- expected: failures (repeat for each key)
- `uv run booking-platform dev` -- expected: listens on 127.0.0.1:8001; `GET /api/health` returns 200
