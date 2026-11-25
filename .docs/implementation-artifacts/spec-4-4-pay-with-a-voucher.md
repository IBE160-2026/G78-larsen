---
title: 'Story 4.4: Pay with a Voucher'
type: 'feature'
created: '2026-11-24'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '4a91e65cb67fb4460f4e72ca014139e4075f4e7a'
context:
  - '{project-root}/.docs/implementation-artifacts/epic-4-context.md'
  - '{project-root}/.docs/planning-artifacts/epics.md'  # Story 4.4 acceptance criteria, lines 1307-1380
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A Guest can get a Voucher (Story 4.3) but cannot spend it, so the credit is worth nothing.

**Approach:** Build FR-28 as epics.md Story 4.4 and AD-30/AD-13/AD-31 state it, in one PR: `POST /api/vouchers/quote`, an optional Voucher on `POST /api/bookings` that is spent by one conditional UPDATE after the lock, the Voucher field on Review, the payment split on Confirmation and in the email, and the README. No migration: `vouchers`, `payments.voucher_id` and their CHECKs exist since `0012`.

## Boundaries & Constraints

**Always:**
- Normalisation (one function in `services.voucher`): a string of at most 32 characters → upper case, remove `-` and spaces, `I`/`L`→`1`, `O`→`0`; anything that is not then exactly 16 Crockford characters, and any string over 32, is `409 voucher_invalid` with no facts, never 422. A non-string is a 422 shape error.
- Quote `POST /api/vouchers/quote {code, kind: 'seats', window_id, seats}`: `require_session` (`401 no_session`), takes no lock, writes nothing. Total = `seats × settings price`; unknown `window_id` is `404 not_found`. A Voucher is valid when its hash exists, `balance_ore > 0` and `expires_at > app_now()`; then `{voucher_part_ore: min(balance, total), card_part_ore: total − part}`, else `voucher_invalid`. No response, log line or table ever holds the code, a balance or an expiry.
- `BookingIn` gains optional `voucher_code` (str, ≤ 1024 for the shape) and `voucher_part_ore` (int ≥ 1); both or neither, else 422. `request_hash` adds `voucher_part_ore` only when a Voucher is sent (hashes without a Voucher stay byte-identical); never the code.
- `create`: before the lock the card part = `seats × settings price − part` (unlocked read); `charge()` is called only when it is > 0. After the lock: key read, `outside_horizon`, `deadline_passed`, Hold release, capacity, Booking insert; then, if `part > total_ore` or `total_ore − part` differs from the pre-lock card part → `voucher_invalid`; then one statement `UPDATE vouchers SET balance_ore = balance_ore - :part WHERE code_hash = :h AND balance_ore >= :part AND expires_at > app_now() RETURNING id` (in `db/vouchers.py`, called only from `services.voucher.spend`); no row → `voucher_invalid` and the transaction rolls back. Then `payments` `charge`/`voucher` (with `voucher_id`) and, when the card part > 0, `charge`/`card`; manage link, email, key as today. Nothing before the lock refuses on the Voucher.
- A repeat (same key, session, body) returns the first outcome and spends nothing again.
- The Booking response (`BookingOut`, confirmation read and `POST` result) gains `paid: {voucher_ore, card_ore}` summed from its `charge` rows; the Booking list keeps showing the stored total.
- Review: the draft keeps `voucher_code`; a successful quote stores the parts in page state; editing the field clears the applied Voucher until applied again. After a refusal and a chosen nearest session, the code is quoted again. A `voucher_invalid` from Pay clears the applied parts, shows the Field error and keeps the input. Pay stays in the first view at 1366×768; no horizontal scroll at 1024/1366/1920.
- `lib/api.js` STATUS and `api/errors.py` STATUS gain `voucher_invalid: 409`.
- Decisions (Lisa, 2026-11-24; closes EXPERIENCE.md Open Item 23), copy verbatim:
  - Field label "Voucher code"; Text link "Apply voucher" beside it (a button styled as a Text link; Enter in the field applies too).
  - `voucher_invalid` (quote or Pay, every cause): Field error and Error summary entry "This voucher code cannot be used. It may be mistyped, used up or expired. Check the code and try again.", input kept (one message for every cause, PRD FR-28; it never says which cause applies).
  - Technical failure of the quote (`try_again`, `no_session` after a new session, no answer): "The voucher could not be checked, please try again." as a Field error, input kept, no Voucher applied.
  - Review summary rows after Total, only while a Voucher is applied: "Voucher" "−NOK {part}" and "To pay by card" "NOK {card}" (the card row left out when 0).
  - Pay: "Pay NOK {card}" when a card part remains; "Book with voucher" when the Voucher covers the whole total. The note "Simulated payment: no money moves" shows only when a card part is paid (Review, Confirmation, email).
  - Confirmation and confirmation email, after Total: "Paid with voucher: NOK {part}" and "Paid by card: NOK {card}", a zero part left out; without a Voucher both stay as today (no new rows).
  - Editing or emptying the field removes the applied Voucher; there is no separate remove control.

**Never:** a migration; a Voucher balance or expiry in any response; the code in a log, table or response; more than one code per Booking; Whole-sauna quotes (`kind: 'whole'`, Epic 5); `services.payment.refund()`; changing the Voucher Change of 4.3; weakening an existing test; a new dependency; reading a clock in Python or the browser for a rule.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Partial | Voucher 25000, 2 Seats × 25000 | Booking total 50000; rows charge/voucher 25000 + charge/card 25000; balance 0 | — |
| Whole | Voucher 50000, 1 Seat × 25000 | charge/voucher 25000 only, `charge()` not called; balance 25000 stays | — |
| Typed | `abcd efgh-ijkl-mnop`-style input with I/L/O | same hash as the issued code | — |
| Invalid | unknown, malformed, > 32 chars, expired (`clock.off`), used up | quote and booking: one identical `409 voucher_invalid`, no facts | nothing written, no email, no Seat |
| Tampered part | `voucher_part_ore` > total | `voucher_invalid` | rolled back |
| No session | quote without cookie | `401 no_session` | — |
| Race | 100 rounds of parallel bookings wanting more than the balance | balance ≥ 0, voucher charges ≤ value, losers `voucher_invalid` and write nothing | — |
| Refusal first | Voucher + full Window / past deadline | `no_seat_free` / `deadline_passed`, balance unchanged | — |
| Repeat | same key + body | first outcome, balance spent once | other body: `invalid_key` |

</frozen-after-approval>

## Code Map

- `src/booking_platform/services/voucher.py` -- add `normalise(text) -> str | None`, `quote(session_id, window_id, seats, code)`, `spend(c, code, part) -> voucher_id` (raises `Refused('voucher_invalid')`). Keep `issue`, `facts`.
- `src/booking_platform/db/vouchers.py` -- add `valid_balance(c, h)` (unlocked, for the quote) and `spend(c, h, part)` (the one conditional UPDATE).
- `src/booking_platform/services/booking.py` -- `request_hash(window_id, seats, voucher_part=None)`; `create(..., voucher_code=None, voucher_part=None)` per Always; `facts` adds `paid`; `confirmation_email` adds the payment rows and shows the note only with a card part, per Decisions. Reuse `nok`, `long_date`.
- `src/booking_platform/db/bookings.py` -- `charges(c, booking_id) -> (voucher_ore, card_ore)`; `insert_payment` already takes `voucher_id`.
- `src/booking_platform/db/venue.py` / `db/seats.py` -- the settings price read already used at `venue[7]`; reuse for the pre-lock card part.
- `src/booking_platform/services/payment.py` -- unchanged `charge()`/`record()`; `record` writes the card row with the card part.
- `src/booking_platform/api/public.py`, `api/schemas.py` -- `POST /api/vouchers/quote` (`VoucherQuoteIn{code: StrictStr ≤ 1024, kind: Literal['seats'], window_id: Id, seats: Seats}`), `BookingIn` fields with a both-or-neither validator, `BookingOut.paid`.
- `src/booking_platform/api/errors.py`, `frontend/lib/api.js` -- `voucher_invalid: 409`.
- `frontend/components/Review.js` -- the Voucher field between `BookingSummary` and the terms section (same column as the terms), quote on the Text link (and Enter in the field), summary rows, Pay label, `voucher_invalid` handling, re-quote after `chooseNearest`; reuse `ErrorSummary`, `FieldError`, `TextLink` styles (a `<button className="text-link">` as `NearestSessions.js:13` does). `lib/draft.js` keeps `voucher_code` in the draft.
- `frontend/components/Confirmation.js`, `lib/copy.js` (`REVIEW`, `VOUCHER_FIELD`, `CONFIRMATION`, `SUMMARY`) -- payment rows and texts per Decisions; `app/styles.css` for the field row.
- Tests: `tests/test_fr28_voucher.py` (new) -- get a Voucher with `give_up`/`code_of` from `test_fr27_voucher_for_seats.py`, race pattern and `ROUNDS = 100` from `test_fr11_last_seat_race.py`; `tests/e2e/test_fr28_voucher.py` (new) -- `_open_manage` pattern of `tests/e2e/test_fr27_voucher.py`, log search of `tests/e2e/test_fr21_privacy.py:211`; extend `test_fr06_payment.py`/`test_fr08_confirmation.py` only for `paid` and the email rows.
- `README.md`, `.docs/sensorveiledning-kravsporing.md` -- how to get and use a Voucher; "Not delivered" drops SC3 and FR-25–FR-28.

## Tasks & Acceptance

**Execution:**
- [x] `services/voucher.py`, `db/vouchers.py` -- normalise, quote, spend -- AD-30.
- [x] `services/booking.py`, `db/bookings.py`, `api/schemas.py`, `api/public.py`, `api/errors.py` -- quote route, Voucher in `create`, `paid`, email rows -- AD-13, AD-30, AD-31.
- [x] `lib/api.js`, `lib/copy.js`, `lib/draft.js`, `Review.js`, `Confirmation.js`, `styles.css` -- field, summary, Pay label, confirmation rows.
- [x] `tests/test_fr28_voucher.py` -- every matrix row, normalisation table, response never holds balance/expiry/code, ledger (charges = total), store order (Window lock before Voucher UPDATE, shown by the race and by a refusal-first test).
- [x] `tests/e2e/test_fr28_voucher.py` -- keyboard-only partial payment with a Voucher from a give-up, invalid code Field error + Error summary with input kept, axe on Review with the field, Pay in first view at 1366×768, widths 1024/1366/1920, no Voucher code in any container log.
- [x] `README.md`, `.docs/sensorveiledning-kravsporing.md` -- DR-2.

**Acceptance Criteria:**
- Given the change, when `uv run pytest` (API + e2e) runs, then everything is green including `test_fr28_voucher.py`, `test_fr27_voucher_for_seats.py` and `test_fr05`/`test_fr06`/`test_fr08`.
- Given a Voucher from a sample Booking's give-up, when the examiner books 2 Seats on Review with it using the keyboard, then Confirmation and the email show the total and the Voucher and card parts, and the Booking list shows the stored total.

## Design Notes

The pre-lock card part needs the price before the lock; the price is a setting no runtime path changes, so the post-insert comparison is a guard, not a flow. `spend` comes last before the ledger rows so every earlier refusal leaves the balance untouched without extra code: the whole `db.run` rolls back.

## Verification

**Commands:**
- `uv run pytest tests --ignore=tests/e2e` -- expected: all pass.
- `uv run pytest tests/e2e` -- expected: all pass.
- `npm --prefix frontend run build` -- expected: no errors.

## Review Triage Log

| # | Layer | Finding | Verdict | Route | Evidence |
|---|-------|---------|---------|-------|----------|
| 1 | verification-gap, blind | Re-quote of a stored code on open and after a chosen nearest session is untested | medium | patch | Filed evidence: `_review` always writes a fresh draft; no test reloads or chooses a nearest session with a Voucher. |
| 2 | verification-gap, blind | "The voucher could not be checked" path (incl. `no_session` re-session) is untested | medium | patch | Filed evidence: no test contains the text; clearing the cookie before Apply reaches it in the stack. |
| 3 | verification-gap | Confirmation for a Voucher covering the whole total ("no Paid by card" row) is untested | low | patch | Filed evidence: the whole-total e2e stops at "Book with voucher"; a one-step extension covers it. |
| 4 | blind | `sprint-status.yaml` says `in-progress` while the spec is `in-review` | low | patch | True at review time; set to `review`. |
| 5 | blind | New lines over 120 characters | low | patch | `db/vouchers.py:1` (133) and `api/schemas.py:96` (121) are new; other long lines predate the change. |
| 6 | blind | Examiner guide row 3 still says "536 tester" | low | patch | `.docs/sensorveiledning-kravsporing.md:11`; the suite now has 518 API + 179 e2e. |
| 7 | blind, edge | Seats paid with a Voucher can be given up for a new one-year Voucher, renewing a near-expiry Voucher indefinitely | medium | defer | Real: 4.3 values the give-up at the stored price with a fresh expiry; the issue rule is FR-27/AD-30 policy, not settled by this story's intent. |
| 8 | blind, edge | A typed but not applied code is ignored at Pay | low | reject | Spec: editing clears the applied Voucher until applied again; Pay then reads "Pay NOK {total}", the designed feedback. A guard adds a new flow. |
| 9 | blind, edge, vg-other | Pay is ignored while a quote is in flight; `api()` has no timeout | low | reject | `Review.js` returns early on `quoting`; the automatic re-quote runs on open, before the Guest can tick the terms, so in everyday use it is settled; a hung fetch hangs Pay alike. Fix needs new busy state. |
| 10 | blind, edge | Apply with an empty field shows the invalid-code error | low | reject | True, but harmless wording on a deliberate empty Apply; the fix adds a branch. |
| 11 | blind | The post-lock `total − part ≠ card_part` guard is untested | low | reject | The price is a setting no runtime path changes (Design Notes); the guard covers an unreachable state. |
| 12 | blind | `test_fr08_confirmation.py` not extended | false | reject | The Code Map says "only for `paid` and the email rows"; both are asserted in `test_fr06_payment.py` and `test_fr28_voucher.py`. |
| 13 | blind, edge | `paid` after a Move/give-up: sums of charge rows can exceed the current total; split Booking has `{0,0}` and keeps the payment note | low | reject | Spec defines `paid` as the sum of `charge` rows (what was paid); the split's email is unchanged from before 4.4. |
| 14 | blind | A card charge decided before the lock can be followed by `voucher_invalid` | false | reject | Same AD-13 pattern as `no_seat_free` after `charge()`; payment is simulated and `refund()` is out of scope by intent. |
| 15 | blind | `request_hash` ignores which code was used | false | reject | The spec's intent says never the code in the hash; a different code with the same part and key is a deliberate trade-off. |
| 16 | blind | No rate limit on `POST /api/vouchers/quote` | low | reject | 80-bit codes make enumeration impractical; rate limiting is EXPERIENCE.md Open Item 24, not this story. |
| 17 | blind | `.text-button` not reused by `NearestSessions.js`; Code Map `quote` signature differs | low | reject | Cosmetic; the second fix edits this spec. |
| 18 | edge | Quote prices a closed or past-deadline Window | low | reject | Pay refuses with `no_seat_free`/`deadline_passed` and nearest sessions; the quote is a price preview only. |
| 19 | edge | A repeat with a card part calls `charge()` again | false | reject | Identical to the pre-4.4 flow without a Voucher (AD-13); the repeat writes nothing. |
