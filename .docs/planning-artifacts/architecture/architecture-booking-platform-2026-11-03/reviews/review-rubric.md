---
review-of: ARCHITECTURE-SPINE.md (architecture-booking-platform-2026-11-03, status draft)
lens: good-spine rubric (build substrate, altitude feature)
reviewed: 2026-11-03
inputs: ARCHITECTURE-SPINE.md, .memlog.md, src/booking_platform/{app.py,db.py,schema.sql,__init__.py}, tests/*, README.md, docker-compose.yml, pyproject.toml, .gitignore, PRD §5, §10.3 (+ FR-2, FR-7, FR-36, FR-39 for checks)
spine-edited: no
---

# Review: Architecture Spine against the good-spine rubric

## Verdict

The spine is strong on the hard part (the store-enforced capacity kernel, lock order, store clock, derived Placement) and ratifies the slice's schema faithfully. It is **not yet ready to build stories from**. Four high findings would let independently built stories diverge or break the existing proof: (1) no carry-over rule for the slice and its 42 tests, (2) refusals that must persist something are rolled back under AD-1 and AD-3 as written, (3) AD-9 does not actually stop a concurrent double submit, (4) the configuration side of the operational envelope is undecided. All are cheap to fix with a sentence or two each. No critical findings.

## Findings at a glance

| ID | Sev | Area | Finding |
| --- | --- | --- | --- |
| F1 | high | Brownfield | No carry-over rule for the slice API and its tests; several ADs and conventions break them silently |
| F2 | high | Rule enforceability | A refusal raised inside `work` rolls back the rows the refusal must keep (sign-in failures, stored outcomes) |
| F3 | high | Rule enforceability | AD-9 does not prevent concurrent double submits, and failed-payment retry semantics are undefined |
| F4 | high | Operational envelope | Configuration undecided: env-var convention, base URL, HTTPS switch, and where Venue rules (Booking horizon) live |
| F5 | medium | Spine vs decision log | CSRF decision and FR-14 trigger test dropped; "to confirm" ADs presented as binding |
| F6 | medium | Missing divergence point | The refusal pipeline (psycopg error to domain refusal to HTTP) has no owner |
| F7 | medium | Internal contradiction | AD-14 puts a test switch in `db.run`, but AD-1 and the diagram say `db` imports nothing above it |
| F8 | medium | Brownfield | AD-3 "lock before first write" for every action contradicts the slice's trigger-only locking for single-statement writes |
| F9 | medium | Brownfield | AD-2 "not duplicated in SQL" contradicts existing SQL rules (Booking deadline, Hold length, Release time) |
| F10 | medium | Rule enforceability | AD-13/AD-14 `payment = "hold"` must wait inside a transaction that holds Window locks, against AD-3 |
| F11 | medium | Missing divergence point | AD-4 catch-up has no named seam; which request catches up what is left to each story |
| F12 | medium | Missing divergence point | AD-8 session lifecycle: when a session is created, token rotation at sign-in, expiry of anonymous sessions |
| F13 | medium | Operational envelope | `uv run pytest` browser tests run against a `dist/` that nothing builds; stale or missing frontend undetected |
| F14 | low | Brownfield | Migration runner transition for a dev database the old `migrate()` already installed |
| F15 | low | Brownfield | AD-7 status/entry_time: `window_booked_seats()` must filter active; `entry_time` vs existing `created_at` |
| F16 | low | Operational envelope | SPA fallback vs `/health` and unknown `/api/*` paths |
| F17 | low | Missing divergence point | Error-code registry, optional `message`, success-response shape |
| F18 | low | Operational envelope | Seed details: "today" on which clock, seed in the test database, Administrator seed credentials |
| F19 | low | Deferred | Voucher balances deferred although If-time 2 gets an epic this round; no amend trigger |
| F20 | low | Brownfield | Test conventions ignore the existing mutation harness (`BP_TEST_MUTATE`) and file names |
| F21 | low | Coverage | NFR-8 dependency audit and the single-process assumption not recorded |
| F22 | low | Consistency | SPA hard-codes `Europe/Oslo` while the store has `settings.venue_tz` |
| F23 | low | Diagrams | Mermaid syntax valid; two semantic mismatches (config arrow, `sign_in_failures` to `accounts`) |
| F24 | low | Bloat | If-time 7 ordering and PRD numbers restated as invariants |

---

## High

### F1 (high). No carry-over rule for the slice and its tests

**Evidence.** The slice exposes `/windows`, `/holds`, `/bookings`, `/whole-bookings`, `/blocks`, `/marks`, `/settings`, `/health` with no `/api` prefix, open Administrator endpoints, a client-supplied `session_id` in bodies, `seats` limited to `le=44`, and `db.migrate()` returning True on a fresh database (`app.py:105-145`, `conftest.py:78,94`). The 42 tests that prove FR-10/11/12/14/35/36/41 call those exact paths and bodies, including `seats=44` and `seats=40` (`test_application_rules.py:52,59,61`, `test_fr14_retry.py:128`). The spine changes every one of these: `/api/` prefix (Naming), `/api/admin/` behind a session (AD-10), server-side session (AD-8, the only change it names), Seats 1–10 (Input), the migration runner (AD-15) and the SPA catch-all (Structural Seed). It never says the slice tests must be migrated, by which story, or how a test fills a 44-Seat Window when one Booking may hold only 10 Seats. The first story that applies AD-10 or the Input convention will turn the FR-10 proof red, and the next story may "fix" it by loosening the rule.

**Fix.** Add one AD: "The slice is reshaped by the first skeleton story; its tests are kept as regression proof, moved to `/api` paths, signed in as Administrator through a test fixture, and fill Windows with several ≤10-Seat Bookings or raw inserts; no rule is loosened to keep a slice test green."

### F2 (high). Refusals that must persist are rolled back

**Evidence.** AD-1 says services "raise domain refusals that `api` maps". AD-3 says every action runs inside exactly one `db.run(work)`, and `db.run` rolls back on any exception (`db.py:68`). AD-11 requires a failed sign-in to write a failure row and still answer 401. AD-9 requires the stored outcome to survive. A story that follows AD-1 and AD-3 literally raises the refusal inside `work`, which rolls back the failure row, so the throttle never trips. That is exactly the divergence AD-11 says it prevents.

**Fix.** Add to AD-3: "A refusal that must keep a record returns a result from `work` (the transaction commits) and is raised after `db.run` returns; only refusals that write nothing may be raised inside `work`."

### F3 (high). AD-9 does not prevent a concurrent double submit

**Evidence.** The rule stores (key, session, outcome) but says nothing about a UNIQUE constraint or about when the key is read relative to `lock_windows`. If two submits with the same key arrive together and the lookup runs before the lock, both miss. Then either two Bookings are created (no UNIQUE), or the second hits a UniqueViolation that the slice's `refusal()` maps to `409 already_exists` (`app.py:57`). The paying Guest then sees an error, which is the outcome AD-9 says it prevents. The rule is also silent on failures: FR-7 says a failed payment "offers a way to try again". If the failure is a stored outcome, retrying with the same key returns the failure forever. If it is not stored, the SPA and the service must agree that the retry reuses the key. Two stories (SPA review page, payment service) will choose differently.

**Fix.** Add to AD-9: "`idempotency_keys` has UNIQUE(key); the lookup runs after `lock_windows`; only success outcomes are stored; after a refusal or failed payment the SPA keeps the same key for the retry."

### F4 (high). Operational envelope: configuration is undecided

**Evidence.** The Structural Seed lists `config.py # settings + frozen test switches`, but the spine never states where settings come from. The code already uses env vars with a `BP_` prefix and defaults (`BP_DATABASE_URL` in `db.py:27` and the README, `BP_TEST_ADMIN_URL` and `BP_TEST_MUTATE` in `conftest.py`), and the spine ignores that convention. Several values need a home that no AD gives them:
- the email base URL (AD-12);
- the HTTPS / `Secure` cookie switch (AD-8, and "one switch" under Deferred);
- the port and host (hard-coded `127.0.0.1:8000` in `app.py:273`).

Worst of all, the Booking horizon is a Venue rule that FR-39 makes Administrator-editable ("never more than 1 month"), and AD-18 needs it to generate Windows. The store already keeps the other Venue rules in the `settings` table (`booking_deadline_minutes`, `release_*`, `venue_tz`). Without a rule, the seed story and the booking story can read the horizon from two different places (a `config.py` constant and a column). The two homes also share the name "settings" (Python `config.settings` and SQL `settings`), which invites that confusion.

**Fix.** Add a Configuration row or AD: "Deployment config (database URL, base URL, HTTPS on/off, port) comes from `BP_*` env vars with local defaults, read only in `config.py`; Venue rules (Booking horizon, Booking deadline, Release time, `venue_tz`) live only in the `settings` table, Booking horizon added in the Core."

---

## Medium

### F5 (medium). The spine has drifted from its decision log

**Evidence.** The memlog decides "CSRF: same origin + SameSite=Strict + JSON body required on every state-changing request; no CSRF tokens" (`.memlog.md:31`). The spine has no such rule, so a story could accept form-encoded POSTs. The memlog also decides "Existing trigger-based FR-14 test stays beside it" (`.memlog.md:33`), and the spine is silent on it. AD-10, AD-12, AD-13, AD-16, AD-17 and AD-19, together with retention-at-startup, the Crockford reference and the envelope, are logged as "Derived in distill, to confirm with Lisa" (`.memlog.md:37-38`). Yet they appear as binding with no marker, while only AD-1 to AD-6 carry `[ADOPTED]`. The spine has no Open Questions section, so nothing shows what is still unconfirmed.

**Fix.** Add the CSRF rule to AD-8 (or as its own AD), note the retained trigger test under AD-14, and tag AD-7 to AD-19 as `[ADOPTED]` or `[PROPOSED]` with an Open Questions list for the unconfirmed ones.

### F6 (medium). The refusal pipeline has no owner

**Evidence.** Today `api` catches psycopg `CheckViolation`/`UniqueViolation` and maps constraint names to codes (`app.py:51-67`). AD-1 forbids `api` from knowing SQL and requires services to raise "domain refusals", but no rule names the refusal type or says which layer translates store errors. Each story will invent its own exception class and its own constraint-name mapping.

**Fix.** Add to AD-1/AD-16: "`db` translates store refusals (by constraint name) into one `Refused(code, **facts)` exception defined in `services`; `api/errors.py` holds the single code→status table."

### F7 (medium). AD-14 contradicts AD-1 and the paradigm diagram

**Evidence.** AD-1: "`db` imports nothing above it", and the diagram shows only `services` reading config. AD-14: `db.run` reads `force_conflict`.

**Fix.** Declare `config` a leaf module importable by every layer (and draw the arrow from `db` too), or have `services` pass the switch into `db.run`.

### F8 (medium). AD-3 overgeneralises the existing lock convention

**Evidence.** `db.lock_windows` is documented "before the first write of a multi-statement unit" (`db.py:77`). The slice's single-statement writes (`POST /blocks`, `DELETE /blocks/{id}`, `DELETE /marks`, `DELETE /holds`) rely on the BEFORE triggers (`a_lock_*`) instead. AD-3 says every action calls `lock_windows` first, and for a Block that means computing the overlapping Windows in Python. The spine neither ratifies the slice nor says it must change.

**Fix.** Add to AD-3: "A single-statement write may rely on the BEFORE lock triggers; any action with more than one statement, or one that reads before it writes, calls `lock_windows` first."

### F9 (medium). AD-2's "not duplicated in SQL" contradicts the existing schema

**Evidence.** The schema already enforces or computes non-capacity rules: `booking_deadline()` and its use in Hold expiry, the `hold_at_most_10_min` CHECK, `CHECK (booking_deadline_minutes <= 45)`, `trg_check_release`. AD-4 also requires time rules to read `app_now()` inside the transaction, which needs SQL. A story following AD-2 could delete these defences, or refuse to add a needed helper.

**Fix.** Reword: "Non-capacity rules are decided and refused in `services`; SQL helpers that compute them and defensive CHECKs already in `0001` stay and may be added."

### F10 (medium). The `payment = "hold"` seam conflicts with AD-3

**Evidence.** FR-36 says the switch "holds the Simulated payment until after the Hold has expired". AD-13 puts `charge` inside the Booking's transaction, and AD-3 says "no lock is held across anything but SQL". Implemented naively, the charge waits while the Window lock is held, which serialises the parallel FR-36 test and breaks AD-3. Nothing says when in the action `charge` decides its outcome.

**Fix.** Add to AD-13: "`charge` decides its outcome (including any `hold` wait) before `lock_windows`; the payment row is written after the lock in the same transaction."

### F11 (medium). AD-4 catch-up has no named seam

**Evidence.** "Caught up by the next request that reads the affected row, and once at startup" covers releases (already done inside `recompute_window`). For retention anonymisation (FR-21), default refunds and Window generation it leaves each story to choose which request triggers what. The memlog makes retention startup-only, so a test that moves `clock.off` cannot see it without restarting the server.

**Fix.** Add: "Catch-up lives in one `services.catch_up(c)` called at startup and at the start of named reads (Window list, Administrator booking list); each due effect registers there."

### F12 (medium). AD-8 leaves the session lifecycle open

**Evidence.** AD-8 fixes storage, but not:
- when an anonymous session row is created (on first page load, which adds a row per visitor, or lazily on the first Hold or Booking);
- whether sign-in rotates the token (session fixation);
- how long anonymous sessions live and when they are purged (they link to Bookings with personal data, FR-21);
- the FK behaviour of `bookings → sessions` when a session is deleted, given that AD-7 never deletes Bookings.

The Hold, Booking and sign-in stories will each choose.

**Fix.** Add: "A session row is created lazily on the first state-changing request; sign-in issues a new token and deletes the old row; anonymous sessions expire after N h and are purged by catch-up; Booking→session FK is `ON DELETE SET NULL`."

### F13 (medium). Browser tests may run against a stale frontend

**Evidence.** The test environment uses "built `dist/`, served by the backend", and `dist/` is git-ignored (`.gitignore`). NFR-6 requires "all tests run with one command", but nothing in `uv run pytest` builds the frontend. E2E and axe tests can pass against an old build, or fail confusingly on a fresh clone.

**Fix.** Add to the environment table: "The pytest session fixture runs `npm run build` (or fails when `frontend/dist` is missing or older than `frontend/src`)."

---

## Low

### F14 (low). Migration runner transition
**Evidence.** Today's `migrate()` installs `schema.sql` when `windows` is missing and records nothing. On the existing dev database, the new runner (AD-15) will try `0001` again and fail on existing tables.
**Fix.** Add to AD-15: "If `windows` exists and `schema_migrations` does not, the runner records `0001` as applied (or the README says `docker compose down -v` once)."

### F15 (low). AD-7 against the existing booked-seat function
**Evidence.** `window_booked_seats()` sums all `bookings` (`schema.sql:83-85`), and `created_at` already exists. AD-7 adds `status` and `entry_time` but does not say that the function must filter `status = 'active'`, or whether `entry_time` is a new column or the existing `created_at`.
**Fix.** State: "Migration 0002 adds `status`, makes `window_booked_seats()` count only active rows, and `entry_time` is `created_at` renamed (or a separate column, with the reason)."

### F16 (low). SPA fallback against `/health` and `/api/*`
**Evidence.** The harness polls `/health` (`conftest.py:94`). "Everything else to the SPA" would serve `index.html` for `/health`, and for a misspelt `/api/...` path.
**Fix.** State: "`/health` moves to `/api/health`; any unknown `/api/*` path returns the JSON 404 envelope, never the SPA."

### F17 (low). Error codes and response shapes
**Evidence.** The slice returns envelopes without `message` (`no_such_window`, `try_again`) and uses codes (`no_seat_free`, `deadline_passed`, `release_after_deadline`, `empty_period`, `already_exists`, `rule_refused`) that are not listed anywhere. The success shape (bare objects such as `{"booking_id": …}`) is not fixed. Generic `refused` puts `str(e)` (store text) into `message`.
**Fix.** Say "`message` optional; codes listed once in `api/errors.py`, starting with the slice's; success bodies are bare JSON objects; store text never goes into `message`."

### F18 (low). Seed details
**Evidence.** AD-18 generates Windows "from today", but does not say on which clock (AD-4 implies `app_now()`). It also does not say whether the seed runs in `booking_test` (the `world` fixture truncates afterwards; accounts are not truncated), or where the seeded Administrator's password comes from (a committed seed means a published password, which must pass FR-19 and be documented in the README).
**Fix.** Add: "'Today' is the Venue date of `app_now()`; the seed runs in every environment; the seeded Administrator's credentials are documented in the README."

### F19 (low). Deferred voucher balances
**Evidence.** PRD §10.3 gives If-time 2 an epic in this round. Voucher balances and the Change history row are deferred "until If-time 2 is planned", with no trigger to amend the spine before those stories are written.
**Fix.** Add to Deferred: "The spine is amended (Voucher balance AD, Manage-link AD) before the first If-time 2 story is written."

### F20 (low). Existing test conventions not ratified
**Evidence.** The harness has a mutation check (`BP_TEST_MUTATE`) that proves each store protection bites. AD-2 asks for a bypass test for each new capacity table, but not for a mutation entry. Existing file names (`test_fr10_bypass.py`, `test_fr14_retry.py`) follow `test_fr<NN>_<topic>.py`, not `test_<area>.py`.
**Fix.** Add to Tests: "Every new store protection gets a `MUTATIONS` entry; file names follow `tests/test_fr<NN>_<topic>.py` (or name the existing files as the pattern)."

### F21 (low). Two operational items missing
**Evidence.** NFR-8 (dependency audit at the freeze) is neither decided nor deferred. The design silently assumes one process: catch-up at startup, test switches frozen in memory. Nothing forbids `--workers`.
**Fix.** Add "NFR-8: `uv run pip-audit` and `npm audit` at the freeze" and "one uvicorn process; no `--workers`".

### F22 (low). Two sources for the Venue time zone
**Evidence.** The Time convention hard-codes `Europe/Oslo` in the SPA, while AD-4 uses `settings.venue_tz`.
**Fix.** State "`venue_tz` is fixed to `Europe/Oslo`" or "the API sends the Venue time zone and the SPA uses it."

### F23 (low). Diagrams
**Evidence.** All three mermaid blocks parse: quoted labels protect `:` and `/`, the `[( )]` cylinder syntax and `}o--o|` / `||--||` cardinalities are valid, and nested subgraphs are fine. There are two semantic mismatches:
1. The paradigm flowchart shows only `services` reading config, which contradicts AD-14 (see F7).
2. The ER diagram draws `accounts ||--o{ sign_in_failures`, but AD-11 keys failures by email "known or not", so there is no FK to `accounts`.

The ER diagram also omits `releases`, `settings`, `clock` and `schema_migrations`, which is acceptable as a sketch.
**Fix.** Add the `db → config` arrow (or move the seam) and draw `sign_in_failures` unattached, keyed by email.

### F24 (low). Bloat
**Evidence.** These sentences are story-level or restate the PRD, not invariants:
- AD-7's make-room order ("ends Holds newest first, then cancels Seat bookings by latest `entry_time`") is If-time 7 behaviour; the Core invariant is only status, entry time and never deleting.
- AD-11's "5 failures / 15 minutes" and "rehash at sign-in", and AD-8's "8 h sliding", repeat PW-1 to PW-6 and FR-15.
- The Accessibility row repeats FR-23.

Rationale is otherwise kept out well.
**Fix.** Cut the numbers to "per PRD FR-15/PW-6", and move the make-room order to the If-time 7 epic, leaving "make room first, in the same transaction".

---

## Rubric scorecard

| Criterion | Result | Notes |
| --- | --- | --- |
| Fixes the real divergence points, misses none | Partial | Strong on capacity, locking, time, Placement, money, email, client module. Missing: refusal pipeline (F6), session lifecycle (F12), catch-up seam (F11), config home (F4), CSRF (F5) |
| Every Rule enforceable and actually prevents its divergence | Partial | AD-9 (F3), AD-11 via AD-1/AD-3 (F2), AD-13 hold seam (F10) do not hold as written; the others are checkable in review or by test |
| Nothing under Deferred lets two units diverge | Mostly | Deferred items are all later phases or out of scope. Voucher balances need an amend trigger (F19) |
| Ratifies, not contradicts, the brownfield code | Partial | Schema, `db.run`, `lock_windows`, `app_now()`, `clock.off`, `seats_left()` and the envelope are ratified well. Contradictions without a change note: F1, F8, F9, F14, F15, F16; ignored conventions: `BP_*` env vars (F4), mutation harness (F20) |
| Every owned dimension decided, deferred or open | Partial | Deployment and environments are decided (table plus seed diagram). Configuration (F4), test build step (F13), audit and process model (F21) are missing. There is no Open Questions section (F5) |
| Mermaid valid | Yes | Two semantic mismatches (F23) |
| No bloat | Mostly | Minor PRD restatement and If-time 7 detail (F24) |

## What is already right (keep)

- AD-2 and AD-6 ratify exactly what addendum A and the 168/168 spikes proved, including the three-part pattern any new capacity table needs. This is the most valuable rule in the document.
- AD-4 matches NFR-11 and the existing `app_now()` / `clock.off` harness one to one.
- AD-15's "0001 is the slice's schema, moved unchanged" protects the proof.
- AD-5 is already true in the slice (`seats_left()` in `GET /windows`).
- The altitude matches PRD §10.3: Core decided in full, later phases only where the Core would otherwise need a rewrite, and Manage links deferred to If-time 2 as the PRD says.
- The environment table covers dev, test and examiner, and matches the README, `docker-compose.yml` (postgres:18, 55432) and NFR-1.
