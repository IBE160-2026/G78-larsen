# Epic 4 Context: A Guest changes seats or takes a voucher

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Give every Seat booking a Manage link in its confirmation email that opens that Booking, and only that Booking, without an account. Until the Cutoff (12 hours before the start) the Guest can move some or all Seats to another session or give them up for a Voucher worth what was paid; Seats are never refunded in money. A Voucher later pays for all or part of a new Booking, and the Administrator sees each Booking's status and Change history in the Booking list. This delivers SC3 (FR-25 to FR-28). Status: 4.1 and 4.2 are merged; 4.3 and 4.4 remain, and the schedule checkpoint is Epic 4 merged by Fri 27 Nov so that Epic 5 can follow. The Manage page and the Change pattern are reused by Epic 5.

## Stories

- Story 4.1: The Manage link opens the Booking
- Story 4.2: Move all or some Seats to another session
- Story 4.3: Give up Seats for a Voucher
- Story 4.4: Pay with a Voucher

## Requirements & Constraints

- **Manage link:** 256-bit token, only its SHA-256 hash stored; valid until the Booking's session ends. Unknown, malformed, revoked, expired and other people's links all get the same `404 not_found` and "This page is not available." The token never appears in a path, query, log line or table (except hashed).
- **No accidental changes:** loading a page changes nothing. Every Change goes through a confirming step with a one-time idempotency key; a repeat applies once and returns the first outcome.
- **Cutoff:** after it, the page still shows the Booking and refuses every Change with the reason and time (`cutoff_passed` with `cutoff_at`).
- **Move:** atomic; no room means nothing changes. A partial move splits the Booking (new reference, own Manage link, same price per Seat and Cutoff). Freed Seats count in Seats left at once.
- **Voucher:** value = Seats given up × price paid per Seat, valid one year, never paid out. When a Voucher paid the Booking (or the Booking it was split from), the new Voucher keeps that Voucher's last valid date instead, so giving up never renews a Voucher (Lisa, 2026-11-24). The code appears only in the Change email, shown on the result page under "Sent by email:". Giving up all Seats cancels the Booking; it is the only way a Seat booking is cancelled.
- **Paying with a Voucher:** one code per Booking; covers all or part, rest by Simulated payment; remaining balance stays until expiry. Expired, used-up and unknown codes get one identical `voucher_invalid` and nothing is written. No response reveals balance or expiry.
- **Concurrency proofs (100 runs):** opposite cross-Window moves and a move racing a new booking never deadlock or oversell; parallel Voucher spends never take `balance_ore` below 0.
- **Accessibility and layout:** axe clean (A/AA) on Manage, confirming steps, result pages and Review with the Voucher field; keyboard only; no horizontal scroll at 1024/1366/1920 px; Pay stays in the first view at 1366×768.
- **Secrets:** the e2e log search finds no Manage token and no Voucher code in any container log.

## Technical Decisions

- **Token and grant:** only `services.manage` writes `access_tokens`; `issue(c, booking_id)` is called only by Booking creators (Seat flow, split, seed, later Epic 5). No Change revokes or reissues the original's token. `manage_grant_valid(session_id, booking_id)` is the one grant predicate; all routes under `/api/manage/{reference}/` sit on one router whose dependency checks it (404, never 401) and touches `last_used_at`.
- **Cutoff:** `bookings.cutoff` is copied from settings at creation and kept on move/split; `change_allowed(booking_id)` is the only Cutoff predicate. Time comes from `app_now()`; tests move it via `clock.off`.
- **Change transaction:** unlocked read → `lock_windows` (id order) → re-read `FOR NO KEY UPDATE` (retry via `db.run` if `window_id` changed) → grant re-check by join → key read. Refusal order: `booking_cancelled`, `booking_changed` (version), `change_invalid` (`seats_exceed`/`same_target`), `outside_horizon`, `deadline_passed`, `cutoff_passed`, then capacity in the store (`no_seat_free` with `seats_left`). `version` rises in the same UPDATE.
- **History:** `booking_changes` written only by `services.history.record`, never by triggers; per-action shape CHECKs (`move`: both Window ids, `seats`, `new_booking_id` on split; `voucher`: `seats`, `voucher_id`).
- **Cancellation (4.3):** `cancelled_at`, `cancel_cause`, `cancel_remedy` with CHECKs including `seat_guest_refund_forbidden`; a trigger refuses un-cancelling and changes to Seats/Window/Sauna on a cancelled row.
- **Change response:** `{booking, new_booking?, voucher?: {value_ore, last_valid_date}, emails}`; emails go through the Outbox with `change_id` and carry no original Manage link and no Sauna name. Idempotency rows hold exactly one of `booking_id`/`change_id`; frontend key slot `draft:change:<reference>:<action>`.
- **Voucher store:** only `services.voucher` writes `vouchers`. Code: 16 Crockford base32 chars (`XXXX-XXXX-XXXX-XXXX`) from `secrets`, unkeyed SHA-256 stored. Input ≤32 chars normalised (upper case, strip hyphens/spaces, I/L→1, O→0); anything invalid is `voucher_invalid`, never 422. `expires_at` = 00:00 Venue time the day after the last valid date. Spend is one conditional `UPDATE … WHERE balance_ore >= :part AND expires_at > app_now() RETURNING id`, after `lock_windows`, the deadline checks and the Booking insert. `POST /api/vouchers/quote` takes no lock and writes nothing; `request_hash` includes the Voucher part, never the code.
- **Ledger:** Voucher Change → `refund`/`voucher` row; Voucher payment → `charge`/`voucher` plus `charge`/`card` for any rest (`charge()` skipped when the Voucher covers all). Splits write no payments rows. Without a split, charges minus returns = `total_ore` while active, 0 when cancelled. `retention_due(booking_id)` becomes the one retention predicate, including Voucher expiry.

## UX & Interaction Patterns

- Shared components in `frontend/components/`: `ManageBookingSummary`, `ConfirmingStep`, `ChangeResult`. Reuse them and the move step's pattern for the Voucher step.
- Established move copy to mirror: confirming step headed "What will happen" with labelled rows and "Nothing changes until you confirm." under it; confirm button names the action and count; result shows a heading, "Your booking has been changed.", the emails under "Sent by email:" and a "Back to your booking" link. `booking_changed`/`invalid_key` show "This booking was changed in the meantime. Check it and choose again." and open a fresh step; other unexpected refusals show "The change could not be completed, please try again."; refusals keep the Guest's choices.
- Change email: subject "Booking changed: {ref}", the Booking as it is now, and last line "The Manage link in your booking confirmation email still works." The Voucher Change adds a block with code, value, last valid date and that a Voucher is never paid out.
- Booking list: one history line per Change under the Booking and a Status column (Active/Cancelled); a Voucher line shows the value issued, never the code. Cancelled Bookings stay listed with cause "Guest" and remedy "Voucher", outside Seats booked.
- Review (4.4): Voucher field (Text field plus Text link) between the Booking summary and the terms, always visible. A valid code shows the Voucher part and the Pay label becomes the card part; any invalid code gives one identical Field error and Error summary entry with the input kept. After a refusal the code stays in the draft and is quoted again.
- Decided for 4.3 (Lisa, 2026-11-24; EXPERIENCE.md "Give up seats wording"): after all Seats are given up the Manage page shows the Booking as cancelled with no Changes; the step, result, email and Booking list copy are fixed there.
- Decided for 4.4 (Lisa, 2026-11-24; EXPERIENCE.md "Pay with a voucher wording", Open Item 23): field "Voucher code" with Text link "Apply voucher"; one invalid-code message; Pay "Book with voucher" when the Voucher covers all, the payment note only with a card part; "Paid with voucher"/"Paid by card" rows on Confirmation and in the email.

## Cross-Story Dependencies

- Builds on Epics 1–3: Seat flow, `lock_windows`, sessions, Outbox, idempotency, Booking list and HTTPS (Manage links are `https://`).
- 4.3 depends on 4.2's `booking_changes`, Change transaction and shared components; 4.4 depends on 4.3's `vouchers` and `payments.voucher_id` and extends `POST /api/bookings`.
- README: after 4.4 it explains how to get a Voucher (give up a Seat on a sample Booking via its Manage link in the Outbox), and "Not delivered" no longer lists SC3 or FR-25 to FR-28.
- Epic 5 reuses the token, grant, Change, history, Voucher and ledger patterns; it also changes capacity counting, so Epic 4's race tests must keep passing.
