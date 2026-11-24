---
title: 'Story 4.2: Move all or some Seats to another session'
type: 'feature'
created: '2026-11-24'
status: 'done'
baseline_commit: '4d56b5a42b18997bcdc563c0b7ce71a289bbe07d'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/implementation-artifacts/epic-4-context.md'
  - '{project-root}/.docs/planning-artifacts/epics.md'  # Story 4.2 acceptance criteria, lines 1181-1242
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A Guest can open their Booking through the Manage link (Story 4.1) but cannot change it. When plans change they must keep a session they cannot use.

**Approach:** Build the first Change, the Seat move (FR-26, AD-29), as epics.md Story 4.2 states it, in one PR. Migration `0011` adds `booking_changes`, `outbox_emails.change_id` and `idempotency_keys.change_id`. `POST /api/manage/{reference}/seats/move` moves all Seats (UPDATE) or some (a split with a new reference and Manage link) in one locked, versioned, idempotent transaction. The Manage page gets a move step and a result page, and the Booking list shows status and history.

## Boundaries & Constraints

**Always:**
- The transaction order and the refusal order of epics.md Story 4.2 / AD-29, verbatim: read `window_id` unlocked, `lock_windows([current, target])`, re-read `FOR NO KEY UPDATE`, retry through `db.run` when `window_id` changed, re-check `manage_grant_valid` by join (404), read the key; then `booking_cancelled`, `booking_changed` (fact: the Booking as the Manage read shows it), `change_invalid` (`reason`: `seats_exceed` | `same_target`), `outside_horizon`, `deadline_passed`, `cutoff_passed` (`cutoff_at`), `no_seat_free` (`seats_left` of the target), and the store's `booked_within_capacity` as the backstop.
- `bookings.version` rises in the same UPDATE as the Change; a split keeps the original's reference, link, `price_per_seat_ore` and `cutoff`, sets `total_ore = seats × price_per_seat_ore`, and the new Booking gets everything epics.md lists (reference through `services.reference`, its own token through `services.manage.issue`, a grant for the acting session, no `payments` rows).
- `services.history.record` is the only writer of `booking_changes`; no trigger writes it. Shape CHECK for `move`: both Window ids and `seats` set, Sauna ids NULL; `new_booking_id` only for a split.
- Idempotency (AD-9): endpoint `POST /api/manage/seats/move`, hash of `{action, reference, seats, version, window_id}`; same key + session + hash returns the first outcome (emails read by `change_id`, the Booking now); anything else known is `409 invalid_key`. Only a success stores a key (`change_id` set, `booking_id` NULL; CHECK exactly one).
- One Change response serializer: `{booking, new_booking?, emails: [{id, subject, body}]}`; `booking`/`new_booking` in the Manage read shape. No name, email, token or Sauna in it.
- Emails go through `outbox.send(..., change_id=)`; none carries the original's Manage link; Seat emails never name a Sauna.
- New codes `booking_cancelled` (409), `booking_changed` (409), `change_invalid` (409) in `api/errors.py` and `lib/api.js`.
- Frontend key slot `draft:change:<reference>:move` (sessionStorage): made when the step opens, reused on reload, deleted on success, on every refusal except `503 try_again`, and on leaving the step. After `booking_changed`/`invalid_key` the step reloads the Booking and opens fresh with a new key.
- The move step reuses `DateCalendar`, `SeatPicker` (limited to 1..Booking Seats), `SessionList` and `GET /api/windows`, and `ConfirmingStep`/`ChangeResult` from 4.1.
- Decisions (Lisa, 2026-11-24):
  - The current session appears in the target list as a disabled row saying "Your current session".
  - Guest copy, verbatim: Manage page link "Move seats". Step `h1` "Move seats"; questions "1. How many seats do you want to move?" (left out when the Booking has 1 Seat), "2. Choose a date", "3. Choose a session"; summary heading "What will happen" with rows "Seats moved", "From", "To", "Seats left in this booking"; note "Nothing changes until you confirm."; button "Move 1 seat" / "Move N seats". Result `h1` "Seats moved", line "Your booking has been changed.", plus for a split "Your moved seats have a new booking reference: {ref}.". Refusals: "Only N seats left in this session. Nothing has changed." / "No seat free in this session. Nothing has changed." (`no_seat_free`); "This session can no longer be booked. Nothing has changed." (`outside_horizon`, `deadline_passed`); "This booking was changed in the meantime. Check it and choose again." (`booking_changed`, `invalid_key`); "The change could not be completed, please try again." (anything else); after `cutoff_passed`, 4.1's Cutoff text.
  - Change email: subject "Booking changed: {ref}"; body "Booking changed", the Venue block, reference, date, session, Seats and total of the Booking now; for a split also "Seats moved: N", "New booking reference: {new}" and "The moved seats have their own confirmation email."; then "The Manage link in your booking confirmation email still works.". The split-off Booking's own email reuses `confirmation_email` with its own link.
  - Booking list: a "Status" column (Active / Cancelled), cancelled Bookings listed too; under a Booking with history one line per entry, "Moved {N seat(s)} on {dd.mm.yyyy HH:MM} from {dd.mm.yyyy HH:MM–HH:MM} to {dd.mm.yyyy HH:MM–HH:MM}", plus " · new booking {ref}" for a split.
  - Scope: one spec and one PR (about 3,400 tokens, accepted).

**Never:** Vouchers, cancellation columns or triggers (4.3), Whole-sauna moves (Epic 5), My booking (FR-34). Edit migrations `0001`–`0010`. Add a dependency. Weaken an existing test. Read a clock in Python or the browser for a rule.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Full move | 2 Seats W1 → W2, version 0 | Same row: `window_id` W2, `entry_time` now, version 1; history row; 1 email | — |
| Split | 3 Seats W1, move 1 → W2 | Original 2 Seats, total 2×price, v+1; new Booking 1 Seat W2 with token + grant; history `new_booking_id`; 2 emails | — |
| E5 | 3 Seats → W2 with 2 left | `409 no_seat_free {seats_left: 2}` | Nothing changes |
| Stale tab | version 0 sent, Booking at 1 | `409 booking_changed` | Page reloads, fresh step |
| Bad request | seats 0 or > Booking Seats; target = current | `409 change_invalid` `seats_exceed` / `same_target` | — |
| After Cutoff | `clock.off` past `lower(during) - cutoff` | `409 cutoff_passed {cutoff_at}` | Page shows 4.1's Cutoff state |
| Repeat | same key, session, body | First outcome, nothing written | Other session/body: `409 invalid_key` |
| No grant | foreign ref / idle grant | `404 not_found` | Never 401 |
| Races ×100 | W1→W2 ∥ W2→W1; move ∥ new booking for last Seats | No deadlock, no oversell, totals kept, exactly one winner when room for one | — |

</frozen-after-approval>

## Code Map

- `migrations/0011_booking_changes.sql` (new) -- `booking_changes` (FKs to bookings, windows, saunas; `action` CHECK `('move')`; shape CHECK), `outbox_emails.change_id` FK + index, `idempotency_keys.change_id` FK, `booking_id DROP NOT NULL`, CHECK `num_nonnulls(booking_id, change_id) = 1`. Do not touch AD-7 trigger column lists.
- `src/booking_platform/db/__init__.py` -- add `Retry` exception caught in `run` like `_TEMPORARY` (for the `window_id` re-read mismatch).
- `src/booking_platform/db/changes.py` (new) -- SQL: unlocked `window_id` read, `FOR NO KEY UPDATE` re-read (status, version, seats, window, price, cutoff, name, email, reference), grant re-check, full-move UPDATE, seats UPDATE, history insert/read (by booking, by change id), change key insert.
- `src/booking_platform/db/bookings.py` -- `key()` also returns `change_id`; `insert_email` takes `change_id`; `emails_by_change`.
- `src/booking_platform/db/seats.py:55` `insert_booking` -- add an optional `cutoff` param (split copies the original's).
- `src/booking_platform/db/manage.py` -- `issue` path returns token id too (`insert_token` already returns it) for the split grant; `upsert_grant` reused.
- `src/booking_platform/services/history.py` (new) -- `record(c, booking_id, action, **cols) -> change_id`; `of_booking(c, booking_id)` for reads.
- `src/booking_platform/services/change.py` (new) -- `move(session_id, ref_booking_id, window_id, seats, version, key)`, the serializer, emails. Reuse `services.windows.ensure_open_for_booking`, `services.booking.confirmation_email/long_date/nok`, `services.manage.issue/link/read`, `reference.claim`.
- `src/booking_platform/services/outbox.py` -- `send(..., change_id=None)`; `of_change(c, change_id)` with ids.
- `src/booking_platform/services/manage.py` -- `read` fills `history` from `services.history`; `issue` unchanged in behaviour.
- `src/booking_platform/api/manage.py` -- `POST /seats/move` on `router` (needs `current_session` and the `Idempotency-Key` header as in `api/public.py:61`); schema `MoveIn{window_id, seats, version}` in `api/schemas.py`.
- `src/booking_platform/api/errors.py`, `frontend/lib/api.js` -- three new codes.
- `src/booking_platform/db/booking_list.py`, `services/booking_list.py` -- status and history per Booking (Decisions).
- `frontend/app/manage/[reference]/move/page.js` (new) + `frontend/components/MoveSeats.js` (new) -- the step and the result; `ManageBooking.js` gets the "Move seats" link while `change_allowed`.
- `frontend/components/SeatPicker.js` -- optional `max` prop (default 10) and optional legend; `SessionList.js` -- optional `currentWindowId` (Decisions).
- `frontend/lib/copy.js` -- `MOVE` and `moveRefusal(code, facts)`; `BOOKING_LIST` status/history strings. `frontend/lib/draft.js` -- change-key slot helpers.
- `frontend/components/BookingList.js` -- Status column and history lines.
- Tests: reuse `tests/conftest.py` (`world`, `api`, `admin`, `set_clock`, `raw_booking`, `state`), `test_fr25_manage_link.py` helpers (`book`, `open_link`, `before_cutoff`), `test_fr10_through_the_api.parallel`, e2e `guest.book_in_browser`, `a11y.check_axe`, `tab_to`.

## Tasks & Acceptance

**Execution:**
- [x] `migrations/0011_booking_changes.sql` -- schema of AC 1 -- AD-9/12/29.
- [x] `db/__init__.py`, `db/changes.py`, `db/bookings.py`, `db/seats.py`, `db/manage.py` -- SQL for the Change -- all SQL stays in `db`.
- [x] `services/history.py`, `services/outbox.py`, `services/change.py`, `services/manage.py` -- the move, emails, repeat, read history -- AD-29.
- [x] `api/manage.py`, `api/schemas.py`, `api/errors.py` -- the route and codes.
- [x] `db/booking_list.py`, `services/booking_list.py`, `components/BookingList.js` -- status and history -- FR-16.
- [x] `lib/api.js`, `lib/copy.js`, `lib/draft.js`, `SeatPicker.js`, `SessionList.js`, `ManageBooking.js`, `MoveSeats.js`, `app/manage/[reference]/move/page.js` -- the step and result.
- [x] `tests/test_fr26_move.py` -- every I/O row, refusal order, emails + `change_id`, history, Seats left in both Windows, store bypass (`UPDATE bookings SET window_id` into a full Window refused; fails under `BP_TEST_MUTATE=nocheck`), both races ×100.
- [x] `tests/test_dr4_migrations.py`, `tests/test_fr16_booking_list.py` -- extend only as the new columns require.
- [x] `tests/e2e/test_fr26_move.py` -- keyboard-only move of 1 of 2 Seats, result page, Booking list, axe on step and result, widths 1024/1366/1920.
- [x] `README.md` -- Status line, "Ikke levert" (FR-26 delivered), how to try a move.

**Acceptance Criteria:**
- Given the change, when `uv run pytest` (API + e2e) runs, then everything is green including `test_fr26_move.py` and `test_dr4_migrations.py`.
- Given a sample Manage link before its Cutoff, when the examiner moves 1 of 2 Seats with the keyboard, then the result page shows both emails under "Sent by email:" with the new reference and its Manage link, and the Booking list shows both Bookings in their sessions and the history line.
- Given a Booking after its Cutoff, when the Manage page loads, then no move link is offered and the 4.1 Cutoff text shows.

## Implementation Notes

- `MoveIn.seats` and `.version` accept any int4, so seats 0 / -1 / too many are `409 change_invalid seats_exceed` (I/O matrix), never 422. An unknown target Window is `404 not_found` (from `ensure_open_for_booking`).
- `services.manage.issue(c, booking_id, grant_to=session_id)` upserts the split's grant itself, so the token id stays inside `services.manage`; `issue` without `grant_to` behaves as before.
- `db.bookings.emails_of_booking` (the payment repeat and the confirmation read) now returns only a Booking's creation emails: no `change_id`, or the split that created it. Without this a later Change email would show up as part of the payment's "first outcome".
- `DateCalendar` got an optional `label` prop (not in the Code Map) for "2. Choose a date".
- Summary row "Seats left in this booking": shown only for a split (Booking Seats − moved); a full move leaves it out (Lisa, 2026-11-24).
- `frontend/package.json` has no `lint` script; only `npm run build` was run.
- Existing tests touched only where the new columns/behaviour require it: `test_fr06_payment` (key columns), `test_fr16_booking_list` (`status`, `history`; cancelled Bookings now listed per Lisa's decision), `test_fr25_manage_link` (0010 test pins migrations up to 0010), e2e `test_fr16_booking_list` (Status cell), e2e `test_fr25_manage` (Move seats link present before / absent after Cutoff), `conftest.clear` (deletes `booking_changes`).

## Spec Change Log

- 2026-11-24, review 1 (B4): "Seats left in this booking" is shown only for a split; a full move leaves the row out (Lisa). Code was not reverted, since the change touches one row.

## Review Triage Log

Review 1 (blind-hunter B, edge-case-hunter E, verification-gap V):

| # | Finding | Verdict | Evidence | Route |
|---|---------|---------|----------|-------|
| B1/E2 | `moveRefusal` sends `booking_cancelled` / `change_invalid` to "please try again" | low | Approved copy maps "anything else" to the try-again text; the step never opens for a cancelled Booking and caps Seats at the Booking's, and a stale tab hits `booking_changed` first (version check precedes `change_invalid`). | reject |
| B2 | Move page of a cancelled Booking shows only h1 + Back | low | No path cancels a Booking before Story 4.3; reachable only by DB edit. Fix needs new copy. | reject |
| B3 | After `no_seat_free` the Session list keeps stale Seats-left and the same choice | medium | `stay` branch does not re-read `/api/windows`; the Guest can send the same doomed request again and sees outdated figures. | patch |
| B4 | "Seats left in this booking" shows the Booking's Seats on a full move (reads like 2 + 2) | medium | Frozen copy names the row but not its value for a full move; two readings (0 / all Seats). Lisa (2026-11-24): leave the row out on a full move; code kept, fixed as a patch instead of a loopback. | intent_gap → patch |
| B5 | Change email has no "from" line | false | Email body is Lisa's approved text, verbatim (Decisions). | reject |
| B6 | Split-off Booking's history is empty | low | Decision: history lines under the Booking that changed; the original's line names the new reference. | reject |
| B7 | Result page has no link onward | low | No approved copy; browser Back / logo work. Noted for Lisa. | reject |
| B8 | `MOVE.sessionQuestion` is dead | low | Unused key; same text as `BOOK.sessionQuestion`. Direct deletion. | patch |
| B9 | `insert_change` f-strings column names | low | Only caller `history.record` checks `HISTORY_COLUMNS`; no outside input reaches it. | reject |
| B10/V1 | `db.Retry` path never exercised | medium | No test moves the same Booking twice concurrently; removing `Retry` from `db.run` fails nothing. | patch |
| B10/V2 | Move-step refusal UI and key-slot rules have no e2e | medium | Only the success path is driven in the browser. | patch |
| B10/V3 | One-seat / full move never driven through the page | medium | Deleting `setSeats(1)` breaks every 1-Seat move with no failing test. | patch |
| B11 | `s.id` on Optional session in `move_seats` | false | `require_grant` runs first and 404s without a session. | reject |
| B12 | README says FR-26 delivered while story in-progress; history rows lack header link; hard-coded `COLUMNS` | low | README matches the state at merge; history line is plain text in a full-width cell. | reject |
| V4/E1 | `changeKey` without `sessionStorage` makes a new key on each call | low | Comment promises a per-page key; `confirm` calls `changeKey` again, so a retry after 503 sends a new key. Direct correction: in-memory fallback. | patch |
| E3 | Failed re-read after `booking_changed` keeps the stale Booking open | low | Needs a reload refusal followed by a failed GET; rare. | reject |
| E4 | Target Window may start inside the Booking's Cutoff | false | epics.md Story 4.2 checks only `outside_horizon` / `deadline_passed` for the target; Cutoff applies to the current Booking. | reject |
| E5 | Acting session's own Hold in target causes spurious `no_seat_free` | false | No page creates Holds (README "Ikke levert"); Manage sessions hold none. | reject |
| E6 | `upsert_grant` result ignored in split | false | The token was inserted in the same transaction before the Cutoff, so it is valid. | reject |

## Design Notes

Retry on a moved Booking: `db.run` treats `db.Retry` as temporary, so a `window_id` that changed between the unlocked read and the locked re-read reruns the whole unit with the new pair of Windows locked in id order. Split order inside the transaction: UPDATE original (seats, total, version) → `reference.claim(insert_booking(..., cutoff=original.cutoff, session_id=acting))` → `manage.issue(new)` → `upsert_grant(session, token_id)` → `history.record` → emails with `change_id` → key row. Seats left is checked in Python first (for the `seats_left` fact) with the store as backstop.

## Verification

**Commands:**
- `uv run pytest tests --ignore=tests/e2e` -- expected: all pass.
- `uv run pytest tests/e2e` -- expected: all pass.
- `BP_TEST_MUTATE=nocheck uv run pytest tests/test_fr26_move.py -k bypass` -- expected: fails.
- `npm --prefix frontend run lint` and `npm --prefix frontend run build` -- expected: no errors; `/manage/[reference]/move` builds.
