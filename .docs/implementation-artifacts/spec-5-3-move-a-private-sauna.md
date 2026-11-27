---
title: 'Story 5.3 (part 2): Move a Private sauna'
type: 'feature'
created: '2026-11-26'
status: 'done'
baseline_commit: 'ab8866fdf8c149d7d42f0a7e502526b7d53d4f98'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/implementation-artifacts/epic-5-context.md'
  - '{project-root}/.docs/planning-artifacts/epics.md'  # Story 5.3 move ACs (search "### Story 5.3")
  - '{project-root}/.docs/implementation-artifacts/spec-5-3-cancel-a-private-sauna.md'  # part 1, the pattern this mirrors
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A Guest with a Private sauna can cancel it (part 1) but not move it: the Manage page offers only "Cancel private sauna", and no move route, move list or `price_differs` exists.

**Approach:** Build the move half of epics.md Story 5.3: `POST /api/manage/{reference}/whole/move {window_id, sauna_id, version}` on Epic 4's Booking-scoped Change pattern, a grant-scoped move list (the AD-24 listing with `ignore_booking`), migration 0015 (whole `move` history shape + Room-ahead honouring `ignore_booking`), the Change email, a "Move" confirming step on the Manage page and the Booking list history line.

**Decisions (Lisa, 2026-11-26):**
- Spec kept whole (about 2800 tokens) despite the 1600 guideline.
- Saunas at another price (all four seeded prices differ): the move step lists the Booking's own Sauna first ("Your sauna"), then other free Saunas; a Sauna whose `whole_price_ore` differs from `total_ore` shows its price and "This sauna has another price than you paid. To book it, cancel this booking and book again." and has no session buttons. The API still refuses `price_differs` (tested in the API layer); the step maps that refusal to the same text.
- Move private sauna wording, accepted as proposed (record verbatim in EXPERIENCE.md as "Move private sauna wording"); `price_differs` text as above:
   - Manage link and `h1` "Move private sauna" (title "Move private sauna – Saunalöyly"); "1. Choose a date", "2. Choose a sauna and a session"; "Your sauna" label; current pair a disabled button "Your current session".
   - "What will happen": "From" {Sauna}, {long date}, {HH:MM}–{HH:MM}; "To" same form; "Price" "NOK {total} (unchanged)"; "Nothing changes until you confirm."; button "Move booking".
   - Result: "Booking moved", "Your booking has been changed.", "Sent by email:", "Back to your booking".
   - Refusals: `sauna_unavailable` "This sauna can no longer be booked for this session. Nothing has changed."; `price_differs` the text above; `same_target` "This is your current session. Nothing has changed."; others reuse Move seats texts; `cutoff_passed` the 72-hour Manage text.
   - Email: subject "Booking changed: {ref}"; body "Booking changed", Venue block, reference, date, session, "Sauna: {name}", "Total: NOK {total}", last "The Manage link in your booking confirmation email still works."
   - Booking list: "Moved on {dd.mm.yyyy HH:MM} from {Sauna} {dd.mm.yyyy HH:MM–HH:MM} to {Sauna} {dd.mm.yyyy HH:MM–HH:MM}".

## Boundaries & Constraints

**Always:**
- Route on `api/manage.py`'s router (`require_grant`), `Idempotency-Key: uuid`, body `WholeMoveIn{window_id: Int4, sauna_id: Int4, version: Int4}` (Strict; 422 `invalid_input`). Wrong kind → `404 not_found` both ways (via `_locked(kind="whole")`).
- Refusal order: `booking_cancelled`, `booking_changed` (fact `booking`), `change_invalid` reason `same_target` (same Window **and** Sauna), `outside_horizon`, `deadline_passed` (target), `cutoff_passed` (Booking, fact `cutoff_at`), `sauna_unavailable` (`whole_bookable(target, booking_id)` false, or unknown Sauna), `price_differs` (target Sauna ≠ Booking's Sauna and its `whole_price_ore` ≠ `total_ore`; same Sauna never checks price). `price_differs` declared once in `api/errors.py` and once in `frontend/lib/api.js`.
- One `db.run(work, refusals=whole.REFUSALS)`: UPDATE `bookings` (`window_id`, `sauna_id`, `version+1`; `entry_time`, reference and `total_ore` kept), then UPDATE the `whole_bookings` row (both columns together), `history.record("move", from/to_window_id, from/to_sauna_id)`, Change email via `outbox.send(…, change_id=)`, key row. No payment row. Key replay returns the first outcome and stored emails; other session/hash → `invalid_key`.
- Migration `0015_whole_move.sql`: `booking_changes_move_shape` allows either the Seat shape (unchanged) or the whole shape (seats, voucher_id, new_booking_id NULL; both Window and both Sauna ids set; Window or Sauna differs); `whole_bookable`'s Room-ahead clause treats the `ignore_booking` row's Sauna as open. Nothing else changes.
- Move list: `GET /api/manage/{reference}/whole/move-list?date=` (grant, noindex, no lock) returns the AD-24 listing shape built by `services.whole.listing(date, ignore_booking=booking_id)`; the Booking's own pair stays listed and the UI shows it as "Your current session".
- History entries gain `from_sauna`/`to_sauna` `{id, name}` only for `kind = 'whole'` Bookings; Seat entries and Seat Change emails never name a Sauna.
- Capacity follows at once in both Windows; ledger (charges − returns) stays `total_ore` after a move.
- Frontend: Manage whole branch adds the move link beside cancel; new step `MovePrivateSauna.js` on `/manage/[reference]/move-sauna`, built from `ManageBookingSummary`/`ConfirmingStep`/`ChangeResult`, `DateCalendar`, key and refusal handling as `MoveSeats.js`/`CancelPrivateSauna.js`; `BookingList.js historyLine` handles a whole move.

**Never:** no charge or refund of a price difference, no change to Seat move behaviour/wording, no Manage token issued or revoked, no Placement (5.4), no browser clock or client-side rule as the only guard.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error Handling |
|---|---|---|---|
| move, same Sauna | Kajo W1 → Kajo W2, before Cutoff | 200; Booking in W2, same ref/`total_ore`/`entry_time`, `version+1`; capacity row moved; `move` history row with both Windows and Saunas; one Change email; Seats left W1 +12, W2 −12 | N/A |
| move, Sauna at same price | test Sauna priced = `total_ore` | 200, Sauna changed | N/A |
| same Window, later Sauna | Rauha W1 → X W1 (equal price, X later in Fill order, Seats fit only with Rauha open) | 200 (0015 Room-ahead fix) | N/A |
| price differs | Kajo → Lumo | 409 `price_differs` | nothing written |
| unavailable | target pair booked whole / Blocked / Room ahead fails | 409 `sauna_unavailable` | nothing written |
| same target | same Window and Sauna | 409 `change_invalid` `same_target` | nothing written |
| target window | outside horizon / past deadline | 409 `outside_horizon` / `deadline_passed` | nothing written |
| Cutoff edge | clock 1 s before / at `start − 72 h` | 200 / 409 `cutoff_passed` | nothing written |
| stale / cancelled / repeat / wrong kind | as part 1 | `booking_changed` / `booking_cancelled` / first outcome / 404 | nothing written |
| move list | Booking's own Window/date | own pair listed; Saunas around it judged as if it were absent | — |
| shape | extra field, missing ids | 422 `invalid_input` | — |

</frozen-after-approval>

## Code Map

- `services/change.py` -- `:76` endpoint consts, `:84-98` hashes (add `whole_move_hash`), `:108` `outcome`, `:131` `_head`, `:192` `cancellation_email` (model for the move email; `change_email` :149 is Seat-only), `:210` `_locked(kind=)`, `:236` `_refuse_unless_current(None)`, `:248` `_refuse_after_cutoff`, `:257` `_refuse_unless_changeable` (same_target compares Window only: add Sauna for whole), `:267` Seat `move` as template, `:345` `whole_cancel`.
- `services/whole.py` -- `:44` `REFUSALS` (maps `whole_bookable`, `booked_within_capacity`, pair key → `sauna_unavailable`; pass it to `db.run`), `:51` `listing(date)` (add `ignore_booking`). `db/whole.py:17` `pairs_on` already takes `ignore_booking`; add `move_capacity(c, booking_id, wid, sid)`.
- `db/changes.py:68` `move_all` sets `entry_time` -- add a whole UPDATE that keeps it; `:122` `_HISTORY` add `from/to_sauna_id` + names; `services/history.py:30-48` entry shape (docstring "never holds a Sauna" → only for Seat bookings).
- `migrations/0012_vouchers_cancellation.sql:66-69` current move shape; `0013:122-131` `whole_bookable`, `0001:68-82` `room_ahead`/`sauna_open_for_seats`; `0013:133-184` triggers (row update judged with `NEW.booking_id`; deferred `check_whole_pair` → UPDATE Booking first); `0014` header style.
- `api/manage.py`, `api/schemas.py`, `api/errors.py:31-35`, `api/public.py:38` (listing response model to reuse).
- Frontend: `ManageBooking.js:77-103` (link list :91-97), `MoveSeats.js` (key :78/93/173/187, refusals :183-209, result :217-235), `CancelPrivateSauna.js`, `PrivateSauna.js` (`SaunaCards` :124 file-private; extract only what the step needs), `SaunaCard.js`, `DateCalendar`, `lib/copy.js` (`MANAGE` :172, `MOVE` :196, `moveRefusal` :280, `CANCEL_WHOLE` :244, `BOOKING_LIST.moved` :370), `lib/api.js:18-23`, `app/manage/[reference]/cancel/page.js`.
- Tests: `test_fr33_whole_change.py` (`far` :53, `whole_opened` :64, `booking_row` :83, `history_rows` :88), `test_fr26_move.py` (`move`, `refused`, `left_in`, `everything`), `test_fr29_whole_booking.py` (`KAJO, LUMO, RAUHA`), `conftest.py` (`set_clock`, `raw_whole`, `state`), `test_dr4_migrations.py`; e2e `test_fr33_whole_cancel.py` (`_book_whole`, `_open_manage`), `test_fr26_move.py` (`_choose`, `_slot`).

## Tasks & Acceptance

**Execution:**
- [x] `migrations/0015_whole_move.sql` -- move shape for whole; Room-ahead honours `ignore_booking`.
- [x] `src/booking_platform/db/{changes,whole}.py`, `services/{whole,history,change,manage}.py` -- whole UPDATEs, listing ignore, history saunas, `whole_move()`, email.
- [x] `src/booking_platform/api/{manage,schemas,errors}.py` -- move route, move-list route, `price_differs`.
- [x] `tests/test_fr33_whole_change.py` -- every matrix row, ledger, Seats left both Windows, Booking list, history shape, 0015 CHECKs; `test_dr4_migrations.py` adjusted; `deferred-work.md` room_ahead entry marked resolved.
- [x] `frontend/{components,app/manage/[reference]/move-sauna,lib}` -- move step, Manage link, copy, refusal mapping, history line.
- [x] `tests/e2e/test_fr33_whole_move.py` (new) -- keyboard-only move, nothing changes before confirm, "Sent by email:", other-price Sauna shown with its reason and no session buttons, axe, `X-Robots-Tag: noindex`, no referrer, Booking list line.
- [x] `EXPERIENCE.md`, `README.md` -- record wording; drop the 5.3 move from "Not delivered".

**Acceptance Criteria:**
- Given epics.md Story 5.3's move, refusal, Cutoff, stale, ledger and e2e ACs, when this spec is done, then each holds and is tested, and 5.3 can be marked done in `sprint-status.yaml`.
- Given `uv run pytest` (both layers) and `npm --prefix frontend run build`, then all pass.

## Implementation Notes

- `db.whole.pairs_on` with `ignore_booking` lists `whole_bookable` pairs plus the `ignore_booking` row's own pair (within the time rules), so the own pair stays listed also when Seats booked meanwhile exceed its Sauna's Room ahead (`test_the_move_list_keeps_the_own_pair_when_seats_exceed_its_room_ahead`).
- Pre-checks in `services.change.whole_move`: `whole_bookable(target, sauna, booking_id)` (also unknown Sauna) then the price; the store's `trg_check_whole`/`booked_within_capacity`/pair key stay the backstop via `whole.REFUSALS`. An unknown target Window is `404 not_found` (via `ensure_open_for_booking`), as in the Seat move.
- The Change hash includes `sauna_id` (`whole_move_hash`); the key slot is `draft:change:<ref>:move` (one move kind per Booking).
- History entries of a Whole-sauna booking always carry `from_sauna`/`to_sauna` (null for `cancel`); Seat entries never have the keys. `test_cancel_for_a_refund_returns_the_card_payment` was adjusted for that.
- `GET …/whole/move-list` answers `404 not_found` for a Seat booking (route of the other kind).
- The move email's total line is "Total: NOK {total}" (no "incl. VAT"), as the accepted wording says.

## Spec Change Log

## Review Triage Log

| # | Source | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|---|
| 1 | blind, edge | After `outside_horizon`/`deadline_passed` the refused pair stays chosen and "Move booking" can be resent | low | `confirm()` re-reads the list only for `sauna_unavailable`/`price_differs`; `moveRefusal` returns `stay` for both codes | patch |
| 2 | blind | An old refusal Notice stays after the Guest picks a new pair | low | `choosePair`/`pickDate` never call `setRefusal(null)`; direct one-line fix | patch |
| 3 | blind, edge, verification-gap | The own pair can be missing from the move list (and no "Your sauna" card) when Seats exceed the own Sauna's Room ahead | medium | `pairs_on` keeps a pair only if `whole_bookable(w, s, ignore_booking)`, which still applies Room ahead to the own pair; Kajo's Room ahead is 17 while Seats can reach 32 around it. Deviates from the matrix row "own pair listed" | patch |
| 4 | blind | No message when the fieldset has no enabled radio | low | Real only if every other own-Sauna session that date is taken; needs new wording Lisa has not decided | reject |
| 5 | blind | 0015 inlines `sauna_open_for_seats` instead of parameterising it | low | Duplicated rule is real; fix adds a parameter to shared functions used by 0003/0013 triggers | reject |
| 6 | blind | `epic-5-context.md` still says the move is next/undecided | low | Lines "Next is the move half", "Move (next work)", "Move wording: NOT decided yet" contradict the shipped wording; direct text edit | patch |
| 7 | blind | Verification section overstates what passed | false | The section lists commands to run, not results; the full API layer (661) and e2e were re-run in step 3 | reject |
| 8 | blind | No test moves to another date | low | Cross-date path is plain data flow (`ordered` returns cards unchanged); adding tests is more than a direct fix | reject |
| 9 | blind, verification-gap | The step's `sauna_unavailable` refusal text and list re-read have no e2e test | medium | Filed pre-verified: only `price_differs` is exercised in `test_fr33_whole_move.py` | patch |
| 10 | blind, verification-gap | Stale-version renewal (new key) and the 72-hour Cutoff on `/move-sauna` have no e2e test | medium | Filed pre-verified: the cancel step has both (`test_fr33_whole_cancel.py:303`, `:342`), the move step neither | patch |
| 11 | blind, verification-gap (other) | The store backstop (`whole.REFUSALS` on move) is never reached by a test | low | Both Windows are locked in id order before the pre-check, so the backstop is practically unreachable; a race test is more than a direct fix | reject |
| 12 | blind, edge | `whole_move_list` reads kind by position and serves a cancelled Booking a move list | low | Writes nothing and the step never opens for a cancelled Booking; the listing is public data | reject |
| 13 | blind | `historyLine` detects a whole move by the Sauna fields, not `action === 'move'` | low | Today only `move` carries both Saunas; direct one-condition fix | patch |

## Verification

**Commands:**
- `uv run pytest -x -q tests --ignore=tests/e2e` -- all pass (local: `DB_PORT=56432`)
- `uv run pytest tests/e2e` -- all pass
- `npm --prefix frontend run build` -- builds
