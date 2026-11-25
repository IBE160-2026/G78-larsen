# Epic 5 Context: A group books a whole sauna

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Let a group book one whole Sauna for one session (shown to Guests as "Private sauna"): a Guest picks a date, sees which Saunas can be booked whole with size, price and free sessions, books and pays, and until 72 hours before the start can cancel for a refund or a Voucher, or move it. Seat bookings are counted around Private saunas so that no Seat is ever lost or sold twice, and the Administrator sees each session's Placement. Delivers SC2/SC4 and FR-29 to FR-33, plus the price per Sauna and the group sentence on Landing (FR-1.7, FR-4) and Whole-sauna bookings and Placement in the Booking list (FR-16). Schedule checkpoints: 5.1–5.3 by 2 Dec, Epic 5 by 4 Dec.

## Stories

- Story 5.1: A Guest sees which saunas can be booked whole
- Story 5.2: Book and pay for a Private sauna
- Story 5.3: Cancel or move a Private sauna
- Story 5.4: The Administrator sees where Seats are counted
- Story 5.5: Placement and Private saunas hold under any sequence and any race

## Requirements & Constraints

- **Prices and Saunas (decided 2026-11-24, changed 2026-11-25):** every Sauna is open for Seats and for Private sauna booking unless marked otherwise (`bookable_whole = false` or no price). Rauha NOK 1,850, Löyly NOK 2,600, Kajo NOK 3,150, Lumo NOK 3,950 (Oslo average about NOK 262 per place × Capacity, rounded to 50).
- **FR-29:** a Sauna can be booked whole in a Window only if it is bookable whole with a price, not Blocked, not already booked whole, the Seats booked plus held fit in the Saunas ahead of it in Fill order (unless it is marked Whole-booking-only and unreleased), and the Window has not started, or has no Seat booking, or the mark applies. The Sauna is not held while the Guest pays; a pair taken meanwhile is refused with nothing charged.
- **FR-30:** for a date the Guest sees only valid pairs (inside the horizon, before the Booking deadline, FR-29), viewable by Sauna or by session, and always picks the Sauna. Confirmation names Sauna and session.
- **FR-4 / AD-25:** no Seat-flow page, response or email names a Sauna or shows Placement. Sauna names appear only in the Venue facts, `kind = 'whole'` responses and `/api/admin/`.
- **FR-33:** Whole-sauna Cutoff 72 h (own `cutoff` on the Booking); cancel with remedy `refund` (back the way it was paid) or `voucher` (full `total_ore`, one year); move keeps reference and price, and a target Sauna with another price is `price_differs`.
- **FR-31/FR-32:** catalogue examples A1–A8, B1–B7, H12 are example tests named by ID; INV-1 to INV-5 checked after every example and race; group-C races run 100 times; Hypothesis machine over `services`.
- **Accessibility:** axe A/AA clean, keyboard only, radio groups in `fieldset`/`legend` with one tab stop, focus to `h1`, no horizontal scroll at 1024/1366/1920, every request to the stack's own origin.

## Technical Decisions

- **One Booking table (AD-23):** `bookings.kind` (`seats` | `whole`) and `sauna_id`; Seat booking `seats` 1–10 and `sauna_id` NULL, Whole-sauna booking `sauna_id` set and `seats` NULL; one CHECK; `kind` immutable by trigger. `whole_bookings` is the capacity row with `booking_id UNIQUE NOT NULL`, existing exactly while its Booking is active with the same Window and Sauna; deferred constraint triggers call `check_whole_pair(booking_id)` and raise `whole_pairing` (a 500). Write order: Booking first, then capacity row; cancel sets status then deletes the row; move updates `bookings` then `whole_bookings`.
- **Counting:** `window_booked_seats()` counts only active `kind = 'seats'` rows; nothing else sums `bookings.seats`. Seats left only from the SQL functions (AD-5).
- **FR-29 predicate (AD-24):** `whole_bookable(wid, sid, ignore_booking DEFAULT NULL)` is the only statement of the store rule; `trg_check_whole` (AFTER INSERT and `UPDATE OF window_id, sauna_id`) calls it and raises `whole_bookable`. In a Whole-sauna action `db` maps `whole_bookable`, `booked_within_capacity` and the `(window_id, sauna_id)` key to `409 sauna_unavailable`; `outside_horizon`, `deadline_passed`, `cutoff_passed` are checked in `services` after the lock, in that order.
- **Listing (AD-24):** `GET /api/private-saunas?date=` → `{saunas: [{id, name, capacity, whole_price_ore, windows: [{id, start, end, already_started}]}], horizon_end, horizon_days}`; no session, no lock, writes only `ensure_generated()`. The Manage move list is the same query with `ignore_booking`.
- **Price:** `saunas.whole_price_ore` nullable, filled by the seed only where NULL (AD-18); Booking `total_ore = whole_price_ore`, `price_per_seat_ore` NULL. Cutoff copied from `settings.cutoff_whole` (72 h, `CHECK >= 2 hours`).
- **Creation (5.2):** `services.whole.create` in one `db.run` with the Seat flow's order (charge decision, lock, key, horizon, deadline, Booking via `services.reference`, capacity row, payment, Manage token, Outbox email); request hash includes `kind` and `sauna_id`; Voucher quote and spend reused from 4.4.
- **Placement (AD-25):** `placement(wid)` → `(sauna_id, state, seats)` in Fill order, `state` in `open|whole|blocked|marked`, placing booked Seats only; the only computation, read only under `/api/admin/`; a brute-force reference lives in `tests/`.
- **Slice reshape (AD-21):** the slice's `/api/admin/whole-bookings` endpoint is removed in 5.1; tests use `raw_whole(pg, wid, sid)`; every slice assertion stays.

## UX & Interaction Patterns

- Landing: two equal Booking choices, "Book seats" and directly under it "Book private sauna", each with a short note (Lisa 2026-11-25; replaces the "Private sauna" Text link); Sauna card price line under the size line for Saunas offered whole; group sentence after the Seat statement on Landing and in the Book seats rail (inside the 1366×768 first-view budget).
- Private sauna page: Date calendar reused from Book seats; "View" radio group regroups one API response (by sauna / by session); Sauna card = photo, name, "Holds N", price, description; by sauna its free sessions are buttons (one click chooses both), by session the sessions are buttons and the free Saunas cards (Lisa 2026-11-25, proposals H and K); empty date says so plainly. Wording in EXPERIENCE.md "Private sauna wording".
- 5.2 Review: same Details/Review/Confirmation, draft slot `draft:whole`, "The sauna is not held while you pay."; after `sauna_unavailable` the Notice "This sauna can no longer be booked for this session. You have not been charged." with the Text link "Choose another sauna or session" (decided 2026-11-24).
- 5.3 reuses `ManageBookingSummary`, `ConfirmingStep`, `ChangeResult` and Epic 4's wording patterns.
- 5.4 Booking list Placement: table "Saunas" per Session group, columns "Sauna" and "Seats counted", cells "7 of 7", "Booked whole · {ref}", "Blocked", "Private sauna only" (decided 2026-11-24).

## Cross-Story Dependencies

- 5.1 lays the schema (`kind`, `sauna_id`, pairing, `whole_bookable`, `cutoff_whole`, `whole_price_ore`) and the listing that 5.2 books from and 5.3 moves through.
- 5.2 adds `sauna_unavailable` to `api/errors.py` and the frontend mirror; its e2e flow books Kajo.
- 5.3 depends on 5.2's payments ledger and Epic 4's Manage, Change, history and Voucher services. 5.4's INV checker and brute-force Placement are reused by 5.5.
- Epic 4's race and model tests must keep passing as capacity counting changes.
