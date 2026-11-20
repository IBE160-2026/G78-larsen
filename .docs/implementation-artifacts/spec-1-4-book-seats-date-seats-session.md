---
title: 'Story 1.4: A Guest picks a date, a number of seats and a session'
type: 'feature'
created: '2026-11-20'
status: 'done'
baseline_commit: '4cadaa73173691fc186977274265a734b74fc243'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/planning-artifacts/epics.md'
  - '{project-root}/.docs/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `/book-seats` does not exist, no Windows are ever generated, and `GET /api/windows` lists every Window with no date, horizon or deadline rule. A Guest cannot pick a date, a number of seats and a session, or see the true Seats left and the total (FR-2, FR-3, FR-4, FR-13).

**Approach:** Build Story 1.4 in `.docs/planning-artifacts/epics.md` (L560–630) exactly as its ACs list: migration `0005` (horizon, high-water mark, Window schedule, time predicates), the schedule in the seed, `windows.ensure_generated()`, the dated listing with nearest Windows, the Book seats page with its new shared components (Error summary, Field error, Nearest sessions) and the Booking draft, plus the API and e2e tests the ACs name.

## Boundaries & Constraints

**Always:**
- Every time rule reads `app_now()`; the listing and later actions call the same SQL predicates. No timestamptz is cast to a date or time without `AT TIME ZONE settings.venue_tz`. The frontend never uses the browser or Next.js clock: `today`, `horizon_end`, `horizon_days` and `already_started` come from the API.
- The listing writes nothing except `ensure_generated()`, and a refused listing (422 or 409) writes nothing at all. Generation never takes a Window lock on existing Windows.
- `POST /api/session` is called once, from Book seats only. Window listings go through `lib/api.js` from a client component; the price comes from `GET /api/venue` through `server-api.js`.
- Copy verbatim from EXPERIENCE.md (L160–212, L296–315). No price or Sauna in any Session row; no urgency cue anywhere. Nothing pre-selected; "Continue booking" always enabled.
- Every keyboard step in e2e goes through `a11y.press` / `a11y.tab_to`. Only `styles.css`, no `style` props.

**Never:**
- Build Details, Review, payment, `POST /api/bookings` changes, Holds UI, the Administrator schedule endpoints or the narrow Fixed action bar (Stories 1.5, 1.6, If time).
- Edit migrations `0001`–`0004`.
- Re-insert Windows before `windows_generated_through` (a removed Window stays removed).

**Decisions (made in planning):**
- **Store (`0005_windows_horizon.sql`):** `settings.booking_horizon_days int NOT NULL DEFAULT 28 CHECK (1..31)`, `settings.windows_generated_through date` (NULL = none yet). Table `window_schedule(start_time time PRIMARY KEY, end_time time NOT NULL, CHECK end > start)` with an exclusion constraint so no two schedule rows overlap (back-to-back allowed). Functions `venue_date(wid)`, `within_horizon(wid)` (`lower(during) <= app_now() + horizon`), `window_started(wid)`, plus a `venue_today()` / horizon-end helper; `booking_deadline` is reused.
- **`t_settings`:** recreated in 0005 as `BEFORE UPDATE OF release_on, release_time, venue_tz`, so moving `windows_generated_through` (or a Venue fact) no longer recomputes and locks every Window. The release behaviour is unchanged.
- **Seed:** `seeds/venue.json` gains `"schedule": [{"start": "10:00", "end": "11:30"}, …]` (eight rows). It is validated in `services/windows.py` (Pydantic): partly overlapping, identical and nested rows are refused, back-to-back accepted (E1, E2); a time that is skipped or repeated on any daylight-saving change day of `venue_tz` (checked with `zoneinfo` over the transition days of the next 10 years) is refused (NFR-3). The seed inserts the schedule only when `window_schedule` is empty.
- **Generation:** `ensure_generated()` is one `db.run`: `pg_advisory_xact_lock`, read the mark, insert `(d + start) AT TIME ZONE tz` to `(d + end) AT TIME ZONE tz` for each Venue date from `max(mark + 1, today)` to the horizon-end date, `ON CONFLICT DO NOTHING` (an overlapping existing Window is skipped), then move the mark. Also run once at startup after the seed.
- **Refusals:** date outside `today..horizon_end` is `409 outside_horizon` (new code, also in `lib/api.js`); a malformed date or Seats outside 1–10 is `422 invalid_input`. Both are judged before `ensure_generated()`.
- **Details address:** `/book-seats/details`. Story 1.5 builds the page; until then Continue reaches the not-available page.
- **Rail order:** DOM order total, Continue booking, Wordmark, Seat statement, changing-time note, Terms and Privacy links; the Wordmark is drawn first with CSS `order` (EXPERIENCE.md L403). The per-seat line "NOK 250 per seat in every session" shows from first arrival; "Total NOK 500 incl. VAT" appears once Seats are chosen, in an `aria-live="polite"` block. If the Venue read fails, the rail shows the "please try again" Notice instead of the price lines and Continue still works.
- **Draft:** `draft:seats` = `{date, seats, window_id}` now; Story 1.5 adds name, email and key. Read and written only in effects.
- **Listing shape (human, 2026-11-20):** `GET /api/windows` with `date` and `seats` both optional. Every response carries `today`, `horizon_end`, `horizon_days` and `dates` (Venue dates with at least one Window inside the horizon and before its deadline); `windows` only when `date` is given; `nearest` only when `seats` is given (and no Window on the date has room). A present but invalid value is still refused. No new route.
- **Scope (human, 2026-11-20):** the story stays whole even though the spec is about 2700 tokens.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected |
|---|---|---|
| Fresh clone | empty `windows`, listing read | Windows from today to horizon end, 8 a day; second read adds none |
| DST | horizon spans 2027-03-28 | Windows still 10:00…20:30 Oslo time |
| Overlapping schedule | seed rows partly overlap / identical / nested | startup stops, one line naming file and field |
| Back-to-back | 15:00–16:30 and 16:30–18:00 | accepted |
| DST schedule time | a row starting or ending 02:30 | refused |
| Listing | `date` in horizon, `seats=2` | Windows of that date in time order, past-deadline left out, `already_started` set, time facts present |
| No room on date | every Window < 2 left | up to 3 `nearest`, same day first, then later days in horizon |
| No room in horizon | nothing has 2 left | `nearest: []` |
| Bad input | `date=2026-13-01`, `seats=0` or `11` | 422, nothing written |
| Outside horizon | yesterday or after `horizon_end` | 409 `outside_horizon`, nothing written |
| Independence | Seats booked in Window A | Seats left of Window B unchanged |

</frozen-after-approval>

## Code Map

- `migrations/0001_core.sql` -- `windows` (`windows_never_overlap` EXCLUDE), `seats_left()`, `booking_deadline()` (start + `booking_deadline_minutes`, so a started Window stays bookable 5 min), `t_settings` BEFORE UPDATE recomputes every Window, `t_windows_ins` recomputes a new Window.
- `src/booking_platform/services/seed.py`, `services/venue.py` (`VenueSeed`), `db/venue.py` -- extend the seed with `schedule`; keep one-line `SeedError`s; `main()` already validates the file before uvicorn.
- `src/booking_platform/services/windows.py`, `db/seats.py` -- replace the unfiltered `list_windows`; keep `get_window` and `ensure_open_for_booking` (used by holds/booking and tests via `GET /api/windows/{id}`).
- `src/booking_platform/api/public.py`, `api/schemas.py`, `api/errors.py` -- listing query params as a strict Pydantic model (`extra="forbid"`); add `outside_horizon: 409`.
- `src/booking_platform/app.py` lifespan -- `windows.ensure_generated()` after `seed.apply()`.
- `tests/conftest.py` `world` -- its three Windows sit on the seed's 10:00/11:30/13:00 Oslo slots on 2026-12-01. Add `windows_generated_through = NULL` to its reset; generation skips the overlapping ones. Clock moves only via `set_clock`.
- `tests/test_fr20_access.py` -- keeps `GET /api/windows/` and `POST /api/windows` as 404.
- `frontend/app/page.js` -- `SEAT_STATEMENT` and "Changing time is part of your session." move to a shared `frontend/lib/copy.js`, reused by Book seats.
- `frontend/components/{GuestShell,Notice,PrimaryButton,TextLink,Wordmark,FocusMover}.js`, `lib/{api,server-api,venue-format}.js` -- reuse. FocusMover already sets "Error: " while `[data-error-summary]` exists.
- `.docs/.../mockups/directions-3.html` L98–132, L148–153 -- layout values and markup of Book seats; DESIGN.md L379, L405–436 win.
- `tests/e2e/test_fr21_privacy.py` -- `PAGES` asserts no cookie; Book seats gets its own test (exactly one cookie).

## Tasks & Acceptance

**Execution:**
- [x] `migrations/0005_windows_horizon.sql` -- columns, `window_schedule`, predicates, `t_settings` recreated -- AD-4, AD-18
- [x] `seeds/venue.json`, `services/{seed,venue,windows}.py`, `db/{venue,seats}.py`, `db/windows.py` (new), `app.py` -- schedule seed and validation, `ensure_generated`, listing with `nearest` -- FR-3, FR-13, NFR-3
- [x] `api/{public,schemas,errors}.py`, `frontend/lib/api.js` -- `GET /api/windows`, `outside_horizon` -- AD-16
- [x] `tests/conftest.py`, `tests/test_fr13_windows.py`, `tests/test_fr03_listing.py` -- matrix rows; `test_e1`, `test_e2`, DST refusals, idempotent generation, DST clock times, independence, `already_started`, nearest order and limit
- [x] `frontend/app/book-seats/page.js` (server: metadata "Book seats", `connection()`, venue price) and `frontend/components/{BookSeats,DateCalendar,SeatPicker,SessionList,TotalBlock,ErrorSummary,FieldError,NearestSessions}.js`, `frontend/lib/{copy,draft,dates}.js`, `app/styles.css` -- the page as the ACs list -- FR-2–4, UX-DR9/12/13/17–21/26/33–35
- [x] `tests/e2e/test_fr02_book_seats.py`, `tests/e2e/test_fr21_privacy.py` -- keyboard-only flow, title, axe, first view at 1366×768 with eight Sessions, no horizontal scroll, stacking below 1200 px, Error summary and "Error: " title, draft restore on reload, one cookie, same-origin requests
- [x] `README.md` -- status and the generation sentence

**Acceptance Criteria:**
- Given `uv run pytest`, then every test passes, those of Stories 1.1–1.3 included.
- Given `npm --prefix frontend run build`, then `/book-seats` is listed as dynamic (ƒ).
- Given Book seats at 1366×768 with all eight Sessions, then the page and the total are in the first view.

## Implementation Notes

## Spec Change Log

## Review Triage Log

Iteration 0 (blind-hunter = BH, edge-case-hunter = EC, verification-gap = VG):

| # | Source | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|---|
| 1 | BH, EC | `_transition_days`: `first.replace(year+10)` raises on 29 Feb | medium | `check_schedule` runs in the seed validator with `dt.date.today()`; on 2028-02-29 startup stops with an unrelated message | patch |
| 2 | BH, VG | e2e `test_a_typed_date_is_checked_on_enter` builds `{d}.{m}.{y+1}`, invalid on 29 Feb | low | real clock; fix is a direct correction | patch |
| 3 | BH, EC | `horizon_end()`/`within_horizon()` add days in the session zone (UTC, `db/__init__.py:38`), not `venue_tz` | low | 28 days across a DST change is 672 h, so the horizon end shifts an hour in Venue time and `horizon_end` can be the wrong date near midnight; direct correction in the new 0005 | patch |
| 4 | EC | `generate()` reads `horizon_end()` twice; `app_now()` uses `clock_timestamp()` | medium | if Venue midnight passes between INSERT and UPDATE, the mark moves past a date never generated and that date never gets Windows | patch |
| 5 | BH | every listing takes the advisory lock and runs the INSERT | false | the spec's Decisions require `ensure_generated()` on every listing; one Venue, a no-op insert | reject |
| 6 | BH, EC | horizon check and listing in separate transactions | low | the spec requires the check before `ensure_generated()`; disagreement only within ms of midnight; the fix restructures the flow | reject |
| 7 | BH | listing queries use per-row functions, no index | false | no named harm at the size of one Venue's horizon (≈ 230 rows a month) | reject |
| 8 | BH, EC | a failed date-less first read shows no calendar and no Notice | medium | `facts` stays null and `SessionList` shows `sessionsUnavailable` only with a date | patch |
| 9 | BH | the "please try again" Notice has no retry action | false | EXPERIENCE.md asks only for the Notice text | reject |
| 10 | BH, EC | a restored draft dropped silently (outside horizon, Window gone, no seats chosen) | low | rare, the spec asks for no Notice, the fix adds branches | reject |
| 11 | BH, EC | emptying the date field and leaving it keeps the old date and session | medium | `commitText` returns early on empty text; field and grid disagree and Continue goes on with the old date | patch |
| 12 | BH, EC | a date typed before `facts` arrives skips the bookable check | low | narrow window at load; a 409 then resets the date; the fix adds a branch | reject |
| 13 | BH | month navigation unmounts the pressed button, focus drops to `<body>` | medium | "Next month" vanishes on the last month and "Previous month" on the first; keyboard users lose their place (FR-23) | patch |
| 14 | BH | non-bookable days are bare numbers in the radiogroup; `cal-past` unused | low | design says plain numbers; axe passes | reject |
| 15 | BH, VG | e2e never drives Nearest sessions, the no-room Notices, a disabled row, the cleared Notice or the outside-horizon draft reset | medium | VG pre-verified: every e2e Window has 44 Seats and no frontend test runner exists | patch |
| 16 | BH | `sessionCleared` wording unconfirmed and not recorded | false | recorded as an open point in `.logs/lisa-larsen/issues.md` | reject |
| 17 | BH | spec `in-review` vs sprint `in-progress` | false | the workflow sets sprint status `review` only after review | reject |
| 18 | BH, EC | task names `db/venue.py`, which is unchanged | false | the fix would edit this spec | reject |
| 19 | BH | `GET /api/windows/{id}` keeps its old shape | false | the spec says keep `get_window` as it is | reject |
| 20 | BH | changed seed schedule ignored without a log line; no Window to midnight | false | AD-18: the seed never overwrites; midnight-crossing rows are out of the schedule's design | reject |
| 21 | BH | README: missing "og" before "landingssiden"; "øktkapselen" not a word | low | direct correction | patch |
| 22 | BH | docstring lines in `seed.py`/`app.py` badly wrapped | low | direct correction | patch |
| 23 | EC | `_ISO_DATE` uses `^…$` and `\d` | low | `$` allows a trailing newline and `\d` other digits; pydantic refuses most, but the guard should not depend on it; direct correction | patch |
| 24 | EC | Continue while the re-read is loading or failed keeps a session without room for the new number | medium | the old `windows` already carry `seats_left`, but `onContinue` does not check them | patch |
| 25 | EC | a response resolving after cleanup overwrites the state | low | `.then` does not check `signal.aborted`; one-line guard | patch |
| 26 | EC | draft with integer `window_id` and non-ISO date | low | needs a hand-edited `sessionStorage` | reject |
| 27 | EC | `page.js` TypeError when `data` is null | false | `GET /api/venue` always returns an object (`server-api.js:23`) | reject |
| 28 | EC | nearest says "No room for N seats on <day>" for a date with no Windows | low | such a date is never offered or accepted from `dates`; only a stale draft reaches it | reject |
| 29 | VG | the seed's re-check against the store's `venue_tz` is untested | medium (unverified impact) | no path can change `venue_tz` yet | defer |

## Verification

**Commands:**
- `docker compose up --build --wait` then `curl -s "http://localhost:8000/api/windows?date=<today>&seats=2"` -- expected: eight Windows (fewer late in the day) and the time facts
- `npm --prefix frontend run build` -- expected: `ƒ /book-seats`
- `uv run pytest -q` -- expected: all pass
