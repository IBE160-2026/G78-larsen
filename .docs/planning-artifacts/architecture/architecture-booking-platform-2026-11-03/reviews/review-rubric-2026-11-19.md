---
review-of: ARCHITECTURE-SPINE.md (architecture-booking-platform-2026-11-03, status draft, updated 2026-11-19)
lens: rubric walker (good-spine checklist), focus on the §4.9 amendment (AD-23 to AD-26 and edits to AD-6, Stack, Conventions, ER, capability map, Deferred)
reviewed: 2026-11-19
inputs: ARCHITECTURE-SPINE.md, .memlog.md, PRD §3, §4.2, §4.4 (FR-16, FR-17), §4.8, §4.9, §7, §10; appendix FR-35, FR-36, FR-38, FR-39; addendum A; src/booking_platform/schema.sql, app.py; tests/conftest.py, tests/test_fr10_bypass.py, test_fr14_retry.py, test_application_rules.py, test_fr10_through_the_api.py
spine-edited: no
---

# Review: §4.9 amendment against the good-spine rubric

## Verdict

The amendment picks the right model (one `bookings` table, `whole_bookings` as the capacity row, one FR-29 predicate, one Placement function, one model test) and ratifies the brownfield kernel, but it is **not yet ready to write §4.9 stories from**: three high findings would let independently built stories ship a store check that does not bite, a pairing invariant that is only half enforced, and a slice test suite that nobody owns reshaping.

## Findings at a glance

| ID | Sev | Location | Finding |
| --- | --- | --- | --- |
| H1 | high | AD-24 | `whole_bookable(wid, sid)` cannot be the same predicate in an AFTER trigger and in the listing: the row counts against itself |
| H2 | high | AD-23 Capacity row | The deferred pairing check names no tables or events; a status-only cancel can leave capacity taken |
| H3 | high | AD-23 vs AD-21, brownfield tests | `booking_id NOT NULL` breaks the slice's `/whole-bookings` endpoint and raw-insert bypass tests; no rule says who reshapes them or how |
| M1 | medium | AD-24 Refusal, AD-1 | Store refusals from `trg_check_whole` carry no constraint name, so "translated by constraint name" cannot work |
| M2 | medium | AD-24 Refusal vs AD-16 | "Every FR-29 refusal is `sauna_unavailable`" collides with `deadline_passed` and the horizon refusal |
| M3 | medium | AD-23 Move vs Price | Move rule updates only `window_id`, yet the Price rule and FR-33 allow a change of Sauna |
| M4 | medium | AD-23 Cutoff vs FR-39, FR-26 | Cutoff read live from `settings` contradicts "existing Bookings keep the Cutoff they were made under" |
| M5 | medium | AD-23 Price vs AD-18 | A per-Sauna `whole_price_ore` cannot get "the seed value as its default"; existing databases never receive prices |
| M6 | medium | AD-9 | Idempotency key not bound to what was asked; a reused key can return a Seat booking to a Private sauna submit |
| M7 | medium | AD-25 | Placement exposure to Guests not forbidden; output shape (one row per Sauna? state?) undecided |
| M8 | medium | AD-26 | First version of the machine does not name the §4.8 actions that already exist when it is written |
| M9 | medium | Deferred / no open-questions | Change history row and cancellation record (time, cause, choice) shared by FR-26/27/33 are neither decided nor listed as deferred |
| M10 | medium | API shape (no AD) | Private sauna endpoint paths, `kind` discriminator in responses and Sauna naming in Guest and Admin payloads are undecided |
| L1 | low | AD-20 | "Every Booking creator" list omits the Whole-sauna flow |
| L2 | low | AD-9 Binds, capability map | FR-29/FR-33 missing from AD-9 Binds; map omits AD-9, AD-10, AD-12, AD-13, AD-16, AD-20 and `api/admin.py` |
| L3 | low | ER diagram, Structural Seed | `saunas |o--o{ bookings` (`bookings.sauna_id`) missing; `services/whole.py` missing from the tree |
| L4 | low | AD-12, `content/` | Shared terms text per kind (72 h Cutoff, refund or Voucher) and the "Sauna is not held" review copy have no named home |
| L5 | low | Deferred | Per-Window Fill order for started Windows (FR-38 F2) changes what `placement(wid)` means; not listed |
| L6 | low | AD-26 | Hypothesis settings (deadline, max_examples, DB reset between examples) undecided; `uv run pytest` runs it every time |
| L7 | low | AD-23 Price | `price_differs` on a move to the *same* Sauna after a price change (FR-38) would refuse a legitimate move |

No critical findings.

---

## High

### H1. `whole_bookable(wid, sid)` counts the row it is judging (AD-24)

- **Problem.** AD-24 says `trg_check_whole` calls `whole_bookable(wid, sid)` and that the listing calls the same function. In `0001` the check is an `AFTER INSERT` row trigger (`t_00_check_whole`), so when it runs the new `whole_bookings` row already exists. With only `(wid, sid)` as arguments the predicate cannot tell "booked whole by another Booking" from "booked whole by me" (UNIQUE `(window_id, sauna_id)` means any row found *is* NEW). Worse, FR-29's started-Window clause is "or the Sauna is not open for Seats"; if written with `sauna_open_for_seats(wid, sid)`, that is always false-open (the Sauna is whole-booked by its own row) and the started-Window rule never refuses. `0001` avoids this by testing `NOT mark_closed(...)` instead, but the spine's wording invites the literal version. "A moved row never counts against itself" is stated, but the signature gives the function no way to know which row is "itself".
- **Failure scenario.** Story A (FR-30 listing) writes `whole_bookable` with `NOT EXISTS whole_bookings` and `sauna_open_for_seats`; correct for the listing. Story B wires it into the AFTER trigger: every INSERT is refused (self found), so the developer "fixes" it by dropping the clause, and the started-Window clause is now vacuous. A raw insert of a whole booking into a started Window with Seat bookings is accepted; no existing bypass test covers that case for UPDATE.
- **Fix.** Replace the Predicate bullet with: "**Predicate:** `whole_bookable(wid int, sid int, self_id bigint DEFAULT NULL)` is the only SQL statement of the store-enforced part of FR-29. It ignores the `whole_bookings` row `self_id` in every sub-check (already booked whole, open for Seats, Room ahead). The started-Window clause is written as in `0001`: refuse when the Sauna is not marked-and-unreleased, Seats are booked, and the Window has started. The listing and `services` call it with `self_id` NULL; `trg_check_whole` calls it with `NEW.id`." Add: "Bypass tests cover INSERT and UPDATE OF `window_id`, `sauna_id` for each clause, including the started-Window clause."

### H2. The pairing check has no stated events (AD-23 Capacity row)

- **Problem.** "A deferred COMMIT check refuses any mismatch" does not say which tables and events fire it. The natural copy of `t_verify` is a constraint trigger on `whole_bookings` only. Then `UPDATE bookings SET status = 'cancelled'` on a whole Booking, without deleting its `whole_bookings` row, commits: the cancelled Booking keeps taking a Sauna's capacity, which is the first thing AD-23 says it prevents. Equally, a `kind = 'whole'` Booking inserted without its capacity row would take no capacity at all, and a `whole_bookings` row could point at a `kind = 'seats'` Booking.
- **Failure scenario.** The FR-33 cancel story sets the status and forgets the delete (or deletes in a branch that a refund failure skips). Seats left stays 15 lower for the Window; the Admin list shows the Booking cancelled; no test fails because the check fires only on `whole_bookings` writes.
- **Fix.** Replace with: "A `DEFERRABLE INITIALLY DEFERRED` constraint trigger `whole_pair_check` fires AFTER INSERT OR UPDATE OF `kind, status, window_id, sauna_id` ON `bookings` and AFTER INSERT OR UPDATE OR DELETE ON `whole_bookings`. At COMMIT it refuses (23514, constraint `whole_pair_check`) when an active `kind = 'whole'` Booking has no `whole_bookings` row with the same `window_id` and `sauna_id`, when a `whole_bookings` row's Booking is not active or not `kind = 'whole'`, or when the two disagree. It gets a bypass test for each case and an entry in `MUTATIONS` (AD-2)."

### H3. The slice's Whole-sauna path and tests break, and nobody owns the reshape (AD-23 vs AD-21)

- **Problem.** `whole_bookings.booking_id NOT NULL REFERENCES bookings` plus the pairing check makes every existing raw write of a Whole-sauna booking fail: `tests/test_fr10_bypass.py:60,65` (`INSERT INTO whole_bookings (window_id, sauna_id) ...`), the slice endpoint `POST /whole-bookings` (`app.py:172`) used by `test_fr14_retry.py:22`, `test_application_rules.py:37` and the mixed-load test `test_fr10_through_the_api.py:181`, and the `TRUNCATE` list in `conftest.py`. AD-21 binds only "the first skeleton story" and says no rule is loosened to keep a slice test green, but it does not say which story migrates these tests to the AD-23 model, nor how a bypass test now creates a Whole-sauna booking around the API.
- **Failure scenario.** The §4.9 migration story adds `booking_id NOT NULL`; ten slice tests go red. Under time pressure the developer makes `booking_id` nullable "for raw inserts", or deletes the bypass cases, or keeps `/whole-bookings` alive as a second creator that bypasses AD-20. Each is a silent weakening AD-21 was written to stop.
- **Fix.** Add to AD-23: "**Brownfield:** the story that adds migration `kind`/`booking_id` also moves every slice test that writes `whole_bookings` to the pair: raw bypass tests insert a `bookings` row (`kind = 'whole'`) and its `whole_bookings` row in one transaction, and API tests use the new Private sauna endpoint. The slice endpoint `/whole-bookings` is removed in the same story. Each bypass case that existed keeps an equivalent that still expects refusal (AD-21)."

## Medium

### M1. Store refusals cannot be translated "by constraint name" (AD-24, AD-1)

- **Problem.** AD-1 says `db` translates store errors to `Refused` by constraint name. Every `RAISE` in `trg_check_whole` (and `trg_check_mark`, `verify_window`) uses `USING ERRCODE = '23514'` with no `CONSTRAINT`, so `diag.constraint_name` is NULL. The slice falls back to `rule_refused` with store text (`app.py:56`), which AD-16 forbids.
- **Failure scenario.** One story parses `message_primary` ("Sauna % is Blocked") to pick `sauna_unavailable`; another maps every unnamed 23514 to `sauna_unavailable`, so a pairing-check or verify failure (a bug) is reported to the Guest as "Sauna unavailable".
- **Fix.** Add to AD-24: "The migration that replaces `trg_check_whole` raises with `USING ERRCODE = '23514', CONSTRAINT = 'whole_bookable'`; `db` maps exactly that name to `sauna_unavailable`. Any other unnamed 23514 is not a refusal and surfaces as a 500."

### M2. "Every FR-29 refusal is `sauna_unavailable`" overlaps existing codes (AD-24 vs AD-16)

- **Problem.** FR-29's first bullet includes the Booking horizon and the Booking deadline. AD-16 already fixes `deadline_passed` for a Window past its deadline, and the Core has a horizon refusal.
- **Failure scenario.** The FR-29 story returns `sauna_unavailable` for a Window past its deadline; the Seat flow returns `deadline_passed`; the shared Review page shows two different messages for the same situation.
- **Fix.** "**Refusal:** when `whole_bookable` is false, the refusal is `409 sauna_unavailable`. Horizon and deadline refusals keep their Core codes (`deadline_passed`, and the horizon code), checked first, in that order."

### M3. Move changes only `window_id`, but FR-33 lets the Sauna change (AD-23)

- **Problem.** The Move bullet updates `window_id` on both rows. The Price bullet refuses "a move to a Sauna whose price differs", and FR-33's assumption allows a move to another Sauna. AD-24 fires the trigger on `UPDATE OF window_id, sauna_id`. Whether a move may change Sauna, and whether `bookings.sauna_id` follows, is not decided.
- **Failure scenario.** The move story updates `whole_bookings.sauna_id` but not `bookings.sauna_id` (or vice versa); H2's check (if fixed) refuses at COMMIT, or (if not fixed) the confirmation names the old Sauna.
- **Fix.** "**Move:** set `window_id`, and `sauna_id` when the Guest picks another Sauna, on both rows in one transaction, with every touched Window locked in id order. The target is judged by `whole_bookable(target_wid, target_sid, self_id)`."

### M4. Cutoff read live contradicts FR-39 and FR-26 (AD-23 Cutoff)

- **Problem.** AD-23 makes the 72 h Cutoff a `settings` column read at Change time. FR-39: "A changed Cutoff applies only to Bookings made after the change. Existing Bookings keep the Cutoff they were made under"; FR-26: both parts of a split keep "the Cutoff setting the original was made under". §10.3 asks the spine to record what would force a rewrite; this does.
- **Failure scenario.** FR-33 stories compute `lower(during) - settings.whole_cutoff`. When §4.13 lets the Administrator change it, every existing Booking's Cutoff silently moves; fixing it later needs a backfill of values nobody stored.
- **Fix.** "**Cutoff:** each Booking stores `cutoff_hours` at creation, from `settings.cutoff_seat_hours` or `settings.cutoff_whole_hours` by kind; a move or split keeps it. One SQL predicate `before_cutoff(booking_id)` (AD-4) is used by every Change." Coordinate with the §4.8 amendment so Seat bookings get the same column.

### M5. A per-Sauna price cannot follow AD-18's "seed value as default" (AD-23 Price vs AD-18)

- **Problem.** AD-18: the seed writes only where the row is absent, and a new reference column gets the seed value as its default. `whole_price_ore` differs per Sauna, so no column default is the seed value, and on any existing database the `saunas` rows already exist, so the seed never writes the prices.
- **Failure scenario.** A developer database (or the examiner's, if started once before the update) has `whole_price_ore` NULL or a single default for all four Saunas; the Private sauna page shows NOK 0 or the same price everywhere.
- **Fix.** Amend AD-18: "A new per-row reference column is nullable; the seed writes its value where the column is NULL. A Sauna with `whole_price_ore` NULL is not offered whole." (Migrations still hold no reference values, AD-15.)

### M6. The idempotency key is not bound to what it was used for (AD-9)

- **Problem.** AD-9 rebuilds "the original response from the Booking" for any known key from the same session. With two flows (Seats and Private sauna) sharing the draft machinery in `sessionStorage`, nothing says each flow has its own key, and the server does not compare the request with the stored Booking.
- **Failure scenario.** A Guest pays a Seat booking with key K, goes back (or a draft slot is shared) and submits a Private sauna review with K: the server returns the Seat booking as success, nothing is booked, and the Guest believes a Sauna is reserved.
- **Fix.** Add to AD-9: "Each review page draft (Seats or Private sauna) has its own key. A known key whose stored Booking differs in kind, Window, Seats or Sauna from the request is refused with `409 invalid_key`." Add FR-29 and FR-33 to Binds.

### M7. Placement exposure and shape (AD-25)

- **Problem.** FR-31: "Guests are never told a Sauna. The Administrator can see the Placement of each Window." AD-25 says every page that shows Placement reads `placement(wid)`, but not that only Administrator endpoints may. It also leaves open whether the function returns a row for every Sauna (including 0 and whole-booked/Blocked/marked ones) and with what state.
- **Failure scenario.** The FR-30 listing story uses `placement()` to explain why a Sauna is unavailable ("3 Seats placed in Kajo") on a Guest page. Separately, the Admin view shows Saunas with 0 Seats inconsistently with the model test's comparison shape.
- **Fix.** "`placement(wid)` returns one row per Sauna in Fill order: `(sauna_id, state, seats)` with `state` in `open | whole | blocked | marked`, `seats` 0 unless open. Only endpoints under `/api/admin/` call it; no Guest endpoint returns a Sauna for a Seat booking."

### M8. The model test's first rule set is not fixed (AD-26)

- **Problem.** AD-26 says "each later If-time item adds its actions", but §4.8 (moves, partial moves, give-up for a Voucher) is built *before* §4.9 and creates the machine's actions FR-31 names. Nothing says the first version must include them.
- **Failure scenario.** The FR-31 story writes rules for Seat booking and Whole-sauna booking/cancel/move only; partial moves (the riskiest Placement change, FR-32 last bullet) never meet Whole-sauna bookings in one sequence.
- **Fix.** "The first version has one rule for every Placement-changing service action that exists when it is written: Seat booking, Seat move (full and partial) and Voucher give-up (§4.8), Whole-sauna booking, cancel and move (§4.9). Blocks and marks may be inserted raw as rules until their services exist."

### M9. Change history and the cancellation record are undecided and not deferred (AD-7, AD-23, Deferred)

- **Problem.** AD-23 says a move "is a history row (AD-7)" and a cancel sets the status; FR-16 requires the cancellation time, cause (Guest, Block, Overbooking fallback) and the Guest's refund-or-Voucher choice. No AD gives the history table or the cancellation columns, and Deferred lists only "Manage-link flow, Voucher balances and refunds".
- **Failure scenario.** The §4.8 amendment designs `booking_changes` for Seat moves with `seats_moved`; the FR-33 story needs `sauna_from/to` and adds a second table or JSON blob; the Admin list renders two histories.
- **Fix.** Add to Deferred (§4.8 amendment): "the Change history row and the cancellation record (time, cause, choice), shaped for both Seat and Whole-sauna Bookings (FR-16, FR-26, FR-27, FR-33)", or decide it now in AD-7.

### M10. Private sauna API shape is not decided (no AD)

- **Problem.** Paths for the FR-30 listing and the FR-29 create, how responses mark `kind`, and how a Sauna is named in Guest payloads (Conventions forbid showing internal ids to Guests; FR-30 requires the confirmation to name the Sauna) are left to each story. The confirmation endpoint (AD-12) and the Admin list (FR-16) both return Bookings of both kinds.
- **Failure scenario.** The backend story exposes `POST /api/whole-bookings` returning `sauna_id`; the SPA story expects `/api/private-saunas` and `sauna_name`; the Admin list story shows "Seats: null" for whole Bookings.
- **Fix.** "Whole-sauna bookings are created by `POST /api/bookings` with `kind: "whole"` and `sauna_id` (the listing `GET /api/saunas/whole?date=` returns `{sauna_id, name, capacity, whole_price_ore, windows[]}`). Every Booking payload (confirmation, Admin list) carries `kind`, and for `whole` the Sauna `name`; `seats` is omitted, not null."

## Low

- **L1 (AD-20).** "Every Booking creator uses it: the Guest flow, the seed and a split" — add "and the Whole-sauna flow".
- **L2 (AD-9 Binds; capability map).** Add FR-29, FR-33 to AD-9 Binds. The FR-29–33 row should also list AD-9, AD-10 (Admin Placement view, `api/admin.py`), AD-12 (§7 emails), AD-13 (price, payment), AD-16 (new codes), AD-20, and the SPA pages.
- **L3 (ER, Structural Seed).** Add `saunas |o--o{ bookings : "booked whole (kind=whole)"`; add `whole` to the `services/` list in the tree.
- **L4 (AD-12, `content/`).** State that the booking terms in `content/` exist per kind (Seat: 12 h Cutoff, no money back; Whole: 72 h Cutoff, refund or Voucher) and that the "Sauna is not held while you pay" sentence (FR-29) is Review-page copy in the SPA.
- **L5 (Deferred).** Add "Fill order frozen for started Windows (FR-38 F2), If-time 7: `placement(wid)` then reads a per-Window order".
- **L6 (AD-26).** Fix the Hypothesis profile: `deadline=None`, a bounded `max_examples`/`stateful_step_count` for `uv run pytest`, and reset (TRUNCATE + `clock.off = 0`) per example.
- **L7 (AD-23 Price).** Scope `price_differs` to a change of Sauna: "a move to *another* Sauna whose `whole_price_ore` differs from the Booking's `total_ore` is refused"; the same Sauna keeps the price paid (FR-38).

## Rubric walk

| Check | Result |
| --- | --- |
| Fixes the real divergence points for FR-29..33 | Mostly. Missing: predicate self-exclusion (H1), pairing events (H2), slice reshape (H3), move-with-Sauna (M3), API shape (M10), history row (M9) |
| Every Rule enforceable and prevents its divergence | AD-23 pairing check and AD-24 trigger/translation not enforceable as written (H1, H2, M1) |
| Nothing under Deferred lets units diverge | Refund/Voucher deferral is gated correctly; history row and Cutoff snapshot are neither deferred nor decided (M4, M9) |
| Ratifies brownfield schema and AD-1..AD-22 | Good on kernel; conflicts with AD-18 (M5), AD-21 test carry-over (H3), AD-16 codes (M2), AD-1 translation (M1) |
| Covers §4.9 capabilities | FR-29 store/listing, FR-31, FR-32 covered. Admin Placement view only partly (M7); confirmation naming the Sauna (M10); "Sauna not held" copy (L4); FR-36-style re-check covered implicitly by AD-3/AD-13 single transaction; emails covered by AD-12 but terms per kind open (L4) |
| Every dimension decided, deferred or open | The spine has no Open Questions section; M9, M10, L5 are in none of the three |
