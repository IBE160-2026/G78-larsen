# Epic 5 Context: A group books a whole sauna

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Let a group book one whole Sauna for one session (called "Private sauna" in guest copy). A Guest picks a date, sees which Saunas can be booked whole with size, price and free sessions, then books and pays. Until 72 hours before the start, the Guest can cancel for a refund or a Voucher, or move the booking to another session. Seat bookings are counted around Private saunas so that no Seat is ever lost or sold twice, and the Administrator sees each session's Placement. The epic builds on Epic 4's Manage link, Change pattern and Voucher. Status: 5.1, 5.2 and 5.3 (cancel and move) are done. Next are 5.4 and 5.5. Schedule: 5.1–5.3 by 2 Dec, Epic 5 by 4 Dec.

## Stories

- Story 5.1: A Guest sees which saunas can be booked whole
- Story 5.2: Book and pay for a Private sauna
- Story 5.3: Cancel or move a Private sauna (cancel and move done)
- Story 5.4: The Administrator sees where Seats are counted
- Story 5.5: Placement and Private saunas hold under any sequence and any race

## Requirements & Constraints

- **Saunas and prices:** every Sauna can be booked whole unless it is marked otherwise (`bookable_whole = false` or no price). Prices: Rauha (7) NOK 1,850, Löyly (10) NOK 2,600, Kajo (12) NOK 3,150, Lumo (15) NOK 3,950.
- **When a Sauna can be booked whole in a Window:** all of these must hold:
  - it is bookable whole, has a price, is not Blocked and is not already booked whole;
  - the Seats booked plus held fit in the Saunas ahead of it in Fill order, unless the mark applies;
  - the Window has not started, or has no Seat booking, or the mark applies.
  The Sauna is not held while the Guest pays.
- **Guest choice:** the Guest only sees valid pairs and always picks the Sauna. No Seat-flow page, response or email, and no Seat-booking Manage response or Change email, names a Sauna or shows Placement.
- **Cutoff:** 72 hours before the start, stored on each Booking as `cutoff`. After it, the Manage page still shows the Booking and every Change is refused with `409 cutoff_passed` carrying `cutoff_at`. Tests check both sides of the 72-hour edge and move the clock only through `clock.off`.
- **Move (done):**
  - The Booking moves to another Window. It keeps its Sauna unless the Guest picks another available one.
  - The reference, price and `entry_time` stay the same, and the original Booking is untouched on any refusal.
  - `409 sauna_unavailable` when the target fails the bookable-whole rule.
  - `409 price_differs` when the target Sauna's `whole_price_ore` differs from the Booking's `total_ore`. The page says the Guest can cancel and book again. No difference is charged or refunded, and keeping the same Sauna keeps the price paid.
  - `change_invalid` with `same_target` when the Window and Sauna are both unchanged. `outside_horizon` and `deadline_passed` apply to the target. Each refusal is tested in order.
  - Capacity follows at once in both Windows. The move sends exactly one email.
- **Cancel (done):** `refund` returns each part the way it was paid: one `refund`/`card` row, plus a new Voucher for any Voucher-paid part, valid until the earliest expiry of the Vouchers used and at least 30 days from now. `voucher` gives one Voucher for the full `total_ore`, valid one year.
- **Ledger:** for a Booking with no split, charges minus returns equal `total_ore` while it is active (including after a move) and 0 once it is cancelled with a remedy. A Voucher balance is never turned into a card refund.
- **Tests:** catalogue IDs A1–A8, B1–B7 and H12 are named tests. INV-1 to INV-5 are checked after every example and race, and group-C races run 100 times. `test_fr33_whole_change.py` covers cancel with each remedy, the move and each refusal.
- **Accessibility and privacy:** axe A/AA clean and usable with the keyboard alone. Radio groups sit in `fieldset`/`legend`, focus goes to the `h1`, and there is no horizontal scroll at 1024, 1366 or 1920 px. Every request stays on the stack's origin. Manage pages send `X-Robots-Tag: noindex` and no referrer.

## Technical Decisions

- **One Booking table:**
  - `kind` is `seats` or `whole` and cannot change. A Whole-sauna booking has `sauna_id` set and `seats` NULL.
  - `whole_bookings` (with `booking_id UNIQUE`) is the capacity row. It exists exactly while its Booking is active, with the same Window and Sauna.
  - Deferred triggers enforce this pairing and raise `whole_pairing` (a 500).
  - **Write order:** cancel sets the status, then deletes the capacity row. A move updates `bookings` first, then `whole_bookings`, setting `window_id` and `sauna_id` together.
- **Bookable-whole predicate:**
  - `whole_bookable(wid, sid, ignore_booking DEFAULT NULL)` is the only statement of the store rule.
  - `trg_check_whole` runs it on INSERT and on `UPDATE OF window_id, sauna_id`, passing `NEW.booking_id`, so a move is not judged against its own capacity row.
  - In a Whole-sauna action, `db` maps `whole_bookable`, `booked_within_capacity` and the `(window_id, sauna_id)` key to `409 sauna_unavailable`.
- **Listing and move list:** `GET /api/private-saunas?date=` returns `{saunas: [{id, name, capacity, whole_price_ore, windows: [{id, start, end, already_started}]}], horizon_end, horizon_days}`. It takes no lock and writes nothing except `ensure_generated()`. The Manage move list is the same query with `ignore_booking` set to this Booking.
- **Manage routes:**
  - `GET /api/manage/{reference}` returns the shared serializer plus `version`, `change_allowed`, `cutoff_at` and history. A move's history entry carries both Windows and both Saunas. The response never includes an email, a Voucher code or a Manage link.
  - `POST …/whole/move {window_id, sauna_id, version}` and `…/whole/cancel {remedy, version}` are confirming POSTs with an `Idempotency-Key`.
  - Routes for the other kind answer `404 not_found`, and no Change issues or revokes a Manage token.
- **Order for a Booking-scoped Change:**
  1. Read `window_id` without a lock.
  2. Lock the current and the target Window in id order with `lock_windows`.
  3. Re-read the Booking `FOR NO KEY UPDATE`, and retry if `window_id` changed.
  4. Re-check the grant, then read the key.
  5. Refuse in this order: `booking_cancelled`, `booking_changed` (with the current Booking), `change_invalid`/`same_target`, `outside_horizon`, `deadline_passed`, `cutoff_passed`, then `sauna_unavailable`/`price_differs`.
  `version` is incremented in the same UPDATE. A repeat with the same key returns the first outcome and its stored emails.
- **Error codes:** `price_differs` is declared once in `api/errors.py` and once in the frontend mirror.
- **Move history:** `services.history.record` writes a `move` row with both Window ids and both Sauna ids, with `seats`, `voucher_id` and `new_booking_id` NULL. The current `move` shape CHECK (0012) forbids a whole move row (it requires `seats` and NULL Sauna ids), so the move needs migration 0015.
- **Change response:** `{booking, voucher?, refund?, emails: [{id, subject, body}]}`.
- **Emails:** each email says the Manage link in the confirmation email still works, and none carries the link. The move email is a Change confirmation giving the Sauna, the new session and the price.
- **Placement (5.4):** `placement(wid)` returns `(sauna_id, state, seats)` in Fill order, where `state` is `open`, `whole`, `blocked` or `marked`. It is read only under `/api/admin/`, and a brute-force reference lives in `tests/`.

## UX & Interaction Patterns

- **Done in 5.1/5.2:** Landing shows two equal Booking choices, "Book seats" and "Book private sauna". The Private sauna page has a date calendar, a "View" toggle ("Show by sauna" / "Show by session") and Sauna cards whose session buttons choose both the Sauna and the session. Review and Confirmation use the summary label "Sauna" (the name only, never the Capacity).
- **Manage page of a Private sauna (decided):** "Sauna" comes first in the summary. Before the Cutoff the page says "You can change this booking until {long date} at {HH:MM}." After the Cutoff, both the page and the `cutoff_passed` reason say "This booking can no longer be changed. Changes are only possible until 72 hours before the session starts." (no date since Lisa's change of 2026-11-26)
- **Cancel wording (accepted by Lisa, 2026-11-26), for reference:**
  - The link and `h1` are "Cancel booking" (changed from "Cancel private sauna", Lisa 2026-11-26), with the question "What do you want back?" and the options "A refund" or "A voucher".
  - "What will happen" lists Sauna and Session, followed by "Nothing changes until you confirm." and the button "Cancel booking".
  - The result page shows "Booking cancelled" / "Your booking has been cancelled.", then "Sent by email:" and "Back to your booking".
  - The email subject is "Booking cancelled: {ref}".
  - The Booking list shows "Cancelled on {dd.mm.yyyy HH:MM} for a refund" (or "for a voucher of NOK {value}") and the Status "Cancelled {dd.mm.yyyy HH:MM} · Guest · Refund|Voucher".
- **Move wording: decided (Lisa, 2026-11-26).** The move half of 5.3 is done: the Manage page offers "Move booking" beside "Cancel booking", and the accepted wording is in EXPERIENCE.md "Move private sauna wording". The planning docs left these texts open:
  - the move link and heading;
  - the step's questions and "What will happen" rows;
  - the confirm button and the result heading;
  - the `price_differs` and `sauna_unavailable` reasons;
  - the move email body;
  - the Booking list history line.

  They were proposed by following the Epic 4 Move seats pattern and the cancel wording above, decided by Lisa and recorded in the story file and EXPERIENCE.md. Texts the docs already fix for a move:
  - The step is built from `ManageBookingSummary`, `ConfirmingStep` and `ChangeResult`, with "What will happen" and "Nothing changes until you confirm.", and a result page with "Your booking has been changed.", "Sent by email:" and "Back to your booking".
  - The date and session choice reuses the Private sauna page's listing with `ignore_booking`, and the Guest can keep or change the Sauna. The current session cannot be chosen, as with "Your current session" on Move seats.
  - `outside_horizon` / `deadline_passed`: "This session can no longer be booked. Nothing has changed."
  - `booking_changed` / `invalid_key`: "This booking was changed in the meantime. Check it and choose again." The step then opens fresh with a new key.
  - Any other refusal: "The change could not be completed, please try again."
  - `price_differs` must give the reason and say the Guest can cancel and book again.
  - The email subject follows the pattern "Booking changed: {ref}", with "Sauna: {name}" in place of Seats. Its last line is "The Manage link in your booking confirmation email still works."
- **Booking list:** the date can be typed, stepped with "Previous day" / "Next day", or picked with "Choose from calendar", which opens the site's own pop-up calendar and accepts any day. For 5.4, each Session group gets a table "Saunas" with columns "Sauna" and "Seats counted". Its cells read "7 of 7", "Booked whole · {ref}", "Blocked" or "Private sauna only", in Fill order and never by colour alone.

## Cross-Story Dependencies

- 5.1 laid the schema and the listing (`whole_bookable`, `ignore_booking`). The 5.3 move uses that listing and relies on the trigger's `ignore_booking`.
- 5.2 added `sauna_unavailable` and the payments ledger. The 5.3 cancel added `services.payment.refund()`, the `cancel` history shape and the Private sauna Manage page, which the move extends with a second Change beside cancel.
- The move reuses Epic 4's Manage grant, key slots, `services.history`, the Change components and the Move seats step structure.
- 5.5's Hypothesis machine uses the Whole-sauna move and cancel (each remedy) as rules and checks the ledger invariant. 5.5 also reuses 5.4's INV checker and brute-force Placement.
- Epic 4's race and model tests must keep passing.
