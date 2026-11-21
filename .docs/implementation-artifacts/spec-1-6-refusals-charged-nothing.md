---
title: 'Story 1.6: A Guest who cannot get the seats is told why and charged nothing'
type: 'feature'
created: '2026-11-20'
status: 'done'
route: 'dispatch'
baseline_commit: '00c919e9943a6ccfd2f7e44487456976756f9c82'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/planning-artifacts/epics.md'
  - '{project-root}/.docs/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** On Review every refusal shows one "please try again" Notice with Pay kept, so a Guest who lost the Seats, hit a closed session or a failed payment is not told why, gets no nearest sessions, and the true `seats_left` is not even in the `no_seat_free` envelope. The booking path never checks the Booking horizon, the last-Seat race has no `test_fr11`, and an idempotency key is deleted with its session, so a retry after a purge can charge twice (FR-7, FR-11, FR-12, FR-14).

**Approach:** Build Story 1.6 in `.docs/planning-artifacts/epics.md` (L707–764) as its ACs list: `seats_left` and `outside_horizon` judged after the lock, the Review refusal states with Nearest sessions, `test_fr11_last_seat_race.py`, `test_fr12_all_or_nothing.py`, `tests/e2e/test_fr11_refusals.py`, and close the two Story 1.5 points and the deferred Review e2e test.

## Boundaries & Constraints

**Always:**
- After `lock_windows` the order stays: key read, then `outside_horizon` (`within_horizon()`), `deadline_passed`, then Holds deleted and `no_seat_free` with `seats_left` from `seats_left()` when it is below the request; the store's `booked_within_capacity` stays the backstop. A refusal writes nothing and stores no key.
- Copy verbatim from EXPERIENCE.md L180–202; codes the frontend handles exist in `api/errors.py` and `lib/api.js` `STATUS`; Review's code → message mapping lives once in `frontend/lib/copy.js`. Keyboard steps in e2e go through `a11y.press` / `a11y.tab_to`; only `styles.css`.
- Name, email, the draft and its key survive every refusal. After `invalid_key` no new key is made except by the Book seats link starting a new draft (AD-9).
- Existing tests keep their assertions, except the purge test's key-count line, which changes with the key decision below.

**Never:** Edit migrations `0001`–`0006`. Add a backend endpoint for Nearest sessions. Show a Sauna. Touch Manage, Vouchers or Holds UI.

**Decisions (Lisa, 2026-11-20):**
- **Keys outlive sessions:** migration `0007_keys_outlive_sessions.sql` makes `idempotency_keys.session_id` nullable with `ON DELETE SET NULL` (constraint name kept). A retry from a new session after a purge is `409 invalid_key` and never a second charge; the purge test expects the key row kept with `session_id` NULL.
- **Seats-left wording:** "Only N seats left in this session. You have not been charged." via `seatsWord` (N ≥ 1); `seats_left` 0 or missing → "No seat free. You have not been charged."
- **Nearest sessions on Review:** the date's other sessions with room for the Seats (`GET /api/windows?date=`), up to three nearest in time to the refused one, shown in time order; if none, the listing's `nearest` (`&seats=`). Frontend only.
- **Scope:** the story stays whole although the spec is about 2300 tokens.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error Handling |
|---|---|---|---|
| Seats taken (A6) | 42 of 44 booked, request 3 | 409 `no_seat_free`, `seats_left` 2; Review Notice "Only 2 seats left…" + nearest | nothing written |
| Last Seat lost (A7) | 44 booked, request 1 | 409 `no_seat_free`, `seats_left` 0; "No seat free. You have not been charged." | nothing written |
| Beyond horizon | clock moved back so the Window starts after now + horizon | 409 `outside_horizon` (before deadline check) | "This session can no longer be booked…" |
| Deadline passed | clock past the Window's deadline | 409 `deadline_passed` | same Notice |
| Payment fail | switch `payment = "fail"` | Error summary, Pay kept, same key; retry after switch off books once | nothing written |
| Pending / retries used | `payment_pending`, `503 try_again`, network | "please try again" Notice, Pay/note/checkbox kept, same key | — |
| Key known elsewhere | `409 invalid_key` | Notice "This booking may already be paid…", Pay removed, Book seats link → new draft | — |
| Session lost | `401 no_session` | `POST /api/session`, draft and key kept, "please try again"; next Pay books | — |
| Choose nearest | link in the Notice | draft `{date, window_id}` updated, Review reloads, checkbox unticked, Pay back, focus on `h1` | — |

</frozen-after-approval>

## Code Map

- `src/booking_platform/services/booking.py` `create.work` -- add the `seats_left` check after `delete_holds`; `services/windows.py:162` `ensure_open_for_booking` -- add `outside_horizon` first (shared with Holds; `test_application_rules.py:34` stays green: `within_horizon` checks only the upper bound).
- `src/booking_platform/db/seats.py:15` `before_booking_deadline` -- add a `within_horizon(%s)` read beside it and a `seats_left(%s)` read; SQL stays in `db/`.
- `migrations/0006_bookings_pay.sql` L85–95 -- `idempotency_keys_session_id_fkey` (CASCADE); the new `migrations/0007_keys_outlive_sessions.sql` changes it. `tests/test_dr4_migrations.py` pins migration files.
- `src/booking_platform/db/refusals.py` -- `idempotency_keys_session_id_fkey` → `no_session` stays.
- `tests/test_fr10_through_the_api.py:82` `test_the_last_seat_has_exactly_one_winner` -- move to `test_fr11_last_seat_race.py` (100 rounds) and assert loser body `{"error":"no_seat_free","seats_left":0}` and one row each in `payments`, `outbox_emails`, `idempotency_keys`; `:96` A6/A7 move to `test_fr12_all_or_nothing.py::test_a6/test_a7`. Helpers `fill`, `left`, `state`, `guests`, `parallel` in that file and `tests/conftest.py` (`set_clock` L195, `win_start` L43, `world` L208).
- `tests/test_fr14_retry.py:76` -- add `payments`, `outbox_emails`, `idempotency_keys` = 0 for the bookings row; `:129` already pins the two codes. `tests/test_fr14_switches.py:103` already covers fail/hold + same key. `tests/test_fr06_payment.py:96/105` cover `invalid_key`. `tests/test_fr21_sessions.py:101` purge test (L122 key count).
- `frontend/components/Review.js` `pay()` catch -- replace `refused` with a refusal state `{code, seatsLeft}`; `components/NearestSessions.js` (needs `date` per item; add `draft.date` to same-date windows), `Notice.js`, `ErrorSummary.js`, `TextLink.js`; `lib/draft.js` `writeDraft`/`replaceDraft`; `lib/copy.js` `REVIEW`, `BOOK.seatsLeft`; `BookSeats.js` `chooseNearest` L209 as the pattern.
- `tests/e2e/conftest.py` `Stack.switches_dir`, `compose` (restart backend to read switches); `tests/e2e/test_fr05_book_and_pay.py` helpers `free_windows`, `set_draft`, `review_draft`, `open_session`.

## Tasks & Acceptance

**Execution:**
- [x] `db/seats.py`, `services/windows.py`, `services/booking.py` -- horizon check and `seats_left` fact after the lock -- FR-12, FR-18 IV-2, AD-4, AD-16
- [x] `migrations/0007_keys_outlive_sessions.sql`, `tests/test_fr21_sessions.py` -- key kept on purge, retry from a new session is `invalid_key` with one Booking and one payment -- AD-9
- [x] `tests/test_fr11_last_seat_race.py`, `tests/test_fr12_all_or_nothing.py` (A6, A7, horizon before deadline via `set_clock`), `tests/test_fr10_through_the_api.py`, `tests/test_fr14_retry.py` -- FR-10, FR-11, FR-12, FR-14
- [x] `frontend/lib/copy.js`, `frontend/components/Review.js`, `NearestSessions.js`, `app/styles.css` -- the refusal states in the matrix -- UX-DR11/13/25/26
- [x] `tests/e2e/test_fr11_refusals.py` -- Seats taken through the DB, last Seat lost, deadline via the clock, payment fail via the switch file + backend restart (restored in `finally`), `invalid_key`, `401` via deleting the session row then a successful Pay with the same key; each: Notice focus, no Booking/email after, axe A/AA clean, nearest links by keyboard -- FR-7, FR-11, FR-12, FR-22, FR-23
- [x] `deferred-work.md` (mark the 1.5 Review e2e entry done), `.logs/lisa-larsen/issues.md` (close the two 1.5 points), `README.md` status

**Acceptance Criteria:**
- Given `uv run pytest`, then every test passes, Stories 1.1–1.5 included, and `test_fr11` runs 100 rounds.
- Given `npm --prefix frontend run build`, then it succeeds.
- Given any refusal on Review, then no Booking, payment, Outbox email or key exists for it, and name and email are still shown.

## Implementation Notes

## Spec Change Log

## Review Triage Log

| # | Layer | Finding | Verdict | Route | Evidence |
|---|---|---|---|---|---|
| 1 | blind, edge | `pay()` no longer clears the previous refusal; a stale Error summary/Notice shows during the next attempt or beside the terms error | medium | patch | The diff removed `setRefused(false)` and adds no `setRefusal(null)`; the `failed` entry stays in `errors` until a new result. |
| 2 | edge | A `closed` refusal with empty `nearest` offers no next step (Pay already removed) | medium | patch | `notice` renders only when `refusal.nearest.length > 0`; `nearestSessions` returns `[]` on any failed read or no room. |
| 3 | blind, edge, verification | No nearest sessions after `outside_horizon`: the listing refuses a date outside the horizon, so the `nearest` fallback is never reached | low | rejected | Real (`services/windows.py:126`), but a Window leaves the horizon only if the Administrator shrinks it; row 2's Book seats link removes the dead end; a second fallback query adds a branch for a rare case. |
| 4 | verification, edge | Holds and admin whole-bookings now return `outside_horizon` (shared `ensure_open_for_booking`) and no test pins it | medium | patch | Intended by FR-18 IV-2 and FR-29 (horizon required); only `/api/bookings` is tested for it. |
| 5 | verification | Nearest ordering (three nearest, time order) not pinned in e2e | medium | patch | The test asserts only count and text shape. |
| 6 | verification | Fallback to the listing's `nearest` never runs in any test | maybe-false (medium if true) | defer | Every e2e refusal uses a date with eight empty Windows; needs filling a whole date in the e2e DB. |
| 7 | verification, blind | `outside_horizon` on Review not exercised (matrix row "Beyond horizon") | medium | patch | No e2e case; deleting the `case` would pass. |
| 8 | edge | Deadline e2e test never checks nearest links by keyboard | low | patch | Spec e2e task requires it; two-line addition. |
| 9 | edge | Moved A6 drops its final assertion (book 1 after the 2 → 409, left 0) | low | patch | Old `test_fr10` lines removed in the diff; "existing tests keep their assertions". |
| 10 | blind | `api/errors.py` `outside_horizon` comment out of date | low | patch | Comment names only the date listing case. |
| 11 | blind | `booking.py` docstring line ~154 chars | low | patch | Rest of file ≤120. |
| 12 | edge | `Date.parse` NaN gives arbitrary sort | false | rejected | `refusedStart` is the API's ISO `start`; Pay only exists while `session` is loaded. |
| 13 | edge | `setRefusal` after unmount while nearest read is pending | low | rejected | React 18 ignores it silently; one extra GET; fix adds a guard. |
| 14 | edge | Modifier-click on Book seats replaces the current tab's draft | low | rejected | Rare; fix adds event branching; the draft was already unusable (`invalid_key`). |
| 15 | edge | `_switch` unlinks a pre-existing switch file | false | rejected | `switches/` is created empty per stack (`tests/e2e/conftest.py:70`); only this test writes it. |
| 16 | edge | Deadline test resets `clock.off` to 0, not its prior value | false | rejected | Each stack starts with `off` 0 and the `db` fixture already resets to 0. |
| 17 | blind | Idempotency keys now have no retention rule | low | rejected | Follows Lisa's decision (keys outlive sessions); growth is one row per Booking, negligible at this scale; a retention rule is new scope. |
| 18 | blind | `max(left, 0)` hides overbooking | false | rejected | `booked_within_capacity` makes negative Seats left unreachable; the clamp only shapes the fact. |
| 19 | blind | Tracking files disagree (sprint-status, issues.md, README) | false | rejected | Mid-workflow state; step 5 and the session log update them. |
| 20 | blind | Spec Verification/log sections incomplete | — | rejected | Fix is to edit this build's spec. |
| 21 | blind | E2E data left behind / order dependence | false | rejected | The e2e stack is created fresh and removed (`down -v`) per run; the seats-taken test runs first in its module. |
| 22 | blind | Focused `role="status"` Notice may be announced twice | maybe-false (low if true) | rejected | Needs a screen-reader check; axe passes; would only be low. |
| 23 | blind | No frontend unit test for `reviewRefusal` | low | rejected | The frontend has no unit-test runner; e2e covers each kind after rows 5/7. |

## Verification

**Commands:**
- `uv run pytest -q` -- expected: all pass
- `npm --prefix frontend run build` -- expected: success
