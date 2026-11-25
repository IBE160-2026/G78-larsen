---
title: 'Story 5.1: A Guest sees which saunas can be booked whole'
type: 'feature'
created: '2026-11-24'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'da21108e2a37694adf56c8e1a224f7f53f8eb83f'
context:
  - '{project-root}/.docs/implementation-artifacts/epic-5-context.md'
  - '{project-root}/.docs/planning-artifacts/epics.md'  # Story 5.1 acceptance criteria (search "### Story 5.1")
  - '{project-root}/.docs/planning-artifacts/architecture/architecture-booking-platform-2026-11-03/ARCHITECTURE-SPINE.md'  # AD-4, AD-18, AD-21, AD-23, AD-24
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** No Guest can see which Saunas can be booked whole, and the store has no Whole-sauna Booking shape: the slice's `whole_bookings` rows have no Booking, the FR-29 rule lives in a trigger with four refusal names, and no Sauna has a price.

**Approach:** Build epics.md Story 5.1 as written: the §4.9 migration (AD-23 shape, pairing, `whole_bookable`, `cutoff_whole`, `whole_price_ore`), the seed prices, `GET /api/private-saunas`, removal of the slice endpoint with tests moved to `raw_whole`, the catalogue tests, the Landing additions and the Private sauna page. Booking and paying is Story 5.2.

**Decisions (Lisa, 2026-11-24; changed 2026-11-25):** every Sauna is open for Seats and for Private sauna booking unless marked otherwise (`bookable_whole = false` or NULL price). `whole_price_ore`: Rauha (7) 185000, Löyly (10) 260000, Kajo (12) 315000, Lumo (15) 395000. Basis: Oslo comparables average NOK 1,837 for about 7 places = NOK 262 per place, × Capacity, rounded to 50. Recorded in EXPERIENCE.md ("Private sauna wording", Open Item 27). Wording is that block, verbatim.

## Boundaries & Constraints

**Always:**
- Migration `migrations/0013_whole_sauna_bookings.sql` (number taken now; re-check at merge). Drop and recreate the `bookings` capacity triggers around the backfill as 0006 does. `bookings.kind text NOT NULL DEFAULT 'seats'`, `sauna_id int REFERENCES saunas`; `seats` and `price_per_seat_ore` become nullable; one CHECK `bookings_kind_shape`: seats-kind ⇒ `seats BETWEEN 1 AND 10`, `sauna_id IS NULL`, `price_per_seat_ore IS NOT NULL`; whole-kind ⇒ `sauna_id IS NOT NULL`, `seats IS NULL`, `price_per_seat_ore IS NULL`. BEFORE UPDATE trigger refuses a change of `kind` (`CONSTRAINT = 'booking_kind_fixed'`). The capacity trigger column lists add `kind`, `sauna_id`.
- `whole_bookings.booking_id bigint UNIQUE NOT NULL REFERENCES bookings` after deleting rows without a Booking. `check_whole_pair(booking_id)` + two `DEFERRABLE INITIALLY DEFERRED` constraint triggers (bookings: INSERT, `UPDATE OF kind, status, window_id, sauna_id`; whole_bookings: INSERT/UPDATE/DELETE, old and new `booking_id`) raise `CONSTRAINT = 'whole_pairing'`; unmapped in `db/refusals.py` so it is a 500. Rule: an active whole Booking has exactly one capacity row with the same Window and Sauna; a capacity row's Booking is whole and active.
- `whole_bookable(wid, sid, ignore_booking bigint DEFAULT NULL)` exactly as AD-24 (bookable_whole AND price NOT NULL, not Blocked, not booked whole except `ignore_booking`'s row, booked+held ≤ `room_ahead` unless `mark_closed`, and (NOT `window_started` OR no Seat booking OR `mark_closed`)). Never calls `sauna_open_for_seats(wid, sid)` for the judged Sauna. `trg_check_whole` fires AFTER INSERT and AFTER `UPDATE OF window_id, sauna_id`, calls it with `NEW.booking_id`, raises `CONSTRAINT = 'whole_bookable'`. Remove the four old names from `db/refusals.py`. `window_booked_seats` counts `status = 'active' AND kind = 'seats'` only.
- `settings.cutoff_whole interval NOT NULL DEFAULT '72 hours'` CHECK `>= interval '2 hours'`. `saunas.whole_price_ore int` nullable, CHECK `> 0`.
- Seed: `Sauna` model gains optional `whole_price_ore` (int > 0); the seed sets it only where the store value is NULL; `seeds/venue.json` per Decisions.
- `GET /api/private-saunas?date=` (public router, no session, no lock, only `ensure_generated()` writes): shape and filter exactly AD-24; Saunas in Fill order; Saunas with no pair omitted; a date outside `today..horizon_end` is `409 outside_horizon` as `/api/windows`. Times as `/api/windows` (Venue tz ISO). SQL in `db/`, rule in `services/whole.py`.
- `GET /api/venue` Saunas gain `whole_price_ore` (null allowed); `seatFlowVenue` still strips Saunas.
- Tests: `raw_whole(pg, wid, sid)` in `tests/conftest.py` inserts a paired whole Booking (reference, name, email, `total_ore` = price) and capacity row in one transaction; `world` gives all four test Saunas a price so catalogue tests are meaningful. `RAW_BOOKING` writes N Seats as `ceil(N/10)` rows of ≤10 in one statement so slice assertions keep their meaning.
- Frontend uses only shared components and `app/styles.css`; draws Saunas and sessions only by regrouping one listing response; calendar facts (`today`, `dates`) come from `GET /api/windows` with no date.

**Never:** no booking/pay for whole (5.2), no `sauna_unavailable` code yet, no Placement, no session cookie on the Private sauna page, no Sauna name in any Seat-flow page/response/email, no Capacity of a whole Booking shown, no second Primary button on Landing, no browser clock for a rule.

## I/O & Edge-Case Matrix

| Scenario | State | Expected |
|---|---|---|
| b1 | Lumo-free Window, 20 Seats booked `[7,10,3,0]` | Lumo listed |
| b2 | Kajo holding Seats | Kajo not listed |
| b3 | 1 Seat booked | Rauha not listed |
| b7 | empty Window | Lumo listed |
| h12 | started Window, 29 Seats `[7,10,12,0]` | Lumo not listed |
| no price | Sauna `whole_price_ore` NULL | never listed; raw insert refused `whole_bookable` |
| past deadline / outside horizon | Window | not listed / 409 for the date |
| pairing | whole Booking without row, row with other Window/Sauna, row for cancelled or seats Booking, delete row of active Booking | COMMIT refused `whole_pairing` |
| kind change | UPDATE kind | refused `booking_kind_fixed` |

</frozen-after-approval>

## Code Map

- `migrations/0001_core.sql`, `0003`, `0006`, `0010`, `0012` -- current `trg_check_whole`, `room_ahead`, `mark_closed`, `window_booked_seats`, capacity triggers with column lists, `b_cancelled_frozen`, `seat_cutoff()`. Pattern for trigger drop/recreate: 0006.
- `src/booking_platform/db/refusals.py:39-47` -- remove `whole_not_bookable|whole_blocked|whole_seats_placed|whole_window_started`; keep `mark_*`.
- `src/booking_platform/api/admin.py:63-65`, `services/whole.py`, `db/venue_admin.py:insert_whole_booking`, `api/schemas.py` `WholeIn` -- slice endpoint to remove; `services/whole.py` becomes the listing service.
- `src/booking_platform/services/windows.py` (`listing`, `_shape`, `ensure_generated`) and `db/windows.py` (`_BOOKABLE`, `horizon`) -- reuse for the private listing.
- `src/booking_platform/services/seed.py:apply`, `db/venue.py:seed_sauna, saunas`, `services/venue.py:Sauna, facts`, `api/schemas.py:SaunaOut` -- seed price and Venue facts.
- `tests/conftest.py` -- `MUTATIONS`, `world`, `clear`, `RAW_BOOKING`; add `raw_whole`, mutations `no_whole_check`, `no_whole_check_update`, `no_pairing_bookings`, `no_pairing_whole`, `no_kind_fixed`.
- Tests using the removed endpoint: `test_application_rules.py` (deadline/horizon lists → assert the pair is absent from `/api/private-saunas`; named-refusal whole cases → `raw_whole` refused `whole_bookable`), `test_fr10_bypass.py:60-66` (use `raw_whole`), `test_fr10_through_the_api.py:181` (per-thread psycopg `raw_whole`, refusals counted as 409), `test_fr14_retry.py:24` and `test_fr20_access.py:22,105` and `test_fr2_input.py:81` (drop the endpoint entries; note in Implementation Notes).
- `test_dr4_migrations.py` -- add a case: 0013 on a DB with Seat bookings and orphan `whole_bookings`.
- Frontend: `app/page.js` (rail, saunas intro), `components/SaunaCard.js`, `components/BookSeats.js` rail (group sentence), `lib/copy.js` (`SEAT_STATEMENT`, add `GROUP_SENTENCE`, `PRIVATE` copy), `lib/venue-format.js:nok,holds`, `components/DateCalendar.js` (props `facts`, `label`), `SessionList.js` (row look), new `app/private-sauna/page.js` + `components/PrivateSauna.js`. e2e: `tests/e2e/test_fr01_landing.py`, `test_fr21_privacy.py`, new `test_fr30_private_sauna.py`, `a11y.py` helpers.

## Tasks & Acceptance

**Execution:**
- [x] `migrations/0013_whole_sauna_bookings.sql` -- schema per Always.
- [x] `src/booking_platform/{db,services,api}` -- refusals, listing, seed, venue facts, remove slice endpoint.
- [x] `seeds/venue.json` -- prices.
- [x] `tests/conftest.py`, slice tests, new `tests/test_fr29_whole_sauna.py` (b1, b2, b3, b7, h12, no-price, deadline, horizon, shape/no-session/no-write), new `tests/test_fr29_whole_store.py` (pairing, kind, `whole_bookable` INSERT/UPDATE bypass incl. H12, B2, B3; each red under its mutation), `test_dr4_migrations.py`, `test_fr04_no_sauna.py` still green.
- [x] Frontend Landing, Book seats rail, Private sauna page; e2e tests.
- [x] `README.md` -- Private sauna page and seed prices; "Not delivered" keeps 5.2–5.5 items.

**Acceptance Criteria:**
- Given the epics.md Story 5.1 ACs, when the story is done, then each holds and is tested.
- Given `uv run pytest` (both layers), then all tests pass, and each new bypass test fails under its mutation.

## Implementation Notes

- **Prices (Decisions):** recorded in `seeds/venue.json` (Rauha 185000, Lumo 395000; Löyly and Kajo absent = NULL), README ("Administrator og eksempelbookinger") and EXPERIENCE.md as before. The seed fills `whole_price_ore` only where the store holds NULL (`db.venue.seed_sauna`); `tests/test_fr01_venue.py` pins fill-only-where-NULL and an invalid price (0) stopping startup.
- **Changed decision (Lisa, 2026-11-25):** every Sauna is open both for Seats and for Private sauna booking unless marked otherwise (`bookable_whole = false` or a NULL price). `seeds/venue.json` now prices all four: Rauha 185000, Löyly 260000, Kajo 315000, Lumo 395000 (this supersedes the 2026-11-24 Decisions above). An existing database where Löyly and Kajo are NULL gets the two new prices at the next start, because the seed fills only NULL prices (`db.venue.seed_sauna`; pinned in `tests/test_fr01_venue.py` by Rauha's emptied price coming back). The Venue facts still give a null price for a Sauna with `bookable_whole = false`. Tests and README updated to the four prices.
- **Migration 0013:** as Always. Trigger names: `b_kind_fixed` (BEFORE UPDATE OF kind, WHEN changed), `t_pair_bookings` / `t_pair_whole` (deferred constraint triggers), `t_00_check_whole` (AFTER INSERT OR UPDATE OF window_id, sauna_id). Constraint names: `bookings_kind_shape`, `cutoff_whole_at_least_2_hours`, `saunas_whole_price_positive`, `whole_bookings_booking_id_key`. `whole_bookable` judges `room_ahead(wid, sid)` as stored: in the trigger the row has already moved, so `ignore_booking` only has to exclude the row from "booked whole". A 5.3 move list read with `ignore_booking` still counts the Booking's current Sauna as closed for Seats in Room ahead of a later Sauna in the same Window (conservative); revisit in 5.3 if a same-Window Sauna change must be offered.
- **`whole_bookable`, `whole_pairing`, `booking_kind_fixed`** are unmapped in `db/refusals.py` (500s). No API path writes `whole_bookings` in 5.1; 5.2 maps `whole_bookable` to `sauna_unavailable`.
- **Slice tests reshaped (AD-21):** `test_fr14_retry.py` and `test_fr20_access.py` (both lists) and `test_fr2_input.py` dropped their `/api/admin/whole-bookings` entries (comments in place); `test_application_rules.py` asserts the deadline/horizon through `/api/private-saunas` and the four old named whole refusals as one `whole_bookable` via `raw_whole`; `test_fr10_bypass.py` and `test_fr10_through_the_api.py` use `raw_whole` (the load test counts store refusals as 409). `test_fr10_bypass.py::test_core_raising_a_booking_after_the_fact_is_refused` now books 8 × 5 Seats so the raised row still holds ≤ 10 and asserts the refusal is `booked_within_capacity`, not the new shape CHECK. `test_dr4_migrations.py`: the 0006 and 0012 cases migrate only up to 0012 (the 0006 case's legacy 40-Seat row cannot pass 0013's 1–10 CHECK; checked: `booking` and `booking_dev` hold no row above 10); new `test_0013_...`. `test_fr27_voucher_for_seats.py` trigger list gains `b_kind_fixed`, `t_pair_bookings`.
- **e2e fills:** every raw fill with more than 10 Seats (`RAW_FILL` in `test_fr02_book_seats.py`, `test_fr11_refusals.py`, `test_fr26_move.py`, and the fill-everything statement in `test_fr02_book_seats.py`) now writes rows of at most 10.
- **Frontend:** the Private sauna page has no rail action (5.2 adds Continue); its rail is the Wordmark, as on Details and Manage. A failed listing reuses "The sessions could not be loaded, please try again." (BOOK.sessionsUnavailable). The group sentence is appended to the Seat statement's paragraph on Landing and in the Book seats rail. The page reads no `?date=` yet (5.2's "Choose another sauna or session" link will need it).

## Spec Change Log

## Review Triage Log

| # | Layer | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|---|
| 1 | blind, edge | 0013 aborts on a Seat booking with > 10 Seats | medium | `bookings_kind_shape` added without a check; `test_0006` was cut to `upto 0012` | patch: fail early with a clear message naming the count |
| 2 | blind | Comments say Booking and capacity row may be written in either order; FK is not deferrable | low | `whole_bookings_booking_id_fkey` immediate; AD-23 order is Booking first | patch: correct the comments |
| 3 | blind | Orphan `whole_bookings` deleted in every environment | false | AD-23 orders this deletion; only dev and slice DBs have orphans | reject |
| 4 | blind, edge | Landing shows a price for a Sauna with `bookable_whole = false` | low | `SaunaCard` reads only `whole_price_ore`; `whole_bookable` needs both | patch: Venue facts return `whole_price_ore` null unless `bookable_whole` |
| 5 | blind | Seed refills a NULL price after restart | false | AD-18: a per-row reference column is filled by the seed where NULL | reject |
| 6 | blind, edge | Failed load cannot be retried with the same date; `outside_horizon` shown as generic failure; stale status for a new date | low | `pickDate` returns early on same date; catch sets `failed` for every error | patch |
| 7 | blind | Results and empty state are not announced to screen readers | medium | no live region on `/private-sauna` | patch: announce as Book seats does |
| 8 | blind | Private sauna rail lacks Terms and Privacy links; no Continue | low | Continue is Story 5.2 by spec; links missing vs other guest rails | patch: add the links only |
| 9 | blind | Endpoint removal drops retry/access/input coverage; `_raw_whole_status` crashes on deadlock | low | entries removed from test_fr14/20/2; raw concurrent writes may deadlock | patch the status helper; coverage returns with 5.2 (defer) |
| 10 | blind, vgap | No listing or store test with Holds filling Room ahead | medium | vgap demonstration: dropping `window_held_seats` passes all tests | patch: add tests |
| 11 | vgap | `mark_closed OR` room branch never reached | medium | Lumo case passes 29 <= 29 without the mark | patch: add a marked Rauha case |
| 12 | blind | `test_b2` duplicates `test_b1` | false | catalogue B2 is the same state judged for Kajo | reject |
| 13 | blind, edge | Horizon check and listing in two transactions | low | same pattern as `windows.listing`; only at Venue midnight | reject |
| 14 | blind | `whole_bookable` per pair may be slow | low | NFR-7 sets no target | reject |
| 15 | blind | e2e `day` fixture may pick today or a date with sample bookings | medium | `free_windows()[0]` can be today | patch: pick a later empty date |
| 16 | blind | README "NOK 1 850" vs UI "NOK 1850" | low | direct text fix | patch |
| 17 | vgap | Regrouping not tested with different free sessions | medium | filed disposition defer; nothing is bookable before 5.2 | defer |
| 18 | edge | Seed price written onto another Sauna holding that id | low | needs a store Sauna with a seeded id but other identity; guard adds branches | reject |
| 19 | edge | `ignore_booking` ignored only in the booked-whole test, not in `room_ahead` | medium | `room_ahead` uses `sauna_open_for_seats`, which still sees the row; only 5.3's move listing passes `ignore_booking` | defer to 5.3 |
| 20 | edge | Horizon and deadline not in `whole_bookable` | false | AD-24 puts them in `services` after the lock | reject |

## Verification

**Commands:**
- `uv run pytest -x -q tests --ignore=tests/e2e` -- all pass
- `BP_TEST_MUTATE=<name> uv run pytest tests/test_fr29_whole_store.py` -- the matching test fails
- `uv run pytest tests/e2e` -- all pass (compose stack)
- `npm --prefix frontend run build` -- builds

Verification (2026-11-25, orchestrator): API layer `uv run pytest tests --ignore=tests/e2e` 561 passed after the review patches. Full e2e run after the patches: 186 passed, 1 failed, 1 error, both in `test_fr30_private_sauna.py` (an assertion that caught Next.js's route announcer, and a module-scoped fixture rebuilt after stack-disrupting modules); fixed, and `test_fr30_private_sauna.py` alone: 5 passed. A second full e2e run was stopped by Claude Code for low system memory and is not confirmed.
