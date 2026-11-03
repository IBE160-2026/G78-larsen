---
review: adversarial
target: ../ARCHITECTURE-SPINE.md
date: '2026-11-03'
lens: 'Two units built independently by different Claude Code sessions, each obeying every AD to the letter, that still build incompatibly'
inputs:
  - ARCHITECTURE-SPINE.md (draft, 2026-11-03)
  - src/booking_platform/schema.sql, app.py, db.py (Core slice)
  - prds/prd-booking-platform-2026-10-29/prd.md (§3, §4.1–4.13, §5, §7, §8)
---

# Adversarial review: Architecture Spine, Saunalöyly Booking Platform

## Verdict

The capacity kernel (AD-2, AD-3, AD-5, AD-6) is hard to break, but the spine leaves the *Core's own* cross-story seams open: the idempotency check, the session identity, the Booking reference, the confirmation page and the time-rule predicates can each be built in two letter-compliant ways that do not fit together, and several of these will diverge in the first Core epic unless the spine adds about a dozen one- or two-sentence rules.

## Method

For each seam, two units one level down (stories or epics) were constructed as a fresh Claude Code session would build them from the spine alone. Each unit reads every AD literally. A pair counts as a hole when both units comply and the merged result is wrong: a crash, a duplicate, a lost confirmation, a rule decided twice with different answers, or a data shape that one side cannot fill. Holes are ranked by how likely the divergence is **in the Core build** (PRD §4.1–4.6), not by how bad it would be.

Likelihood scale: **High** = the obvious implementation of at least one side diverges; **Medium** = a reasonable session could go either way; **Low** = needs an If-time item or an unusual choice.

## Summary of holes

| # | Hole | Seam | Core likelihood | ADs touched |
| --- | --- | --- | --- | --- |
| 1 | Idempotency lookup before the Window lock; key scope; what "outcome" is | FR-6 booking vs AD-9 module | High | AD-3, AD-9 |
| 2 | Session identity shape and when an anonymous session is born | AD-8 auth vs FR-6/FR-8 booking vs Holds | High | AD-3, AD-8, AD-9 |
| 3 | Confirmation page cannot find "its" Outbox email; Outbox is admin-only | FR-8 page vs AD-12 Outbox | High | AD-10, AD-12 |
| 4 | Booking horizon decided in three places, with no stored value; SPA uses the browser clock | FR-2/3 find vs FR-6/18 book vs AD-18 seed vs SPA | High | AD-2, AD-4, AD-18 |
| 5 | Booking reference "retries on collision" vs "services never retry" and an aborted transaction | FR-8 reference vs AD-3 | High | AD-3, Conventions |
| 6 | Window generation only at startup; resurrection and overlap crash against FR-38 | AD-18 seed vs FR-3 find vs FR-38 admin | Medium-High | AD-4, AD-18 |
| 7 | Seed vs migration vs Administrator ownership of reference data (prices, horizon, Saunas) | AD-15 vs AD-18 vs FR-38/39 | Medium-High | AD-15, AD-18 |
| 8 | Refusal codes and status for time rules: 409 vs 422 | FR-6 book vs FR-18 validation | Medium-High | AD-16, Conventions |
| 9 | Catch-up "on read" makes GETs write and lock Windows; non-capacity UPDATEs on `bookings` fire the capacity triggers | FR-21 retention vs FR-16 list vs AD-2 triggers | Medium | AD-2, AD-3, AD-4, AD-7 |
| 10 | Two migrations with the same number; slice databases with no `schema_migrations` | AD-15 runner vs parallel stories | Medium | AD-15 |
| 11 | `sign_in_failures` drawn with an FK to `accounts`; concurrent failures beat the count | AD-11 vs ER diagram | Medium | AD-11 |
| 12 | Terms text and emailed link paths owned twice (SPA and services) | FR-5/8 SPA vs AD-12 email | Medium | AD-12, AD-16 |
| 13 | Seeded sample Bookings (DR-2) have no path | DR-2 README story vs AD-18 seed vs FR-6 | Medium | AD-12, AD-13, AD-18 |
| 14 | "Total paid" stored twice (`bookings` and `payments`) | FR-16 list vs FR-8 confirmation vs FR-28 | Low-Medium | AD-13 |
| 15 | Venue date by implicit cast in the connection's TimeZone | FR-3 find vs FR-16 list | Low-Medium | AD-4 |
| 16 | Personal data copied into the Outbox and idempotency outcomes outlives retention | FR-21 vs AD-9 vs AD-12 | Low-Medium | AD-9, AD-12 |
| 17 | Sign-in rotates the session row and orphans Holds and confirmations | AD-8 auth vs FR-35/FR-37 | Low (Core) | AD-8 |
| 18 | `payment = "hold"` cannot be honoured without holding a lock across a wait | AD-13/14 vs AD-3 | Low (Core) | AD-3, AD-13, AD-14 |
| 19 | `force_conflict` in `db.run` also hits startup migrate/seed and reads | AD-14 vs AD-18 | Low | AD-14 |
| 20 | "No lock is held across anything but SQL" is literally unsatisfiable | AD-3 wording | Low | AD-3 |

---

## Ranked holes

### 1. Idempotency lookup before the Window lock; key scope; what "outcome" is — High

**Unit A (FR-6 booking story).** Writes `services/booking.create(c, session, key, req)`: `lock_windows([window_id])` first (AD-3), then checks deadline, inserts the Booking, charges, sends the email, stores the key.

**Unit B (AD-9 idempotency story, written to be reused by FR-25 later).** Builds a generic `services/idempotency.run_once(session, key, action)` that looks the key up and, if unknown, calls the action's `work`. The lookup is the first statement of the transaction, before the action's `lock_windows`. AD-9 only says the key is *stored* in the same transaction; it says nothing about *when it is read*. AD-3 forbids a *write* before the lock, not a read, so Unit B complies.

**Clash.** Double click: both requests read "unknown" before either holds the lock. Request 2 then waits on the Window lock, gets it after request 1 commits, inserts a second Booking (if Seats remain) and then fails on the key's unique index, which the slice's `refusal()` maps to `409 already_exists`, or, if the primary key is `(key, session_id)` and both used the same session, succeeds twice. Either FR-6 consequence ("never two Bookings", "a repeat returns the first outcome") fails. A third variant: AD-9 says a key from another session "is treated as unknown"; with a primary key on `key` alone, "unknown" then crashes on insert, and with `(key, session_id)` it books again.

Second divergence on the same seam: Unit B stores the outcome as the full JSON response; the confirmation story (FR-8) rebuilds the page from the Booking. A refusal (no Seat, failed payment) rolls back under AD-3, so nothing is stored, and a retry with the same key after a failed payment (FR-7 "a way to try again") re-runs, which is right. But a session that "stores every outcome" commits a failure row and the Guest can never retry on that review page.

**Proposed rule (tighten AD-9).** *The key is read only after `lock_windows`, as the first statement after it, inside the action's own `work`; `idempotency_keys` has primary key `key` alone, and a key found under another session is refused as `409 invalid_key`, never re-run. Only success is stored, as `(key, session_id, booking_id)`; the repeat response is rebuilt from the Booking, and a refusal stores nothing, so the same key may be retried.*

### 2. Session identity shape and when an anonymous session is born — High

**Unit A (AD-8 sessions, built with Administrator sign-in, FR-15).** `sessions(id bigserial, token_hash bytea unique, role, account_id, expires_at)`. Creates a session only at sign-in, because that is all FR-15 needs; anonymous sessions are "created when needed". Sign-out and expiry *delete* rows (AD-8: "Sign-out deletes the row"); a startup catch-up deletes expired rows (AD-4).

**Unit B (FR-6/FR-8 booking).** Needs "the browser session that paid" (FR-8) and a session for the key (AD-9). Because the slice's `holds.session_id` is `text`, it stores the cookie's *hash* (hex) in `bookings.session_id text`, or it adds `bookings.session_id bigint REFERENCES sessions ON DELETE CASCADE` "for tidiness", or plain `REFERENCES sessions` (RESTRICT). It creates the anonymous session lazily inside `POST /api/bookings` when no cookie is present.

**Clash.**
- Shape: one side references `sessions.id`, the other the token hash; a join from Booking to session fails, and the confirmation ownership check compares unlike values.
- Deletion: with CASCADE, deleting an expired anonymous session deletes Bookings (breaks AD-7); with RESTRICT, the startup clean-up fails and the server does not start.
- Birth: if the session is born on the submit request and that response is lost, the browser never gets the cookie; the retry arrives with no session, so the key is "from another session" and the Guest is booked twice or refused (hole 1).
- Lifetime: AD-8 sets 8 h sliding for Administrators only; anonymous lifetime, and so how long FR-8's "for as long as that session lasts" is, is left to each story.

**Proposed rule (tighten AD-8).** *Everything that refers to a session stores `sessions.id` (bigint FK, `ON DELETE SET NULL` from `bookings` and `holds`, `ON DELETE CASCADE` from `idempotency_keys`), never the token or its hash, and migration 0002 converts `holds.session_id`. An anonymous session is created only by `POST /api/session`, which the SPA calls before it shows the review page; a state-changing Guest endpoint without a valid session answers `401 no_session` and creates nothing; anonymous sessions last 24 h sliding.*

### 3. The confirmation page cannot find "its" Outbox email — High

**Unit A (AD-12 Outbox, built with FR-17).** Implements exactly the specified `services.outbox.send(c, to, subject, body)` and `outbox_emails(id, sent_at, to, subject, body)`, and `GET /api/admin/outbox`. "Only the Administrator API lists it."

**Unit B (FR-8 confirmation page).** Must show "that email as sent", only in the paying session, and survive reload. The ER diagram draws `bookings ||--o{ outbox_emails : "about"`, but the only allowed send function has no booking parameter, so B either (a) adds a `booking_id` keyword (changing A's signature), (b) finds the email by `to` + subject + time (fragile, and leaks other Bookings' emails to the same address), or (c) re-renders the body from the Booking (no longer "as sent", and email text now built in two places). Separately, it needs a URL: internal ids "are never shown to Guests", the reference "opens nothing alone", so B picks `/confirmation/:reference` + session check, while the booking story's SPA navigates to `/confirmation` with the result held in React state (lost on reload).

**Clash.** Three incompatible link mechanisms, and a non-Administrator read of the Outbox that AD-12's wording forbids.

**Proposed rule (new AD-12a).** *`outbox.send(c, to, subject, body, *, booking_id=None)` returns the email id, and every email about a Booking passes its id. The Guest confirmation is `GET /api/bookings/{reference}/confirmation`, answered by one service function that requires the Booking's `session_id` to be the caller's session (else 404, AD-10) and returns the Booking facts plus the stored email row; this is the only Guest-facing read of `outbox_emails`, and the SPA route is `/confirmation/:reference`.*

### 4. Booking horizon decided in three places, with no stored value — High

**Units.** (A) FR-2/FR-3 "Find a Window" filters dates in `services/windows.py`; (B) FR-6/FR-18 booking refuses outside the horizon in `services/booking.py`; (C) AD-18 seed "generates Windows from today through the Booking horizon"; (D) the SPA date control limits the picker (FR-2).

AD-2 says horizon "lives in services and is not duplicated in SQL". The 0001 `settings` row has no horizon column; FR-39 makes it a Setting with default 4 weeks and limit 1 month (recently corrected, commit 8518b81). So: A writes `HORIZON = timedelta(weeks=4)`; B writes `lower(during) <= app_now() + interval '1 month'` (confusing default and limit); C reads a `horizon_days = 28` key in `seeds/`; D computes `today + 28` from `new Date()`. Inclusive vs exclusive edge also differs (`<` vs `<=`, start vs end of Window, whole days vs elapsed time "counted from the moment of booking").

**Clash.** A Window listed as bookable is refused at payment (or vice versa); seed leaves the last day of the horizon empty; under a test that moves `clock.off` (NFR-11), the SPA's picker (browser clock) disagrees with the server (store clock). The same pattern already exists, solved once, for the Booking deadline (`booking_deadline()` in SQL, used by both slice endpoints), but AD-2's wording pushes new rules away from that pattern.

**Proposed rule (new AD-4a, amending AD-2's last sentence).** *Every time-rule value (Booking horizon, Booking deadline, Cutoffs, Release time) is a column of the `settings` row added by migration with the PRD default, and every time-rule predicate is one SQL function (`within_horizon(wid)`, `before_deadline(wid)`, `bookable(wid)`) called by both the listing query and the action; Python decides only which predicate applies and which refusal code to raise. The API returns the bookable date range computed from `app_now()`, and the SPA never uses the browser clock for a rule.*

### 5. Booking reference "retries on collision" vs "services never retry" — High

**Unit A (FR-8 reference generator, Conventions row "Ids and references").** One function in `services` "that retries on collision". The natural code is `try: INSERT … except UniqueViolation: retry`.

**Unit B (AD-3, the booking action).** "Services never retry on their own." Also, in PostgreSQL a `UniqueViolation` aborts the whole transaction, so A's loop can only work with a savepoint (`with c.transaction():`) or `ON CONFLICT DO NOTHING`. The slice's `guard()` already maps `UniqueViolation` to `409 already_exists`.

**Clash.** A session that follows AD-3 generates without retry: a rare collision answers a paying Guest `409 already_exists`. A session that follows the Convention with `except IntegrityError` inside a savepoint also swallows `CheckViolation` (`no_seat_free` is an IntegrityError) and retries a capacity refusal five times. A session that pre-checks with `SELECT` races. The seed (hole 13) and the FR-26 split (If-time 2) would each write a third version.

**Proposed rule (tighten the Convention, exempt from AD-3).** *`services.reference.new(c)` draws a candidate and claims it with `INSERT … ON CONFLICT (reference) DO NOTHING RETURNING` into the row being created, looping at most 5 times with no exception and no savepoint; it is the only retry permitted in `services`, and every creator of a Booking (Guest flow, seed, split) calls it.*

### 6. Window generation only at startup; resurrection and overlap crash — Medium-High

**Unit A (AD-18 seed).** At startup, "adds only what is missing" from today through the horizon. Implemented as `INSERT … WHERE NOT EXISTS (SELECT 1 FROM windows WHERE during = x)`.

**Unit B (FR-3 find, plus the tests of NFR-11).** A server left running for three days, or a test that moves `clock.off` forward 10 days, finds the far end of the horizon empty: AD-4's catch-up list does not include Window generation, so no request generates them.

**Unit C (FR-38, If-time 7, shape-only but the Core choice forces it).** The Administrator deletes or moves an empty seeded Window, or creates a Window of another length. At the next start, A re-creates the deleted Window (FR-38 says "v1 has no recurring schedule"), and for the moved or odd-length one the `windows_never_overlap` exclusion constraint raises inside startup: the server does not start.

**Proposed rule (tighten AD-18).** *Window generation is a catch-up effect: `services.windows.ensure_generated(c)` runs at startup and before every Window listing, under `pg_advisory_xact_lock`, generating only Venue dates after a stored high-water mark (`settings.windows_generated_through`) up to the horizon, with `INSERT … ON CONFLICT DO NOTHING` so an overlapping Administrator Window is skipped. Gaps before the mark are never refilled, so a Window an Administrator removed stays removed.*

### 7. Seed vs migration vs Administrator ownership of reference data — Medium-High

**Unit A (a Core story that needs the Seat price, FR-3/FR-6).** Adds `settings.seat_price_ore int NOT NULL DEFAULT 25000` in a migration. The migration now holds the price.

**Unit B (AD-18 seed story).** Puts prices in `seeds/venue.toml` (AD-18 lists "prices" as seed data; DR-5 wants seed data in one folder) and writes them "only if missing". The column is NOT NULL with a default, so it is never missing: editing `seeds/` has no effect, or B decides to always overwrite, which later reverts every FR-38/FR-39 change at each restart.

**Unit C (If-time 3 Whole-sauna).** Adds `saunas.price_ore` NOT NULL and fills it with an `UPDATE` in the migration, a second copy of seed values in `migrations/`. The 0001 `INSERT INTO settings DEFAULT VALUES` already sets the precedent that migrations insert data.

**Proposed rule (tighten AD-15 and AD-18).** *Migrations create structure and singleton rows only; every reference value (Saunas, Capacities, Fill order, prices, Setting values, Window schedule) comes from `seeds/`, and a new reference column is added with the seed value as its DEFAULT in the same change. The seed writes a value only where the row is absent; after first start the store owns it, so a restart never reverts an Administrator change.*

### 8. Refusal codes and status for time rules: 409 vs 422 — Medium-High

**Unit A (FR-6 booking).** Follows the slice: past deadline is `409 deadline_passed`; adds `409 outside_horizon`.

**Unit B (FR-18 validation story).** FR-18 lists "outside the Booking horizon, or past its Booking deadline" under *input validation*, and the Conventions map invalid input to `422 invalid_input` with `fields`. B validates the Window against horizon and deadline in a Pydantic validator or service pre-check and returns 422.

**Clash.** The SPA's single error type (AD-17) branches on codes; two codes and two statuses for one rule, and AD-16 names no registry. A Pydantic validator that reads the clock also breaks AD-4 (time read outside the transaction, before the lock).

**Proposed rule (tighten AD-16).** *All refusal codes, with their status and facts, are declared in one table in `api/errors.py` that the SPA mirrors; 422 is only for shape (Pydantic) errors, and every rule judged against the store or clock (horizon, deadline, capacity, Cutoff) is a 409 raised by `services` after the lock.*

### 9. Catch-up "on read" makes GETs write and lock Windows — Medium

**Unit A (FR-21 retention).** AD-4: "caught up by the next request that reads the affected row, and once at startup". So the Administrator booking list (FR-16) first runs `UPDATE bookings SET guest_name = '', email = '' WHERE …past retention`.

**Unit B (FR-16 list and the AD-2 triggers).** `a_lock_bookings` and `t_bookings` fire on *any* UPDATE of `bookings` (schema.sql lines 259 and 266), so this anonymisation locks each touched Window in scan order (not id order, contrary to AD-3) and recomputes it. A read-only Administrator page now takes Window locks and can deadlock with Guest bookings, and it must call `lock_windows` first to satisfy AD-3. A second session, reading AD-4 the other way, does retention only at startup, and the test "move the clock 13 months, the list shows no name" passes only in one of the two builds.

**Proposed rule (tighten AD-4 and AD-2).** *A due effect is evaluated as a condition by the read (for example the list masks a Guest past retention in SQL), so GET endpoints never write; it is materialised only at startup or by a write that touches the row, through one `services.catchup` function per effect. The `bookings` triggers fire only on `INSERT`, `DELETE` and `UPDATE OF window_id, seats, status`, so updates that do not change capacity never lock a Window.*

### 10. Two migrations with the same number; slice databases — Medium

Two parallel sessions (for example FR-6 adding Booking columns and FR-15 adding `sessions`) each create the next free number, `0002_booking_fields.sql` and `0002_sessions.sql`. AD-15 does not say whether the runner records the number or the file name: by number, the second file is silently skipped; by name, the order between them is arbitrary. Also, existing `booking` dev databases were built by the slice's `db.migrate()` and have no `schema_migrations`, so a runner that starts at 0001 fails on `CREATE TABLE clock`.

**Proposed rule (tighten AD-15).** *The runner records full file names, refuses to start if two files share a number, and treats a database that has `windows` but no `schema_migrations` as having 0001 applied; a story takes its migration number when it merges (renumbering on rebase), never when it starts.*

### 11. `sign_in_failures` with an FK to `accounts` — Medium

The ER diagram draws `accounts ||--o{ sign_in_failures : "by email"`. A session that implements the diagram adds an FK, which cannot record failures for unknown emails, while AD-11 requires counting "known or not". Counting failure rows per request also lets 20 parallel wrong guesses all read "4 failures" and proceed, so PW-6 fails under a parallel test.

**Proposed rule (tighten AD-11).** *Failures live in `sign_in_throttle(email_lower PRIMARY KEY, failures, locked_until)` with no FK; each sign-in first upserts and locks that row (`… FOR UPDATE`), then decides, so attempts for one email are serialised. The ER line is removed.*

### 12. Terms text and emailed link paths owned twice — Medium

FR-5 (review page) and FR-8 (page *and* email) both show the booking terms. AD-16 puts page text in the SPA; AD-12 puts email text in `services`. The two stories write two copies of the terms, which drift. The same for link paths: the confirmation email links to "Before you come" (`/#before-you-come` built by `services` from the base URL) while the SPA story names the anchor `#before-you-come-section`.

**Proposed rule (tighten AD-12/AD-16).** *Text that appears in both a page and an email (the booking terms, "what happens next") lives once in `content/` and is read by both the SPA build and `services`; every path or anchor that `services` puts in an email is a constant in `config.links`, and an end-to-end test opens each emailed link in the SPA.*

### 13. Seeded sample Bookings (DR-2) have no path — Medium

DR-2 requires "the seeded sample Bookings" in the README, but AD-18 lists only Saunas, Fill order, prices, schedule and the Administrator. The README story adds them as raw SQL in `seeds/`: no reference (hole 5), no payment row, no Outbox email, and "adding only what is missing" has no natural key for a Booking, so every restart adds more (and changes Seats left). Another session routes them through `services.booking.create`, which needs a session and an idempotency key.

**Proposed rule (extend AD-18).** *Sample Bookings are created by the seed through `services.booking.create` under one fixed seed session, each with a fixed idempotency key, so a rerun is a no-op (AD-9) and every sample has a reference, a payment row and an Outbox email like a real Booking.*

### 14. "Total paid" stored twice — Low-Medium

AD-13: "A Booking stores the price per Seat and the total it was charged", and `payments` records the charge. The FR-16 list story reads `payments.amount_ore`; the FR-8 story reads `bookings.total_ore`. Equal in the Core; different as soon as a Voucher pays part (FR-28) or a partial move splits a Booking (FR-26).

**Proposed rule (tighten AD-13).** *`bookings.total_ore` is the Booking's value and is what every page and email shows as "total paid"; `payments` rows record how it was funded (one row per part) and are read only by refunds and the payment audit.*

### 15. Venue date by implicit cast — Low-Medium

FR-3 (`?date=YYYY-MM-DD`) and FR-16 (list a date) both select Windows of a Venue date. One session writes `lower(during)::date = %s`, which uses the connection's `TimeZone` (UTC in the Docker image); the other writes `(lower(during) AT TIME ZONE venue_tz)::date`. AD-4 says Venue-time arithmetic uses `settings.venue_tz`, but an implicit cast does not look like arithmetic. Windows near midnight land on different dates in the two lists.

**Proposed rule (tighten AD-4).** *A Window's Venue date comes only from the SQL function `venue_date(wid)` (or an equivalent generated column); a cast of a `timestamptz` to `date` or `time` without `AT TIME ZONE` is forbidden, and the pool sets `TimeZone = 'UTC'` explicitly so the mistake is visible in tests.*

### 16. Personal data copied into the Outbox and idempotency outcomes — Low-Medium

FR-21 anonymises names and emails after the retention period. AD-12 stores emails "exactly as sent" (name, address, reference); a session following hole 1's "store the response" stores the same data in `idempotency_keys`. The retention story anonymises `bookings` only.

**Proposed rule (extend AD-12 and AD-9).** *The retention catch-up also removes the recipient and body of every Outbox email linked to an anonymised Booking (via `booking_id`, hole 3), and idempotency rows hold no personal data (only ids), so `bookings` and `outbox_emails` are the only places retention must touch.*

### 17. Sign-in rotates the session row and orphans Holds and confirmations — Low (Core)

AD-3 lists "session change" as part of an action; AD-8 says nothing about rotation. The Core FR-15 session builds the standard "delete the anonymous row, insert a new signed-in row" on sign-in. FR-37 puts the sign-in choice *after* **Book**, so with Holds (If-time 5) the Guest's Hold and any confirmation tied to the old row are lost at sign-in.

**Proposed rule (tighten AD-8).** *Sign-in, sign-up and privilege change rotate the token (new token, new hash) on the same `sessions` row and set its role and account; the row id, which Holds, Bookings and keys reference, never changes until sign-out deletes it.*

### 18. `payment = "hold"` vs no lock across a wait — Low (Core)

AD-14 reserves `payment = "hold"` for FR-36 (hold the payment until the Hold has expired). With a synchronous `charge()` inside the locked transaction (AD-13), the only way to "hold" is to wait inside it, which AD-3 forbids; a session that implements it as `sleep` blocks the Window for everyone, and tests "never wait in real time" (NFR-11).

**Proposed rule (tighten AD-14).** *`payment = "hold"` makes `charge()` raise `PaymentPending` before anything is written, so the action returns `409 payment_pending` and stores nothing; the test then moves the clock and resubmits with the same key, which runs the FR-36 path.*

### 19. `force_conflict` hits startup and reads — Low

AD-14 puts `force_conflict` in `db.run`, and every `db.run` honours it. If the seed or catch-up uses `db.run`, a server started with the switch on cannot start (startup writes and conflicts five times).

**Proposed rule (tighten AD-14).** *`force_conflict` applies only to `db.run` calls made for an HTTP request (`db.run(work, request=True)`), never to migrations, seed or startup catch-up.*

### 20. "No lock is held across anything but SQL" — Low

Formatting the confirmation email, generating the reference and reading the payment switch are Python steps inside the locked transaction, so AD-3 read literally cannot be met, and a strict session moves email building before the lock, where the reference does not yet exist.

**Proposed rule (reword AD-3).** *No lock is held across waits: network calls, sleeps, password hashing or anything outside this process; in-process computation on data already read is allowed.*

---

## Seams that held

These were attacked and did not yield a letter-compliant divergence worth recording:

- **Two writers of capacity.** AD-2's three-part rule plus the bypass test makes a second capacity path fail its own test.
- **Lock order between Window actions.** `lock_windows` sorts ids in SQL, and the Block and settings triggers also lock in id order; mixed orders only arise through hole 9 (triggers on non-capacity updates) and are retried by `db.run`.
- **Seats left computed twice.** AD-5 names the three SQL functions; a Python recomputation is visibly non-compliant.
- **Placement stored by one story and derived by another.** AD-6 is explicit.
- **Administrator endpoints outside the guarded router.** AD-10 makes it a path rule that a test can enumerate.

## Recommended order of fixes

Holes 1, 2, 3 and 5 all meet in the first Core booking story (FR-6/FR-8) and should be settled in the spine before that story starts. Hole 4 should be settled before FR-2/FR-3. Holes 6, 7 and 10 before the seed and migration runner story. The rest can be added as the stories that touch them are planned.
