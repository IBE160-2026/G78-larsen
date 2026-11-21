---
title: 'Story 2.2: Booking list for a chosen day'
type: 'feature'
created: '2026-11-21'
status: 'done'
baseline_commit: '877f6227e7d58568d1271ec98261146ae1136a62'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/planning-artifacts/epics.md'
  - '{project-root}/.docs/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A signed-in Administrator sees only the bar and an `h1` on `/admin/bookings`. Nothing shows the day's sessions, how full they are or who booked, and nothing yet proves FR-16 or the FR-21 retention rule.

**Approach:** Build Story 2.2 as written in `.docs/planning-artifacts/epics.md` (L847–909): migration `0009` with `retention_due(booking_id)`, a read-only `GET /api/admin/bookings`, a startup catch-up in `services/catchup.py`, and the Booking list page with its tests.

## Boundaries & Constraints

**Always:**
- `GET /api/admin/bookings` (guarded router) takes an optional `date` (`YYYY-MM-DD`, same validator as `WindowsQuery`, extra fields forbidden). It answers `{"today", "date", "windows": [...]}`. With no date it uses `venue_today()`, so the page's default is the API's `today`, never the browser clock. Any calendar date is allowed, including past ones and dates after the horizon.
- Each Window: every Window with `venue_date(w.id) = date` (no bookable filter), in start order, with `id`, `start`, `end` (Venue-tz ISO, as in `windows._shape`), `seat_capacity` = `window_open_capacity`, `seats_booked` = `window_booked_seats`, `seats_left` = `seats_left` and `bookings`. Bookings are the `status='active'` rows, ordered by `created_at` then `id`, with `reference`, `name`, `email`, `seats`, `total_ore` and `created_at` (Venue-tz ISO).
- The read calls `windows.ensure_generated()` first, then one `db.run` of SELECTs. It takes no lock and writes nothing else.
- Masked read: when `retention_due(b.id)`, `name` and `email` are returned as the anonymised values (see Decisions) by SQL `CASE`, never by writing.
- `retention_due(bid bigint) RETURNS boolean`: `app_now() > upper(w.during) + interval '12 months'` for the Booking's Window. It is the only retention predicate. Epic 4 extends it with the Voucher clause.
- `services/catchup.py` has one function per effect, each one `db.run` returning its count: `anonymise_bookings()` sets name and email to the anonymised values for due Bookings not yet anonymised; `clear_emails()` sets `recipient` and `body` to `''` on the Outbox emails of due Bookings. `run()` calls both, and the lifespan calls `run()` after `seed.apply_bookings()` and logs the counts only. Running it twice changes nothing the second time.
- Page copy comes from `lib/copy.js`, browser calls go only through `lib/api.js`, styling only in `app/styles.css`, and keyboard steps in e2e tests only through `a11y.press`/`a11y.tab_to`. Stored text is rendered as React text, never as HTML.

**Never:** Edit migrations `0001`–`0008`. Add search, sorting, editing, booking status or Whole-sauna columns. Read the browser clock for the default date. Write anything on a GET apart from `ensure_generated()`. Build the Outbox page (Story 2.3).

**Decisions (Lisa, 2026-11-21):**
- Anonymised values: name `Anonymised`, email `anonymised@example.invalid`, both in the masked read and in the catch-up.
- A date with no sessions shows "No sessions on this day" under the date field.
- Scope: the story stays whole (about 2700 tokens).

**Decisions (planning, confirmed by Lisa at approval 2026-11-21):**
- The date lives in the address: `/admin/bookings?date=YYYY-MM-DD`. "Previous day" and "Next day" are real Text links to the neighbouring dates, so reload and Back keep the day. Without `?date` the page shows the API's `today`. The date field commits on Enter or blur and replaces the address. A malformed typed date shows a Field error with the existing `BOOK.dateFormat` copy, "Enter the date as dd.mm.yyyy".
- Layout follows `mockups/key-booking-list.html`: one `section` per session with an `h2` "10:00–11:30" (`aria-label` "Session 10:00 to 11:30"), then "Seat capacity 44 · Seats booked 6 · Seats left 38", then a table with a visually hidden caption "Bookings in the session 10:00 to 11:30" and columns Reference, Name, Email, Seats, Total, Time of booking (the last three right-aligned). A full session's header has the `unavailable` fill, with "Seats left 0" and "Sold out" in weight 600.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error Handling |
|---|---|---|---|
| Day with Bookings | `world` Windows plus Guest-flow Bookings | 3 Windows in time order, Bookings oldest first, `seats_left` equal to `GET /api/windows` | — |
| No date | `GET /api/admin/bookings` | `date` = `today` | — |
| Empty day | date with Windows, no Bookings | every Window with `bookings: []` | page: "No bookings" per session |
| No Windows | date after the horizon | `windows: []` | page: "No sessions on this day" |
| Bad query | `date=2026-1-1`, `date=x`, `foo=1` | `422 invalid_input`, nothing written | — |
| Anonymous / Guest session | no cookie, or a booking session | `401 not_signed_in` | page goes to Sign-in |
| New Booking | a Booking between two reads | appears on the second read | — |
| Retention | clock moved to 12 months + 1 s after the Window end | name/email masked, row unchanged | — |
| Catch-up | same clock, `catchup.run()` | rows anonymised, linked emails' recipient and body `''`, second run counts 0 | — |
| Hostile text | raw row with name `<script>alert(1)</script>`, SQL text in email | shown as text, no dialog | — |
| Failed read | `5xx` or network error | — | Notice "…please try again" |

</frozen-after-approval>

## Code Map

- `migrations/0008_accounts_sign_in.sql` -- latest. New `0009_retention.sql` adds `retention_due(bid bigint)` (LANGUAGE sql VOLATILE, because `app_now()` is volatile). `tests/test_dr4_migrations.py` picks it up automatically.
- `migrations/0001_core.sql:74-96` -- `window_open_capacity`, `seats_left`; `0006_bookings_pay.sql:53` -- `window_booked_seats` counts only `active`. `0006:13-48` bookings columns and CHECKs; `0006:75-82` `outbox_emails` (recipient/body `NOT NULL`, `booking_id` FK). Name/email updates fire no Window trigger.
- `src/booking_platform/db/windows.py:60-69` -- `windows_on` and `_ROW`: the pattern for the new admin query, without `_BOOKABLE`. `horizon()` (:22) gives `venue_today()` and `venue_tz`.
- `src/booking_platform/services/windows.py:107-150` -- `ensure_generated()`, `_shape()`, `listing()`: follow the same shape. Put the new read in a new `services/booking_list.py` with its SQL in `db/booking_list.py`.
- `src/booking_platform/api/schemas.py:17-36` -- `Strict`, `WindowsQuery` and its date validator: reuse the validator for `BookingListQuery`. `api/errors.py:59` turns validation errors into `invalid_input`.
- `src/booking_platform/api/admin.py:16` -- guarded router; add the GET here (`Annotated[BookingListQuery, Query()]`, as in `api/public.py:29`).
- `src/booking_platform/app.py:28-43` -- lifespan; add `catchup.run()` and update the module docstring.
- `tests/conftest.py` -- `world` (3 Windows from 2026-12-01 10:00 Oslo, clock at `EARLY`), `api`, `admin`, `pg`, `raw_booking`, `set_clock` (:196), `start_backend`.
- `frontend/app/admin/bookings/page.js` -- server page with `metadata.title` "Booking list" and the guard. Add a client `components/BookingList.js` inside `AdminGuard`, wrapped in `Suspense` (it uses `useSearchParams`).
- `frontend/lib/dates.js` -- `dotted`, `parseDotted`, `clockTime`. Add `addDays(iso, n)` and `dottedTime(ts)` (`dd.mm.yyyy HH:MM` sliced from the Venue-tz ISO, no Intl). `lib/venue-format.js:21` `nok`. `lib/copy.js` `ADMIN` gets the page copy.
- `frontend/components/Notice.js`, `FieldError.js`, `TextLink.js` -- reuse. `components/BookSeats.js:172-199` is the commit-on-blur/Enter pattern.
- `frontend/app/styles.css` -- tokens `--color-unavailable`, `.tabular`, `.heading-md`, `.admin-main` (1099-1155). There is no table CSS yet; add `.booking-table` and `.session-group` here.
- `tests/e2e/test_fr15_sign_in.py:26-77` -- `LOGIN`, `no_throttle`, `open_sign_in`, `type_login`: move them to a shared `tests/e2e/admin.py` and import them in both tests. `tests/e2e/test_fr05_book_and_pay.py:32-64` -- `free_windows`, `open_session`, `book_in_browser`: move them to `tests/e2e/guest.py` likewise.

## Tasks & Acceptance

**Execution:**
- [x] `migrations/0009_retention.sql` -- `retention_due` -- FR-21, AD-4
- [x] `db/booking_list.py`, `services/booking_list.py`, `api/schemas.py`, `api/admin.py` -- the read with masking -- FR-16, AD-4, AD-5
- [x] `services/catchup.py`, `app.py` -- the startup catch-up -- FR-21, AD-4, AD-12
- [x] `tests/test_fr16_booking_list.py` -- the matrix rows except the page ones; equality with `GET /api/windows` after Guest-flow Bookings that make one Window 42 of 44 and another full; ordering; a GET writes nothing (row counts and `xmin` unchanged) -- FR-16, FR-18
- [x] `tests/test_fr21_retention.py` -- masked read with no write; `catchup.run()` effects and idempotence; one day before the limit nothing is masked; a `start_backend` run past the limit anonymises at startup -- FR-21
- [x] `frontend/components/BookingList.js`, `app/admin/bookings/page.js`, `lib/dates.js`, `lib/copy.js`, `app/styles.css` -- the page -- UX-DR31, UX-DR33, UX-DR37
- [x] `tests/e2e/admin.py`, `tests/e2e/guest.py`, `tests/e2e/test_fr15_sign_in.py`, `tests/e2e/test_fr05_book_and_pay.py` -- move the shared helpers, no assertion changes
- [x] `tests/e2e/test_fr16_booking_list.py` -- sign in; a Guest-flow Booking is found in the right group with its reference, name, "NOK" total and time; Previous/Next day by keyboard only; the hostile raw row renders as text and no dialog opens; the sold-out header says "Sold out"; the failed-read Notice via `page.route`; title "Booking list – Saunalöyly"; axe A/AA; no horizontal scroll at 1024/1366/1920 -- FR-16, FR-22, FR-23

**Acceptance Criteria:**
- Given `uv run pytest`, then every test passes, including those of Stories 1.1–2.1.
- Given `npm --prefix frontend run build`, then it succeeds.
- Given the seeded stack, when the Administrator opens the list for today + 2 and today + 3, then the sessions show Seats left 2 and a sold-out header, matching Book seats.

## Implementation Notes

## Spec Change Log

## Review Triage Log

Iteration 0 (layers: blind-hunter, edge-case-hunter, verification-gap).

| # | Source | Location | Verdict | Route | Evidence |
|---|---|---|---|---|---|
| 1 | verification-gap | `BookingList.js` 401 branch | medium | patch | Pre-verified gap: only a 500 is stubbed; dropping the 401 branch would leave an expired admin on "please try again" with no failing test. |
| 2 | verification-gap | `0009_retention.sql` `>` vs `>=` | low | reject | `app_now()` keeps running after `set_clock`, so "exactly LIMIT" cannot be pinned; the proposed test would read a time past LIMIT. Boundary is one instant. |
| 3 | blind-hunter, edge-case-hunter | `BookingList.js` `asked` guard | low | patch | `?date=2026-02-30` passes the shape regex, the API answers 422 and the page shows a Notice a retry cannot fix; `parseDotted(dotted(raw)) === raw` (parseDotted checks days in month) is a direct correction matching the malformed-address fallback. |
| 4 | edge-case-hunter | `BookingList.js` commit, year 0000 | low | reject | Typing 00.01.0000 by hand is unlikely; fix adds a guard. |
| 5 | edge-case-hunter | `dates.js` `addDays` years < 100 | low | reject | Only reachable by hand-typing a year below 100; fix adds code. |
| 6 | blind-hunter, edge-case-hunter | `BookingList.js` `shown` while loading | low | patch | While a new `?date` loads, `shown` is the old day, so Previous/Next point at the old day's neighbours and the old sessions stay under a changed address; preferring `asked` and not keeping the old data is a direct correction. |
| 7 | edge-case-hunter | `BookingList.js` setText while typing | low | reject | A fetch only starts on navigation; typing during that load is rare; fix adds a focus check. |
| 8 | blind-hunter, edge-case-hunter | blur commit vs link click | low | reject | Either outcome lands on a valid day; fix needs a mousedown flag. `replace` for the typed date is what the spec asks. |
| 9 | blind-hunter, edge-case-hunter | failed first read hides date bar | low | reject | The Notice says to try again and reload is the remedy; showing Prev/Next needs a date there is none of; fix adds a branch. |
| 10 | blind-hunter | field text after a failed `?date` read | low | reject | Cosmetic mismatch until the next successful read; fix adds an effect. |
| 11 | blind-hunter | Whole-sauna bookings / blocked sessions "Sold out" | false | reject | Intent's Never list excludes Whole-sauna columns; a session with no Seats left is unavailable to Guests too, which is what the header states. |
| 12 | blind-hunter | `retention_due` per row, `venue_date` scan | low | reject | One Venue, a few Windows per day; spec makes `retention_due(booking_id)` the only predicate. No named harm at this size. |
| 13 | blind-hunter, edge-case-hunter | catch-up only at startup | false | reject | Intent specifies a startup catch-up plus masked reads; there is no other admin read of name/email yet (Outbox page is Story 2.3). |
| 14 | blind-hunter, edge-case-hunter | two transactions in `catchup.run()` | false | reject | Spec requires one `db.run` per effect; both writes are idempotent, so the next start completes a partial run; failing startup on a DB error matches the other lifespan steps. |
| 15 | blind-hunter, edge-case-hunter | e2e leaves rows behind / today+4 empty | false | reject | The e2e `stack` fixture ends with `compose down -v`, so every run starts from a fresh database; today+4 is inside the seeded horizon (test passed). |
| 16 | blind-hunter | `no_throttle` autouse in `admin.py` | low | reject | Works as imported; the spec places the helpers in `tests/e2e/admin.py`; moving it to conftest changes which modules get it. |
| 17 | blind-hunter | misleading `noqa` in `test_fr05` / leftover imports in `test_fr15` | false | reject | `test_fr11` and `test_fr21_privacy` still import these names from `test_fr05`; `psycopg` and `pytest` are used in `test_fr15` (lines 89, 100). |
| 18 | blind-hunter | no unit tests for `addDays`/`dottedTime`, Feb 29/DST | low | reject | Repo has no frontend unit tests; e2e covers Next/Previous and the time format; `win_start(1)` is fixed at 2026-12-01, so the 29 February case cannot occur. |
| 19 | blind-hunter | `win_start(1)` comment | false | reject | The comment is correct: `win_start(1)` is the end of Window 1. |
| 20 | blind-hunter | Time column right-aligned | false | reject | Spec: "the last three right-aligned". |
| 21 | blind-hunter | no `th scope="row"`, log grammar "1 bookings" | low | reject | Cosmetic; axe passes; not asked for in the spec. |
| 22 | blind-hunter | spec not in the diff | false | reject | Deliberate: the spec goes only to the edge-case layer as claims. |

## Verification

**Commands:**
- `uv run pytest -q` -- expected: all pass
- `npm --prefix frontend run build` -- expected: success
