---
title: 'Story 5.3 (part 1): Cancel a Private sauna'
type: 'feature'
created: '2026-11-26'
status: 'done'
baseline_commit: '81c223467df47510c93171db705f587143e7b79e'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/implementation-artifacts/epic-5-context.md'
  - '{project-root}/.docs/planning-artifacts/epics.md'  # Story 5.3 acceptance criteria (search "### Story 5.3"); the move ACs are NOT in this spec
  - '{project-root}/.docs/planning-artifacts/architecture/architecture-booking-platform-2026-11-03/ARCHITECTURE-SPINE.md'  # AD-23, AD-28, AD-29, AD-30, AD-31
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A Guest who booked a Private sauna (5.2) cannot cancel it: the Manage page shows the Booking with no actions, and no refund path exists (`services.payment.refund()` is missing).

**Approach:** Build the cancel half of epics.md Story 5.3: `POST /api/manage/{reference}/whole/cancel {remedy, version}` reusing Epic 4's Booking-scoped Change pattern, AD-31's `refund()`, migration 0014 (`cancel` history action), the cancellation email, the Manage page's "Cancel" confirming step, the cancelled Manage page, and the Booking list's cancel entry. Move is split off (Lisa 2026-11-26) into its own spec under Story 5.3; until then the Manage page of a Whole-sauna booking offers only Cancel.

**Decisions (Lisa, 2026-11-26):**
- Move is split off into its own spec under Story 5.3; the spec is kept whole (about 2600 tokens) despite the 1600 guideline.
- Whole-sauna cancel wording, accepted as proposed (record verbatim in EXPERIENCE.md as "Cancel private sauna wording"):
  - Manage page link: "Cancel private sauna". Cutoff text: "You can change this booking until {long date} at {HH:MM}." (existing) and after Cutoff "…until 72 hours before the session starts, and that was …".
  - Step heading "Cancel private sauna"; legend "What do you want back?"; options "A refund" (hint: "Paid back the way you paid.") and "A voucher" (hint: "A voucher for the full NOK {total}, valid for one year.").
  - "What will happen": Sauna, Session, then for refund "Refund to card" NOK x (if > 0), "New voucher" NOK y + "Valid until" (if > 0); for voucher "Voucher value", "Valid until" and the 4.3 note "No money is paid back. The voucher can pay for a new booking until it expires." Then "Nothing changes until you confirm."; button "Cancel booking".
  - Result: heading "Booking cancelled", "Your booking has been cancelled.", then "Your refund is in the email below." / "Your voucher code is in the email below.", "Back to your booking".
  - Cancelled Manage page: "This booking was cancelled on {long date} at {HH:MM}. You chose a refund, which was sent by email." / "…You chose a voucher, which was sent by email."
  - Email: subject "Booking cancelled: {ref}", body "Booking cancelled", Venue block, reference, date, session, "Sauna: {name}", then refund "Refunded to card: NOK x" + "Simulated payment: no money moves" (if card part) and the Voucher block (if Voucher part), or the Voucher block; last "The Manage link in your booking confirmation email still works."
  - Booking list history line: "Cancelled on {dd.mm.yyyy HH:MM} for a refund" / "…for a voucher of NOK {value}"; Status cell as today ("Cancelled … · Guest · Refund|Voucher").

## Boundaries & Constraints

**Always:**
- Route sits on `api/manage.py`'s router (grant via `require_grant`), takes `Idempotency-Key: uuid`, body `WholeCancelIn{remedy: 'refund'|'voucher', version: Int4}` (Strict, 422 `invalid_input` otherwise).
- `services/change.py`: parameterise `_locked` by expected kind (`'seats'` for existing routes, `'whole'` for the new one; wrong kind → `404 not_found` both ways). Refusal order: `booking_cancelled`, `booking_changed` (fact `booking`), `cutoff_passed` (fact `cutoff_at`). Key replay returns the first outcome and its stored emails and never a second refund or Voucher; other session/hash → `invalid_key`.
- One `db.run`, AD-23 write order: UPDATE booking (`status='cancelled'`, `cancelled_at=app_now()`, `cancel_cause='guest'`, `cancel_remedy`, `version+1`; generalise `db/changes.py:cancel_for_voucher`), DELETE `whole_bookings` row (new `db/whole.py:delete_capacity`), `history.record(action='cancel', voucher_id=…)`, payments, `outbox.send(…, change_id=)`, key row.
- `services/payment.py:refund(c, booking_id) -> {card_ore, voucher: {id, code, value_ore, last_valid_date} | None}` per AD-31: card charges → one `refund`/`card` row (simulated, cannot fail); Voucher charges → one new Voucher of their sum via `voucher.issue(last_valid_date=max(earliest last date of the Vouchers used, venue date of app_now()+30 days))` plus a `refund`/`voucher` row; a Booking with a split in its history (any `booking_changes.new_booking_id` = it, or it is a `new_booking_id`) raises an internal error (500). No path turns a Voucher balance into a card refund.
- Remedy `voucher`: one Voucher of full `total_ore`, one year (`voucher.issue` default), `refund`/`voucher` row; no card row.
- Migration `0014_whole_cancel.sql`: `booking_changes` action CHECK becomes `('move','voucher','cancel')` plus `cancel_shape` CHECK (`action<>'cancel' OR (seats, from/to_window_id, from/to_sauna_id, new_booking_id all NULL)`); `voucher_id` set exactly when the Booking's remedy is voucher is enforced in service code and tested. Nothing else changes.
- Change response `{booking, voucher?: {value_ore, last_valid_date}, refund?: {card_ore}, emails}`; on replay `refund` is rebuilt from the Booking's `refund`/`card` payments row. Code only inside the email.
- Manage read (`manage.booking_now`) adds `cancel_remedy` and, for an active whole Booking, `refund_split: {card_ore, voucher_ore, voucher_last_valid_date|null}` computed server-side (no browser clock for a rule); no email, code or link.
- Seats left rises by the Sauna's Capacity at once; the Booking list shows it cancelled with time, cause, remedy and does not count it.
- Ledger: for each test Booking, charges − returns = `total_ore` while active, 0 once cancelled.
- Frontend: `ManageBooking.js` whole branch shows the 72-hour Cutoff text and the Cancel link (`/manage/[reference]/cancel`), a new `CancelPrivateSauna.js` built from `ConfirmingStep`/`ChangeResult` and `GiveUpSeats.js`'s key and refusal handling; remedy is a radio group in `fieldset`/`legend`; `MANAGE.cutoffPassed` takes the hours; `BookingList.js historyLine` handles `cancel`.

**Never:** no move of a Whole-sauna booking (next spec), no `price_differs`, no Placement, no change to Seat Changes' behaviour or wording, no Manage token issued or revoked, no Sauna name in any Seat response, no browser clock for a rule.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error Handling |
|---|---|---|---|
| refund, card | Kajo paid by card, before Cutoff | 200; cancelled/guest/refund; no capacity row; `cancel` history row (voucher_id NULL); `refund`/`card` 315000; email; Seats left +12 | N/A |
| refund, partial Voucher | Kajo, NOK 250 Voucher + card | `refund`/`card` 290000; new Voucher 25000 with last date = max(earliest used, now+30 d); `refund`/`voucher` row; email has card line, payment note, Voucher block | N/A |
| voucher remedy | partial Voucher or card | one Voucher 315000, 1 year; `refund`/`voucher` row; no card row; history voucher_id set | N/A |
| Cutoff edge | clock 1 s before / at `start − 72 h` | 200 / 409 `cutoff_passed` with `cutoff_at` | nothing written |
| stale / cancelled | old `version`; second cancel with new key | 409 `booking_changed` (current Booking) / 409 `booking_cancelled` | nothing written |
| repeat | same key, same body/session | first outcome and stored emails; one refund, one Voucher | other session or body → 409 `invalid_key` |
| wrong kind | whole Booking on `…/seats/*`; Seat Booking on `…/whole/cancel` | 404 `not_found` | — |
| store rules | Seat Booking cancelled guest+refund via SQL; `refund()` on a split Booking | CHECK `seat_guest_refund_forbidden` refuses; 500 | — |
| shape | remedy missing/unknown, extra field | 422 `invalid_input` | nothing written |

</frozen-after-approval>

## Code Map

- `src/booking_platform/api/manage.py:40-58` -- router, `require_grant`, Seat routes as template for `POST /whole/cancel`. `api/schemas.py:83-93` -- `MoveIn`/`VoucherIn` pattern for `WholeCancelIn`; Change out schema gains `refund`.
- `src/booking_platform/services/change.py` -- `:65` endpoint constants, `:79` hash pattern, `:89` `outcome` (add `refund`), `:141` `voucher_block`, `:153` `voucher_email`/`_head`, `:169` `_locked` (kind guard `:180`), `:195` `_refuse_unless_current` (skip `seats_exceed` for whole), `:205` `_refuse_after_cutoff`, `:268` `voucher()` as the transaction template.
- `src/booking_platform/db/changes.py` -- `:23` `Locked` (add `sauna_id`, `total_ore`), `:87` `cancel_for_voucher` (generalise remedy), `:109` history SQL.
- `src/booking_platform/db/whole.py` -- add `delete_capacity(c, booking_id)`; `check_whole_pair` (0013:149) is deferred, so UPDATE before DELETE.
- `src/booking_platform/services/payment.py` -- add `refund`; `db/bookings.py:35` `insert_payment`, `:43` `charges`; `db/vouchers.py:56-63` Vouchers used by a Booking; `services/voucher.py:52` `issue`.
- `src/booking_platform/services/manage.py:89` `booking_now` -- add `cancel_remedy`, `refund_split`.
- `migrations/0013_whole_sauna_bookings.sql` -- header style; `0012:62-64` current action CHECK name and shape CHECKs.
- `services/booking.py:43` `SIMULATED`, `:88` `nok`, `:94` `long_date`.
- Frontend: `components/ManageBooking.js:65-101`, `GiveUpSeats.js` (template), `ConfirmingStep.js`, `ChangeResult.js`, `ManageBookingSummary.js`, `BookingList.js:42` `historyLine`, `lib/copy.js:171` `MANAGE` (+ new `CANCEL_WHOLE`), `app/manage/[reference]/voucher/page.js` as route template, `lib/draft.js` `changeKey`.
- Tests: `tests/test_fr27_voucher_for_seats.py` helpers (`ledger`, `_refused_by`), `test_fr26_move.py` (`refused`, `guest`), `test_fr25_manage_link.py` (`book`, `open_link`, `TOKEN`), `test_fr29_whole_booking.py` (`book_whole`, `:387` partial-Voucher booking, `:445` 404 test), `conftest.py` (`set_clock`, `world`, `raw_whole`, `state`). Clock: `BEFORE` is past the 72 h Cutoff; use a clock ≥ 72 h before the Window. e2e: `tests/e2e/test_fr27_voucher.py`, `test_fr30_private_sauna.py:423` `book_whole_in_browser`, `a11y.py`.

## Tasks & Acceptance

**Execution:**
- [x] `migrations/0014_whole_cancel.sql` -- `cancel` action and `cancel_shape` CHECK.
- [x] `src/booking_platform/db/{changes,whole,manage}.py` -- Locked fields, remedy cancel, capacity delete, read fields.
- [x] `src/booking_platform/services/{payment,change,manage}.py` -- `refund()`, `whole_cancel()`, email, outcome `refund`, `refund_split`.
- [x] `src/booking_platform/api/{manage,schemas}.py` -- route and schemas.
- [x] `tests/test_fr33_whole_change.py` (new) -- every matrix row, ledger asserts, Seats left, Booking list row, history row shape, 0014 CHECK via `_refused_by`.
- [x] `frontend/{components,app/manage/[reference]/cancel,lib}` -- Manage whole branch, cancel step, cancelled page, copy, history line.
- [x] `tests/e2e/test_fr33_whole_cancel.py` (new) -- keyboard-only cancel with each remedy, nothing changes before confirm, "Sent by email:" shows the stored email, axe on step and result, `X-Robots-Tag: noindex`, no referrer; cancelled page; Booking list.
- [x] `.docs/.../EXPERIENCE.md`, `README.md` -- record accepted wording; "Not delivered" lists only the whole move for 5.3.

**Acceptance Criteria:**
- Given the epics.md Story 5.3 ACs for the Manage page, cancel (both remedies), Cutoff, stale/cancelled, store rules, ledger and e2e, when this spec is done, then each holds and is tested; the move ACs remain open for the next spec.
- Given `uv run pytest` (both layers) and `npm --prefix frontend run build`, then all pass.

## Implementation Notes

- History `voucher_id` for remedy `refund` stays NULL even when `refund()` returns a Voucher; the response's `voucher` for a cancel is read from the Booking's `refund`/`voucher` payment row (either remedy), and `refund` is rebuilt from the `refund`/`card` row.
- For a Whole-sauna booking the Manage read's `voucher_last_valid_date` is one year ahead (the Voucher remedy), not `next_last_valid_date`.
- `MANAGE.cutoffPassed(longDate, time, hours = 12)`; the Whole-sauna pages pass `MANAGE.wholeHours` (72).
- `test_dr4_migrations.py::test_0013_…` now migrates up to 0013 only, and `test_fr27_…::test_the_history_and_payment_shapes_of_a_voucher` uses an unknown action instead of `cancel` (which 0014 allows).

## Spec Change Log

## Review Triage Log

| # | Layer | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|---|
| 1 | verification-gap, blind | No browser test of a Private sauna past its 72 h Cutoff (Manage page Notice, no Cancel link, cancel step Notice) | medium | Pre-verified gap: only `test_fr25_manage.py` renders `cutoffPassed`, for a Seat booking ("12 hours"); dropping `MANAGE.wholeHours` passes every test | patch — fixed: `test_after_the_72_hour_cutoff_the_pages_give_the_reason` |
| 2 | verification-gap, blind | `db/changes.py:cancel_for_voucher` is dead | low | grep: no caller left in `src`/`tests`; `voucher()` calls `cancel_by_guest` | patch — fixed |
| 3 | verification-gap, blind | `MANAGE.seatHours` is unused | low | grep: only its definition in `copy.js:179` | patch — fixed |
| 4 | blind | `has_split` reads `booking_changes` from `services.payment`, against the `db/changes.py` docstring rule "only `services.history` calls…" | low | Docstring rule is now false; a later reader trusting it would miss this reader | patch — fixed |
| 5 | verification-gap, edge, blind | Whole booking cancelled without remedy (`block`/`overbooking`) shows no cancelled text; "You chose…" would misstate an Administrator cancel | low | No code path cancels with cause `block`/`overbooking` (grep `src`; only 0012's data fix of old Seat rows); Blocks have no page yet (README) | reject (unreachable, fix adds branches) |
| 6 | edge | Failed re-read after `booking_changed` leaves the step open with a stale version | low | True: `load.status = 'failed'` keeps `prev.booking`; but it only shows the loadFailed Notice and a repeat confirm is refused again, nothing written; same pattern as `GiveUpSeats.js:56`/`MoveSeats.js:64` | reject (rare, harmless, fix adds a guard) |
| 7 | edge | `changeKey` creates a fresh key outside the open-step rule after a failed re-read | low | Same state as #6; the request is refused `booking_changed`, no write | reject (as #6) |
| 8 | blind | Frontend falls back to an invented `refund_split` (all to card) | low | Unreachable: the step opens only for an active whole Booking, and `booking_now` always adds `refund_split` then | reject |
| 9 | blind | One-year rule duplicated (`a_year_ahead` vs `vouchers.insert` default) | low | Both are `(app_now() AT TIME ZONE venue_tz)::date + interval '1 year'`; same today, diverges only if one is edited | reject (fix is a refactor) |
| 10 | blind | No race tests (concurrent cancels → double refund) | false | `_locked` takes `lock_windows` + `FOR NO KEY UPDATE`; the second cancel sees `status = 'cancelled'` → `booking_cancelled`; group-C races are Story 5.5 | reject |
| 11 | blind | Zero total breaks the Voucher remedy | false | `saunas_whole_price_positive CHECK (whole_price_ore > 0)` (0013:90) and `total_ore = whole_price_ore` | reject |
| 12 | blind | Result says "Your refund is in the email below." when part returns as a Voucher; list line "for a refund" | false | Lisa's approved wording, verbatim in the frozen intent; refund history row has `voucher_id` NULL by design | reject |
| 13 | blind | `epic-5-context.md` already stale ("Not decided yet", "hardcodes 12 hours", Move) | false | The cache is invalid as soon as a planning file is newer; EXPERIENCE.md changed in this diff, so the next story recompiles it | reject |
| 14 | blind | No migration test applying 0014 over existing `move`/`voucher` rows | low | Re-added CHECKs hold trivially for those rows (action in set; `cancel_shape` vacuous for non-cancel) | reject |
| 15 | blind | Import order / lines > 120 chars | false | The project has no linter config (no ruff/isort in `pyproject.toml`) and the same style is used elsewhere | reject |

## Verification

**Commands:**
- `uv run pytest -x -q tests --ignore=tests/e2e` -- all pass
- `uv run pytest tests/e2e` -- all pass (compose stack)
- `npm --prefix frontend run build` -- builds
