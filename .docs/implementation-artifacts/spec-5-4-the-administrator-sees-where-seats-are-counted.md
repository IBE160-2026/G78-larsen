---
title: 'Story 5.4: The Administrator sees where Seats are counted'
type: 'feature'
created: '2026-11-27'
status: 'done'
baseline_commit: 'a1a4298169de13b98f6b146950d912fb6c460fc1'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/implementation-artifacts/epic-5-context.md'
  - '{project-root}/.docs/planning-artifacts/epics.md'  # Story 5.4 ACs (search "### Story 5.4")
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Placement is derived (AD-6) but nothing computes or shows it: the Administrator cannot see which Saunas are booked whole or how many Seats each Sauna counts, and no test proves FR-31's catalogue examples or INV-1 to INV-5.

**Approach:** Add the one Placement computation, SQL `placement(wid)` (AD-25), in migration 0016; carry it per Window in the Administrator Booking list response; show it as a "Saunas" table in each Session group; prove it with the FR-31 catalogue examples against a brute-force reference and a shared INV-1..INV-5 checker in `tests/` that Story 5.5 reuses.

**Decisions (planning, approved by Lisa 2026-11-27; spec kept whole at about 2300 tokens):**
- Placement travels in `GET /api/admin/bookings` (one `placement` list per Window); no separate `/windows/{id}/placement` route (epics.md allows either).
- State precedence when several apply: `whole` > `blocked` > `marked` > `open` (a Block can be inserted over a Whole-sauna booking; staff must still see the Guest's booking). `marked` means `mark_closed(wid, sid)` (a released mark is `open`).
- Wording (EXPERIENCE.md, already decided): table "Saunas", columns "Sauna" and "Seats counted"; cells "{seats} of {capacity}" (e.g. "7 of 7", "0 of 12"), "Booked whole · {ref}", "Blocked", "Private sauna only". Shown in every Session group (also with no Bookings), after the figures line, before the Bookings table.

## Boundaries & Constraints

**Always:**
- `migrations/0016_placement.sql`: `placement(wid int) RETURNS TABLE (sauna_id int, state text, seats int)`, one row per Sauna ordered by `fill_order`. Seats are the Window's booked Seats only (`window_booked_seats`, no Holds), placed greedily in Fill order over `open` Saunas: `seats = LEAST(capacity, GREATEST(0, booked − capacity of earlier open Saunas))`; 0 for every other state. `whole` = a `whole_bookings` row; `blocked` = a Block overlapping the Window; `marked` = `mark_closed`. Volatile, read-only, no lock. Header comment in the 0014/0015 style. Nothing else changes.
- `db/booking_list.py` reads `placement(w.id)` joined to `saunas` (name, capacity) and, for `whole`, the active Whole-sauna booking's reference via `whole_bookings.booking_id`. `services/booking_list.day()` adds `placement: [{sauna: {id, name}, capacity, state, seats, reference}]` (reference null unless `whole`) to each Window; still no lock and no write beyond `ensure_generated()`.
- Only `/api/admin/` responses carry Placement (AD-10, AD-25); anonymous/Guest session 401, as the existing Booking list.
- Brute force in `tests/placement.py` (pure Python from raw store rows: Saunas, booked Seats, Whole-sauna rows, Blocks, marks/releases/clock via `mark_closed`), plus `assert_invariants(pg, wid)` checking INV-1..INV-5 on `placement(wid)` against raw rows and `placement(wid) == brute_force(pg, wid)` and Seats left. Importable by Story 5.5.
- Frontend: `BookingList.js SessionGroup` renders the "Saunas" table (`caption` visually hidden, `th scope`), tabular figures, text in every cell — never colour alone. Copy in `lib/copy.js BOOKING_LIST`.

**Never:** no Placement in Python or the frontend outside `tests/` (the page shows the API's rows as given); no Sauna name or Placement in any Guest/Seat response or email; no stored Placement column; no new table or trigger; no change to capacity rules or Fill order behaviour (F2 is later).

## I/O & Edge-Case Matrix

Windows start empty; Saunas `[Rauha 7, Löyly 10, Kajo 12, Lumo 15]`; `[a,b,c,d]` = seats per Sauna, `—` = booked whole.

| Scenario | Input / State | Expected |
|---|---|---|
| A1 | book 5, then 4 | `[7,2,0,0]`, Seats left 35 |
| A2 | at `[7,10,5,0]` give up 3 Seats | `[7,10,2,0]`, left 25 |
| A3 | then give up 2 more | `[7,10,0,0]`; Kajo listed bookable whole |
| A4 | at `[7,10,5,0]` give up 2 | `[7,10,3,0]` |
| A5 | at `[7,10,12,3]` give up 5 | `[7,10,10,0]` |
| A8 | give up 1 of a 4-Seat Booking at `[7,10,5,0]` | `[7,10,4,0]` |
| B4 | Rauha whole; book 10,10,10,7 | state `whole` + `[—,10,12,15]`; 1 more refused `no_seat_free` |
| B5 | Löyly whole in empty Window; book 9 | `[7,—,2,0]`, left 25 |
| B6 | Löyly whole at `[7,—,12,4]`; cancel it (refund) | `[7,10,6,0]` |
| Blocked / marked | raw Block on Kajo; raw mark on Lumo (unreleased, then released) | `blocked` 0 seats; `marked` 0 → `open` after release |
| Whole + Block | Block over a Whole-sauna-booked Sauna | `whole` with its reference |
| Holds | Hold of 3 in an empty Window | all seats 0 (Holds not placed) |
| Access | anonymous / Guest session on `/api/admin/bookings` | 401, no Placement |

</frozen-after-approval>

## Code Map

- `migrations/0001_core.sql:62-82` -- `mark_closed`, `sauna_open_for_seats`, `room_ahead`, `window_booked_seats` (reuse, do not change); `0015_whole_move.sql` header style.
- `src/booking_platform/db/booking_list.py:16` `windows_on` -- add a `placement_on(c, date)` query (one statement over the date's Windows, `ORDER BY` Window start then `fill_order`).
- `src/booking_platform/services/booking_list.py:22` `day()` -- attach `placement` per Window; update docstring.
- `src/booking_platform/api/admin.py:46` `bookings` -- docstring only.
- `frontend/components/BookingList.js:74` `SessionGroup` -- new table between `.session-group-header` content and `booking-table`; `frontend/lib/copy.js:386` `BOOKING_LIST` (add `saunas`, `saunasCaption(start,end)`, columns, `counted(n,cap)`, `bookedWhole(ref)`, `blocked`, `privateOnly`); `frontend/app/styles.css` reuse `.booking-table`/`.num`/`.tabular` patterns.
- Tests to reuse: `tests/conftest.py` (`clear`, `raw_booking`, `raw_whole`, `set_clock`, `state`, `admin`, `api`), `test_fr27_voucher_for_seats.py` (`opened`, `give_up` for Seat give-ups through the API), `test_fr33_whole_change.py` (`whole_opened`, whole cancel), `test_fr29_whole_sauna.py` (`listed` for A3), `test_fr16_booking_list.py` (`booking_list`, 401 tests), `test_fr04_no_sauna.py` (`assert_no_sauna`, walk), `test_dr4_migrations.py` (numbering picks 0016 up).
- e2e: `tests/e2e/test_fr16_booking_list.py` (`sign_in`, `open_day`, `group`), `tests/e2e/guest.py free_windows`, `tests/e2e/a11y.py` (`check_axe`, `tab_to`, `no_horizontal_scroll`); rows the test creates must be deleted afterwards (spec-e2e-free-dates).

## Tasks & Acceptance

**Execution:**
- [x] `migrations/0016_placement.sql` -- `placement(wid)` as above.
- [x] `src/booking_platform/db/booking_list.py`, `services/booking_list.py`, `api/admin.py` -- Placement per Window in the Booking list.
- [x] `tests/placement.py` (new) -- brute force + `assert_invariants`; self-test that it fails on a hand-made violating Placement.
- [x] `tests/test_fr31_placement.py` (new) -- one test per matrix row named by catalogue ID (`test_a1` … `test_b6`), `assert_invariants` after every step; `placement` equals brute force; Booking list `placement` equals `placement(wid)` and its `open` seats sum to `seats_booked`.
- [x] `tests/test_fr04_no_sauna.py` -- walks also assert no `placement` key outside `/api/admin/`.
- [x] `frontend/components/BookingList.js`, `frontend/lib/copy.js`, `frontend/app/styles.css` -- "Saunas" table.
- [x] `tests/e2e/test_fr16_booking_list.py` -- a Session group with a Whole-sauna booking and Seats shows the Saunas in Fill order with "Booked whole · {ref}" and "{n} of {cap}"; axe clean; keyboard reachable; no horizontal scroll at 1024 px.
- [x] `README.md` -- where the Administrator sees Placement; drop 5.4 from "Not delivered"; `.docs/sensorveiledning-kravsporing.md` FR-31 row if present.

**Acceptance Criteria:**
- Given epics.md Story 5.4's ACs, when this spec is done, then each holds and is tested, and 5.4 can be marked done in `sprint-status.yaml`.
- Given `uv run pytest` (both layers) and `npm --prefix frontend run build`, then all pass.

## Implementation Notes

## Spec Change Log

## Review Triage Log

| # | Source | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|---|
| 1 | verification-gap | "Blocked" / "Private sauna only" cells never rendered by any test | medium | Searched tests: only `open`/`whole` reach the page; dropping a `countedText` branch passes every test | patch |
| 2 | blind, vg-other | `BOOKING_LIST.saunas` defined but unused; no visible "Saunas" label | low | Spec asks for a visually hidden caption, so no visible label is right; the key is dead code | patch (delete key) |
| 3 | blind, edge | `countedText` shows "n of cap" for an unknown state / null reference | false | `placement()` CASE yields only the four states; a `whole` row always has `booking_id`, so reference is non-null | reject |
| 4 | blind, edge | `tests/placement.py` claims "one snapshot" but reads several statements under READ COMMITTED | medium | `db/__init__.py:40` and psycopg default are READ COMMITTED; Story 5.5 races would compare rows from different snapshots | patch |
| 5 | blind | Brute force shares `mark_closed` with `placement()` | false | Spec (Always) prescribes marks/releases/clock "via `mark_closed`"; module docstring says so | reject |
| 6 | blind, edge | e2e keyboard check never crosses the table | false | Same test asserts the table has no `a, button, input, [tabindex]`, so it adds no tab stop or trap | reject |
| 7 | blind, edge | e2e "empty group" check is weak (`endswith("of 15")`, emptiness unproven) | low | `.first` group's emptiness is never asserted; "15 of 15" would pass | patch |
| 8 | blind | sprint-status `in-progress` vs spec `in-review` | false | Workflow sets the sprint status when the story finishes (step 5) | reject |
| 9 | blind | README "Ikke levert": SC2/SC4 bullet omits 5.4; "FR-31 til FR-51 … (FR-29 til FR-31 er delvis levert)" self-contradicts | low | New wording puts FR-31 inside the not-delivered range and FR-29/30 outside it | patch |
| 10 | blind | Sensor guide row 3 test counts dated 2026-11-25 | low | Stale since before this story (5.3 did not refresh it) | defer |
| 11 | blind | A6, A7, B1–B3 not covered | false | Story 5.4 ACs list exactly A1–A5, A8, B4–B6; but sensor guide says "A1–A8", which overclaims | patch (doc wording) |
| 12 | blind | `check()` only compares Window 1; `placement_on` join over several Windows unexercised | low | Every catalogue test uses `wid=1`; other Windows are checked only for names | patch |
| 13 | blind | `placement_on` reference join has no active-status guard | low | Correct only through 0013's rule that a `whole_bookings` row exists while its booking is active; undocumented reliance | patch (comment) |
| 14 | blind | e2e magic `2` for Löyly; duplicate scroll check; broad `.booking-table .col-sauna`; `min-width: 320px` | low | Magic number and duplicate check real; `.col-sauna` used only in the Saunas table and 320 px fits every supported width: no harm | patch (first two), reject (rest) |
| 15 | edge | `placement_on` and `windows_on` read in separate READ COMMITTED statements; table sum can differ from figures | low | Real but transient on one Administrator page; same pattern already between `windows_on` and `bookings_on`; fix touches AD-3 isolation | reject |
| 16 | edge | VOLATILE `mark_closed` per Sauna inside `placement()` sees different snapshots | low | Only under a concurrent mark/release commit; same as existing `window_open_capacity`; fix is a volatility change to core functions | reject |
| 17 | edge | Booked Seats above open capacity silently vanish from Placement | false | `recompute_window` CHECK refuses booked > open capacity, and `t_settings` recomputes on release changes; `assert_invariants` INV-2 would flag it | reject |
| 18 | edge | `test_fr04` checks only the substring `"placement"` (with quotes) | low | `"placements"` key would slip through; dropping the quotes is a direct correction | patch |

## Verification

**Commands:**
- `uv run pytest -x -q tests --ignore=tests/e2e` -- all pass
- `uv run pytest tests/e2e` -- all pass
- `npm --prefix frontend run build` -- builds
