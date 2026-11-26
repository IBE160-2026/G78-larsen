# Epic 5 Context: A group books a whole sauna

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Let a group book one whole Sauna for one session (shown to Guests as "Private sauna"). A Guest picks a date, sees which Saunas can be booked whole with size, price and free sessions, then books and pays. Until 72 hours before the start, the Guest can cancel for a refund or a Voucher, or move the booking. Seat bookings are counted around Private saunas so that no Seat is ever lost or sold twice, and the Administrator sees each session's Placement. The epic delivers SC2/SC4 and FR-29 to FR-33. It also adds the price per Sauna and the group sentence on Landing (FR-1.7, FR-4), and shows Whole-sauna bookings and Placement in the Booking list (FR-16). It depends on Epic 4's Manage link, Change pattern and Voucher. Schedule checkpoints: 5.1–5.3 by 2 Dec, Epic 5 by 4 Dec.

## Stories

- Story 5.1: A Guest sees which saunas can be booked whole
- Story 5.2: Book and pay for a Private sauna
- Story 5.3: Cancel or move a Private sauna
- Story 5.4: The Administrator sees where Seats are counted
- Story 5.5: Placement and Private saunas hold under any sequence and any race

## Requirements & Constraints

- **Saunas and prices (Lisa 2026-11-24, changed 2026-11-25):** every Sauna is open for Seats and for Private sauna booking unless it is marked otherwise (`bookable_whole = false` or no price). Prices: Rauha (7) NOK 1,850, Löyly (10) NOK 2,600, Kajo (12) NOK 3,150, Lumo (15) NOK 3,950.
- **FR-29:** a Sauna can be booked whole in a Window only when all of these hold:
  - it is bookable whole and has a price;
  - it is not Blocked and not already booked whole;
  - the Seats booked plus held fit in the Saunas ahead of it in Fill order, unless the mark applies;
  - the Window has not started, or has no Seat booking, or the mark applies.

  The Sauna is not held while the Guest pays. A pair taken in the meantime is refused, and nothing is charged.
- **FR-30:** the Guest sees only valid pairs and always picks the Sauna. The confirmation names the Sauna and the session.
- **FR-4:** no Seat-flow page, response or email, and no `/api/manage/` response or Change email for a Seat booking, names a Sauna or shows Placement.
- **FR-33 (cancel or change a Whole-sauna booking):**
  - **Cutoff:** 72 hours before the start. Each Booking has its own `cutoff`. After the Cutoff, the Manage page still shows the Booking and every Change is refused with `409 cutoff_passed` carrying `cutoff_at`. The 72-hour edge is tested on both sides, moving the clock only through `clock.off`.
  - **Cancel with `refund`:** each part goes back the way it was paid. The card part is one `refund`/`card` row. The Voucher-paid part becomes one new Voucher of that sum, recorded as a `refund`/`voucher` row. Its last valid date is the earliest of the Vouchers used, but never less than 30 days after `app_now()`.
  - **Cancel with `voucher`:** one Voucher of the full `total_ore`, valid one year, also when part of the Booking was paid by Voucher. No card refund row is written.
  - **Move:** to another Window, keeping the Sauna or picking another available one. The reference, price and `entry_time` are kept. A target where FR-29 fails is `409 sauna_unavailable`. A target Sauna whose `whole_price_ore` differs from the Booking's `total_ore` is `409 price_differs`, and the page says the Guest can cancel and book again (no difference is charged or refunded). Keeping the same Sauna keeps the price paid.
  - **After either action:** capacity is restored at once (Seats left rises by the Sauna's Capacity on cancel). Every cancel or move sends one email. The Administrator list shows a cancelled Booking with its time, cause and remedy, and does not count it.
- **Never money from a Voucher:** a Seat booking can never be cancelled with `guest` + `refund` (CHECK `seat_guest_refund_forbidden`). `refund()` on a Booking with a split in its history raises a 500.
- **Ledger:** for a Booking with no split, charges minus returns equal `total_ore` while it is active and 0 once it is cancelled with a remedy.
- **Tests:** catalogue examples A1–A8, B1–B7 and H12 are tests named by ID. INV-1 to INV-5 are checked after every example and race. Group-C races run 100 times. `test_fr33_whole_change.py` covers cancel with each remedy, move and each refusal.
- **Accessibility and privacy:** axe A/AA clean and keyboard only. Radio groups sit in `fieldset`/`legend` with one tab stop. Focus moves to the `h1`. No horizontal scroll at 1024, 1366 or 1920 px. Every request goes to the stack's own origin. Manage pages carry `X-Robots-Tag: noindex` and send no referrer.

## Technical Decisions

- **One Booking table:**
  - `bookings.kind` is `seats` or `whole`. A Whole-sauna booking has `sauna_id` set and `seats` NULL; a Seat booking has `seats` 1–10 and `sauna_id` NULL. A trigger keeps `kind` immutable.
  - `whole_bookings` is the capacity row, with `booking_id UNIQUE NOT NULL`. It exists exactly while its Booking is active, with the same Window and Sauna.
  - Deferred triggers call `check_whole_pair()` and raise `whole_pairing`, which is a 500.
  - **Write order:** create writes the Booking, then the capacity row. Cancel sets the status, then deletes the row. Move updates `bookings`, then `whole_bookings`, with `window_id` and `sauna_id` together.
- **Counting:** `window_booked_seats()` counts only active `kind = 'seats'` rows. Seats left comes only from the SQL functions.
- **FR-29 predicate:** `whole_bookable(wid, sid, ignore_booking DEFAULT NULL)` is the only statement of the store rule. `trg_check_whole` calls it on INSERT and on `UPDATE OF window_id, sauna_id`, passing `NEW.booking_id`, so a move is not judged against its own row. In a Whole-sauna action, `db` maps `whole_bookable`, `booked_within_capacity` and the `(window_id, sauna_id)` key to `409 sauna_unavailable`.
- **Listing:** `GET /api/private-saunas?date=` returns `{saunas: [{id, name, capacity, whole_price_ore, windows: [{id, start, end, already_started}]}], horizon_end, horizon_days}`. It needs no session, takes no lock and writes nothing except `ensure_generated()`. The Manage move list is the same query with `ignore_booking` = the Booking.
- **Price and Cutoff:** `saunas.whole_price_ore` is nullable and filled by the seed only where NULL. On a Booking, `total_ore = whole_price_ore` and `price_per_seat_ore` is NULL. `cutoff` is copied from `settings.cutoff_whole` (72 h, `CHECK >= 2 hours`).
- **Creation (5.2):**
  - `services.whole.create` runs in one `db.run`, in this order: charge decision, lock, key, horizon, deadline, Booking through `services.reference`, capacity row, payment, Manage token, Outbox email.
  - The request hash includes `kind` and `sauna_id`.
  - The Voucher quote and spend from Story 4.4 are reused, writing `charge`/`voucher` and `charge`/`card` rows.
- **Manage routes (5.3):**
  - **Read:** `GET /api/manage/{reference}` returns the shared serializer (`kind`, `seats` null, `sauna {id, name}`, `window`, `total_ore`, `status`) plus `version`, `change_allowed`, `cutoff_at` and history (with both Saunas for a move). It never returns an email, a Voucher code or a Manage link.
  - **Changes:** `POST …/whole/cancel {remedy, version}` and `POST …/whole/move {window_id, sauna_id, version}`, each a confirming POST with an `Idempotency-Key`.
  - **Wrong kind:** `…/seats/move` and `…/seats/voucher` answer `404 not_found` for a Whole-sauna booking, as `…/whole/*` routes do for a Seat booking.
  - **Manage token:** no Change issues or revokes one.
- **Booking-scoped order (cancel and move):**
  1. Read `window_id` without a lock.
  2. Call `lock_windows` with that Window and the target, in id order.
  3. Re-read the Booking `FOR NO KEY UPDATE`; if `window_id` changed, retry.
  4. Re-check the grant, then read the key.
  5. Refuse in this order: `booking_cancelled`, `booking_changed` (old `version`, with the current Booking), `change_invalid`/`same_target` (same Window and Sauna), `outside_horizon`, `deadline_passed` (target), `cutoff_passed` (Booking), then `sauna_unavailable` / `price_differs`.

  `version` is incremented in the same UPDATE. A repeat with the same key returns the first outcome and its stored emails, never a second refund or Voucher.
- **Cancel transaction:** one transaction sets `status = 'cancelled'`, `cancelled_at`, `cancel_cause = 'guest'` and `cancel_remedy`. It then deletes the capacity row and writes the history row through `services.history.record`. It writes the `payments` rows through `services.payment.refund()` (refund) or `services.voucher.issue()` (voucher), and finally the email. The 5.3 migration only adds `cancel` to the `booking_changes.action` CHECK, with its shape: `voucher_id` set only for a Voucher remedy, and `seats`, Window and Sauna ids and `new_booking_id` NULL.
- **Change response:** `{booking, voucher?: {value_ore, last_valid_date}, refund?: {card_ore}, emails: [{id, subject, body}]}`. The Voucher code appears only inside the email.
- **Emails:** each email says the Manage link in the confirmation email still works, and none carries the link.
  - **Move:** Change confirmation with the Sauna, the new session and the price.
  - **Cancellation:** the Sauna and the session, then either the card refund with the payment note plus any returned Voucher block (code, value, last valid date), or the Voucher block.
- **Placement (5.4):** `placement(wid)` returns `(sauna_id, state, seats)` in Fill order, with `state` in `open|whole|blocked|marked`. It is read only under `/api/admin/`. A brute-force reference lives in `tests/`.

## UX & Interaction Patterns

- **Landing:** two equal Booking choices, "Book seats" and directly under it "Book private sauna". Each Sauna card shows "Private sauna: NOK …" under the size line. The group sentence goes on Landing and in the Book seats rail.
- **Private sauna page:**
  - Date calendar, then a "View" radio group ("Show by sauna" / "Show by session") that regroups the one response.
  - Sauna card: photo, name, "Holds N", price and description.
  - By sauna, each card's session buttons choose both the Sauna and the session in one click. By session, the session buttons come first, then the free Saunas as cards.
- **Review and Confirmation (5.2):** the same pages as the Seat flow, with draft slot `draft:whole`. The summary label is "Sauna", showing the name and never the Capacity. The terms come from `content/terms-whole`: "Up to 72 hours before the session starts, you can cancel for a refund or a voucher, or move the booking to another session." After `sauna_unavailable`, Review shows a Notice saying nothing was charged, with the link "Choose another sauna or session".
- **Manage page for a Whole-sauna booking (5.3):**
  - Shows "Sauna" first in the summary, then the session and total, and offers "Cancel" and "Move".
  - Each is a confirming step built from `ManageBookingSummary`, `ConfirmingStep` and `ChangeResult`: "What will happen", "Nothing changes until you confirm.", then a result page with "Sent by email:" and "Back to your booking".
  - Cancel asks for the remedy (refund or voucher). Move reuses the date and session choice with the `ignore_booking` listing and lets the Guest keep or change the Sauna.
  - After `booking_changed` or `invalid_key`: "This booking was changed in the meantime. Check it and choose again." The step reloads and opens fresh with a new key.
  - `outside_horizon` / `deadline_passed`: "This session can no longer be booked. Nothing has changed."
  - **Not decided yet:** the exact wording of the Whole-sauna steps, the `price_differs` and `sauna_unavailable` reasons, the cancelled-Booking page and the Booking list's refund remedy label. Follow Epic 4's patterns and the decisions on Open Items 19–22, and record each new text with Lisa's decision in the story file and EXPERIENCE.md.
  - **Cutoff copy:** the current Manage "until" and Cutoff text (`MANAGE.untilText`, `MANAGE.cutoffPassed`) hardcodes "12 hours". A Whole-sauna booking needs a 72-hour variant.
- **Booking list:**
  - Cancelled status reads "Cancelled {dd.mm.yyyy HH:MM} · Guest · {remedy}".
  - Placement (5.4) is a table "Saunas" per Session group, with columns "Sauna" and "Seats counted" and cells "7 of 7", "Booked whole · {ref}", "Blocked" and "Private sauna only".

## Cross-Story Dependencies

- 5.1 lays the schema (`kind`, `sauna_id`, pairing, `whole_bookable`, `cutoff_whole`, `whole_price_ore`) and the listing. 5.2 books from that listing, and 5.3 moves through it with `ignore_booking`.
- 5.2 adds `sauna_unavailable` and the payments ledger (card and Voucher charge rows). Its Manage page currently shows a Whole-sauna booking with no Changes and no Cutoff text, and 5.3 adds both.
- 5.3 declares `price_differs` once in `api/errors.py` and the frontend mirror (it does not exist yet). It reuses Epic 4's Manage grant, key slots, `services.history`, `services.voucher.issue` and the Change components, and adds `services.payment.refund()`.
- 5.5's Hypothesis machine takes the FR-33 move and cancel (each remedy) as rules and checks the ledger invariant. 5.4's INV checker and brute-force Placement are reused by 5.5.
- Epic 4's race and model tests must keep passing as capacity counting changes.
