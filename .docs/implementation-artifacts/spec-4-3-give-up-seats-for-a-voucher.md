---
title: 'Story 4.3: Give up Seats for a Voucher'
type: 'feature'
created: '2026-11-24'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/implementation-artifacts/epic-4-context.md'
  - '{project-root}/.docs/planning-artifacts/epics.md'  # Story 4.3 acceptance criteria, lines 1244-1305
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A Guest who can no longer use some or all of their Seats can only move them (Story 4.2). They cannot get back the value they paid, so a visit they cannot make is lost money.

**Approach:** Build the second Change, the Voucher instead of Seats (FR-27, AD-29, AD-30, AD-31), as epics.md Story 4.3 states it, in one PR. Migration `0012` adds `vouchers`, the cancellation columns and their trigger, `booking_changes.voucher_id` with the `voucher` shape, `payments.voucher_id` and the Voucher clause of `retention_due`. `POST /api/manage/{reference}/seats/voucher {seats, version}` gives up some Seats (the Booking shrinks) or all of them (the Booking is cancelled) in one locked, versioned, idempotent transaction that issues one Voucher. The Manage page gets a voucher step and a result page, and the Booking list shows the Voucher history line and the cancellation.

## Boundaries & Constraints

**Always:**
- The transaction follows `services.change.move`: unlocked `window_id` read, `lock_windows([current])`, re-read `FOR NO KEY UPDATE`, `db.Retry` when `window_id` moved, grant re-check by join (404), key read; then `booking_cancelled`, `booking_changed` (fact: the Booking now), `change_invalid` (`seats_exceed`), `cutoff_passed` (`cutoff_at`). No target Window, so no `same_target`, `outside_horizon`, `deadline_passed` or capacity refusal.
- Some Seats: `seats − n`, `total_ore = seats × price_per_seat_ore`, `version + 1` in one UPDATE. All Seats: one UPDATE sets `status = 'cancelled'`, `cancelled_at = app_now()`, `cancel_cause = 'guest'`, `cancel_remedy = 'voucher'`, `version + 1`, Seats and total unchanged.
- `services.voucher` (new) is the only writer of `vouchers`. `issue(c, booking_id, value_ore, *, last_valid_date=None) -> (id, code, last_valid_date)`: 16 Crockford base32 chars from `secrets`, displayed `XXXX-XXXX-XXXX-XXXX`, store only `sha256(code)`; value `n × price_per_seat_ore`, `balance_ore = value_ore`; last valid date = Venue date of `app_now()` + 1 year (29 Feb → 28 Feb), `expires_at` = 00:00 `venue_tz` the day after, computed in SQL from `app_now()`.
- Per Change: one `booking_changes` row `action = 'voucher'` with `seats` and `voucher_id` (via `services.history.record`), one `payments` row `refund`/`voucher` of the value with `voucher_id`, one email through `outbox.send(..., change_id=)`, then the key row. No `card` refund row.
- Idempotency: endpoint `POST /api/manage/seats/voucher`, hash of `{action: 'voucher', reference, seats, version}`; a repeat returns the first outcome (same email, no second Voucher); another session or body is `409 invalid_key`.
- Response: the one Change serializer gains `voucher: {value_ore, last_valid_date}`, rebuilt from the Change's `voucher_id` on a repeat. The code is never in a response, the Manage read, the history, a log or the Booking list; only in the email body.
- Store: `vouchers` CHECK `value_ore > 0 AND 0 <= balance_ore AND balance_ore <= value_ore`; cancellation CHECKs of AD-29 (all NULL while active; `cancelled_at` and `cause` set when cancelled; `guest` requires a remedy; `seat_guest_refund_forbidden`: `NOT (cancel_cause = 'guest' AND cancel_remedy = 'refund')`, since every `bookings` row is a Seat booking until Epic 5 adds `kind`); a BEFORE UPDATE trigger raising named constraint `booking_cancelled_frozen` for `cancelled → active` and for a change of `window_id` or `seats` on a cancelled row; `payments_voucher_id_matches_method` (`(method = 'voucher') = (voucher_id IS NOT NULL)`); `booking_changes` action CHECK `('move', 'voucher')`, `move` shape also requires `voucher_id IS NULL`, `voucher` shape: `seats` and `voucher_id` set, Window/Sauna ids and `new_booking_id` NULL.
- `retention_due(bid)`: past 12 months after the Window's end AND past the latest `expires_at` of Vouchers with `booking_id = bid` (none → only the first clause). The Booking list masking and the catch-up already call it.
- Frontend key slot `draft:change:<reference>:voucher`, same rules as the move step. The step reuses `SeatPicker` (max = Booking Seats, left out for 1 Seat), `ConfirmingStep`, `ChangeResult`.
- Decisions (Lisa, 2026-11-24):
  - The Voucher value is always Seats given up × the Booking's stored `price_per_seat_ore` (not the current setting); every "NOK {value}" below is that amount.
  - Manage page of a cancelled Booking (EXPERIENCE.md Open Item 19): the link still opens it; it shows reference, date, session and the Seats given up, the line "This booking was cancelled on {long date} at {HH:MM}. You gave up all seats for a voucher, which was sent by email." and no Change links. The Manage read carries `cancelled_at`.
  - Guest copy, verbatim: Manage page link "Give up seats for a voucher". Step `h1` "Give up seats"; question "How many seats do you want to give up?" (left out for a 1-Seat Booking); summary heading "What will happen" with rows "Seats given up", "Seats left in this booking" (only when some remain), "Voucher value" ("NOK {value}"), "Valid until" ({long date}); notes "No money is paid back. The voucher can pay for a new booking until it expires." and "Nothing changes until you confirm."; button "Give up 1 seat" / "Give up N seats". Result `h1` "Seats given up", line "Your booking has been changed." (some) or "Your booking has been cancelled." (all), then "Your voucher code is in the email below.", the email under "Sent by email:", and "Back to your booking". Refusals reuse the move texts: "This booking was changed in the meantime. Check it and choose again." (`booking_changed`, `invalid_key`), 4.1's Cutoff text (`cutoff_passed`), "The change could not be completed, please try again." (anything else).
  - Voucher email: some Seats — subject "Booking changed: {ref}", body as 4.2's Change email (the Booking now: Seats and total). All Seats — subject "Booking cancelled: {ref}", body "Booking cancelled", the Venue block, reference, date, session, "Seats given up: N". Both then the block "Voucher", "Code: XXXX-XXXX-XXXX-XXXX", "Value: NOK {value}", "Valid until: {long date}", "Use the code when you pay for a new booking. A voucher is never paid out in money.", and last "The Manage link in your booking confirmation email still works."
  - Booking list: history line "Gave up {N seat(s)} on {dd.mm.yyyy HH:MM} for a voucher of NOK {value}"; a cancelled Booking's Status cell "Cancelled {dd.mm.yyyy HH:MM} · Guest · Voucher" (time, cause, remedy).
  - Scope: one spec and one PR (about 3,600 tokens, accepted).

**Never:** Pay with a Voucher, `/api/vouchers/quote`, `voucher_invalid`, code normalisation (4.4). `services.payment.refund()`, `cancel` history action, Whole-sauna (Epic 5). A `bookings.kind` column. Edit migrations `0001`–`0011`. Add a dependency. Weaken an existing test. Read a clock in Python or the browser for a rule.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Partial | 4 Seats × 25000, give up 1 | 3 Seats, total 75000, v+1; Voucher 25000; Seats left +1; history, refund/voucher row, 1 email | — |
| All | 2 Seats, give up 2 | cancelled, guest, voucher, Seats 2 kept; Voucher 50000; Seats left +2 | — |
| Cancelled | any Change on it | `409 booking_cancelled` | Nothing changes |
| Stale tab | version 0 sent, Booking at 1 | `409 booking_changed` | Page reloads, fresh step |
| Bad count | seats 0, −1, > Booking Seats | `409 change_invalid seats_exceed` | — |
| After Cutoff | `clock.off` past Cutoff | `409 cutoff_passed {cutoff_at}` | 4.1 Cutoff text |
| Repeat | same key, session, body | first outcome, same email, one Voucher | other session/body: `409 invalid_key` |
| No grant | foreign ref / idle grant | `404 not_found` | Never 401 |
| Ledger | after partial and full | charges − returns = `total_ore` / 0 | — |
| Store bypass | direct UPDATE guest+refund; cancelled→active; seats on cancelled | refused by named constraints | — |

</frozen-after-approval>

## Code Map

- `migrations/0012_vouchers_cancellation.sql` (new) -- everything in the store bullets of Always; `CREATE OR REPLACE FUNCTION retention_due`. Do not add `cancelled_at`/`cancel_*` to the AD-7 trigger column lists (only `status` matters, already listed). Order: `vouchers` before the FKs that point to it.
- `src/booking_platform/db/vouchers.py` (new) -- insert (hash, value, `issued_at = app_now()`, `expires_at` from SQL `((app_now() AT TIME ZONE tz)::date + interval '1 year')::date + 1` at 00:00 tz, returning id and last valid date), read by id (value, last valid date).
- `src/booking_platform/services/voucher.py` (new) -- `CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"`, `new_code()`, `display(code)`, `code_hash(code)`, `issue(...)`.
- `src/booking_platform/db/changes.py` -- `HISTORY_COLUMNS` + `voucher_id`; `give_up_for_voucher(c, id, n)` (reuse `give_up_seats` body) and `cancel_for_voucher(c, id)`; `_HISTORY`/`history_of` join `vouchers` for `value_ore`; `change()` also returns `voucher_id`.
- `src/booking_platform/db/bookings.py:36` `insert_payment` -- optional `voucher_id`.
- `src/booking_platform/services/history.py` -- entries gain `voucher_value_ore` (null for a move).
- `src/booking_platform/services/change.py` -- `voucher(session_id, booking_id, reference, seats, version, key)`; extract the shared lock/re-read/grant/key prologue from `move` into one helper (move behaviour unchanged); `outcome()` adds `voucher` when the Change has one; Voucher email builder (Decisions).
- `src/booking_platform/services/manage.py` `booking_now` / `db/manage.py` `booking` -- add `cancelled_at` (null while active) for the Manage page.
- `src/booking_platform/api/manage.py`, `api/schemas.py` -- `POST /seats/voucher`, `VoucherIn{seats: Int4, version: Int4}` (any int, as `MoveIn`).
- `src/booking_platform/db/booking_list.py`, `services/booking_list.py` -- `cancelled_at`, `cancel_cause`, `cancel_remedy` per Booking.
- `frontend/app/manage/[reference]/voucher/page.js` (new), `frontend/components/GiveUpSeats.js` (new, modelled on `MoveSeats.js` without date/session), `ManageBooking.js` (link; cancelled state per Decisions), `BookingList.js` (`historyLine` for `voucher`, cancelled status), `lib/copy.js` (`MANAGE`, `VOUCHER`, `voucherRefusal` or reuse `moveRefusal`, `BOOKING_LIST`).
- Tests: `tests/conftest.py` `clear` must also delete `vouchers` (after `payments`/`booking_changes`); reuse `test_fr26_move.py` helpers (`opened`, `refused`, `before_cutoff`, `guest`, `left_in`), `test_fr25_manage_link.py` (`book`, `open_link`, `rows`), e2e `tests/e2e/test_fr26_move.py` (`_open_step` pattern), log search pattern of `tests/e2e/test_fr21_privacy.py:211`.

## Tasks & Acceptance

**Execution:**
- [ ] `migrations/0012_vouchers_cancellation.sql` -- store of Always -- AD-29/30/31.
- [ ] `db/vouchers.py`, `services/voucher.py` -- issue and code -- AD-30.
- [ ] `db/changes.py`, `db/bookings.py`, `services/history.py`, `services/change.py`, `services/manage.py`, `db/manage.py` -- the Change, ledger row, email, repeat, read.
- [ ] `api/manage.py`, `api/schemas.py` -- the route.
- [ ] `db/booking_list.py`, `services/booking_list.py`, `components/BookingList.js` -- history and cancellation -- FR-16.
- [ ] `lib/copy.js`, `ManageBooking.js`, `GiveUpSeats.js`, `app/manage/[reference]/voucher/page.js` -- step, result, cancelled Manage page.
- [ ] `tests/test_fr27_voucher_for_seats.py` -- every I/O row, refusal order, value, code format (regex `^[0-9A-HJKMNP-TV-Z]{4}(-[0-9A-HJKMNP-TV-Z]{4}){3}$` in the email) and that `code_hash = sha256(code)` and no column holds the code, expiry (incl. a 29 Feb clock), response shape without code, history, Seats left, cancellation columns and every store CHECK/trigger (fail under `BP_TEST_MUTATE=nocheck` where that switch applies), ledger, `retention_due` with a later-expiring Voucher.
- [ ] `tests/test_dr4_migrations.py`, `test_fr16_booking_list.py`, `test_fr21_retention.py`, `test_fr26_move.py` -- extend only as new columns require.
- [ ] `tests/e2e/test_fr27_voucher.py` -- keyboard-only give-up of 1 of 2 Seats, code in the email on the result page, Booking list line, all-Seats give-up and the cancelled Manage page, axe on step/result/cancelled page, widths 1024/1366/1920, no Voucher code in any container log.
- [ ] `README.md`, `.docs/sensorveiledning-kravsporing.md` -- Status, "Ikke levert" (FR-27 delivered), how to try it.

**Acceptance Criteria:**
- Given the change, when `uv run pytest` (API + e2e) runs, then everything is green including `test_fr27_voucher_for_seats.py`, `test_fr26_move.py` and `test_dr4_migrations.py`.
- Given a sample Manage link before its Cutoff, when the examiner gives up 1 of 2 Seats with the keyboard, then the result page shows the email with the Voucher code, value and last valid date, and the Booking list shows 1 Seat and the history line.
- Given all Seats given up, when the Booking list opens that date, then the Booking is listed as cancelled by the Guest with a Voucher and is outside Seats booked.

## Design Notes

A shared prologue keeps the two Changes in one order: `_locked(c, session_id, booking_id, extra_windows, key, endpoint, h) -> Locked | outcome` does the unlocked read, `lock_windows`, re-read, `Retry`, grant re-check and key read, returning the first outcome on a repeat. `move` passes `[window_id]`, `voucher` passes `[]`. Voucher write order inside the transaction: UPDATE Booking → `voucher.issue` → `history.record(..., 'voucher', seats=n, voucher_id=v)` → `payments` refund/voucher → email → key. A price of 0 cannot yield a Voucher (`value_ore > 0`); no v1 path sets price 0, so that case is a 500 from the store and is not handled further.

## Verification

**Commands:**
- `uv run pytest tests --ignore=tests/e2e` -- expected: all pass.
- `uv run pytest tests/e2e` -- expected: all pass.
- `npm --prefix frontend run build` -- expected: no errors; `/manage/[reference]/voucher` builds.
