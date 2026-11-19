---
review: adversarial
target: ../ARCHITECTURE-SPINE.md (AD-23 to AD-26, draft 2026-11-19)
date: '2026-11-19'
lens: 'Two units one level down that each obey every AD to the letter yet still build incompatibly: clashing shared-data shapes, two owners of one entity, conflicting state-mutation paths'
inputs:
  - ARCHITECTURE-SPINE.md (updated 2026-11-19)
  - .memlog.md (2026-11-19 entries)
  - prds/prd-booking-platform-2026-10-29/prd.md (§3 glossary, §4.4 FR-16, §4.8, §4.9)
  - prds/prd-booking-platform-2026-10-29/appendix-fr-34-51.md (FR-39 Cutoff rule)
  - prds/prd-booking-platform-2026-10-29/addendum.md §A
  - src/booking_platform/schema.sql, src/booking_platform/app.py (slice)
  - tests/conftest.py, tests/test_application_rules.py, tests/test_fr10_bypass.py, tests/test_fr10_through_the_api.py, tests/test_fr14_retry.py
---

# Adversarial review: AD-23 to AD-26 (Whole-sauna booking)

## Verdict

The pairing model in AD-23 (a `bookings` row plus a `whole_bookings` capacity row) is sound. But AD-24's single two-argument predicate cannot serve both the listing and an AFTER trigger. The refusal-code rule contradicts AD-16 and a slice test that AD-21 freezes. And `booking_id NOT NULL` breaks the slice's own `whole_bookings` write path. So stories 1, 3, 5 and 7 will diverge unless about ten rules are tightened before they are written.

## Method

The units are the seven §4.9 stories from the brief:

| # | Story |
| --- | --- |
| U1 | Migration: `kind`, `sauna_id`, `seats` NULL, `whole_bookings.booking_id`, the pairing check, `whole_bookable`, `placement`, `whole_price_ore`, the Cutoff column |
| U2 | FR-30 Private sauna listing |
| U3 | FR-29 book a whole Sauna: payment, idempotency, confirmation email |
| U4 | Administrator Booking list showing Whole-sauna bookings and Placement |
| U5 | FR-33 cancel or move (refund and Voucher deferred to §4.8) |
| U6 | FR-31 Hypothesis model test |
| U7 | C1 to C5 parallel race tests |

A pair counts as a hole when both units comply literally and the merged result is wrong: a crash, a store rule silently lost, one fact with two shapes, two writers of one row, or one refusal with two codes.

## Summary

| # | Hole | Units | Severity |
| --- | --- | --- | --- |
| 1 | `whole_bookable(wid, sid)` counts its own row when called from the AFTER trigger: either every booking is refused or the started-Window rule disappears from the store | U1 ↔ U2/U3 | critical |
| 2 | Refusal codes: AD-24 "every FR-29 refusal is `sauna_unavailable`" vs AD-16 `deadline_passed` and the frozen slice test; store 23514/23505 carry no translatable constraint name | U3 ↔ U7, U1 ↔ U3 | high |
| 3 | `booking_id NOT NULL` breaks the slice's `whole_bookings` writer, its raw-insert tests and legacy rows; two owners of `whole_bookings` inserts | U1 ↔ skeleton/slice tests ↔ U3 | high |
| 4 | Pairing check undefined: which table, which events, both directions; move of `sauna_id` not in AD-23 Move | U1 ↔ U5 | high |
| 5 | Booking-scoped actions (cancel, move) read the Booking's Window before the lock, and may lock the Booking row before the Windows | U5 ↔ U7 (and §4.8 moves) | high |
| 6 | Idempotency key not bound to the request kind or target; one draft slot for two flows | U3 ↔ Core FR-6 SPA/service | medium |
| 7 | No shared Booking shape for `seats` NULL: JSON, email, admin row, model reference | U3 ↔ U4 ↔ U6 | medium |
| 8 | `whole_price_ore` on Saunas that already exist: no migration value, seed writes only absent rows → NULL price | U1 ↔ seed ↔ U2/U3 | medium |
| 9 | Cutoff is a `settings` column, but FR-39 says a Booking keeps the Cutoff it was made under | U3 ↔ U5 (↔ later FR-39) | medium |
| 10 | `placement(wid)` shape: closed Saunas, held Seats, equivalence with Room ahead | U1/U4 ↔ U6 | medium |
| 11 | "Started" is judged by two predicates (`already_started` vs inline in `whole_bookable`) | U1 ↔ Core listing | medium |
| 12 | C3/C4 and the model's "cancellation" have no v1 service for Seat cancellation; Deferred blocks "§4.9 stories" without saying which | U6 ↔ U7 ↔ §4.8 | medium |
| 13 | AD-2 checklist (lock trigger, `MUTATIONS`, bypass test) has no owner for the new parts | U1 ↔ U7 | low |
| 14 | Move side effects: `entry_time`, history-row writer, `kind`/`sauna_id` immutability | U5 ↔ §4.8 | low |

---

## 1. One predicate, two meanings: the trigger sees its own row (critical)

**Units.** U1 writes `whole_bookable(wid, sid)` and rewires `trg_check_whole` to call it on INSERT and `UPDATE OF window_id, sauna_id` (AD-24, Store). U2 calls the same function for the listing (AD-24, Listing). U3 may call it in `services` after the lock for a better message (AD-2, AD-24 Refusal).

**How each obeys.** AD-24 says `whole_bookable(wid, sid)` is "the only SQL statement of the store-enforced part of FR-29". It lists the clauses: not booked whole by another Booking, Room ahead, and the started-Window rule. FR-29 states the started-Window rule as "has not started, or has no Seat booking, or the Sauna is not open for Seats". U1 transcribes that faithfully as `NOT sauna_open_for_seats(wid, sid)` and `NOT EXISTS (whole_bookings for wid, sid)`. Schema `0001` fires the check AFTER INSERT (`t_00_check_whole`), and AD-24 keeps the trigger.

**Incompatibility.** The listing calls the function while the row is absent. The trigger calls it while the row is present. With two arguments, the function cannot tell "my own row" from "another Booking's row":

- **"Not booked whole" clause.** In the trigger, the clause always finds the new row, so every Whole-sauna booking is refused. The obvious repair is to drop the clause and rely on `UNIQUE (window_id, sauna_id)`. The listing then offers Saunas that are already booked whole, which breaks FR-30 ("only the pairs FR-29 allows").
- **Started-Window clause.** After the insert, `sauna_open_for_seats(wid, sid)` is false for the Sauna itself, because it is now Whole-sauna booked. The third alternative of the clause is therefore always true in the trigger. The store stops refusing a Whole-sauna booking over seated Guests in a started Window, and nothing errors. `0001` avoided this by testing `mark_closed()` instead; the AD does not say so.
- **BEFORE trigger instead.** If U1 moves the check to a BEFORE trigger to dodge self-counting, a move to another Sauna in the same Window is judged with the old Sauna still closed. Its Room ahead is then understated, and a valid move is refused.

AD-24's own phrase "a moved row never counts against itself" needs an identity that the signature does not carry.

**Severity: critical.** A store-enforced FR-29 rule can vanish silently, and the AD's central promise (one predicate for the listing and the write) cannot be implemented as written.

**Closing wording (AD-24, Predicate):**
> `whole_bookable(wid int, sid int, ignore_booking bigint DEFAULT NULL)` evaluates FR-29 as if the `whole_bookings` row of `ignore_booking` did not exist. The listing and `services` pass NULL; `trg_check_whole` (AFTER INSERT OR UPDATE OF window_id, sauna_id) passes `NEW.booking_id`. The started-Window alternative "the Sauna is not open for Seats" is `mark_closed(wid, sid)`, never `sauna_open_for_seats` of the Sauna being booked. A store test books a started Window with Seat bookings through a raw insert and expects a refusal.

## 2. One refusal, three codes (high)

**Units.** U3 (book) and U7 (C1/C2 races) against Core FR-6 and the slice tests kept by AD-21. Also U1 (how the store raises) against U3 (how `db` translates).

**How each obeys.**
- **U3** follows AD-24: "every FR-29 refusal is `409 sauna_unavailable`". FR-29's first bullet includes "inside the Booking horizon and before its Booking deadline", so a Whole-sauna booking after the deadline answers `sauna_unavailable`.
- **The Core and the slice** follow AD-16: "A Window past its Booking deadline is refused with `deadline_passed`." `tests/test_application_rules.py::test_nothing_can_be_held_booked_or_booked_whole_after_the_booking_deadline` asserts `deadline_passed` for the whole-booking path. AD-21 freezes that test ("no rule is loosened to keep a slice test green").
- **U1** keeps `0001`'s `RAISE ... USING ERRCODE = '23514'`, with no constraint name.
- **U3's `db` layer** translates "by constraint name" (AD-1). The slice's `refusal()` maps an unnamed 23514 to `rule_refused` with `message_primary`, which is store text and is forbidden by AD-16. It maps 23505 to `already_exists`.

**Incompatibility.**
- The deadline case gets two codes depending on which AD the story author reads first, and the SPA mirror table (AD-16) cannot hold both.
- In C1, the loser of the same-Sauna race either reaches the services pre-check (`sauna_unavailable`) or hits `UNIQUE (window_id, sauna_id)` first (23505, `already_exists`). Which one depends on whether U3 pre-checks.
- If U1 renames or reorders the trigger so that the recompute runs before the check, an open-Sauna booking fails `booked_within_capacity` and is translated to `no_seat_free` with a `seats_left` fact on the Private sauna page.
- The deferred pairing check and `verify_window` also raise unnamed 23514 at COMMIT, where a translator around `execute` never sees them.

**Severity: high.** U7's assertions are written against one code and U3 returns another.

**Closing wording (AD-24, Refusal, and AD-1):**
> FR-29's horizon and deadline parts keep their Core codes (`outside_horizon`, `deadline_passed`) and are checked first. `sauna_unavailable` covers only the store-enforced part. Every store refusal raised from a trigger names itself: `RAISE ... USING ERRCODE = '23514', CONSTRAINT = '<name>'`. `db` maps by that name, including at COMMIT:
>
> | Store refusal | Code |
> | --- | --- |
> | `whole_bookable` | `sauna_unavailable` |
> | `whole_bookings_window_id_sauna_id_key` (23505) | `sauna_unavailable` |
> | `booked_within_capacity` | `no_seat_free` |
> | `whole_pairing`, `verify_window` | an internal error (500), never a refusal |
>
> Unmapped store errors never put store text in `message`.

## 3. The slice already writes `whole_bookings`, and `booking_id NOT NULL` breaks it (high)

**Units.** U1 (migration) against the skeleton story (AD-21) and the slice tests. Also U3, which builds the paying whole-booking endpoint, against the skeleton, which keeps the slice's `POST /whole-bookings` under `/api`.

**How each obeys.**
- **The skeleton story** moves every slice path to `/api` (AD-21, "the `/api` paths"), so `POST /api/whole-bookings` survives as an insert into `whole_bookings` with no Booking, payment or reference.
- **The kept slice tests** write `whole_bookings` directly:
  - `test_fr10_bypass.py`: `INSERT INTO whole_bookings (window_id, sauna_id)`;
  - `test_fr14_retry.py`, the 800-request mixed load in `test_fr10_through_the_api.py`, and `test_application_rules.py`: through `/whole-bookings`.
- **U1** adds `booking_id UNIQUE NOT NULL REFERENCES bookings` (AD-23).
- **AD-15** says a legacy database "counts as having `0001` applied", so the dev and examiner databases may hold `whole_bookings` rows with no Booking.

**Incompatibility.**
- U1 fails on legacy rows (23502), or turns 4+ frozen tests red. Fixing them is either "loosening" (dropping NOT NULL) or rewriting a test that AD-21 says to keep, and U1 has no rule for which is allowed.
- `whole_bookings` gains two writers: the slice endpoint and `services.whole`. U3 may add a second endpoint (`/api/private-sauna/bookings`) while the slice one remains.

**Severity: high.** It is certain to happen, because the code exists today.

**Closing wording (AD-23, new bullet "Slice path"):**
> U1 removes the slice's whole-booking endpoint. The only writer of `whole_bookings` is `services.whole`. Slice tests that wrote `whole_bookings` are rewritten to call a test helper `raw_whole(pg, wid, sid)`, which inserts a paired `kind='whole'` Booking and its capacity row in one transaction. This is a reshape under AD-21, not a loosening, and every assertion stays. The migration deletes `whole_bookings` rows that have no Booking; they can exist only in dev and slice databases.

## 4. The pairing check has no defined shape (high)

**Units.** U1 (implements "a deferred COMMIT check refuses any mismatch") against U5 (cancel and move).

**How each obeys.**
- **U1** writes one `DEFERRABLE INITIALLY DEFERRED` constraint trigger on `whole_bookings`. It checks that its Booking is active, `kind='whole'`, and has the same `window_id` and `sauna_id`.
- **U5** follows AD-23 Move ("update `window_id` on both rows"). Following FR-33's assumption, it lets the Guest pick another Sauna, so it also updates `sauna_id`. AD-23's own `price_differs` rule presumes Sauna changes.

**Incompatibility.**
- A check placed only on `whole_bookings` never fires for an active `kind='whole'` Booking whose capacity row was never inserted, for example by a seed or a future admin path. That is a paid Private sauna still sold as Seats, the exact case AD-23's "Prevents" names.
- It also never fires when a Booking's `window_id` is updated alone.
- A check placed on `bookings` alone misses an orphaned `whole_bookings` UPDATE.
- AD-23 Move mentions only `window_id`, so a U5 that obeys it to the letter cannot do a Sauna-changing move, while a U5 that follows FR-33 contradicts the AD's text.
- AD-7 restricts the `bookings` triggers to `UPDATE OF window_id, seats, status`, so a check hung on those triggers misses `sauna_id` and `kind` changes.

**Severity: high.**

**Closing wording (AD-23, Capacity row):**
> One function `check_whole_pair(booking_id)` is called by two deferred constraint triggers:
> - one on `bookings` (INSERT, UPDATE OF kind, status, window_id, sauna_id);
> - one on `whole_bookings` (INSERT, UPDATE, DELETE, checking OLD and NEW `booking_id`).
>
> It raises `CONSTRAINT = 'whole_pairing'`. Write order:
> - **Create:** the Booking row first (AD-20 reference claim), then `whole_bookings`.
> - **Cancel:** the status first, then the DELETE.
> - **Move:** `bookings` first, then `whole_bookings`, updating `window_id` and `sauna_id` together.
>
> `kind` never changes after insert (a BEFORE UPDATE trigger refuses it).

## 5. Lock order for actions that start from a Booking (high)

**Units.** U5 (cancel and move a Whole-sauna booking) against U7 (C3/C4/C5) and the §4.8 Seat moves that share the pattern.

**How each obeys.** AD-3 requires `lock_windows` "with every Window it can touch before its first write". For a Booking-scoped action, the Windows are not in the request. U5 obeys in one of two ways:

- **(a)** reads `bookings.window_id` with a plain SELECT, then calls `lock_windows([old, target])`;
- **(b)** runs `SELECT ... FROM bookings WHERE id = $1 FOR UPDATE` first (a read, not a write, so AD-3's letter allows it), then `lock_windows`.

**Incompatibility.**
- **With (a):** a concurrent move commits between the read and the lock, so the cancel locks the wrong Window. Its first write's BEFORE trigger then locks the real Window outside id order, which can deadlock. Worse, its Cutoff (72 h) and `price_differs` checks were judged on the stale Window.
- **With (b):** one story takes the Booking row lock before Window locks while another (the Core booking flow, an admin D4 later) takes Window locks before touching the same Booking. That is the inverted order AD-3 exists to prevent. Retries on 40P01 hide it in tests but make C3/C4 flaky.

**Severity: high.**

**Closing wording (AD-3, new bullet "Booking-scoped actions"):**
> An action that starts from an existing Booking:
> 1. reads its `window_id` without a lock;
> 2. calls `lock_windows` with that Window and any target;
> 3. re-reads the Booking (`FOR NO KEY UPDATE`).
>
> If `window_id` changed, it raises the retryable conflict and `db.run` starts it again. No row lock is taken before `lock_windows`. Time rules (Cutoff) are judged only on the re-read.

## 6. Idempotency key not bound to what it confirmed (medium)

**Units.** U3 (book whole) against the Core FR-6 SPA and service.

**How each obeys.** AD-9: the SPA makes the key "when the Guest reaches the review page", keeps it "with the booking draft in `sessionStorage`" and reuses it "until the booking is paid". "A known key from the same session rebuilds the original response from the Booking". The table is `(key, session_id, booking_id)`. AD-9 binds FR-6, FR-7 and FR-25, not FR-29.

**Incompatibility.**
- U3 keeps its draft in the same `sessionStorage` slot as the Seat flow, which is a natural reuse. A Guest who abandons a Seat review after a lost response and opens Private sauna in the same tab resends the old key. The server rebuilds the Seat Booking as the Private sauna confirmation.
- U3 may add a separate endpoint whose rebuild code assumes `kind='whole'` and crashes on a Seat Booking, or the reverse: the Core rebuild does `seats * ...` on NULL.
- AD-9 never checks that the replayed request matches the stored one, and AD-13 forbids recomputation but not a mismatched replay.

**Severity: medium.**

**Closing wording (AD-9):**
> Binds FR-29 too. `idempotency_keys` also stores `kind`. A known key whose Booking's `kind`, `window_id` or `sauna_id`/`seats` differ from the request is refused with `409 invalid_key`. The SPA keeps one draft and one key per flow (`draft:seats`, `draft:whole`).

## 7. No shared shape for a Booking with `seats` NULL (medium)

**Units.** U3 (confirmation JSON and email), U4 (admin list) and U6 (model reference), against the Core serializers.

**How each obeys.** AD-23 makes `seats` NULL for `kind='whole'`. AD-5 says Seats figures come from SQL functions, and AD-13 says `total_ore` is never recomputed. FR-16 shows "each Booking's reference, name, email, Seats, total".

**Incompatibility.**
- U4 shows `saunas.capacity` in the Seats column. That value changes under FR-38, so a past Booking's "Seats" changes. U3 sends `seats: null`. The Core SPA component formats "`${seats}` Seats", which renders "null Seats".
- U6's brute-force reference sums `seats` over the rows and hits `None + int`.
- The Core confirmation endpoint (AD-12) returns a Seat shape that U3 must either extend or fork, which gives two Booking JSONs.

**Severity: medium.**

**Closing wording (AD-23, new bullet "Shape"):**
> One serializer in `services` produces every Booking JSON and every email fact block: `kind`, `seats` (int or null), `sauna` ({id, name} or null), `window`, `total_ore`, `status`. Pages show the Sauna name for a Whole-sauna booking and never its Capacity. No code outside `window_booked_seats()` sums `bookings.seats`.

## 8. `whole_price_ore` for Saunas that already exist (medium)

**Units.** U1 (adds the column) against the seed story and U2/U3 (read the price).

**How each obeys.**
- **AD-15:** migrations hold "never reference values". AD-18 adds that a new reference column "gets the seed value as its default in the same change", but a per-Sauna price cannot be one column default.
- **AD-18:** the seed "writes a value only where the row is absent". On every existing dev or examiner database the `saunas` rows exist, so the seed never writes the new price.

**Incompatibility.** The price stays NULL. U2 lists a Sauna with no price, or filters it out. U3 inserts `total_ore` NULL, or crashes.

**Severity: medium.**

**Closing wording (AD-18, Writes):**
> The seed writes a value where the row is absent, and also where a reference column the seed owns is NULL. A per-row reference column is added nullable. Until it is filled, a NULL `whole_price_ore` means the Sauna is not offered whole (`whole_bookable` is false).

## 9. Cutoff: a setting read at change time, or kept per Booking? (medium)

**Units.** U3 (creates the Booking) against U5 (judges the 72-hour Cutoff), with FR-39 later.

**How each obeys.** AD-23: "the 72-hour Whole-sauna Cutoff is a `settings` column (AD-4)". U3 stores nothing. U5 compares `lower(during) - settings.whole_cutoff` at change time. FR-26 and FR-39 in the appendix say "Existing Bookings keep the Cutoff they were made under", and the §4.8 author therefore stores a per-Booking Cutoff.

**Incompatibility.** Seat bookings carry a Cutoff snapshot and Whole-sauna bookings do not. When FR-39 arrives, Whole-sauna bookings made before it have no recorded Cutoff, and a backfill guesses. Two Cutoff predicates exist, against AD-4's "one SQL function".

**Severity: medium.** This is the "forces a rewrite later" case that §10.3 asks the spine to decide.

**Closing wording (AD-23, Cutoff, and AD-4):**
> Every Booking stores `cutoff_at` (timestamptz) when it is created, from the `settings` Cutoff for its `kind`. A move recomputes it from the target Window with the Booking's original Cutoff length. One predicate, `change_allowed(booking_id)`, judges it for both kinds.

## 10. `placement(wid)` has no fixed shape (medium)

**Units.** U1 (writes `placement`) and U4 (shows it) against U6 (compares it with the brute force).

**How each obeys.** AD-25 says `placement(wid)` "returns `(sauna_id, seats)` in Fill order". The AD does not say:
- whether Saunas that are Whole-sauna booked, Blocked or marked appear (with 0) or are omitted;
- whether held Seats are placed.

Meanwhile `whole_bookable` judges Room ahead against Seats booked plus held.

**Incompatibility.**
- U4 needs a per-Sauna state ("Private", "Blocked") and adds a Python join over `sauna_open_for_seats`, which is a second derivation.
- U1 omits closed Saunas while U6's reference returns every Sauna, so the comparison needs a translation that each side writes differently.
- If `placement` ignores Holds, the admin view shows Sauna 4 empty while the listing refuses it. The two computations of "Seats in or before S" disagree.

**Severity: medium.**

**Closing wording (AD-25):**
> `placement(wid)` returns one row per Sauna in Fill order: `(sauna_id, state, seats)`. `state` is one of `open`, `whole`, `blocked` or `marked`, and `seats` is 0 unless the Sauna is `open`. It places booked Seats only (INV-2). `whole_bookable` and `placement` agree when Holds are 0, and the model test asserts that agreement. Holds are reported separately as `window_held_seats`.

## 11. "Started" is decided twice (medium)

**Units.** U1 (`whole_bookable`, with the started test inline: `lower(during) <= app_now()`) against the Core listing (AD-16 `already_started`).

**How each obeys.** AD-4 requires one SQL function per time-rule predicate. AD-24 puts "the started-Window rule" inside `whole_bookable`, but does not name a shared predicate.

**Incompatibility.** The two can differ at the edge (`<` vs `<=`). At the exact start instant, the Seat page says "not started" while the store refuses the Private sauna as started, or the reverse.

**Severity: medium**, because the clock is moved to exact edges in tests.

**Closing wording (AD-4, Predicates):**
> `window_started(wid)` (`app_now() >= lower(during)`) is the only started test. `already_started` and `whole_bookable` both call it.

## 12. Cancellation actions the tests need do not exist in v1 (medium)

**Units.** U6 (the model machine needs "cancellations" for A2, A3 and B6) and U7 (C3 "a cancellation that races a Whole-sauna booking", C4 "two simultaneous cancellations"), against §4.8 and the Deferred list.

**How each obeys.**
- AD-26 calls only `services`.
- AD-14 says no endpoint changes a switch, but says nothing about test-only endpoints.
- Deferred says "§4.9 stories are written after that amendment", without saying whether this means all of FR-29 to FR-33 or only FR-33.

**Incompatibility.**
- U7 cancels Seats with raw `UPDATE bookings SET status` (the bypass style).
- U6 needs a service and invents `services.booking.cancel` with its own signature. When §4.8 lands, FR-27 "give up all Seats for a Voucher" is a second cancellation path with Voucher side effects.
- One reader holds stories U1 to U4 until §4.8 is amended; another builds them now.

**Severity: medium.**

**Closing wording (Deferred, and AD-26):**
> - **Deferred:** only FR-33 waits for the §4.8 amendment; FR-29 to FR-32 do not.
> - **AD-26:** the model machine and the C tests cancel Seats only through the §4.8 service (FR-27 give-up-all) and cancel Whole-sauna bookings only through FR-33. Until §4.8 exists, the Seat-cancellation rules and C3/C4 are marked pending, not substituted. No test-only endpoint is added.

## 13. The AD-2 checklist has no owner for the new parts (low)

**Units.** U1 against U7.

**How each obeys.** AD-2 lists the parts every new capacity column needs: a BEFORE lock trigger, an AFTER recompute trigger, inclusion in `verify_window`, a bypass test and an entry in `MUTATIONS`. U1 reads "the bypass test and `MUTATIONS`" as the test stories' job. U7 reads them as part of the migration.

**Incompatibility.** Neither story adds `nopair` or `nowholecheck` mutations, so the deferred pairing check and `whole_bookable` are never shown to bite.

**Severity: low.**

**Closing wording (AD-2):**
> The story that adds a store rule also adds its `MUTATIONS` entry and the bypass test that turns red under it.

## 14. Move side effects left open (low)

**Units.** U5 against §4.8 (FR-26 move).

**How each obeys.** AD-7 says a Change is "a history row" and that `entry_time` is "the time of the Change that moved them in" for Seat bookings. AD-23 Move is silent on `entry_time` and on who writes the history row: a trigger or `services`.

**Incompatibility.** §4.8 writes history in `services`, while U5 adds a trigger on `UPDATE OF window_id`. A Seat move then writes two history rows.

**Severity: low.**

**Closing wording (AD-7):**
> History rows are written only by `services`, in the Change's transaction. A Whole-sauna move leaves `entry_time` unchanged (it is used only by the Overbooking fallback for Seat bookings).

---

## Not holes (checked)

- **`seats` NULL against `CHECK (seats > 0)`:** a NULL passes a CHECK, so only `NOT NULL` must be dropped, and the AD-23 CHECK covers the tie between the three columns.
- **`SUM(seats)`:** it ignores NULL, so `window_booked_seats` is safe even before the `kind` filter.
- **Trigger order on whole-booking insert:** with the Booking first, the `bookings` AFTER recompute sees no change, then `whole_bookings` triggers recompute. The deferred pairing check tolerates the transient state.
- **FK lock interaction:** the `whole_bookings → bookings` and `bookings → saunas` foreign keys take KEY SHARE locks. These do not conflict with status or `capacity` updates (NO KEY UPDATE), so they add no deadlock against AD-3's order.
- **A cancelled Booking's capacity:** it is released by the DELETE alone, because `sauna_open_for_seats` reads only `whole_bookings`, never `bookings.status`.
