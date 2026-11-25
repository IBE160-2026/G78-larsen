---
stepsCompleted: [step-01-validate-prerequisites, step-02-design-epics, step-03-create-stories, step-04-final-validation]
inputDocuments:
  - .docs/planning-artifacts/prds/prd-booking-platform-2026-10-29/prd.md
  - .docs/planning-artifacts/prds/prd-booking-platform-2026-10-29/addendum.md
  - .docs/planning-artifacts/prds/prd-booking-platform-2026-10-29/appendix-fr-34-51.md (only where the PRD lacks it, and to list FR-34 to FR-51 as not planned)
  - .docs/planning-artifacts/architecture/architecture-booking-platform-2026-11-03/ARCHITECTURE-SPINE.md
  - .docs/planning-artifacts/architecture/technology.md (only where it adds to the spine)
  - .docs/planning-artifacts/ux-designs/ux-booking-platform-2026-11-05/DESIGN.md
  - .docs/planning-artifacts/ux-designs/ux-booking-platform-2026-11-05/EXPERIENCE.md
  - .docs/sensorveiledning-kravsporing.md
  - .docs/planning-artifacts/backcasting-2026-11-01.md (sizing only)
  - review reports under prds/, architecture/*/reviews/ and ux-designs/ (only for findings not carried into the final documents)
---

# Saunalöyly Booking Platform - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for the Saunalöyly Booking Platform, decomposing the requirements from the PRD, the UX design contract (DESIGN.md and EXPERIENCE.md) and the architecture spine into implementable stories.

The PRD, the spine and the UX spines stay the source of truth. Each requirement below is a short handle on the full text; a story names the FR consequences (FR-40.1 style, or the bullet) and the AD numbers it delivers, and the developer reads the source for the detail.

**Build process (Lisa, 2026-11-19).** These choices apply to every epic and story:

- **Vertical slices.** Each epic, and as far as possible each story, delivers one piece of user value through every layer it needs: migration, `db`, `services`, `api`, frontend page and tests. Code for one feature stays in that feature's own modules (one `services/<feature>.py`, one `api` router file, one route folder in `frontend/app/`), so a slice can be read, reviewed and reverted on its own.
- **DRY through shared folders.** Anything a second slice needs is moved to, or created in, a shared home instead of being copied: backend `src/booking_platform/{config.py, db/, services/errors.py, services/outbox.py, services/reference.py …}` and `api/errors.py`; frontend `frontend/components/` (shared UI components), `frontend/lib/` (`api.js`, `server-api.js`, formatting helpers), `frontend/app/styles.css` (the one stylesheet) and `content/` (text shared by pages and emails). Tests share `tests/conftest.py`, `tests/client.py` and `tests/e2e/conftest.py`.
- **Tests in every story.** Each story's acceptance criteria include its tests, run by `uv run pytest` (NFR-6). There is no separate test epic.
- **Lisa takes part in each story.** Stories are built one at a time with `bmad-build` in interactive sessions, with Lisa reviewing as the work goes, rather than in one autonomous `/goal` run. PRD §10, §10.1 and §10.3 were updated to match on 2026-11-19. Stories are therefore sized for one interactive session each.
- **Traceability.** One branch and one pull request per story, with FR numbers in the commit messages (architecture Conventions, examiner criterion 1). Branches are named `story/<epic>-<story>-<short-name>`, for example `story/1-1-backend-structure` (Lisa, 2026-11-20). Lisa merges each pull request herself once the story's tests are green and she has reviewed it, with a normal merge commit (not squash) so the FR-numbered commits stay in `main`; the next story branches from the updated `main`.

## Requirements Inventory

### Functional Requirements

*Planned in this round: FR-1 to FR-33 (Core FR-1 to FR-23; If-time 1 to 3 FR-24 to FR-33). Floor: FR-1 to FR-24.*

**§4.1 Find a Window (Core)**

- **FR-1: Landing page.** A Guest opens the website without signing in and starts a Seat booking in one step. FR-1.1 Venue name and a short description that names no number of Saunas and does not say they are shared. FR-1.2 The **Book seats** action opens date and Seat selection directly. FR-1.3 Links to Terms and Privacy notice. FR-1.4 A directly linkable "Before you come" section: what to bring, safety, practical. FR-1.5 Saunas as places to visit, one image and one line each, never suggesting that a Seat booking chooses one. FR-1.6 Opening hours and the Window schedule (the schedule lives on Book seats, EXPERIENCE.md Content Homes). FR-1.7 Price per Seat (and per Sauna once §4.9 exists). FR-1.8 Fictional address and contact details that cannot reach anyone.
- **FR-2: Date and number of Seats.** A Guest chooses a date and 1 to 10 Seats. A date can be chosen only if it has a Window inside the Booking horizon and before its Booking deadline. The date can be typed or picked and works with the keyboard alone. A Seat number outside 1–10 cannot be submitted, and the server rejects it.
- **FR-3: Windows with Seats left.** For the chosen date and number, every bookable Window is listed with start, end and Seats left, plus one total. Seats left = Seat capacity − Seats booked and equals the Administrator list. A Window with too few Seats is unavailable and says so in text ("1 seat left"). No room on the date → up to three nearest Windows with room, same day first, then the following days within the horizon. A Window past its Booking deadline is not offered. No urgency cues. The total is shown once, equals Seats × price per Seat in NOK incl. VAT, and is the amount charged.
- **FR-4: Seats, not Saunas.** No page or email in the Seat flow shows a Sauna identifier. The flow says in plain words that the Guest books Seats in the shared Saunas and may move freely between those open for Seats (and, once §4.9 exists, that a group should book a Private sauna).

**§4.2 Book and pay for Seats (Core)**

- **FR-5: Guest details and review.** Name (1–100 characters) and email (valid, ≤ 254) only. Details and Review are two pages. Review shows the Window, Seats, total in NOK incl. VAT, name and email, Venue identity and contact, and the booking terms (no right of withdrawal for a fixed date; what can be changed; Guest chooses refund or Voucher if Saunalöyly cancels). Until §4.8 the terms say a Booking cannot be changed or refunded. Terms must be accepted before paying; links to Terms and Privacy notice; going back keeps everything entered.
- **FR-6: Simulated payment creates the Booking.** The pay button states obligation and amount ("Pay NOK 500"). No payment credentials or external service. "Simulated payment: no money moves" on the pay step and in every email that mentions a payment. Seats left drops by exactly the Seats booked. The charge is recorded in the same atomic step as the Booking. A one-time key per review: a repeat never creates a second Booking or charge and returns the first outcome. Back from Confirmation never reaches a page that can pay again.
- **FR-7: Failed payment.** A test switch can force failure. A failed payment creates no Booking, takes no Seats and sends no email; the Guest can try again.
- **FR-8: Confirmation page and email.** Both show the Booking reference, date and Window, Seats and total paid, the Guest's email, Venue identity and contact, what happens next (the reception sentence), the booking terms and a link to "Before you come". The email is stored in the Outbox and shown on the page as sent. The page opens only in the paying browser session (reload works there). No Manage link in the Core. The reference alone opens nothing.
- **FR-9: One Window per Booking.** A request for Seats in more than one Window is rejected as invalid input.

**§4.3 Capacity integrity under concurrency (Core)**

- **FR-10: Never exceed capacity.** N parallel requests never get more Seats than are left; Seats left never goes below zero. In every phase the data store refuses an over-capacity write even when the application is bypassed (a bypass test writes around the API).
- **FR-11: The last-Seat race has exactly one winner.** Two parallel requests for the last Seat create exactly one Booking; Seats left becomes 0; the loser is told no Seat is free, is not charged, gets no email and holds nothing, and is offered the nearest Windows (CT-2, CT-3). The race test runs in every test run, 100 repetitions, against real PostgreSQL.
- **FR-12: All or nothing.** A request for more Seats than are left is rejected whole (A6: 42 of 44 booked, 3 requested; A7: 44 booked, 1 requested). The message states the true Seats left and offers the nearest Windows.
- **FR-13: Windows are Venue-wide and never overlap.** Overlapping (partial, identical, nested) Windows are rejected in seed and Administrator input; back-to-back Windows are accepted (E1, E2). The seed generates Windows from the run date through the Booking horizon on the eight-a-day schedule; a rerun adds only missing Windows. Partial unavailability is a Block, never another Window (E3). Windows are independent (E2, E4, E6).
- **FR-14: Temporary conflicts end cleanly.** Bounded retries; "No seat free" (definite loss) and "please try again" (retries used up) are different messages; either leaves no Booking, charge, email or partial data; a test switch can force every attempt to conflict.

**§4.4 Administrator sign-in, booking list and Outbox (Core)**

- **FR-15: Administrator sign-in and sign-out.** A seeded Administrator exists and the README documents its login. Accounts and password changes only through the seed or a documented command, both applying FR-19; the API never returns a password. Wrong email and wrong password give the same message (PW-5). After 5 failed sign-ins in a row for one email, that email is refused for 15 minutes, also with the right password; success resets the count; the same applies to unknown emails with the same message (PW-6). After sign-out the session grants nothing.
- **FR-16: Booking list.** A signed-in Administrator lists the Bookings of a chosen date, grouped by Window: start and end; Seat capacity, Seats booked, Seats left; each Booking's reference, name, email, Seats, total and time of booking. A new Booking appears on the next load. Figures equal what Guests see. Stored text is shown escaped. From §4.8: status active or cancelled, history of Changes, cancelled Bookings stay with time, cause and remedy and are not counted.
- **FR-17: Outbox.** A signed-in Administrator lists every simulated email with time, recipient, subject and full body including links. Anonymous and Guest requests are refused and reveal nothing. A Guest sees an email only on the page of the action that sent it (Confirmation; the result pages of a Change).

**§4.5 Security and personal data (Core)**

- **FR-18: Server-side input validation.** Rejected with no Hold, Booking, payment or email (IV-1 to IV-4): Seat number 0, negative, fractional, not a number, above 10 or above Seats left; malformed or unknown date or Window, outside the horizon or past the deadline; missing required or unknown extra field; empty, too long or malformed name or email. SQL, script tags and HTML are never executed or rendered as markup (IV-5). Invalid Administrator input, including seed data, is rejected (IV-6).
- **FR-19: Hashed passwords.** Salted slow hashes only, never stored, logged or returned in plain text; same password gives different hashes (PW-1, PW-4). New or changed passwords: at least 15 characters, at least 64 allowed, any characters; refused if common or equal to the email; no composition rules (PW-2, PW-3). Paste and password managers work.
- **FR-20: Role-based access.** The server checks the role on every request. Administrator functions: anonymous refused as not signed in (RB-1, IV-7), Administrator allowed (RB-3); signed-in Guest refused (RB-2, with §4.12, not planned). A Booking opens only with its Manage link (§4.8); guessing a reference or link gives the same response whether or not the Booking exists (RB-4); a Guest's own link reaches that Booking only (RB-5). RB-6 comes with §4.12 (not planned).
- **FR-21: Personal data and privacy notice.** Guests: name and email only; Administrators: email and password hash. A privacy notice, separate from the terms and linked wherever data is collected, states controller and contact, what and why, legal basis, retention and who sees it, rights including Datatilsynet. Guest data is deleted or anonymised 12 months after the Window, or after the last Voucher from the Booking expires if later. No marketing email. Only strictly necessary cookies; the session cookie is set only on Book seats, a Manage link or Administrator Sign-in. No third-party requests. Passwords, Manage-link tokens and Door codes never in logs. The privacy notice or the README states how data is protected.

**§4.6 Look, feel and laptop layout (Core)**

- **FR-22: Finnish-inspired website on a laptop screen.** Every Core page works without horizontal scrolling at 1366×768, 1920×1080 and from 1024 px wide. All styling from one stylesheet. Self-hosted OFL fonts listed in the asset register. Error and sold-out messages say what happened and what to do next; "Sold out" is availability information with alternatives, not an error.
- **FR-23: Accessible Core pages.** WCAG 2.2 AA, except 1.4.10 Reflow until FR-51. An automated check reports no A or AA failure (1.4.10 listed as a known gap). A manual keyboard-only pass of the booking flow and the Administrator list, with focus always visible and never hidden. A manual 200 % zoom pass at 1366×768 and 1920×1080 loses nothing (1.4.4). AA contrast; targets at least 24×24 px; no information by colour alone; errors as text by the field and in a summary.

**§4.7 HTTPS (If time 1)**

- **FR-24: HTTPS only (HT-1 to HT-4).** Plain HTTP to the website or the API is redirected to HTTPS, and nothing is returned or changed over HTTP. Every HTTPS response carries Strict-Transport-Security. Session cookies are Secure and HttpOnly, never sent over HTTP (the local test checks the attributes and that an HTTP request with the cookie is only redirected; the README states the `localhost` limit). Every email link starts with `https://`.

**§4.8 Change Seats or take a Voucher (If time 2)**

- **FR-25: Manage link.** Token of at least 128 random bits, stored only as a hash. The link shows the Booking until its Window ends; Changes only before the Cutoff. Invalid, expired or replaced links answer like unknown ones. A new link stops the previous one (FR-34). Manage pages load no third-party resource and send no referrer. Every Change needs an explicit confirming action, and loading a page changes nothing. Each confirming action carries a one-time key; a repeat applies the Change once and returns the first outcome.
- **FR-26: Move Seats to another Window.** Before the Cutoff, atomic: a target without room changes nothing (E5). Moving some Seats splits the Booking: the moved Seats become a new Booking with its own reference and Manage link, emailed and shown on the result page; the original keeps its reference and link. Both keep the price per Seat and the Cutoff of the original. Moving all Seats keeps the reference. The target must be inside the horizon and before its deadline. No extra cost. Every move sends a confirmation email shown on the result page. Freed Seats count at once; the Administrator list shows the Change. After the Cutoff every Change is refused with an explanation.
- **FR-27: Voucher instead of Seats.** Before the Cutoff, give up some or all Seats for a Voucher worth the price paid for them. Code, value and expiry (one year; when a Voucher paid the Booking, that Voucher's expiry, so a Voucher is never renewed by booking and giving up Seats: Lisa, 2026-11-24) are in the Change's one email, shown on the result page. Freed Seats count at once. No money is refunded.
- **FR-28: Pay with a Voucher.** A Voucher pays for all or part of a Booking, with the rest by Simulated payment; any remainder stays until expiry. Expired, used-up and unknown codes get the same refusal. Never paid out in money. Two simultaneous uses never spend more than its value. On a refunded cancellation, each part goes back the way it was paid; the Voucher part as a new Voucher with the earliest expiry of those used, never less than 30 days.

**§4.9 Whole-sauna booking (If time 3)**

- **FR-29: Book a whole Sauna.** Allowed when the Sauna is Bookable whole; the Window is inside the horizon and before its deadline; the Sauna is not Blocked or already booked whole; Seats booked (plus held) ≤ its Room ahead, unless it is an unreleased Whole-booking-only Sauna; and the Window has not started, or has no Seat booking, or the Sauna is not open for Seats. Examples B1, B2, B3, B7, H12. No Hold: Review says the Sauna is not held while paying; FR-29 is checked again at payment and nothing is charged if the Sauna was taken. Two simultaneous requests for one Sauna and Window: exactly one succeeds (C1).
- **FR-30: Choose the Sauna.** For a date, the Private sauna page lists each Sauna that can be booked whole, with Capacity, price and free Windows; the Guest picks a Window in that list or opens one Sauna and picks there. Only FR-29-allowed pairs. The Guest always picks; the confirmation names the Sauna and the Window.
- **FR-31: Placement follows the Fill order.** After every booking, Change, cancellation and Whole-sauna booking (and later Block, mark, release, Capacity and Fill-order change), INV-1 to INV-5 hold. Examples A1 to A5, A8, B4 to B6. Placement is never shown to a Guest with a Seat booking; only the Administrator sees Placement per Window. A model-based test checks INV-1 to INV-5 against a brute-force reference after every step.
- **FR-32: Seat and Whole-sauna requests never interleave.** C2 (Seat vs. last Sauna), C3 (cancellation vs. Whole-sauna booking), C4 (two cancellations), C5 (invariants under any interleaving); a cross-Window Change raced with a Whole-sauna booking or an opposite Change keeps INV-1 to INV-5 in both Windows. C6 and F1 come with §4.13 (not planned).
- **FR-33: Cancel or change a Whole-sauna booking.** Before its 72-hour Cutoff, with the Manage link: cancel for a Simulated refund or a Voucher of the full price (one year), also when part was paid by Voucher; capacity restored; the Administrator sees it. A move to a Window where the Sauna is not available whole is refused and changes nothing; a move to a Sauna with a different price is refused with the reason. Every cancellation or move sends a confirmation email. After the Cutoff every Change is refused with an explanation.

**Specified, not planned in this round (PRD §10.3).** These have no epics or stories in this round. They are listed so that the readiness check does not count them as orphans. Where a planned story must leave room for one, the story says so.

| FR | Feature | Label | Source |
|---|---|---|---|
| FR-34 | "My booking" Manage-link resend | If time 4 | appendix §4.10 |
| FR-35, FR-36 | Seat Hold during payment; payment after a Hold expires | If time 5 | appendix §4.11 |
| FR-37 | Optional Guest accounts (RB-2, RB-6, PW-2/3/6 for Guests) | If time 6 | appendix §4.12 |
| FR-38 to FR-42 | Administrator tools: Windows, Capacity, prices, Fill order; five Settings (SC8); Blocks; Whole-booking-only and Release time; Overbooking fallback and Remedy page | If time 7 | appendix §4.13 |
| FR-43, FR-44 | Gift cards | Step 2 — 1 | appendix §4.14 |
| FR-45 to FR-50 | Door codes and Gradual opening | Step 2 — 2 | appendix §4.15 |
| FR-51 | Mobile layout and any window size (WCAG 1.4.10) | Step 2 — 3 | appendix §4.16 |
| §4.17 | Vision items (several locations, children, memberships, remote doors, one-Sauna access, heating, several websites, more languages, real payment and email, other resources, Window patterns) | Vision | PRD §4.17 |

### NonFunctional Requirements

- **NFR-1 Runs locally.** A fresh clone runs from the README alone on a laptop, with no keys, paid accounts or external services at run time. The examiner installs uv (Python), Node.js and Docker only. `docker compose up --build --wait` runs db, backend, frontend and Caddy. One more command (`uv run pytest`) runs all tests after two one-time preparation commands (`npm --prefix frontend ci`, `uv run playwright install chromium`).
- **NFR-2 One API, and the server decides.** The website reaches the platform only through one API, and the platform enforces every rule whatever the website does.
- **NFR-3 Venue time.** All time rules are in Europe/Oslo, also on daylight-saving days; a Window keeps its local clock times. Offsets are elapsed time from the Window's start or end; the Release time is a clock time on the Window's start date. A Window belongs to the date it starts. A Window that would start or end in a skipped or repeated hour is refused.
- **NFR-4 Money.** Prices in NOK including VAT, from seed data in the Core. A Booking keeps the price it was paid at.
- **NFR-5 English.** Website and emails in English only.
- **NFR-6 Test depth.** Each story includes its tests as part of done. Concurrency, capacity, validation and SC1 in depth; other features in breadth. Concurrency tests run in parallel against real PostgreSQL, never a mock. All tests run with one command.
- **NFR-7 No performance promise.** No throughput or latency target.
- **NFR-8 Dependencies.** At the freeze, dependencies are current and an audit reports no known critical vulnerability.
- **NFR-9 Honest interface.** No dark patterns: no countdowns, false scarcity, pre-ticked options or hidden fees.
- **NFR-10 Real data.** Windows, Capacity, prices, Bookings and the Outbox are stored in the data store and survive a restart. Nothing shown is faked.
- **NFR-11 Time rules are checked, not scheduled.** Time rules are conditions evaluated against the store's clock when a request is handled, after its lock. No background jobs; timed effects are caught up at start and by the next request that reads them. Tests control the clock and never wait in real time.

**Delivery requirements (PRD §8.1)**

- **DR-1 AI use and quality assurance.** Documentation of how AI was used and steered at each stage and how the result was checked, including rejected or wrong AI output.
- **DR-2 README.** One-command start, dev start of backend and frontend, how to run all tests, the Administrator test login and seeded sample Bookings (from §4.8 where to find a sample Manage link), how to view the Outbox, and which success criteria were not delivered.
- **DR-3 Clean assets.** Every image, font, icon and text is AI-generated, freely licensed or checked, and listed with source and licence in the asset register (`ASSETS.md`).
- **DR-4 Traceability.** Planning documents, small descriptive commits and session logs show the path from plan to code.
- **DR-5 Tidy repository.** No secret committed; secrets generated on first start or read from a git-ignored file with a committed example; seed data, tests and planning documents each in one named folder, named in the README.

### Additional Requirements

*From the architecture spine (status final, 2026-11-19). AD numbers refer to it.*

**Starting point (Epic 1, Story 1).** There is no starter template. The build starts from the existing slice (`src/booking_platform/app.py`, `db.py`, `schema.sql`, 42 tests in `tests/`). The first skeleton story reshapes it without loosening any rule (AD-21):
- `schema.sql` moves unchanged to `migrations/0001_core.sql`; a migration runner applies numbered SQL files at startup and at test start and records them in `schema_migrations` (AD-15).
- All paths move under `/api` (`/health` becomes `/api/health`); Administrator endpoints sit under `/api/admin/` on one router (AD-10).
- Server-side sessions replace the client-supplied `session_id` (AD-8); Seats are capped at 1–10.
- The layered package `api/`, `services/`, `db/`, `config.py` (AD-1, AD-22).
- The compose stack: proxy (Caddy on plain HTTP `:8000`), backend, frontend (Next.js scaffolded with `create-next-app`, scaffold assets deleted), db, with healthchecks and `up --wait` (AD-17, AD-27).
- The slice's tests stay as regression proof; they sign in through a fixture and fill Windows with Bookings of at most 10 Seats or raw inserts.
- The Caddy, compose and Next.js details were never run (Docker was off, issues.md 2026-11-19): the skeleton story proves them live (healthchecks, `caddy adapt`, `curl -i`, `next build` listing dynamic routes).

**Backend structure and rules**
- AD-1: `api` → `services` → `db`, all may import `config`; SQL only in `db/` and `migrations/`; every refusal is `services.errors.Refused(code, **facts)`; store errors are mapped by constraint name; an unmapped store error is a 500.
- AD-2: capacity is enforced in PostgreSQL (counters, `CHECK booked_within_capacity`, recompute triggers, deferred `verify_window`). Any new table or column that changes Seat capacity, booked or held adds a BEFORE lock trigger, an AFTER recompute trigger, inclusion in `verify_window`, a bypass test and a `MUTATIONS` entry in the test harness.
- AD-3: one user action = one `db.run(work)` transaction at READ COMMITTED; `lock_windows(c, ids)` in id order before the first write; Booking-scoped actions read, lock, re-read; no lock across waits; retries (40001, 40P01) only in `db.run`.
- AD-4: every time rule reads `app_now()` after the lock; Venue rule values are columns of the `settings` row (Booking horizon added in the Core); one SQL predicate per rule (`booking_deadline`, `within_horizon`, `venue_date`, `window_started`, later `change_allowed`); no timestamptz→date cast without `AT TIME ZONE settings.venue_tz`; no background jobs; catch-up only at startup or by a touching write (`services/catchup.py`); GETs never write, except `windows.ensure_generated()` and the session/grant touch; tests move the clock only through `clock.off`.
- AD-5: Seats left, booked and capacity come only from `seats_left()`, `window_booked_seats()`, `window_open_capacity()`.
- AD-6, AD-25: Placement is derived, never stored; `placement(wid)` is the only computation and is read only under `/api/admin/`.
- AD-7: Bookings are never deleted; migration `0002` adds `status` and `entry_time`.
- AD-8: one `sessions` table with hashed 256-bit tokens; cookie HttpOnly, `SameSite=Strict`, `Path=/`, `Secure` when `BP_HTTPS`; created only by `POST /api/session` (Book seats, Sign-in, after `401 no_session`) and `POST /api/manage/open`; anonymous 24 h and Administrator 8 h, sliding; sign-in rotates the token on the same row; sign-out deletes it; CSRF by `Origin` or `Sec-Fetch-Site: same-origin`, else `403 cross_origin`.
- AD-9: `Idempotency-Key` on every confirming request; `idempotency_keys` table; only successes stored; a repeat returns the first outcome, any other known key is `409 invalid_key`.
- AD-10: `/api/admin/` router (401 anonymous, 403 non-Administrator); unknown `/api` paths and 405s answer the JSON `404 not_found` envelope; `redirect_slashes=False`; links never built from the request.
- AD-11: `sign_in_throttle` table locked `FOR UPDATE`; Argon2id (`argon2-cffi`), rehash on parameter change; one FR-19 password-rule function with a packaged common-password list, used by the seed, `create-admin` and later sign-up.
- AD-12: `services.outbox.send` is the only sender, inside the action's transaction; plain-text bodies built in `services`; absolute links from `BP_BASE_URL` and `config.links`; text shared by page and email lives once in `content/` (JSON); `GET /api/bookings/{reference}/confirmation` is checked against the paying session; only `/api/admin/` lists the Outbox; retention clears recipient and body.
- AD-13: money is integer øre; `bookings.total_ore` and `price_per_seat_ore` are the Booking's value; `payments` rows record charges and refunds; `charge()` decides before the lock and writes after it.
- AD-14: test switches read once at startup from `BP_TEST_SWITCHES` (default `config/test-switches.toml`, git-ignored; `config/test-switches.example.toml` committed); seams `payment.charge` (`ok | fail | hold`) and `db.run` (`force_conflict`); no endpoint reads or changes a switch; compose mounts the `config/` directory read-only.
- AD-15: plain SQL migrations `migrations/NNNN_name.sql`, numbered at merge, never edited after merge, structure and singleton rows only.
- AD-16: every refusal code declared once in `api/errors.py` with its status and facts and mirrored by the frontend; 422 only for shape errors; rules judged against store or clock are 409; envelope `{"detail": {"error", "message"?, …facts}}`; `no_seat_free` carries `seats_left`; `deadline_passed`, `outside_horizon`; listings carry `already_started` per Window and `today`, `horizon_end`, `horizon_days`; Venue facts (Saunas, prices, schedule, contact) come from the API.
- AD-18: `seeds/` applied idempotently after migrations at every start (Saunas, Capacities, Fill order, Bookable-whole marks, prices, Settings, Window schedule, Administrator, sample Bookings); never overwrites; sample Bookings created through `services.booking.create` with fixed keys; seed validated like Administrator input; `create-admin` prompts for the password.
- AD-19: no request bodies, headers or cookies logged; Caddy access log off; the e2e layer searches the compose logs for the test password and issued tokens.
- AD-20: Booking reference = 8 upper-case Crockford base32 characters, inserted with `ON CONFLICT DO NOTHING`, at most 5 tries, used by every Booking creator.
- AD-22: `config.py` is the only reader of `BP_DATABASE_URL`, `BP_BASE_URL`, `BP_HTTPS`, `BP_HOST`, `BP_PORT`, `BP_ROOT`, `BP_TEST_SWITCHES`; working local defaults; dev and test databases (`booking_dev`, `booking_test`) created when missing; one uvicorn process; `/docs` and `/openapi.json` off.

**Frontend structure (AD-17)**
- Next.js App Router in JavaScript, `output: 'standalone'`, behind Caddy. No `app/api/`, `route.js`, Server Actions, `middleware.js` or `proxy.js`.
- `frontend/lib/api.js` is the only browser `fetch` caller (relative `/api/…`, same-origin cookies, `Idempotency-Key`, one error type). `frontend/lib/server-api.js` is the only server-side caller, for public Venue-fact GETs only (`cache: 'no-store'`, no cookie, never throws, `unstable_rethrow`, pages await `connection()`).
- One origin, no third-party requests; fonts through `@font-face` from `public/`; plain `<img>`; no `next/font` or `next/image`; `NEXT_TELEMETRY_DISABLED=1`; content copy and telemetry handled by a Node script.
- Each `page.js` is a Server Component exporting `metadata`; one client component in the root layout manages focus (fragment target on first load, else nothing; `h1` or fragment target after navigation) and the "Error: " title prefix.
- `sessionStorage`, `location`, `history` read only inside effects.
- Root layout `<noscript>` line "This booking page needs JavaScript."
- `app/not-found.js`, `app/error.js`, `app/global-error.js` with the EXPERIENCE.md copy; Next.js default pages never shown.
- No favicon; every file in `frontend/public/` is listed in `ASSETS.md`, checked by a test.
- `frontend/Dockerfile` per Next's `with-docker` layout on `node:24-alpine`; root `.dockerignore`.
- Dev: `next dev -H 127.0.0.1` with `/api` rewrites to `127.0.0.1:8001` in development only; `skipTrailingSlashRedirect: true`.
- Not adopted from `technology.md`: TypeScript, Tailwind, shadcn/ui or any UI library.

**Proxy and deployment (AD-27)**
- Caddy (`caddy:2.11`) is the only published web port, on `127.0.0.1`; `@api path /api /api/*` to the backend, everything else to the frontend; database port published on `127.0.0.1:${DB_PORT}`.
- Core mode: `SITE_ADDRESS http://localhost:${HTTP_PORT:-8000}`, `BP_HTTPS off`, `BP_BASE_URL http://localhost:8000`. The FR-24 story switches these three compose lines together to HTTPS `:8443`.
- Healthchecks on every service (db `pg_isready` over TCP, backend `/api/health`, frontend `/privacy`, proxy admin `:2019`), `depends_on: service_healthy`.
- Headers on every site response: `Referrer-Policy: no-referrer`, `Cache-Control: no-store` on `@api`, `X-Robots-Tag: noindex` on Manage paths; HSTS from FR-24. The backend and frontend set none of these.
- Named volumes for db and `caddy_data`.

**Tests (architecture Conventions)**
- Files `tests/test_fr<NN>_<topic>.py`; catalogue examples as test names (`test_b2`).
- Two layers, both started by `uv run pytest`: the API layer (`tests/`) starts its own backend with uv against `booking_test` and goes through `tests/client.py::api_client`, which sends `Origin`; the e2e layer (`tests/e2e/`) runs the compose project `booking_e2e` behind Caddy with Playwright (Chromium) and axe-core from `frontend/node_modules`.
- The session fixture runs `docker compose up -d --wait db` first.
- Race tests: 100 repetitions per run (FR-11), asserting INV-1 to INV-5 and Seats left for group C.
- FR-31: one Hypothesis `RuleBasedStateMachine` in `tests/test_fr31_placement_model.py`, calling `services` in-process, profiles `default` and `thorough` (AD-26).
- `tests/e2e/a11y.py` (Lisa, 2026-11-19): the shared accessibility helper from Story 1.2 (`check_axe`, `no_horizontal_scroll`, `press`, `tab_to`, `tab_order`, `zoomed`); every keyboard-only e2e step goes through it, so focus visibility is checked in every story, and Story 2.4's manual passes confirm the automated checks rather than repeat them.
- `tests/e2e/test_fr21_privacy.py`: every request goes to the stack's origin; no cookie after Landing, Terms, Privacy notice and "Before you come"; one session cookie after Book seats; anonymous Administrator address goes to Sign-in; one stylesheet per page; `/#before-you-come` focus.

**If-time architecture (stories of Epics for §4.7 to §4.9)**
- AD-23: a Whole-sauna booking is a `bookings` row with `kind = 'whole'`, paired with its `whole_bookings` capacity row; `check_whole_pair`; one serializer for every Booking JSON and email fact block; the slice's whole-booking endpoint is removed.
- AD-24: `whole_bookable(wid, sid, ignore_booking)` is the one FR-29 predicate, used by `trg_check_whole` and by `GET /api/private-saunas?date=`; refusal order `outside_horizon`, `deadline_passed`, `cutoff_passed`, then `sauna_unavailable`.
- AD-26: the FR-31 model includes the Seat move, the Voucher, and the FR-33 move and cancel as rules, and checks AD-31's ledger.
- AD-28: Manage link `<base>/manage#t=<token>`; `access_tokens` (hash only, one unrevoked manage token per Booking); `POST /api/manage/open` exchanges it for a `manage_grants` row on the session (30 minutes sliding); routes under `/api/manage/{reference}/` per kind; `GET /api/manage/{reference}` returns no email, code or link.
- AD-29: `bookings.version`; check order `booking_cancelled`, `booking_changed`, `change_invalid`, horizon, deadline, Cutoff, capacity; split rules; `booking_changes` history via `services.history.record`; cancellation columns and CHECKs (`seat_guest_refund_forbidden`); one Change response serializer; one email per Change plus the split-off Booking's own.
- AD-30: Vouchers as 16-character Crockford codes, hashed; `POST /api/vouchers/quote` (no lock, no write); spend by one conditional `UPDATE` after the lock; expiry by Venue date; at most one Voucher per Booking; `retention_due()`.
- AD-31: every return is a `payments` row; `refund()` returns card part as one card refund row and the Voucher part as one new Voucher (earliest expiry, at least 30 days); the FR-33 cancel writes all of it in one transaction; split Seat bookings are not refunded in v1.
- AD-4: the §4.8 migration adds `settings.cutoff_seats` and `bookings.cutoff`; the §4.9 migration adds `settings.cutoff_whole`.
- AD-18: the §4.8 story gives each sample Booking a Manage token with its Outbox email.
- AD-27: the FR-24 story adds HSTS, the e2e TLS part and `tests/e2e/test_fr24_https.py` (HT-1 to HT-4) in one PR, plus the README HTTPS section.

**Carried from `issues.md` and review reports (not yet in the source documents)**
- NFR-3's refusal of a Window in a skipped or repeated hour is not explicit in the spine; it is covered in the seed or FR-13 story.
- The code must deliver AD-16's facts: `seats_left` on `no_seat_free`, `deadline_passed`, `already_started`, `horizon_end`, `horizon_days`.
- README needs a security section (FR-21): password hashing, server-side role checks, Manage-link token hashing, whether HTTPS is on, no third-party requests.
- Whole-sauna prices and which Saunas are Bookable whole are chosen by Lisa in the first §4.9 story (spine Deferred; EXPERIENCE.md Open Item 27).
- A split Seat booking's refund raises 500 until If-time 7 (Deferred); no planned flow refunds one.
- UX validation (2026-11-06): the 12 high findings are closed in EXPERIENCE.md; 42 medium and 44 low findings are not yet triaged, and stories touching Book seats, Review and Confirmation should check `review-accessibility.md` and `review-content.md` for relevant ones.
- FR-11 hot-row performance has no sourced figure; NFR-7 makes no promise, so no story sets a load target.

**Stack (spine, 2026-11-19).** Python 3.12 with uv 0.12.x; PostgreSQL 18; FastAPI 0.162.0; Starlette 1.10.0; Pydantic 2.14.2; psycopg 3.3.7 and psycopg-pool 3.3.3; uvicorn 0.54.0; argon2-cffi 25.1.0; pytest 9.2.0; hypothesis 6.170.15; pytest-playwright 0.10.0 / playwright 1.64.1; Caddy 2.11.9; Node.js 24 LTS; Next.js 16.4.6; React 19.3.1; axe-core 4.14.1.

### UX Design Requirements

*From DESIGN.md (visual identity, tokens) and EXPERIENCE.md (behaviour, copy, states). Both are final (2026-11-09; EXPERIENCE.md updated for Next.js on 2026-11-19).*

**Foundations**
- **UX-DR1 Design tokens.** One stylesheet `frontend/app/styles.css` defines every DESIGN.md token as a CSS custom property: 15 colours (`page`, `surface`, `text`, `muted`, `primary`, `on-primary`, `button-edge`, `bar`, `on-bar`, `link`, `focus`, `border`, `unavailable`, `error`, `success`), 17 type roles, the spacing scale 4–96 px and the layout widths (`rail-width` 320, `date-column` 348, `page-max` 1320, `measure-text` 640, `measure-lead` 800, `hero-height` 468, `sauna-image-height` 320, `band-height` 220, `before-image-height` 300, `button-height` 48, `control-height` 44, `session-row-height` 40, `calendar-cell-height` 34). Square corners, flat (no shadows), light mode only, no `style` props, no CSS Modules.
- **UX-DR2 Fonts.** Finlandica (weights 400–700) and Source Sans 3 (300–700), self-hosted in `frontend/public/` via `@font-face`, both with ö, tabular figures kept for times, dates and Seat counts, the DESIGN.md fallback stack, and both listed in `ASSETS.md`.
- **UX-DR3 Shells.** Guest pages: sticky left rail (320 px) plus fluid main, centred up to 1320 px, rail and main on `page`. Details, Review, Confirmation, Terms and Privacy notice carry only the Wordmark in the rail. Administrator pages: full-width Administrator bar, no rail, one column up to 1320 px.
- **UX-DR4 Images.** The final images from `ux-designs/…/mockups/images/` (hero, towels, one per Sauna, steam band, Before-you-come image) move to `frontend/public/` with their alt text and `ASSETS.md` rows. No logo, favicon or icons.

**Shared components (`frontend/components/`)**
- **UX-DR5 Primary button.** One per page, `primary` fill with 1.5 px `button-edge`, at least 48 px high; the label says what happens; on Pay it states the amount; while processing the label is "Processing", it takes no second press and keeps focus.
- **UX-DR6 Text link.** `link` colour, always underlined; never starts a Booking or takes payment; leaving Details or Review for Terms or Privacy notice and returning keeps everything entered.
- **UX-DR7 Wordmark.** "Saunalöyly" typeset in Finlandica 52 px; the page's heading on Landing, a link to Landing elsewhere.
- **UX-DR8 Rail and Rail note.** Rail order: Wordmark, facts or total, action, notes. Rail notes in `muted`, plain text only.
- **UX-DR9 Text field and Field error.** Label always visible above, hint below, 44 px input; Field error in `error` under the field (border unchanged); input kept; paste and password managers work.
- **UX-DR10 Terms checkbox.** Never pre-ticked; whole line is the target; Pay without it gives an Error summary and a Field error and charges nothing.
- **UX-DR11 Notice.** `surface` with `border`, never `error`; for availability and neutral messages; announced as a status message; takes focus (`tabindex="-1"`) only when it replaces the focused element.
- **UX-DR12 Error summary.** Top of a form, `error` line and text, no title; each entry links to its field; an entry without a field is plain text; takes focus when it appears; the page title gains "Error: ".
- **UX-DR13 Nearest sessions.** Up to three Text links inside a Notice, each with date, time and Seats left, 40 px high, its own tab stop; choosing one selects that date and Session and keeps the number, name and email; focus then goes to the Review heading (on Review) or the chosen Session (on Book seats).
- **UX-DR14 Booking summary, Reference display, Email as sent.** Label/value rows with lines between; the 8-character reference in 32 px with tabular figures, selectable; Email as sent labelled "Sent by email:", line breaks kept, showing the stored email only.

**Landing (FR-1)**
- **UX-DR15 Landing layout.** Main: hero (468 px), Venue description in `lead`, "Before you come" with three Rule lists (What to bring, Safety, Practical) in three columns down to 1200 px and stacked below, then one image; "The saunas" with the Seat statement intro and four Sauna cards in a loose two-column grid (even cards 72 px lower); the steam band; "Find us" in three columns with address, contact, Terms and Privacy notice links. Rail: Wordmark, opening hours and Session length, price per seat, Book seats. Book seats is in the first view at 1366×768.
- **UX-DR16 Rule list, Sauna card, Find us block.** Rule list: heading with a line under it, items without bullets or lines. Sauna card: not a link, image, name, "Holds 7"-style size line, one line of text; Sauna names appear here and never in the Seat flow. Venue facts come from the API (AD-16); if the read fails, a Notice says "please try again" and Book seats still works.

**Book seats (FR-2 to FR-4)**
- **UX-DR17 Date calendar.** Text field (`dd.mm.yyyy`, hint "Type it as dd.mm.yyyy, or pick a day below") above a month grid; typed and picked dates stay in step; only FR-2-allowed dates choosable; a sold-out date can be chosen and then shows availability; the calendar ends at the horizon with "Booking opens 4 weeks ahead." (number from the server); "Next month" and, once forward, "Previous month"; the grid is a radio group named "Pick a day, <Month> <Year>" with full day names; typed date checked on blur or Enter with "Enter the date as dd.mm.yyyy" or "This date cannot be booked. Pick a day below."
- **UX-DR18 Seat picker.** Ten radio cells 1–10 in a `fieldset` with the question as `legend`; changing the number updates the total and which Sessions are too small.
- **UX-DR19 Session list and Session row.** All Sessions of the date in time order, including unavailable ones, excluding past-deadline ones; whole row is the label; accessible name includes the Seats left text ("13:00 to 14:30, 12 seats left"); unavailable rows are disabled with text ("1 seat left, not enough for 2", "Sold out"); "Already started" on a started but bookable Session; no price in rows; "Loading sessions" while reading; a selected Session that stops fitting is cleared with a Notice; changing the date clears the Session.
- **UX-DR20 Total block.** In the rail only, appears once a number is chosen, "Total NOK 500 incl. VAT" with the per-seat line under it; announced when it changes.
- **UX-DR21 Book seats validation.** Nothing pre-selected on arrival. Continue ("Continue booking") is always enabled; with a choice missing it shows an Error summary ("Choose a date", "Choose the number of seats", "Choose a session") and Field errors; summary links move focus to the date field or the chosen/first available radio. No room on the date: Notice with Nearest sessions ("No room for 2 seats on Saturday. The nearest sessions with room:"); no room in the horizon: "There is no room for 2 seats in the next 4 weeks." with no alternatives.
- **UX-DR22 Book seats layout budget.** Heading, calendar, ten seat buttons and all eight Sessions fit about 570 px, so the whole page and the total are in the first view at 1366×768; two columns (date 348 px, then seats and Sessions) down to 1200 px, stacked below.

**Details, Review, Confirmation (FR-5 to FR-8)**
- **UX-DR23 Details.** Heading "Your details", Back, name, email, Privacy notice link, "Continue booking"; errors "Enter your name", "Enter a valid email address".
- **UX-DR24 Review.** Heading "Review" and Back; two equal columns down to 1200 px: Booking summary (Date, Session, Seats, Total, Name, Email, Venue, Contact) on the left; on the right "Booking terms" with the three shared statements (from `content/`), Terms and Privacy links, "I accept the booking terms", Pay ("Pay NOK 500") with "Simulated payment: no money moves" beside it. Pay ends at about 440 px at 1366 px wide (first view).
- **UX-DR25 Review refusals and recovery.** After a refusal the Guest stays on Review with name and email kept; a Notice under Back takes focus; Pay, the payment note and the Terms checkbox are removed for the refused Session; Booking summary and terms stay; choosing a nearest Session reloads Review with them back. Copy per refusal: "Only 1 seat left in this session. You have not been charged.", "No seat free. You have not been charged.", "This session can no longer be booked. You have not been charged.", "The payment failed. You have not been charged. You can pay again." (Error summary, Pay stays), "please try again" (Pay, note and checkbox stay). `409 invalid_key`: Notice "This booking may already be paid. Check your email for a confirmation before you book again.", Pay removed, Book seats as a Text link. `409 payment_pending`: treated as "please try again" with the same key.
- **UX-DR26 Booking draft.** The draft (choices, name, email, idempotency key) lives in `sessionStorage` (`draft:seats`) and survives a reload in the same tab; Details without a Session or Review without name/email goes to the earliest page with something missing; after payment the draft holds only the reference, so Back from Confirmation shows Confirmation; Book seats after payment starts a new draft and key; `401 no_session` makes a new browser session, keeps the draft and key, and shows "please try again" (copy never says "session" for this).
- **UX-DR27 Confirmation.** "Booking confirmed" in `success`, Reference display, the reception sentence directly under it with no heading, Booking summary (stored total), booking terms, link to "Before you come", "Sent by email:" with the stored email. Any other browser or no browser session: "This page is not available."

**Static pages and errors**
- **UX-DR28 Terms and Privacy notice.** Full texts as rendered in `mockups/key-terms.html` (sections Who we are … Your data) and `mockups/key-privacy.html` (Who is responsible … Your rights), heading "Booking terms" on Terms; separate pages; no session cookie set on them.
- **UX-DR29 Error and fallback pages.** "This page is not available." with a link to Landing for unknown addresses, unknown Bookings and API 404s (one component); "please try again" Notice on `error.js` and `global-error.js`; the `<noscript>` line.

**Administrator (FR-15 to FR-17)**
- **UX-DR30 Sign-in.** Administrator bar with the name only, heading, email, password, "Sign in". Every refusal (wrong email, wrong password, throttled) shows "Wrong email or password" in an Error summary with no Field error. An anonymous visit to any Administrator address goes to Sign-in; after Sign out, and after expiry on the next action, back to Sign-in (copy never says "session" for this).
- **UX-DR31 Booking list.** Administrator bar (Booking list, Outbox, Sign out); heading; a date Text field defaulting to today with "Previous day" and "Next day" links; one Session group per Session in time order with Seat capacity, Seats booked and Seats left, shown even without Bookings ("No bookings"); a full Session has an `unavailable` header with "Sold out" and "Seats left 0" in weight 600; Booking table with reference, name, email, Seats, total and time of booking (`dd.mm.yyyy HH:MM`, oldest first), numbers right-aligned in tabular figures; escaped text; read failure → Notice "please try again".
- **UX-DR32 Outbox.** Administrator bar, heading, Outbox entries newest first, each always open with time, recipient, subject and full body with plain-text links; empty → "No emails".

**Cross-cutting behaviour**
- **UX-DR33 Focus and titles.** Page title "<heading> – Saunalöyly" (Landing: "Saunalöyly"), set before focus moves; "Error: " prefix while an Error summary shows. Focus to the `h1` after each client navigation, or to an existing fragment target (`/#before-you-come`) on first load and after navigation; targets carry `tabindex="-1"`. When the focused element disappears, focus goes to what replaced it.
- **UX-DR34 Interaction primitives.** Click and keyboard always both; no hover-only information, drag or gestures; focus ring 3 px `focus` with 2 px offset on every interactive element (on the visible cell for hidden radios); Date, Seat and Session choices are radio groups with one tab stop and arrow keys; no dialogs; no live updates (re-read on date or number change); minimal motion respecting reduced motion; banned: countdowns, viewer counts, padded numbers, pre-ticked options, hidden fees, any Hold or time-limit wording, consent banner.
- **UX-DR35 Accessibility floor.** Seat picker and Session list as `fieldset`/`legend`; page language English with Finnish words marked `lang="fi"`; image alt text; targets at least 24×24 px; colour never the only cue; name and email never asked twice; axe-core in `tests/e2e/`; manual passes: keyboard-only flow, 200 % zoom at 1366×768 and 1920×1080 (Continue and Pay stay reachable), screen reader (check double announcements with Next.js's route announcer), and the Book seats tab order (main before rail) against WCAG 2.4.3.
- **UX-DR36 Responsive (Core).** No horizontal scroll from 1024 px up; the rail stays from 1024 to 1365 px; Book seats, Review and "Before you come" keep two (three) columns down to 1200 px and stack below (`max-width: 1199px`). The narrow layout below 1024 px is specified in EXPERIENCE.md but belongs to FR-51 (not planned); no fixed width may block it.
- **UX-DR37 Copy rules.** "session" is the Guest-facing word for a Window everywhere, never for a browser session; plain sentence case (seats, saunas, session lower case); every fixed and accepted text in EXPERIENCE.md Voice and Tone is used verbatim; the no-repetition rule (each fact has one home per page) with its listed exceptions.
- **UX-DR38 Emails.** Plain text in English; the confirmation follows the line layout in `mockups/key-confirmation.html`; the reception sentence without a heading; the payment note in every email that mentions a payment; absolute links from `BP_BASE_URL`; Seat emails never name a Sauna.

**If-time plug-ins (only when their epic is built)**
- **UX-DR39 Voucher field (§4.8).** On Review between the Booking summary and the terms, always visible once built: a Text field with a Text link beside it; reduces the amount and updates the Pay label; expired, used-up and unknown codes get one identical Field error; rest by Simulated payment. Wording when the Voucher covers the whole total is open (Open Item 23) and is decided in that story.
- **UX-DR40 Manage booking (§4.8, §4.9).** Reached from the Manage link (`/manage#t=…` → `/manage/[reference]`); shows the Booking and the Changes allowed; each Change has a confirming step that changes nothing, then a result page with "Sent by email:"; after the Cutoff the Booking is shown and every Change refused with the reason; an invalid, expired or replaced link shows "This page is not available."; `X-Robots-Tag: noindex`, no referrer. Open Items 19–22 (after a Voucher, after a Venue cancellation, after the Window ends, Cutoff wording) are decided in the §4.8 stories.
- **UX-DR41 Private sauna (§4.9).** Two equal Booking choices in the Landing rail, Book seats and directly under it Book private sauna, the same size and with no other text (Lisa 2026-11-25; replaces the Text link); the price per Sauna on each Sauna card under the size line; the Seat statement gains the group sentence on Landing and in the Book seats rail; a Private sauna page with Sauna options (name, size and price, then Session rows), viewable by Session or by Sauna by regrouping one API response; the same Details, Review ("The sauna is not held while you pay.") and Confirmation (naming the Sauna).

### FR Coverage Map

*Cross-cutting FRs (FR-18, FR-20 to FR-23) have a primary epic and are applied again by every later story that adds a page, an input or an endpoint.*

| FR | Epic | Brief |
|---|---|---|
| FR-1 | Epic 1 | Landing page with Book seats, Before you come, Saunas, Find us |
| FR-2 | Epic 1 | Date and 1–10 Seats |
| FR-3 | Epic 1 | Windows with Seats left, nearest Windows, one total |
| FR-4 | Epic 1 (group sentence in Epic 5) | Seats, never a Sauna, in the Seat flow |
| FR-5 | Epic 1 | Details and Review with booking terms |
| FR-6 | Epic 1 | Simulated payment creates the Booking; one-time key |
| FR-7 | Epic 1 | Failed payment creates nothing |
| FR-8 | Epic 1 | Confirmation page and email |
| FR-9 | Epic 1 | One Window per Booking |
| FR-10 | Epic 1 | Store refuses over-capacity writes |
| FR-11 | Epic 1 | Last-Seat race has exactly one winner |
| FR-12 | Epic 1 | All or nothing |
| FR-13 | Epic 1 | Venue-wide, non-overlapping Windows; seed generation; NFR-3 |
| FR-14 | Epic 1 | Temporary conflicts end cleanly |
| FR-15 | Epic 2 | Administrator sign-in, throttle, sign-out |
| FR-16 | Epic 2 (status and history in Epic 4; Whole-sauna bookings and Placement in Epic 5) | Booking list by Window |
| FR-17 | Epic 2 (Guest-visible Change emails in Epic 4 and 5) | Outbox |
| FR-18 | Epic 1 (Guest input, seed IV-6); Epic 2 (sign-in input); Epic 4 and 5 (Change input) | Server-side validation |
| FR-19 | Epic 2 | Hashed passwords and password rules |
| FR-20 | Epic 2 (RB-1, RB-3, IV-7); Epic 1 (RB-4, guessed reference); Epic 4 (RB-4 guessed link, RB-5) | Role-based access |
| FR-21 | Epic 1 (privacy notice, cookies, no third party, no secret logs); Epic 2 (README security section); Epic 4 (Manage pages) | Personal data and privacy notice |
| FR-22 | Epic 1 (Guest pages); Epic 2 (Administrator pages); Epic 4 and 5 (their pages) | Laptop layout, one stylesheet |
| FR-23 | Epic 1 (Guest pages); Epic 2 (Administrator pages and the Core-done passes); Epic 4 and 5 (their pages) | WCAG 2.2 AA |
| FR-24 | Epic 3 | HTTPS only |
| FR-25 | Epic 4 | Manage link |
| FR-26 | Epic 4 | Move Seats |
| FR-27 | Epic 4 | Voucher instead of Seats |
| FR-28 | Epic 4 | Pay with a Voucher |
| FR-29 | Epic 5 | Book a whole Sauna |
| FR-30 | Epic 5 | Choose the Sauna |
| FR-31 | Epic 5 | Placement follows the Fill order (model test) |
| FR-32 | Epic 5 | Seat and Whole-sauna requests never interleave |
| FR-33 | Epic 5 | Cancel or move a Whole-sauna booking |
| FR-34 to FR-51, §4.17 | Not planned in this round | See the table under Functional Requirements |

**NFRs and DRs.** NFR-1, NFR-10 and DR-5 start in the skeleton story (Epic 1) and are proven from a fresh clone in Epic 2's Core-done story. NFR-2, NFR-3, NFR-4, NFR-5, NFR-9 and NFR-11 apply in every story that touches them; NFR-3's skipped/repeated-hour refusal is in Epic 1's Window story. NFR-6 is an acceptance criterion of every story. NFR-7 sets no target. NFR-8, DR-1 and the final DR-2 list of what is not delivered belong to the freeze (12–15 December), not to a story. DR-2 and DR-3 grow with each story and are checked in Epic 2's Core-done story. DR-4 is met by one branch and PR per story.

## Epic List

**Order and stopping points.** Epics are built in order 1 → 5. Each one works without the ones after it. After Epic 2 the Core is done; after Epic 3 the floor (Core plus HTTPS) is reached. Whatever is not reached by the feature cutoff (11 December) is reported as not delivered (DR-2). On 2026-11-19, with about 20 stories and interactive building, Epics 1 to 3 are the realistic target, and Epics 4 and 5 are planned so that they can be started if time allows.

### Epic 1: A Guest finds a session and books seats
A Guest opens the website, sees what Saunalöyly is and how to prepare, picks a date and a number of Seats, sees every session with its true Seats left and one total, enters a name and email, reviews the terms and pays with a Simulated payment. The Guest gets a confirmation page and the email as sent. However many Guests press Pay at once, no Seat is ever sold twice, and a Guest who loses gets a clear message, the nearest sessions with room and no charge. The Guest pages are complete (final copy, images, fonts), private by design and accessible on a laptop.
**FRs covered:** FR-1 to FR-14; FR-18 (Guest input, seed); FR-20 (RB-4, guessed reference); FR-21; FR-22 and FR-23 (Guest pages)
**Implementation notes:** Story 1 is the skeleton (AD-21): the compose stack (Caddy on HTTP, backend, Next.js, PostgreSQL), the migration runner, `/api`, server sessions and the layered package, proven live, ending in a real Landing served at `http://localhost:8000` with Venue facts from the API. This epic creates the shared homes that later epics reuse: `styles.css` with the design tokens, `frontend/components/`, `frontend/lib/api.js` and `server-api.js`, `content/`, `services/errors.py`, `outbox.py`, `reference.py`, `payment.py`, `tests/client.py` and the e2e fixture. The FR-10 bypass, FR-11 race (100 repetitions) and FR-14 tests travel with the stories that own them.

### Epic 2: The Administrator sees who is coming
The Administrator signs in safely, sees each session of a chosen day with its Seat capacity, Seats booked, Seats left and every Booking, and reads every email in the Outbox. Guests and anonymous visitors get nothing. The epic ends with the Core done: the README lets the examiner start, sign in and run every test from a fresh clone, and the accessibility passes cover every Core page.
**FRs covered:** FR-15, FR-16, FR-17, FR-19; FR-20 (RB-1, RB-3, IV-7); FR-18 (sign-in input); FR-21 (README security section); FR-22 and FR-23 (Administrator pages and the Core-wide passes)
**Implementation notes:** Depends only on Epic 1. Epic 1's tests get an Administrator session from a fixture, so they do not wait for this epic. The last story is "Core done": README (DR-2), clean-clone check (NFR-1, SM-4), axe on every Core page, the automated tab-order, 200 % zoom and Session-row-name checks, the short manual keyboard, 200 % zoom, screen-reader and tab-order passes that confirm them (FR-23), and the `ASSETS.md` check (DR-3).

### Epic 3: Every connection is secure (HTTPS)
The website and the API are served over HTTPS only, so passwords, sessions and, later, Manage links never travel unencrypted. The examiner can see the redirect, the headers and the cookie attributes for themselves.
**FRs covered:** FR-24 (HT-1 to HT-4)
**Implementation notes:** One story under AD-27: the three compose lines switch together, the HSTS header, the e2e fixture's TLS part, `tests/e2e/test_fr24_https.py`, and the README HTTPS section with the `localhost` limits. Reaching the end of this epic reaches the floor.

### Epic 4: A Guest changes seats or takes a voucher
With the Manage link in the confirmation email, a Guest can see their Booking and, until 12 hours before the start, move some or all Seats to another session or give them up for a Voucher worth what was paid. A Voucher pays for a later Booking in full or in part. The Administrator sees each Change in the Booking list.
**FRs covered:** FR-25, FR-26, FR-27, FR-28; FR-16 (status and history); FR-18 (Change input); FR-20 (RB-4 guessed link, RB-5); FR-21, FR-22 and FR-23 (Manage pages)
**Implementation notes:** Depends on Epics 1 to 3 (HTTPS before Manage links are sent, PRD §10.1). The Manage page and its confirming-step pattern become shared components that Epic 5 reuses. Moving Seats is built before the Voucher (PRD §4.8). The sample Bookings get Manage links in the Outbox (AD-18).

### Epic 5: A group books a whole sauna
A Guest chooses Private sauna, sees which Saunas can be booked whole on a date, with size, price and free sessions, and books one. Until 72 hours before the start, the Guest can cancel it for a refund or a Voucher, or move it. Seat bookings are counted around Private saunas so that no Seat is ever lost or sold twice, and the Administrator sees each session's Placement.
**FRs covered:** FR-29, FR-30, FR-31, FR-32, FR-33; FR-1.7 and FR-4 (price per Sauna, group sentence); FR-16 (Whole-sauna bookings and Placement in the list)
**Implementation notes:** Depends on Epic 4 (FR-33 uses the Manage link and the Voucher). The first story starts with Lisa choosing the Whole-sauna prices and which Saunas are Bookable whole (seed). This epic builds the FR-31 Hypothesis model (AD-26), which also takes Epic 4's move and Voucher actions as rules, and the group-C parallel races.

## Epic 1: A Guest finds a session and books seats

A Guest opens the website, sees what Saunalöyly is and how to prepare, picks a date and a number of Seats, sees every session with its true Seats left and one total, enters a name and email, reviews the terms and pays with a Simulated payment. The Guest gets a confirmation page and the email as sent. However many Guests press Pay at once, no Seat is ever sold twice, and a Guest who loses gets a clear message, the nearest sessions with room and no charge. The Guest pages are complete (final copy, images, fonts), private by design and accessible on a laptop.

### Story 1.1: The capacity slice runs on the spine's backend structure

As Lisa, the builder,
I want the existing slice moved onto the layered backend, the migration runner, the `/api` paths and server-side sessions without loosening any rule,
So that every later story builds on the spine's structure and the FR-10 proof stays green throughout.

**Acceptance Criteria:**

**Given** the slice in `src/booking_platform/` (`app.py`, `db.py`, `schema.sql`)
**When** the story is done
**Then** the code lives in `api/`, `services/`, `db/` and `config.py` as in the spine's Structural Seed, with `api` → `services` → `db` and `config` as a leaf (AD-1)
**And** SQL text appears only in `db/` and `migrations/`, and no `api` module opens a connection or holds a business rule

**Given** the slice's `schema.sql`
**When** the backend starts, or the test run starts
**Then** the runner in `db/migrate.py` applies `migrations/0001_core.sql` (the slice's `schema.sql`, moved unchanged) and any later numbered file in order, records full file names in `schema_migrations`, and refuses to start if two files share a number (AD-15)
**And** a database that has `windows` but no `schema_migrations` counts as having `0001` applied

**Given** a refusal anywhere in the backend
**When** it is raised
**Then** it is `services.errors.Refused(code, **facts)`, store errors are translated in `db` by constraint name (also at COMMIT), and an unnamed or unmapped store error is a 500 whose store text never reaches the response (AD-1)
**And** `api/errors.py` is the one code → status table, starting with the slice's codes and `403 cross_origin`, and every refusal uses the envelope `{"detail": {"error", "message"?, …facts}}` (AD-16); shape errors are `422 invalid_input` with `fields`

**Given** the slice's endpoints
**When** they are called
**Then** every path is under `/api` (`/health` is `/api/health`), Administrator-only endpoints (Whole-sauna booking, Blocks, marks, Settings) are on one `/api/admin/` router whose dependency answers 401 to anonymous callers and 403 to non-Administrators and changes nothing (AD-10)
**And** any unknown `/api` path, and any 405, answers the JSON `404 not_found` envelope, `redirect_slashes=False` is set on the app and every router, and `/docs` and `/openapi.json` are off (AD-10, AD-22)

**Given** a browser with no session
**When** it calls `POST /api/session`
**Then** a `sessions` row is created in a new numbered migration with only the SHA-256 hash of a 256-bit token, the cookie is HttpOnly, `SameSite=Strict`, `Path=/` (and `Secure` only when `BP_HTTPS` is on), the anonymous lifetime is 24 hours sliding, and a still-valid session is returned instead of a new one (AD-8)
**And** the slice's client-supplied `session_id` is gone; the slice's Hold endpoint uses the server session, a Guest write without a session is `401 no_session`, and expired sessions are purged at startup

**Given** a state-changing request
**When** its `Origin` is not the `BP_BASE_URL` origin, or it has no `Origin` and no `Sec-Fetch-Site: same-origin`
**Then** it is refused `403 cross_origin` and nothing changes, and no switch turns the check off (AD-8)
**And** `tests/test_fr18_csrf.py` asserts this

**Given** a Seat request
**When** it asks for fewer than 1 or more than 10 Seats
**Then** Pydantic refuses it (422) before any write, and every Pydantic model uses `extra="forbid"` (FR-2, Conventions: Input)

**Given** `config.py`
**When** the backend starts
**Then** it is the only reader of `BP_DATABASE_URL`, `BP_BASE_URL`, `BP_HTTPS`, `BP_HOST`, `BP_PORT`, `BP_ROOT` and `BP_TEST_SWITCHES`, each with a working local default (AD-22), and `booking_dev` is created through the server's `postgres` database when the default URL is used and it is missing
**And** `config` refuses to start when `BP_HTTPS` is on and `BP_BASE_URL` is not `https://`

**Given** the test-switch file
**When** the backend starts
**Then** a missing file, or a path that is not a regular file, means every switch is off; an unreadable or unparsable file stops startup with one line naming it; the switches are frozen in `config` and read only at the seams `payment.charge` and `db.run` (`force_conflict`, for HTTP-request runs only) (AD-14)
**And** `config/test-switches.example.toml` (all off) is committed and `config/test-switches.toml` is git-ignored

**Given** `db.run(work)`
**When** an action runs
**Then** it runs at READ COMMITTED set on the pool with `TimeZone = 'UTC'`, retries 40001 and 40P01 a bounded number of times, and `db.lock_windows(c, ids)` locks Windows in id order (AD-3, AD-4)

**Given** the CLI
**When** `uv run booking-platform dev` or `serve` is run
**Then** one uvicorn process starts on `127.0.0.1:8001` (dev with `--reload`), migrates, and no request body, header or cookie is logged (AD-19, AD-22)

**Given** the slice's tests (`test_application_rules.py`, `test_fr10_bypass.py`, `test_fr10_through_the_api.py`, `test_fr14_retry.py`)
**When** `uv run pytest` runs
**Then** the session fixture first runs `docker compose up -d --wait db`, the API layer starts its own backend with uv against a recreated `booking_test`, and every request goes through the new shared `tests/client.py::api_client`, which sends `Origin` (Conventions: Tests)
**And** every slice test passes with its assertions unchanged: Administrator calls use a fixture-made Administrator session, and Windows are filled with Bookings of at most 10 Seats or raw inserts (AD-21)
**And** the harness derives its admin URL from `BP_DATABASE_URL`, `BP_TEST_ADMIN_URL` is dropped, and each `MUTATIONS` entry run with `BP_TEST_MUTATE` still turns its bypass test red (AD-2)

**Given** the README
**When** the story is merged
**Then** it states the dev backend command and `uv run pytest`, and no longer says that architecture has not started (DR-2)

### Story 1.2: The platform starts with one command and shows its Terms and Privacy notice

As a Guest,
I want to open Saunalöyly's booking terms and privacy notice in a calm, readable page,
So that I know the rules and how my data is handled before I book.

**Acceptance Criteria:**

**Given** a fresh clone with uv, Node.js and Docker installed
**When** `docker compose up --build --wait` is run
**Then** four services start (proxy, backend, frontend, db), each with the healthcheck of AD-27 (db `pg_isready` over TCP, backend `/api/health`, frontend `wget` on `/privacy`, proxy Caddy admin `:2019`) and `depends_on: condition: service_healthy`, and the website answers at `http://localhost:8000` (NFR-1)
**And** Caddy (`caddy:2.11`) is the only published web port, on `127.0.0.1`; `@api path /api /api/*` goes to the backend with the path unchanged and everything else to the frontend; the database port is published on `127.0.0.1:${DB_PORT:-55432}`; the db and `caddy_data` use named volumes (AD-27)
**And** the compose file sets the Core mode: `SITE_ADDRESS: http://localhost:${HTTP_PORT:-8000}`, `BP_HTTPS: "off"`, `BP_BASE_URL: http://localhost:${HTTP_PORT:-8000}`, and mounts the directory `${SWITCHES_DIR:-./config}` read-only at `/app/config` (AD-14, AD-27)

**Given** the backend image
**When** it is built
**Then** the root `Dockerfile` copies only the named paths (`pyproject.toml`, `uv.lock`, `README.md`, `.python-version`, `src/`, `migrations/`, `seeds/` if present, `content/` if present, `config/`), runs `uv sync --locked`, sets `PATH`, `UV_PYTHON_DOWNLOADS=never` and `BP_ROOT=/app`, and runs without `uv run` (AD-22)
**And** the root `.dockerignore` lists `**/node_modules`, `**/.next`, `.venv`, `.git`, `.logs`, `.docs`, `config/test-switches.toml` and `frontend/content` (AD-17)

**Given** `frontend/`
**When** it is scaffolded
**Then** it is Next.js with the App Router in JavaScript, `output: 'standalone'`, with no `app/api/`, `route.js`, Server Action, `middleware.js` or `proxy.js`; the files `create-next-app` adds (`favicon.ico`, `icon.*`, `page.module.css`, `globals.css`, everything in `public/`) are deleted; `NEXT_TELEMETRY_DISABLED=1` is set by a Node script, not by shell syntax (AD-17)
**And** `frontend/Dockerfile` follows Next's `with-docker` layout on `node:24-alpine` with the repository root as build context, `HOSTNAME=0.0.0.0`, `PORT=3000` and `node server.js`
**And** `npm --prefix frontend run dev` runs `next dev -H 127.0.0.1` on port 3000 with `skipTrailingSlashRedirect: true`, and rewrites `/api/:path*` to `http://127.0.0.1:8001/api/:path*` in development only (AD-17)

**Given** the shared frontend homes
**When** this story creates them
**Then** `frontend/app/styles.css` is the one stylesheet, imported once in the root layout (and in `global-error.js`), defining every DESIGN.md token as a CSS custom property (UX-DR1), with square corners, no shadows and light mode only
**And** Finlandica and Source Sans 3 are self-hosted in `frontend/public/` through `@font-face` with the DESIGN.md fallback stack, keep tabular figures and ö, and are listed in `ASSETS.md` (UX-DR2, DR-3)
**And** `frontend/lib/api.js` is the only browser `fetch` caller (relative `/api/…`, same-origin cookies, `Idempotency-Key` support, one error type from the envelope), and `frontend/lib/server-api.js` is the only server-side caller (`API_INTERNAL_URL`, `cache: 'no-store'`, no cookie, never throws, `unstable_rethrow` first in its catch) (AD-17)
**And** `frontend/components/` holds the first shared components: the Guest shell (sticky 320 px rail plus main, centred up to 1320 px, UX-DR3), Wordmark (UX-DR7), Rail (UX-DR8) and Text link (UX-DR6)
**And** the shell keeps its rail from 1024 to 1365 px, uses `max-width: 1199px` as the one breakpoint where two- and three-column page parts stack, and sets no fixed width that would block the narrow layout of FR-51 (UX-DR36)

**Given** the root layout
**When** any page renders
**Then** it carries the `<noscript>` line "This booking page needs JavaScript.", English page language, and one client component that moves focus as AD-17 says (fragment target on first load only if it exists; after client navigation the fragment target or the page's `h1`; targets with `tabindex="-1"`) and sets page titles "<heading> – Saunalöyly" with the "Error: " prefix when a form shows errors (UX-DR33)
**And** `app/not-found.js` shows "This page is not available." with a link to Landing, `app/error.js` and `app/global-error.js` show the "please try again" Notice, and Next.js's default 404 and error pages are never shown (UX-DR29)

**Given** a Guest opens Terms or the Privacy notice
**When** the page loads
**Then** it shows the full text rendered in `mockups/key-terms.html` (heading "Booking terms"; Who we are … Your data) or `mockups/key-privacy.html` (Who is responsible … Your rights), in the Guest shell with only the Wordmark in the rail (UX-DR28, FR-5, FR-21)
**And** the Privacy notice states the controller and contact, what is stored and why, legal basis, retention, who sees the data, rights including Datatilsynet, and how the data is protected (FR-21)
**And** neither page calls the API, so `/privacy` renders with the backend stopped

**Given** the e2e layer
**When** `uv run pytest` runs
**Then** `tests/e2e/conftest.py` (a new shared home) starts compose project `booking_e2e` with its own env file (`HTTP_PORT`, `HTTPS_PORT`, `DB_PORT`, `SWITCHES_DIR`), runs `up --build --wait` and ends with `down -v`, routes every compose call through one helper, and exposes one `base_url` (`http://localhost:<HTTP_PORT>`) that every e2e test uses (AD-27)
**And** `npm --prefix frontend ci` and `uv run playwright install chromium` are the two one-time preparation commands (NFR-1)

**Given** the running e2e stack
**When** `tests/e2e/test_stack_routing.py` runs
**Then** `/api/health` answers through Caddy, `/api` and `/api/x` answer the JSON `404 not_found` envelope (never a page), `/api/x/` is the same 404 with no redirect, an unknown page shows "This page is not available.", the `<noscript>` line is present, `/privacy` renders while `backend` is stopped, and every site response carries `Referrer-Policy: no-referrer` and every `/api` response `Cache-Control: no-store` (AD-10, AD-17, AD-27)
**And** the story's record states that the healthchecks, `caddy adapt` of the Caddyfile and `curl -i http://localhost:8000/` were run live, and that `next build` lists the routes that use `server-api.js` as dynamic (closes the issues.md items on Caddy, compose and Next.js not being run)

**Given** `tests/e2e/a11y.py`, the shared accessibility helper (a new shared home)
**When** an e2e test uses it
**Then** it offers `check_axe(page)` (axe-core from `frontend/node_modules`, no level A or AA failure, 1.4.10 Reflow listed as the one known gap) and `no_horizontal_scroll(page)` at 1024, 1366 and 1920 px wide (FR-22, FR-23)
**And** it offers `press(page, key)` and `tab_to(page, locator)`, which after every key press assert that the focused element shows the 3 px `focus` ring (its computed outline) and is not hidden: inside the viewport after scrolling, and the topmost element at its centre (WCAG 2.4.7, 2.4.11, UX-DR34)
**And** it offers `tab_order(page, steps)`, which returns the focus stops in order as role and accessible name, and `zoomed(browser, width, height)`, which opens a page with a viewport of half the given width and height and `deviceScaleFactor` 2, so the page is laid out as at 200 % browser zoom (WCAG 1.4.4)
**And** every e2e step "with the keyboard alone", in this story and every later one, goes through `press` and `tab_to`, so focus visibility is checked in each story and not first in Story 2.4

**Given** Terms and the Privacy notice
**When** the e2e tests run
**Then** `check_axe` passes, every link can be reached and followed through `tab_to` and `press`, and `no_horizontal_scroll` passes (FR-22, FR-23, UX-DR34)
**And** `tests/e2e/test_fr21_privacy.py` is created and asserts for both pages that every request goes to the `base_url` origin, no cookie is set, and exactly one stylesheet of ours and no `<style>` element of ours is loaded (FR-21, Conventions: Tests)

**Given** `ASSETS.md`
**When** `tests/test_dr3_assets.py` runs
**Then** every file in `frontend/public/` has a row in `ASSETS.md` and the test fails when one is missing (AD-17, DR-3)

**Given** the README
**When** the story is merged
**Then** it gives the one start command, the two preparation commands, `uv run pytest`, the dev frontend command, and the local operations (`docker compose logs backend proxy`, `down`, `down -v`) (DR-2)

### Story 1.3: The Landing page presents the Venue

As a first-time Guest,
I want a calm landing page that tells me what Saunalöyly is, how to prepare and where it is,
So that I want to visit and can start booking in one step.

**Acceptance Criteria:**

**Given** a database after migrations
**When** the backend starts
**Then** `seeds/` is applied idempotently in every environment (AD-18): the four Saunas Rauha 7, Löyly 10, Kajo 12 and Lumo 15 in that Fill order, the price of NOK 250 per Seat (25000 øre), the opening hours 10:00–22:00, the Session length of 1 h 30 min, and the Venue address and contact (Badstubrygga 4, 0000 Havbukta; +47 01 23 45 67; hello@saunaloyly.example) (addendum J, EXPERIENCE.md Open Item 4)
**And** the seed writes a value only where the row is absent or a seed-owned column is NULL, never overwrites, and goes through the same validation as Administrator input, so a negative price or Capacity in the seed stops startup with a clear error (FR-18 IV-6)
**And** any new reference column added by this story's migration gets the seed value as its default in the same change (AD-18)

**Given** the Venue facts
**When** a client calls the public Venue-facts endpoint (`GET /api/venue`, confirmed by Lisa 2026-11-20)
**Then** it returns the Venue name, address and contact, opening hours, Session length, price per Seat in øre and the Saunas (id, name, Capacity) in Fill order, needs no session and writes nothing (AD-4, AD-16)
**And** `tests/test_fr01_venue.py` asserts the response shape and that a restart does not change or duplicate the seeded rows (NFR-10)

**Given** a Guest opens `/`
**When** the page renders
**Then** the rail shows the Wordmark as the page's one heading (not a link), the opening hours and Session length, the price per seat and the **Book seats** primary button, all in the first view at 1366×768 (FR-1.2, FR-1.6, FR-1.7, UX-DR5, UX-DR15)
**And** the main column shows, top to bottom, the hero image, the Venue description "Löyly is the steam that rises when water meets the hot stones. At Saunalöyly you come to Finnish saunas by the sea, where you can swim all year round.", "Before you come", "The saunas", the image band and "Find us" (FR-1.1, UX-DR15)
**And** the page's server component reads the Venue facts through `server-api.js` after awaiting `connection()`, and no Venue fact is hard-coded in the frontend (AD-16, AD-17)

**Given** "Before you come"
**When** it renders
**Then** it holds three Rule lists, What to bring, Safety and Practical, with the verbatim items in EXPERIENCE.md Voice and Tone, in three columns down to 1200 px and stacked below, followed by one image (FR-1.4, UX-DR15, UX-DR16)
**And** the section has `id="before-you-come"` and `tabindex="-1"`, and opening `/#before-you-come` directly shows and focuses it (FR-1.4, AD-17)

**Given** "The saunas"
**When** it renders
**Then** its intro is the Seat statement "A booking gives you seats in the shared saunas open during your session. On site you can move freely between them." and each Sauna card shows its image, name, size line ("Holds 7"), and its line ("Rauha means peace." …), is not a link and is not selectable (FR-1.5, FR-4, UX-DR16)

**Given** "Find us"
**When** it renders
**Then** it shows the fictional address and contact from the Venue facts and Text links to Terms and the Privacy notice (FR-1.3, FR-1.8, UX-DR16)

**Given** the Venue-facts call fails or times out
**When** Landing renders
**Then** a Notice says "please try again" and the Book seats action is still there and works (UX-DR11, UX-DR16)
**And** the shared Notice component is created in `frontend/components/` by this story

**Given** the final images in `ux-designs/…/mockups/images/`
**When** they are moved to `frontend/public/`
**Then** each has alt text that says what it shows, a row in `ASSETS.md` with source and licence, and is shown as a plain `<img>`; Finnish words other than names are marked `lang="fi"` (UX-DR4, UX-DR35, DR-3)
**And** `tests/test_dr3_assets.py` passes

**Given** the Book seats action
**When** the Guest presses it
**Then** it navigates to the Book seats route (the page itself arrives in Story 1.4), and no Landing load creates a session (FR-1.2, AD-8)

**Given** the e2e layer
**When** `tests/e2e/test_fr01_landing.py` runs
**Then** it asserts the sections above, the page title "Saunalöyly", axe with no A or AA failure, that every link and the button can be reached with the keyboard alone, and no horizontal scroll at 1024, 1366 and 1920 px (FR-22, FR-23)
**And** `tests/e2e/test_fr21_privacy.py` gains Landing and `/#before-you-come`: no cookie, every request to the `base_url` origin, one stylesheet of ours (FR-21)

### Story 1.4: A Guest picks a date, a number of seats and a session

As a Guest,
I want to pick a day and the number of seats and see every session with its true seats left and one total,
So that I know in seconds whether there is room for us and what it will cost.

**Acceptance Criteria:**

**Given** the `settings` row
**When** this story's migration runs
**Then** it adds the Booking horizon (default 4 weeks, from the moment of booking to the Window's start) and `windows_generated_through`, and the seed holds the Window schedule: eight Windows a day of 1 h 30 min starting at 10:00, 11:30, 13:00, 14:30, 16:00, 17:30, 19:00 and 20:30 Venue time (AD-4, AD-18, addendum J)
**And** the time predicates are SQL functions called by both the listing and later actions: `venue_date(wid)`, `within_horizon(wid)`, `window_started(wid)` (`app_now() >= lower(during)`) and the existing `booking_deadline(wid)`; no timestamptz is cast to a date or time without `AT TIME ZONE settings.venue_tz` (AD-4)

**Given** the Venue date of `app_now()`
**When** a Window listing is read
**Then** `windows.ensure_generated()` first inserts, under an advisory lock, only the Windows after `windows_generated_through` up to the end of the Booking horizon, and a second call creates no duplicates, so a fresh clone always has bookable dates (FR-13, AD-4)
**And** the generated Windows keep their local clock times across a daylight-saving change (NFR-3)

**Given** seed or Administrator input
**When** it holds Windows that partly overlap, are identical or are nested
**Then** it is rejected, while back-to-back Windows such as 15:00–16:30 and 16:30–18:00 are accepted (FR-13 E1, E2)
**And** a Window that would start or end in a skipped or repeated hour on a daylight-saving day is refused (NFR-3)
**And** `tests/test_fr13_windows.py` holds `test_e1`, `test_e2`, the DST refusals and the idempotent generation, moving the clock only through `clock.off` (AD-4)

**Given** a date and a number of Seats from 1 to 10
**When** the Guest's client calls the Window listing (`GET /api/windows?date=&seats=`, confirmed by Lisa 2026-11-20)
**Then** it returns every Window of that Venue date that is inside the Booking horizon and before its Booking deadline, in time order, each with id, start, end, `seats_left` from `seats_left()` and `already_started`, plus `today`, `horizon_end` and `horizon_days` (FR-3, AD-5, AD-16)
**And** Windows past their Booking deadline are left out, and the listing writes nothing except `ensure_generated()` (AD-4)
**And** a date outside the horizon or malformed, or a Seat number outside 1–10, is refused and nothing is written (FR-2, FR-18 IV-1, IV-2)

**Given** no Window on the date has room for the chosen number
**When** the listing is read
**Then** it also returns up to three nearest Windows with room for that number, from the same day first, then the following days within the horizon, each with its date, time and Seats left; with no room anywhere in the horizon it returns none (FR-3)
**And** `tests/test_fr03_listing.py` asserts Seats left = Seat capacity − Seats booked, the nearest-Windows order and limit, `already_started` on a started Window before its deadline, and that Windows are independent: Seats booked in one Window leave Seats left in another unchanged (FR-13 E2, E4)

**Given** a Guest opens Book seats from Landing
**When** the page loads
**Then** the frontend calls `POST /api/session` once, so exactly one session cookie is set, and the page shows the heading "Book seats" and three questions with nothing pre-selected: date, number of seats, session (AD-8, FR-21, UX-DR21)
**And** the rail shows the Wordmark linking to Landing, the Seat statement, the changing-time note and the Terms and Privacy notice links (FR-4, UX-DR8)

**Given** the Date calendar
**When** the Guest types `dd.mm.yyyy` or picks a day
**Then** the field and the grid stay in step; only dates with a Window inside the horizon and before its deadline can be chosen; the calendar ends at `horizon_end` with the line "Booking opens 4 weeks ahead." (number from `horizon_days`); "Next month" and, once forward, "Previous month" move the month (FR-2, UX-DR17)
**And** the grid is a radio group named "Pick a day, <Month> <Year>" with full day names, one tab stop and arrow keys; a typed date is checked on blur or Enter with "Enter the date as dd.mm.yyyy" or "This date cannot be booked. Pick a day below." as a Field error (UX-DR9, UX-DR17, UX-DR34)

**Given** the Seat picker and the Session list
**When** the Guest chooses a number and a date
**Then** the Seat picker is a `fieldset` of ten radio cells 1–10, and the Session list is a `fieldset` listing every Window of the date in time order with "Loading sessions" while reading (UX-DR18, UX-DR19, UX-DR35)
**And** each row shows start, end and Seats left, has the Seats left text in its accessible name ("13:00 to 14:30, 12 seats left"), shows "Already started" when started, and a row with too few Seats is a disabled radio labelled "1 seat left, not enough for 2" or "Sold out" (FR-3, UX-DR19)
**And** no row shows a price or a Sauna, and no countdown, viewer count or other urgency cue appears anywhere (FR-3, FR-4, NFR-9)

**Given** a number of Seats is chosen
**When** the Total block renders in the rail
**Then** it shows "Total NOK 500 incl. VAT" for 2 Seats at the seed price, with the per-seat line under it, once and never per Session, and the change is announced without moving focus (FR-3, UX-DR20)

**Given** the Guest changes the date or the number
**When** the Sessions are read again
**Then** changing the date clears the chosen Session, and a chosen Session that no longer fits the number is cleared with a Notice at question 3 (UX-DR19)
**And** a date with no room shows a Notice "No room for 2 seats on Saturday. The nearest sessions with room:" with the Nearest sessions links (a new shared component), and choosing one selects that date and Session, keeps the number and moves focus to the chosen Session (FR-3, UX-DR13, UX-DR21)
**And** no room in the whole horizon shows "There is no room for 2 seats in the next 4 weeks." with no alternatives (UX-DR21)

**Given** "Continue booking" is always enabled
**When** the Guest presses it with a choice missing
**Then** an Error summary (a new shared component) appears at the top of the main column with "Choose a date", "Choose the number of seats" or "Choose a session", takes focus, links each entry to its question, the matching Field errors show, and the title gains "Error: " (UX-DR12, UX-DR21, UX-DR33)
**And** with all three chosen, the date, number and Window are stored in the Booking draft in `sessionStorage` (`draft:seats`, read only inside effects) and the Guest goes to the Details address (the Details page arrives in Story 1.5) (AD-9, AD-17, UX-DR26)
**And** a reload of Book seats restores the draft and reads the Sessions again

**Given** the e2e layer
**When** `tests/e2e/test_fr02_book_seats.py` runs
**Then** it completes the three choices with the keyboard alone, checks the page title "Book seats – Saunalöyly", axe with no A or AA failure, the whole page and the total in the first view at 1366×768 with all eight seed Sessions, and no horizontal scroll at 1024, 1366 and 1920 px; below 1200 px the date column stacks above the seats and Sessions (FR-22, FR-23, UX-DR22, UX-DR36)
**And** `tests/e2e/test_fr21_privacy.py` asserts exactly one session cookie after Book seats and every request to the `base_url` origin (FR-21)

### Story 1.5: A Guest pays and gets a confirmation

As a Guest,
I want to enter my name and email, review the booking and its terms, pay, and get a confirmation with the email as sent,
So that I am certain the seats are mine and know what to do when I arrive.

**Acceptance Criteria:**

**Given** this story's migration
**When** it runs
**Then** `bookings` gains `reference`, `name`, `email`, `price_per_seat_ore`, `total_ore`, `session_id` (FK `sessions`, `ON DELETE SET NULL`), `status` (`active` | `cancelled`) and `entry_time` (default `app_now()`, apart from `created_at`); `window_booked_seats()` counts only active rows; the `bookings` triggers fire only on `INSERT`, `DELETE` and `UPDATE OF window_id, seats, status` (AD-7, AD-13)
**And** it creates `payments`, `outbox_emails` and `idempotency_keys` (FK `sessions` `CASCADE`, `UNIQUE key`, `endpoint`, `request_hash`, `booking_id`) as AD-9, AD-12 and AD-13 define them, and nothing else

**Given** a Guest with a session, a Window and 1–10 Seats
**When** the client sends `POST /api/bookings` with `{window_id, seats, name, email}` and an `Idempotency-Key`
**Then** in one `db.run` transaction, after `lock_windows`, the key is read first, the Booking is inserted with a reference from `services.reference` (8 upper-case Crockford characters, `ON CONFLICT DO NOTHING`, at most 5 tries), the charge decided before the lock by `services.payment.charge()` is written as a `payments` row, and the confirmation is written by `services.outbox.send()` (AD-3, AD-9, AD-13, AD-20, AD-12)
**And** the Booking stores `price_per_seat_ore` and `total_ore = seats × price` and every page and email shows those values, never a recomputation (AD-13, NFR-4)
**And** Seats left for the Window drops by exactly the Seats booked (FR-6)
**And** the run needs no payment credential or external service (FR-6)

**Given** the same key from the same session with the same request
**When** it is sent again (double click, reload or retry)
**Then** nothing is written and the first outcome is returned: the Booking and the email it sent (FR-6, AD-9)
**And** only a success is stored under a key, the `request_hash` covers only outcome-defining fields and never name or email, and `tests/test_fr06_payment.py` asserts one Booking and one charge after two identical submits

**Given** the input
**When** it is invalid
**Then** these are rejected with no Booking, payment or email: Seats that are 0, negative, fractional, not a number or above 10 (IV-1); a malformed or unknown Window (IV-2); a missing required field or an unknown extra field (IV-3); a name that is empty or over 100 characters or an email that is empty, over 254 characters or malformed (IV-4, FR-5); a request for more than one Window (FR-9)
**And** a name holding SQL, a script tag or HTML is stored and only ever shown as escaped text, never executed (IV-5)
**And** `tests/test_fr18_validation.py` holds IV-1 to IV-5 for this endpoint

**Given** the text shared by pages and emails
**When** this story creates `content/`
**Then** the booking terms ("A booking for a fixed date cannot be withdrawn." "A booking cannot be changed or refunded." "If Saunalöyly cancels your session, you choose a refund or a voucher.") and the reception sentence "Keep your booking reference and give it at reception when you arrive." live once in `content/` as JSON `{"paragraphs": [...]}`, and both `services` and the frontend read them; a Node `predev`/`prebuild` script copies them to `frontend/content/` (git-ignored) (AD-12, AD-17, UX-DR37)

**Given** a successful Booking
**When** the confirmation email is written
**Then** it is plain English text in the line layout of `mockups/key-confirmation.html` with the Booking reference, date and session, Seats, total paid, the Guest's email, Venue identity and contact, the reception sentence with no heading, the booking terms, an absolute link to `/#before-you-come` built from `BP_BASE_URL` and `config.links`, and "Simulated payment: no money moves" (FR-6, FR-8, AD-12, UX-DR38)
**And** it contains no Manage link and no Sauna name (FR-4, FR-8)

**Given** the paying browser session
**When** the client reads `GET /api/bookings/{reference}/confirmation`
**Then** it returns the Booking facts and the stored email; from any other session, or for an unknown reference, it returns the same `404 not_found`, so guessing a reference reveals nothing (FR-8, FR-20 RB-4, AD-12)

**Given** the Booking draft from Story 1.4
**When** the Guest opens Details
**Then** the page shows "Your details", Back, name and email Text fields, a Privacy notice link and "Continue booking"; empty or invalid fields give an Error summary and Field errors ("Enter your name", "Enter a valid email address") with input kept; Details with no chosen Session goes to Book seats without an error (FR-5, UX-DR9, UX-DR23, UX-DR26)

**Given** Details is complete
**When** the Guest opens Review
**Then** it shows "Review" and Back, then two columns down to 1200 px: the Booking summary (Date, Session, Seats, Total, Name, Email, Venue, Contact) on the left, and on the right "Booking terms" with the three shared statements, Terms and Privacy notice links, the unticked "I accept the booking terms" checkbox, and "Pay NOK 500" with "Simulated payment: no money moves" beside it (FR-5, FR-6, UX-DR10, UX-DR14, UX-DR24)
**And** the idempotency key is made when the Guest reaches Review and kept in the draft for every retry (AD-9)
**And** Pay without the checkbox gives an Error summary and a Field error and charges nothing; while paying, Pay shows "Processing", keeps focus and takes no second press (FR-5, UX-DR5)
**And** Back, the browser back button, and leaving for Terms or the Privacy notice and returning keep everything entered (FR-5, UX-DR6)

**Given** the payment succeeds
**When** the Guest lands on `/confirmation/[reference]`
**Then** it shows "Booking confirmed" in `success`, the Reference display, the reception sentence directly under it, the Booking summary with the stored total, the booking terms, a link to "Before you come" and "Sent by email:" with the stored email (FR-8, UX-DR14, UX-DR27)
**And** a reload in the same browser session shows it again, any other browser gets "This page is not available.", and after payment the draft holds only the reference, so Back from Confirmation and the addresses of Details and Review show Confirmation and can never pay again (FR-6, FR-8, UX-DR26)
**And** pressing Book seats after a paid Booking starts a new draft with a new key

**Given** the seed
**When** the backend starts
**Then** a few sample Bookings, given as offsets from the run date, are created through `services.booking.create` under one fixed seed session and fixed keys, including one Window with 42 of 44 Seats booked and one fully booked; a restart creates no duplicates (AD-18, addendum J)
**And** Lisa approves the exact list in this story

**Given** the Seat flow
**When** `tests/test_fr04_no_sauna.py` walks its responses and the confirmation email
**Then** no Sauna name or id appears (FR-4, AD-25)

**Given** the e2e layer
**When** `tests/e2e/test_fr05_book_and_pay.py` runs
**Then** a Guest books 2 Seats from Landing to Confirmation with the keyboard alone, the Window then shows 2 fewer Seats left, axe reports no A or AA failure on Details, Review and Confirmation, the titles are "Your details – Saunalöyly", "Review – Saunalöyly" and "Booking confirmed – Saunalöyly", Pay is in the first view at 1366×768, and there is no horizontal scroll at 1024, 1366 and 1920 px (FR-22, FR-23, SM-1 first part)
**And** `tests/e2e/test_fr21_privacy.py` covers Details, Review and Confirmation, and a name with a script tag is shown as text on Review and Confirmation (FR-18 IV-5, FR-21)

### Story 1.6: A Guest who cannot get the seats is told why and charged nothing

As a Guest,
I want a clear message, the nearest sessions with room and no charge when the seats are gone, the session has closed or the payment fails,
So that I can trust that I never pay for seats I did not get and can book again without retyping.

**Acceptance Criteria:**

**Given** a Window with fewer Seats left than requested
**When** `POST /api/bookings` is judged after the lock
**Then** it is refused `409 no_seat_free` with the fact `seats_left` (0 or the true number), and no Booking, payment, Outbox email or idempotency key is written (FR-12, AD-16)
**And** `tests/test_fr12_all_or_nothing.py::test_a6` (42 of 44 booked, 3 requested) and `::test_a7` (44 booked, 1 requested) assert the refusal and that nothing changes

**Given** a Window outside the Booking horizon or past its Booking deadline
**When** a booking request reaches it after the lock
**Then** it is refused `409 outside_horizon` or `409 deadline_passed` in that order, judged on `app_now()`, and nothing is written (FR-18 IV-2, AD-4, AD-16)
**And** the tests move the clock only through `clock.off` and never wait in real time (NFR-11)

**Given** the test switch `payment = "fail"`
**When** a Guest pays
**Then** the request is refused, no Booking, Seats, charge or email is created, nothing is stored under the key, and a retry with the same key after the switch is off succeeds (FR-7, AD-9, AD-14)
**And** with `payment = "hold"` the action returns `409 payment_pending` before anything is written, and resubmitting with the same key after the switch is off books once (AD-14)

**Given** the switch `force_conflict`
**When** a Guest pays
**Then** every attempt rolls back, `db.run` stops after its bounded retries, the answer is `503 try_again`, and no Booking, charge, email or partial data remains; the trigger-based test that produces a real 40001 stays alongside (FR-14, AD-3, AD-14)
**And** `tests/test_fr14_retry.py` asserts "No seat free" and "please try again" are different codes

**Given** two parallel requests for the one remaining Seat
**When** `tests/test_fr11_last_seat_race.py` runs them through the API against real PostgreSQL, 100 repetitions per run
**Then** in every repetition exactly one Booking is created, Seats left becomes 0 and never negative, the loser gets `409 no_seat_free` with `seats_left` 0, has no payment row, no Outbox email and no key stored (FR-11, CT-2, CT-3)
**And** N parallel requests that together ask for more Seats than are left never get more than are left (FR-10), and the slice's API test of this runs on the new booking endpoint with its assertions unchanged (AD-21)

**Given** `test_fr10_bypass.py` on the new layout
**When** it writes an over-capacity Booking straight to the store, around the API
**Then** the store refuses it by the named constraint, and each `MUTATIONS` entry run with `BP_TEST_MUTATE` turns its test red (FR-10, AD-2)

**Given** a key known from another session, or with a different request
**When** it is sent
**Then** the answer is `409 invalid_key` and nothing is written (AD-9)

**Given** a booking write without a session
**When** it reaches the API
**Then** it is `401 no_session`; the frontend then calls `POST /api/session`, keeps the draft and its key, and shows "please try again" without the word "session" (AD-8, UX-DR26)

**Given** a refusal on Review (`no_seat_free`, `deadline_passed` or `outside_horizon`)
**When** it arrives
**Then** the Guest stays on Review with name and email kept, a Notice under Back takes focus with "Only 1 seat left in this session. You have not been charged.", "No seat free. You have not been charged." or "This session can no longer be booked. You have not been charged.", Pay, the payment note and the Terms checkbox are removed for that session, and the Booking summary and terms stay (FR-11, FR-12, UX-DR11, UX-DR25)
**And** the Notice holds "The nearest sessions with room:" with up to three Nearest sessions from the Story 1.4 listing; choosing one reloads Review for that session with name and email kept and Pay, the note and the checkbox back, and moves focus to the Review heading (FR-3, UX-DR13)

**Given** other outcomes on Review
**When** they arrive
**Then** a failed payment shows an Error summary "The payment failed. You have not been charged. You can pay again." with Pay kept; `503 try_again` and `409 payment_pending` show "please try again" with Pay, the note and the checkbox kept and the same key reused; `409 invalid_key` shows the Notice "This booking may already be paid. Check your email for a confirmation before you book again.", removes Pay and offers Book seats as a Text link that starts a new draft (FR-7, FR-14, UX-DR25)
**And** every refusal code the frontend handles is mirrored from `api/errors.py` in one place in `frontend/lib/` (AD-16)

**Given** the e2e layer
**When** `tests/e2e/test_fr11_refusals.py` runs
**Then** it reaches Review for 2 Seats, takes Seats away through the database, presses Pay and sees the true Seats left, the nearest sessions and focus on the Notice; a lost last Seat shows "No seat free. You have not been charged."; a deadline passed by moving the clock shows its message; the failed-payment switch shows its Error summary; in each case no Booking or email exists afterwards (FR-7, FR-11, FR-12, FR-22)
**And** axe reports no A or AA failure on Review in each refusal state, and the nearest-session links work with the keyboard alone (FR-23)

## Epic 2: The Administrator sees who is coming

The Administrator signs in safely, sees each session of a chosen day with its Seat capacity, Seats booked, Seats left and every Booking, and reads every email in the Outbox. Guests and anonymous visitors get nothing. The epic ends with the Core done: the README lets the examiner start, sign in and run every test from a fresh clone, and the accessibility passes cover every Core page.

### Story 2.1: Administrator signs in and out

As an Administrator,
I want to sign in with my email and password and sign out again,
So that only staff can reach the Administrator pages, and a guessed or stolen password gets an attacker nowhere.

**Acceptance Criteria:**

**Given** a fresh database
**When** the backend starts and applies `seeds/`
**Then** an `accounts` row exists for `admin@saunaloyly.example` with role Administrator and an Argon2id hash in PHC format (`argon2-cffi` defaults, AD-11)
**And** the seed's password is the documented local test value that Lisa chooses in this story, kept in `seeds/` and written in the README (FR-15, DR-5, AD-18)
**And** a restart does not overwrite the stored hash (AD-18)

**Given** the migration added in this story
**When** it is applied
**Then** it creates only what sign-in needs: `accounts(id, email UNIQUE, password_hash, role)`, `sessions.account_id` (nullable FK) and `sign_in_throttle(email_lower PRIMARY KEY, failures, locked_until)` with no foreign key to `accounts` (AD-11, AD-15)
**And** no column or table holds a readable password, and the same password stored for two accounts gives two different hashes (PW-1, PW-4, `tests/test_fr19_passwords.py`)

**Given** one service function `services.auth.check_password_rules(password, email)` and the packaged list `src/booking_platform/data/common-passwords.txt`
**When** a password is set by the seed or by `create-admin`
**Then** a password shorter than 15 characters, on the common list, or equal to the account's email (case-insensitive) is refused, and nothing is written (PW-2)
**And** a password of 15 to at least 64 characters, with any characters including spaces and non-ASCII, and no required mix of types, is accepted and stored only as a hash (PW-3, FR-19)
**And** the seed, `create-admin` and later sign-up all call this one function (AD-11)

**Given** the `booking-platform create-admin` command
**When** it is run (`docker compose exec backend booking-platform create-admin`, or `uv run booking-platform create-admin` against `booking_dev`)
**Then** it prompts for the email and for the password twice without echo, and never accepts the password as an argument or environment variable (AD-18, AD-19)
**And** it creates a new Administrator, or sets a new password for an existing one, applying FR-19
**And** the password never appears in its output or in any log

**Given** an anonymous browser session on the Sign-in page
**When** `POST /api/admin/sign-in {email, password}` is sent with the correct credentials
**Then** the same `sessions` row gets a new token (old token no longer works), its role becomes Administrator and its lifetime 8 hours, sliding (AD-8)
**And** the response is a bare JSON object that never contains a password or hash (FR-15)
**And** the frontend moves to the Booking list address (the page itself is built in Story 2.2; until then the address shows the Administrator bar and a heading only)

**Given** a wrong password for a known email, any password for an unknown email, or a throttled email
**When** sign-in is attempted
**Then** the API answers the same `401` with the same error code, and the page shows "Wrong email or password" in an Error summary with no Field error (PW-5, UX-DR30)
**And** no response, timing branch or message reveals whether the email has an account (Argon2 verification runs against a dummy hash for unknown emails)

**Given** 5 failed sign-ins in a row for one email, known or unknown, compared in lower case
**When** a sixth attempt is made within 15 minutes, even with the correct password
**Then** it is refused with the same `401` and message (PW-6, FR-15)
**And** after the clock is moved past 15 minutes through `clock.off`, the correct password succeeds, and a success resets `failures` to 0 (AD-4 test clock)
**And** each attempt upserts and locks its throttle row `FOR UPDATE` before deciding, and a refusal is returned from `work` so its count commits (AD-3, AD-11)
**And** 10 parallel wrong attempts for one email leave `failures` = 10, never fewer (`tests/test_fr15_sign_in.py`)

**Given** a signed-in Administrator
**When** they choose "Sign out" in the Administrator bar (`POST /api/admin/sign-out`)
**Then** the `sessions` row is deleted, the cookie is cleared, and a request with the old token to any `/api/admin/` endpoint answers `401` (FR-15)
**And** the page returns to Sign-in, and the browser Back button also leads to Sign-in (UX-DR30)

**Given** the `/api/admin/` router from Story 1.1
**When** its dependency now resolves the caller from the session's `account_id` and role
**Then** an anonymous caller gets `401` and nothing changes (RB-1, IV-7); a signed-in Administrator is allowed (RB-3)
**And** the test fixture's Administrator session is created through real sign-in with the seeded account, so the slice tests keep running (AD-21)
**And** sign-in and sign-out are state-changing requests under the CSRF rule: without a same-origin `Origin` or `Sec-Fetch-Site` they get `403 cross_origin` (AD-8)

**Given** the frontend
**When** an anonymous visitor opens any Administrator address
**Then** the page sends them to Sign-in and shows nothing else (UX-DR30, UJ-3)
**And** an Administrator whose session has expired is sent to Sign-in on their next action, with copy that never uses the word "session" for this (UX-DR30, UX-DR37)

**Given** the Sign-in page and the shared Administrator bar component in `frontend/components/`
**When** they render
**Then** Sign-in shows the bar with the name only, the heading, email, password and "Sign in" in that order; the bar on other Administrator pages holds Booking list, Outbox and Sign out (UX-DR3, UX-DR30)
**And** the page title is "Sign in – Saunalöyly", with "Error: " while an Error summary shows (UX-DR33); paste and password managers work (FR-19, WCAG 3.3.8)
**And** opening Sign-in calls `POST /api/session` (AD-8), and no other Administrator page load creates a session
**And** `tests/e2e/test_fr15_sign_in.py` signs in and out with the keyboard alone, runs axe with no A or AA failure, and checks no horizontal scroll at 1024, 1366 and 1920 px (FR-22, FR-23)

**Given** the full test run
**When** the stack runs a sign-in with the test password
**Then** neither the password nor the session token appears in `docker compose -p booking_e2e logs` (AD-19, FR-21)

### Story 2.2: Booking list for a chosen day

As an Administrator,
I want to see every session of a chosen day with how full it is and who has booked,
So that I know who is coming without doing arithmetic, and can find a Guest who gives a reference or a name at reception.

**Acceptance Criteria:**

**Given** a signed-in Administrator
**When** `GET /api/admin/bookings?date=YYYY-MM-DD` is called for a Venue date
**Then** the response lists every Window starting on that Venue date in time order, each with `start`, `end`, `seat_capacity`, `seats_booked` and `seats_left` taken from `window_open_capacity()`, `window_booked_seats()` and `seats_left()` (AD-5, FR-16)
**And** each Window lists its Bookings oldest first, with reference, name, email, Seats, `total_ore` and time of booking (`created_at`)
**And** Windows without Bookings are included with an empty list
**And** the endpoint takes no Window lock and writes nothing, apart from `ensure_generated()` (AD-4)

**Given** a malformed date or an unknown query field
**When** the list is requested
**Then** the API answers `422 invalid_input` and changes nothing (FR-18, IV-2, IV-3)

**Given** an anonymous caller
**When** the list endpoint is called
**Then** it answers `401` and reveals nothing (RB-1, IV-7, `tests/test_fr16_booking_list.py`)

**Given** a Window with Bookings made through the Guest flow, including the seeded Window with 42 of 44 Seats booked and the fully booked one (Story 1.5)
**When** the Administrator list and the Guest listing (`GET /api/windows`) are read for the same date
**Then** every Window's Seats left is equal in both (FR-3, FR-16)
**And** a Booking made between two reads appears on the next read (FR-16)

**Given** a Booking whose name is `<script>alert(1)</script>` and whose email field holds SQL text inserted as a raw row
**When** the Booking list page renders
**Then** both are shown as text, no script runs and no markup is rendered (IV-5, FR-16, FR-18)

**Given** a `retention_due(booking_id)` SQL predicate (true when `app_now()` is more than 12 months after the end of the Booking's Window; the Voucher clause of AD-30 is added in Epic 4)
**When** the list is read for a Window whose Bookings are past retention
**Then** their name and email are masked in the response, without any write (AD-4 "reads never write", FR-21)
**And** at startup, `services/catchup.py` anonymises those Bookings and clears the recipient and body of their Outbox emails in one function per effect (AD-4, AD-12)
**And** a test moves the clock through `clock.off` past 12 months and checks both the masked read and the startup catch-up

**Given** the Booking list page at the Administrator address
**When** it opens
**Then** it shows the Administrator bar, the heading, a date Text field defaulting to today's Venue date taken from the API (`today`, never the browser clock, AD-4, AD-16), and "Previous day" and "Next day" Text links (UX-DR31)
**And** each Session group shows the time in `heading-md` with its Seat capacity, Seats booked and Seats left on one line in tabular figures, and the Booking table below it (UX-DR31)
**And** the time of booking is shown as `dd.mm.yyyy HH:MM` in Venue time, amounts as "NOK 500", numbers right-aligned (UX-DR31, Conventions: Time and Money)
**And** all UI copy says "session" for a Window (UX-DR37)

**Given** a Session with no Seats left
**When** its group renders
**Then** the header has the `unavailable` fill with "Sold out" and "Seats left 0" in weight 600, and the state is said in words, not by colour alone (UX-DR31, FR-23)

**Given** a date with no Bookings, or a failed read
**When** the page renders
**Then** every Session is shown with its figures and "No bookings"; a failed read shows a Notice with "please try again" (UX-DR31)

**Given** reception looks up a Guest
**When** the Administrator searches the page with the browser's find for a reference, name or email
**Then** the Booking is found, because all three are plain text in the table (PRD §3 Reception, EXPERIENCE.md Open Item 13; no new function is added)

**Given** the page
**When** `tests/e2e/test_fr16_booking_list.py` runs
**Then** it signs in, moves between days with the keyboard alone, finds a Booking made through the Guest flow in the right group, runs axe with no A or AA failure, and checks no horizontal scroll at 1024, 1366 and 1920 px (FR-22, FR-23)
**And** the page title is "Booking list – Saunalöyly" (UX-DR33)

### Story 2.3: Outbox

As an Administrator, or the examiner using the README's test login,
I want to read every simulated email exactly as it was sent,
So that I can check what a Guest was told, including the emails no Guest page shows.

**Acceptance Criteria:**

**Given** a signed-in Administrator
**When** `GET /api/admin/outbox` is called
**Then** it returns every `outbox_emails` row newest first, each with time, recipient, subject and the full body exactly as stored, links included in plain text (FR-17, AD-12)
**And** it takes no lock and writes nothing (AD-4)

**Given** an anonymous caller, or a Guest browser session from the booking flow
**When** the Outbox endpoint is called
**Then** it answers `401` and reveals nothing, not even a count (FR-17, FR-20, RB-1, IV-7, `tests/test_fr17_outbox.py`)

**Given** a Booking made through the Guest flow
**When** the Outbox is read
**Then** its confirmation email is there, and its body equals the "Sent by email:" block that the Confirmation page showed (FR-8, FR-17)
**And** every link in it is absolute and starts with `BP_BASE_URL` (`http://localhost:8000` in the Core, AD-12, AD-22)

**Given** an email linked to a Booking that is past retention
**When** the Outbox is read
**Then** its recipient and body are masked by the `retention_due` predicate from Story 2.2, and after the next startup they are cleared (FR-21, AD-12)

**Given** an email whose body holds HTML or a script tag (inserted as a raw row)
**When** the Outbox page renders it
**Then** it is shown as text with its line breaks kept and nothing runs (IV-5)

**Given** the Outbox page
**When** it opens from the Administrator bar
**Then** it shows the bar, the heading "Outbox" and one Outbox entry per email, always open, with time, recipient and subject in `label` above the body in `small` (UX-DR32)
**And** times are `dd.mm.yyyy HH:MM` in Venue time
**And** the Outbox entry reuses the Email-as-sent block from `frontend/components/` with the extra header lines, so the two never drift (UX-DR14, DRY)

**Given** an empty Outbox (a test database with no Bookings)
**When** the page renders
**Then** it shows "No emails" (UX-DR32)

**Given** the page
**When** `tests/e2e/test_fr17_outbox.py` runs
**Then** it signs in, opens the Outbox with the keyboard alone, finds a confirmation email made in the same test, runs axe with no A or AA failure, and checks no horizontal scroll at 1024, 1366 and 1920 px (FR-22, FR-23)
**And** the page title is "Outbox – Saunalöyly" (UX-DR33)

### Story 2.4: Core done: the examiner can run, sign in and check everything

As the examiner,
I want to start the platform, sign in and run every test from a fresh clone by following the README alone,
So that I can verify the Core without help, and Lisa knows the Core website is complete.

**Acceptance Criteria:**

**Given** the README
**When** it is read after this story
**Then** it covers, in order (DR-2, AD-27 Core mode):
- the three tools to install (uv, Node.js, Docker) and nothing else (NFR-1);
- `docker compose up --build --wait`, then `http://localhost:8000` (use `localhost`, not `127.0.0.1`);
- the dev commands (`uv run booking-platform dev`, `npm --prefix frontend run dev`, `http://127.0.0.1:3000`);
- the two one-time preparation commands and `uv run pytest`;
- the Administrator test login, the seeded sample Bookings and where to see them;
- how to view the Outbox, which also holds the emails Guests do not see on a page (FR-17);
- `create-admin`, test switches (copy the example, edit, `docker compose restart backend`), `docker compose logs`, `down` and `down -v` (AD-14, AD-18);
- the folders for seed data, tests and planning documents (DR-5);
**And** every command in it is copied from the commands actually run in this story

**Given** the README's security section
**When** it is read
**Then** it states how data is protected: Argon2id password hashing, server-side role checks on every request, no third-party requests, no secrets in logs, that HTTPS is not yet on (until Epic 3), and that Manage-link tokens will be stored only as hashes once §4.8 is built (FR-21)
**And** the privacy notice and the README do not contradict each other

**Given** the README's "Not delivered" section
**When** it is read
**Then** it lists the success criteria and FRs not delivered at this point (HTTPS, SC2 to SC8, FR-25 to FR-51, and WCAG 1.4.10 Reflow until FR-51), so that it is true on the day it is merged (DR-2, FR-23); later epics shorten it

**Given** a fresh clone of `main` in a new folder, with no `config/test-switches.toml`, no `booking_dev` database and no Docker volumes for the project
**When** Lisa follows the README word for word on her laptop
**Then** the stack starts, Landing loads, a Seat booking completes, the Administrator signs in, and the Booking list and Outbox show it (NFR-1, SM-4)
**And** `uv run pytest` passes after the two preparation commands
**And** every step that did not work as written is fixed in the README or the code in this story, and the run is recorded in the session log

**Given** every Core page (Landing with "Before you come", Book seats, Details, Review, Confirmation, Terms, Privacy notice, Sign-in, Booking list, Outbox, the not-available page)
**When** `tests/e2e/test_fr23_accessibility.py` visits each in the states the flow reaches (including an Error summary, a refusal Notice and a sold-out Session)
**Then** axe-core reports no level A or AA failure, and the only known gap listed in the report is 1.4.10 Reflow (FR-23)
**And** each page has no horizontal scroll at 1366×768, 1920×1080 and 1024 px wide (FR-22)

**Given** `tests/e2e/test_fr23_keyboard_and_zoom.py`, the automated part of the FR-23 manual passes, built on `tests/e2e/a11y.py` (Story 1.2)
**When** it runs on the e2e stack
**Then** the Book seats `tab_order` puts the date field, the calendar, the Seat picker and the Session list before the rail's total and "Continue booking" (WCAG 2.4.3, EXPERIENCE.md Open Item 14)
**And** in `zoomed` pages for 1366×768 and 1920×1080, Book seats, Details and Review are completed through `press` and `tab_to`, "Continue booking" and Pay are reached and pressed, and a full-page screenshot of each page is saved under `test-results/zoom/` (git-ignored) for Lisa's manual look (WCAG 1.4.4)
**And** the `ariaSnapshot` of the Session list shows every row's name with its Seats left text ("13:00 to 14:30, 12 seats left"), and unavailable rows as disabled with their text ("1 seat left, not enough for 2", "Sold out") (UX-DR19, UX-DR35)
**And** the keyboard-only flows from Landing to Confirmation (Story 1.5) and through Sign-in, Booking list, Outbox and Sign out (Stories 2.1 to 2.3) already go through `press` and `tab_to`, so every focus stop on those pages is checked

**Given** the manual passes of FR-23, which confirm the automated checks rather than repeat them
**When** Lisa runs them on the compose stack, with NVDA and Chrome for the screen-reader pass
**Then** the results are recorded in `tests/manual/core-accessibility.md`, a checklist with one row per check giving date, browser (and screen reader), outcome and the automated test that covers it (DR-1):
- keyboard only: one run through the booking flow from Landing to Confirmation and through Sign-in, Booking list and Outbox, looking for what the focus checks cannot see (an order that makes no sense, a stop that does nothing);
- 200 % zoom at 1366×768 and 1920×1080 in the browser, plus a look at the screenshots in `test-results/zoom/`: nothing cut off or overlapping (WCAG 1.4.4);
- the Book seats tab order, seen once against the `tab_order` test (WCAG 2.4.3);
- a screen-reader pass of Book seats, Review and Confirmation: Session rows are read with Seats left, and Next.js's route announcer does not double the page announcement (UX-DR35);
**And** any failure is fixed in this story, or recorded as an issue with its WCAG criterion if it cannot be fixed in time

**Given** `ASSETS.md` and `frontend/public/`
**When** the asset test from Epic 1 runs
**Then** every file in `frontend/public/` has an `ASSETS.md` row with source and licence, and every image and font row points to a file that exists (DR-3)

**Given** `tests/e2e/test_fr21_privacy.py`
**When** this story extends it to the Administrator pages
**Then** an anonymous visit to each Administrator address is sent to Sign-in; Sign-in sets exactly one session cookie; every request on Sign-in, Booking list and Outbox goes to the stack's `base_url` origin; and each loads exactly one stylesheet of ours (FR-21, AD-17)

**Given** the full e2e run, which signs in with the documented test password and makes Bookings
**When** `docker compose -p booking_e2e logs` is searched through the fixture's compose helper
**Then** the test password, the session tokens and the request bodies appear nowhere (AD-19, FR-21)

**Given** the Core done definition (PRD §10.1)
**When** this story is merged
**Then** every Core page has final copy and images with no placeholder, SC1, SC9 without HTTPS (IV-1 to IV-7, PW-1 to PW-6, RB-1, RB-3, RB-4 for references) and the laptop part of SC10 pass, and `main` is green
**And** the session log states that the Core is done, or lists exactly what is missing

## Epic 3: Every connection is secure (HTTPS)

The website and the API are served over HTTPS only, so passwords, sessions and, later, Manage links never travel unencrypted. The examiner can see the redirect, the headers and the cookie attributes for themselves.

### Story 3.1: Serve the website and the API over HTTPS only

As a Guest or an Administrator,
I want every page and API call to go over HTTPS, with plain HTTP only redirected,
So that my password, my browser session and the links I am emailed never travel unencrypted.

**Acceptance Criteria:**

**Given** the Core stack runs in compose with Caddy on plain HTTP `:8000`, `BP_HTTPS` off and `BP_BASE_URL=http://localhost:8000` (AD-27 Build order)
**When** this story's pull request is merged
**Then** the three mode lines in `docker-compose.yml` have changed together, in one PR: the proxy's `SITE_ADDRESS` is `localhost:${HTTPS_PORT:-8443}`, the backend's `BP_HTTPS` is `"on"` and its `BP_BASE_URL` is `https://localhost:${HTTPS_PORT:-8443}` (AD-27 Modes, AD-22)
**And** the proxy publishes `HTTPS_PORT` (default 8443) as the same host port on `127.0.0.1`, keeps publishing `HTTP_PORT` (default 8000), and its `environment:` still passes `HTTP_PORT` (and `HSTS_MAX_AGE` when set) unchanged (AD-27 Ports)
**And** the Caddyfile gets no `tls` line, no `https_port` and no `handle_errors`; Caddy issues the `localhost` certificate from its internal CA, with `skip_install_trust` kept in the global options (AD-27 Modes)
**And** no healthcheck changes: the proxy's check still reads Caddy's admin endpoint on `:2019`, and `docker compose up --build --wait` still waits for all four services (AD-27 Startup)

**Given** the backend starts
**When** `BP_HTTPS` is on and `BP_BASE_URL` does not start with `https://`
**Then** `config` refuses to start with one line that names the two variables (AD-22)
**And** a unit test covers both the refusal and a valid `https://` base URL

**Given** the stack runs in HTTPS mode
**When** a client sends a plain-HTTP request to `http://localhost:<HTTP_PORT>/x?y`, to a page or to an `/api` path
**Then** Caddy's automatic redirect answers with `Location: https://localhost:<HTTPS_PORT>/x?y`, same path and query (FR-24, HT-1)
**And** the redirect carries no `Strict-Transport-Security` header and none of the site's headers (AD-27 Headers)
**And** no request reaches the backend or the frontend, and nothing in the database changes (FR-24: no data returned or changed over HTTP)

**Given** the stack runs in HTTPS mode
**When** any HTTPS response is served by the site
**Then** it carries `Strict-Transport-Security: max-age={$HSTS_MAX_AGE:3600}`, without `includeSubDomains` and without `preload`, added by one `header` directive without `defer` in the Caddyfile (FR-24, HT-2, AD-27 Headers)
**And** the headers from the Core (`Referrer-Policy: no-referrer`, `Cache-Control: no-store` on `@api`) are still present
**And** the backend and the frontend set none of these headers themselves

**Given** the stack runs in HTTPS mode
**When** the backend sets a session cookie (`POST /api/session`, Administrator sign-in)
**Then** every `Set-Cookie` has `Secure`, `HttpOnly`, `SameSite=Strict` and `Path=/`, because `BP_HTTPS` is on (FR-24, HT-3, AD-8)
**And** a plain-HTTP request that carries that session cookie is answered only by Caddy's redirect, and the session row (its token hash and expiry) is unchanged afterwards

**Given** the stack runs in HTTPS mode
**When** any action sends an email through `services.outbox.send`
**Then** every link in its body is absolute and starts with `https://localhost:<HTTPS_PORT>`, the configured base URL (FR-24, HT-4, AD-12)

**Given** the e2e fixture (`tests/e2e/conftest.py`) starts compose project `booking_e2e` with its own env file (`HTTP_PORT`, `HTTPS_PORT`, `DB_PORT`, `SWITCHES_DIR`)
**When** the stack is up
**Then** the fixture copies Caddy's root from the proxy (`/data/caddy/pki/authorities/local/root.crt`) through its compose helper, retrying until the file exists, and builds an `ssl.SSLContext` loaded from it (AD-27 Tests)
**And** the one exposed `base_url` becomes `https://localhost:<HTTPS_PORT>`, every HTTP call in the e2e layer verifies TLS with that context, and Playwright runs with `ignore_https_errors`
**And** no test writes a literal URL; every e2e test takes its URL from `base_url`
**And** the fixture still moves the clock and seeds rows through `DB_PORT`, and still ends with `down -v`

**Given** `tests/e2e/test_fr24_https.py`
**When** `uv run pytest` runs
**Then** HT-1 is checked with a client that keeps no HSTS state: the redirect's `Location`, the missing `Strict-Transport-Security`, and an unchanged database
**And** HT-2 checks the headers on a Next.js page, on an API `404 not_found` envelope, on a static asset from `frontend/public/`, and on a Caddy-generated 502 after the fixture stops `frontend` (and starts it again through `up --wait`); `Alt-Svc` is ignored
**And** HT-3 checks every `Set-Cookie` attribute and the HTTP request with the cookie against the session row
**And** HT-4 checks that every link in every Outbox email starts with the stack's `base_url`
**And** the AD-19 log search (`docker compose -p booking_e2e logs` through the helper) still finds neither the test password nor any session token

**Given** every e2e test written in Epics 1 and 2
**When** they run over HTTPS
**Then** they all pass unchanged apart from taking `base_url` from the fixture
**And** `tests/e2e/test_fr21_privacy.py` still finds every request on every Core page going to the stack's `base_url` origin, with no third-party request (FR-21)

**Given** an examiner with a fresh clone
**When** they follow the README
**Then** the README's start section says `docker compose up --build --wait` and then `https://localhost:8443`, using `localhost` and not `127.0.0.1`, and that the browser warns once about the certificate (FR-24, AD-27 README, DR-2)
**And** it shows how to copy Caddy's root with `docker compose cp proxy:/data/caddy/pki/authorities/local/root.crt .`, says that importing it is optional and should be undone after grading, and that after `docker compose down -v` the root is new and must be copied again
**And** it shows `curl -i http://localhost:8000/` as the way to see HT-1
**And** it states the Known limits: browsers send `Secure` cookies to `http://localhost`, where Caddy only redirects, and Chrome and Firefox ignore HSTS from `localhost` (FR-24)
**And** the README security section now says HTTPS is in place and ends at Caddy, the backend and the frontend are reachable only on the internal compose network, no request goes to a third party, and a production deployment would use a public certificate and one year of HSTS (FR-21, AD-27 README)
**And** every Outbox link the README points to, and the base URL it names, start with `https://localhost:8443`
**And** the README's "Not delivered" section no longer lists HTTPS (DR-2)

## Epic 4: A Guest changes seats or takes a voucher

With the Manage link in the confirmation email, a Guest can see their Booking and, until 12 hours before the start, move some or all Seats to another session or give them up for a Voucher worth what was paid. A Voucher pays for a later Booking in full or in part. The Administrator sees each Change in the Booking list.

### Story 4.1: The Manage link opens the Booking

As a Guest with a Seat booking,
I want the link in my confirmation email to open my Booking, and nothing else,
So that I can check it and, later, change it without an account or anyone's help.

**Acceptance Criteria:**

**Given** the Core Seat flow from Epic 1 and HTTPS from Epic 3
**When** this story's migration runs
**Then** it adds `access_tokens(id, purpose, booking_id, token_hash bytea UNIQUE, created_at, revoked_at)` with `purpose` CHECK `'manage'` and the unique partial index `access_tokens_one_manage` (one unrevoked manage token per Booking), and `manage_grants(session_id, token_id, last_used_at)` with UNIQUE `(session_id, token_id)` and `ON DELETE CASCADE` from `sessions` (AD-28)
**And** it adds `settings.cutoff_seats interval` (default 12 hours, `CHECK >= interval '2 hours'`), `bookings.cutoff interval NOT NULL` filled from `cutoff_seats` for existing rows, and `bookings.version int NOT NULL DEFAULT 0`, not in AD-7's trigger column list (AD-4, AD-29)
**And** `change_allowed(booking_id)` (`app_now() < lower(during) - cutoff`) is the one Cutoff predicate in SQL (AD-4)

**Given** a Guest pays for a Seat booking
**When** `services.booking.create` runs
**Then** it copies `cutoff_seats` into the Booking and calls `services.manage.issue(c, booking_id)` inside the same transaction, which stores only the SHA-256 hash of a new 256-bit token (`secrets.token_urlsafe(32)`) (FR-25, AD-8, AD-28)
**And** the confirmation email carries the absolute link `<BP_BASE_URL>/manage#t=<token>`, starting with `https://` (FR-24 HT-4, AD-12), and the Confirmation page shows that email as sent (FR-8, FR-17)
**And** the token appears in no path or query, in no table except as its hash, and in no log line (AD-19); the e2e run searches `docker compose -p booking_e2e logs` for the issued token and finds nothing

**Given** the seed runs at startup (AD-18)
**When** a sample Booking has no unrevoked manage token
**Then** the seed issues one through `services.manage.issue` with an Outbox email that carries its Manage link, and a second start issues nothing new
**And** the README says where to find a sample Manage link in the Outbox and that it works until its session ends (DR-2)

**Given** a Guest opens `/manage#t=<token>`
**When** the client component mounts
**Then** it reads the fragment once (guarded against React Strict Mode's double effect), removes it with `history.replaceState`, sends `POST /api/manage/open {token}` through `lib/api.js`, and navigates to `/manage/[reference]`, where focus moves to the `h1` (AD-17, AD-28, UX-DR33)
**And** `POST /api/manage/open` creates or reuses the browser's session (AD-8; this is the one page load besides Book seats and Sign-in that sets the session cookie, FR-21), checks the token, upserts the grant and returns `{reference}`

**Given** a token that is unknown, malformed, revoked, or whose Booking's session has ended
**When** it is opened
**Then** `POST /api/manage/open` answers `404 not_found` exactly as for a token that never existed, and the page shows "This page is not available." with a link to Landing (FR-25, RB-4 guessed link, UX-DR29, UX-DR40)
**And** Lisa confirms in this story that the page after the session has ended is this same page (EXPERIENCE.md Open Item 21)

**Given** a session holds a grant for Booking A
**When** it requests `GET /api/manage/{reference}` for Booking A, for another existing Booking B, or for a reference that does not exist
**Then** Booking A is returned, and B and the unknown reference both answer the same `404 not_found`, with or without a session (FR-20 RB-4, RB-5, AD-28 Access)
**And** every route under `/api/manage/{reference}/` is on one router whose dependency checks `manage_grant_valid(session_id, booking_id)` (last use within 30 minutes, token unrevoked, before the end of the Booking's session) before the action and touches `last_used_at` in one autocommit statement (AD-4, AD-28)

**Given** a valid grant
**When** `GET /api/manage/{reference}` is called
**Then** it changes nothing apart from the touch and returns the AD-23 serializer (`kind`, `seats`, `sauna: null`, `window`, `total_ore`, `status`) plus `version`, `change_allowed`, `cutoff_at` and an empty history list (AD-28 Read)
**And** it never returns an Outbox body, a Voucher code or a Manage link, and a test walks the response and finds no Sauna name (FR-4, AD-25)

**Given** a grant whose last use was more than 30 minutes ago (clock moved through `clock.off`)
**When** the Manage page is reloaded
**Then** the read answers `404 not_found`, and opening the link from the email again restores access
**And** signing out an Administrator session in the same browser deletes its grants by cascade, and startup purges grants of expired sessions and of tokens whose session has ended (AD-8, AD-28)

**Given** the Manage page for an active Seat booking before its Cutoff
**When** it renders
**Then** it shows the Booking reference, date, session, Seats and total paid, states until when Changes are possible (from `cutoff_at`, formatted in Venue time), and offers the Changes that later stories add; loading the page changes nothing (FR-25, UX-DR40)
**And** the shared components it introduces (`ManageBookingSummary`, `ConfirmingStep`, `ChangeResult` with "Sent by email:") live in `frontend/components/` so the Change stories and Epic 5 reuse them

**Given** the Cutoff has passed (`change_allowed` false)
**When** the Manage page renders
**Then** it still shows the Booking and states, in text, that it can no longer be changed and why, with the time from `cutoff_at` (FR-26, FR-33)
**And** Lisa accepts the wording of that reason in this story (EXPERIENCE.md Open Item 22), and it is added to the frontend copy and its mirror of the code table (`cutoff_passed` with `cutoff_at`, AD-16)

**Given** §4.8 replaces the Core change statement
**When** this story merges
**Then** the shared terms text in `content/` (`terms-seats`), the Terms page section "Changes and refunds", Review, Confirmation and the confirmation email all state what a Guest can do up to 12 hours before the start (move Seats or take a Voucher, no money back) instead of "A booking cannot be changed or refunded." (FR-5, AD-12)
**And** Lisa accepts the new wording in this story, and Review still fits Pay in the first view at 1366×768 (UX-DR24)

**Given** the compose stack
**When** an e2e test requests `/manage`, `/manage/<reference>`, `/api/manage/open` and `/api/manage/<reference>`
**Then** each response carries `X-Robots-Tag: noindex` and `Referrer-Policy: no-referrer` from Caddy (AD-27), and `tests/e2e/test_fr21_privacy.py` asserts that the Manage page makes no request outside the stack's origin (FR-21, FR-25)
**And** axe reports no A or AA failure on the Manage page and on "This page is not available.", and the page works with the keyboard alone and without horizontal scrolling at 1024, 1366 and 1920 px (FR-22, FR-23)

**Given** the API test layer
**When** `uv run pytest` runs
**Then** `tests/test_fr25_manage_link.py` covers token hashing and length, the email link format, the seed tokens, open with valid, unknown, revoked and expired tokens, grant expiry, RB-4 and RB-5, the read's fields and the absence of emails, codes, links and Sauna names, and every earlier test still passes

### Story 4.2: Move all or some Seats to another session

As a Guest whose plans have changed,
I want to move all or some of my Seats to another session before the Cutoff,
So that I keep what I paid for without writing to anyone.

**Acceptance Criteria:**

**Given** Story 4.1
**When** this story's migration runs
**Then** it adds `booking_changes(id, booking_id, action, at, seats, from_window_id, to_window_id, from_sauna_id, to_sauna_id, new_booking_id)` with an `action` CHECK allowing `move` and the AD-29 shape CHECK for `move`, `outbox_emails.change_id` (FK `booking_changes`) and `idempotency_keys.change_id` with exactly one of `booking_id` and `change_id` set (AD-9, AD-12, AD-29)
**And** `services.history.record(c, booking_id, action, **cols)` is the only writer of `booking_changes`, and no trigger writes it (AD-7, AD-29)

**Given** a Guest with a valid grant on an active Seat booking before its Cutoff
**When** they send `POST /api/manage/{reference}/seats/move {window_id, seats, version}` with an `Idempotency-Key`
**Then** the action reads the Booking's `window_id` unlocked, calls `lock_windows` with the current and target Windows in id order, re-reads the Booking `FOR NO KEY UPDATE`, retries through `db.run` if `window_id` changed, re-checks the grant by join and reads the key, all in one transaction (AD-3, AD-9, AD-28)
**And** it then refuses in this order: `booking_cancelled`; `booking_changed` when `version` differs (fact: the current Booking); `change_invalid` with `reason` `seats_exceed` (Seats outside 1 to the Booking's Seats) or `same_target`; `outside_horizon` and `deadline_passed` for the target; `cutoff_passed` with `cutoff_at`; then capacity in the store (AD-16, AD-24, AD-29)

**Given** the Guest moves all Seats
**When** the move succeeds
**Then** the Booking's `window_id` changes in one UPDATE with `entry_time = app_now()`, `version + 1`, the same reference, total and Manage link, and one `move` history row with both Window ids and `seats` (FR-26, AD-29)
**And** one Change confirmation email (reference, new session, Seats) is sent with the Change's `change_id`, says the Manage link in the confirmation email still works, carries no Manage link and names no Sauna (AD-12, AD-25, AD-29)

**Given** a Booking of 3 Seats in Window W1
**When** the Guest moves 1 Seat to Window W2
**Then** the original keeps its reference, link, `price_per_seat_ore` and `cutoff`, now has 2 Seats with `total_ore = 2 × price_per_seat_ore`, and its `version` rises (FR-26, AD-13, AD-29)
**And** a new `kind = 'seats'` Booking in W2 gets 1 Seat through `services.reference` (AD-20), the original's name, email, price per Seat and Cutoff, `session_id` = the acting session, `created_at = entry_time = app_now()`, `status = 'active'`, its own Manage token through `services.manage.issue`, no `payments` rows, and a grant for the acting session (AD-28, AD-29, AD-31)
**And** the history row has `new_booking_id`, and two emails go out: the Change confirmation on the original (Seats left, Seats moved, the new reference) and the split-off Booking's own confirmation with its Manage link (PRD §7, AD-29)

**Given** a move to a Window without room for the Seats moved (catalogue E5: 3 Seats to a Window with 2 left)
**When** it is submitted
**Then** it is refused with `409 no_seat_free` carrying the target's `seats_left`, nothing changes, the original keeps its 3 Seats, and Seats left is unchanged in both Windows (FR-26, AD-16)
**And** the store, not only Python, refuses it: a bypass test that updates `bookings.window_id` into a full Window around the API is rejected by `booked_within_capacity`, and the case is in the harness's `MUTATIONS` (AD-2)

**Given** a Change succeeded
**When** the same request is sent again with the same key from the same session
**Then** nothing is written and the response returns the first outcome: the emails that Change sent, read by id, and the Booking as it is now (AD-9)
**And** a known key with a different request or from another session is `409 invalid_key`; after it, or after `409 booking_changed`, the Manage page reloads the Booking and opens a fresh step with a new key from the slot `draft:change:<reference>:move` (AD-9, UX-DR40)

**Given** the move succeeded
**When** a Guest lists the source and target dates, or the Administrator opens the Booking list
**Then** the freed Seats count in Seats left at once and the moved Seats count in the target (FR-26, AD-5)
**And** the Booking list shows each Booking's status and its history entries (what moved, when, from and to which session, and the new reference for a split), and the split-off Booking appears under its own session (FR-16)

**Given** the Manage page of a Seat booking before its Cutoff
**When** the Guest chooses to move Seats
**Then** a confirming step lets them choose how many Seats (1 to the Booking's Seats) and a target session by date, reusing the shared Date calendar, Seat picker and Session list components and the Windows listing from Epic 1 (UX-DR17 to UX-DR19)
**And** the step states what will happen and changes nothing until the Guest confirms (FR-25); Lisa decides in this story how the current session is shown in the target list

**Given** the Guest confirms
**When** the move succeeds
**Then** a result page confirms the Change and shows each email the Change sent under "Sent by email:", including the split-off Booking's reference and Manage link for a partial move (FR-17, FR-26, UX-DR14, UX-DR40)
**And** a refusal shows a Notice with the reason from the code table and keeps the Guest's choices; after `cutoff_passed` the page shows the Cutoff state from Story 4.1

**Given** two Bookings, one in W1 and one in W2, each Window near full
**When** a move from W1 to W2 and a move from W2 to W1 run in parallel, and separately a move into W2 races a new Seat booking for W2's last Seats, each 100 times (FR-11 repetitions)
**Then** no run deadlocks, Seats booked never exceed Seat capacity in either Window, the total Seats across both Windows is unchanged, and when room exists for only one request exactly one succeeds (FR-10, FR-32 cross-Window part, AD-3)

**Given** the API and e2e test layers
**When** `uv run pytest` runs
**Then** `tests/test_fr26_move.py` covers full and partial moves, `test_e5`, every refusal in the AD-29 order including `cutoff_passed` after moving the clock, repeats and `invalid_key`, emails and their `change_id`, the store bypass and the races
**And** an e2e test moves 1 of 2 Seats through the Manage page with the keyboard alone, checks the result page and the Booking list, and axe reports no A or AA failure on the confirming step and the result page (FR-23)

### Story 4.3: Give up Seats for a Voucher

As a Guest who can no longer use some or all of my Seats,
I want to give them up for a Voucher worth what I paid,
So that I lose nothing but the visit I cannot make.

**Acceptance Criteria:**

**Given** Story 4.2
**When** this story's migration runs
**Then** it adds `vouchers(id, code_hash bytea UNIQUE, value_ore, balance_ore, issued_at, expires_at, booking_id)` with `CHECK (value_ore > 0 AND 0 <= balance_ore AND balance_ore <= value_ore)` (AD-30), `booking_changes.voucher_id` and the `voucher` shape CHECK (AD-29), and `payments.voucher_id` with the AD-13 CHECK that it is set exactly when `method = 'voucher'`, if Epic 1 did not already add it
**And** it adds `bookings.cancelled_at`, `cancel_cause` (`guest`, `block`, `overbooking`) and `cancel_remedy` (`refund`, `voucher` or NULL) with the AD-29 CHECKs, including `seat_guest_refund_forbidden`, and a BEFORE UPDATE trigger, raising a named constraint, that refuses `cancelled` → `active` and any change of `window_id`, `seats` or `sauna_id` on a cancelled row

**Given** a Guest with a valid grant on an active Seat booking of 4 Seats at NOK 250 each, before its Cutoff
**When** they send `POST /api/manage/{reference}/seats/voucher {seats: 1, version}` with an `Idempotency-Key`
**Then** after the lock, re-read, grant check, key read and the AD-29 checks, the Booking keeps 3 Seats with `total_ore` 75000, its `version` rises, and the freed Seat counts in Seats left at once (FR-27, AD-29)
**And** `services.voucher.issue` creates one Voucher worth `1 × price_per_seat_ore` (25000 øre), `balance_ore = value_ore`, with `booking_id` set, a last valid date one year after the Venue date of `app_now()`, and `expires_at` at 00:00 `venue_tz` on the day after it (FR-27, AD-30)

**Given** a Voucher is issued
**When** its code is created
**Then** it is 16 upper-case Crockford base32 characters from `secrets`, shown as `XXXX-XXXX-XXXX-XXXX`, and only its unkeyed SHA-256 hash is stored, with no part of the code (AD-30)
**And** the code reaches the Guest only inside the Change's email: the response carries `voucher: {value_ore, last_valid_date}` without the code, the Manage read never returns it, and the e2e log search finds it in no log (AD-19, AD-28, AD-29)

**Given** the Voucher Change
**When** it commits
**Then** one `voucher` history row with `seats` and `voucher_id` is written, one `payments` row `refund`/`voucher` of the Voucher's value with its `voucher_id`, and no `card` refund row (FR-27 "no money is refunded", AD-31)
**And** one Change confirmation email with the Seats left and a Voucher block (code, value, last valid date, and that a Voucher is never paid out in money) is sent with the `change_id`, names no Sauna, and is shown on the result page under "Sent by email:" (FR-17, FR-27, PRD §7, AD-29)

**Given** a Seat booking
**When** the Guest gives up all its Seats for a Voucher
**Then** the Booking is cancelled in the same transaction: `status = 'cancelled'`, `cancelled_at = app_now()`, `cancel_cause = 'guest'`, `cancel_remedy = 'voucher'`, Seats unchanged on the row, and it no longer counts in Seats booked (FR-16, AD-7, AD-29)
**And** this is the only way a Seat booking is cancelled; a direct UPDATE setting `cancel_cause = 'guest'` with `cancel_remedy = 'refund'` on a Seat booking is refused by `seat_guest_refund_forbidden`, and changing a cancelled row back to active is refused by the store

**Given** a cancelled Booking
**When** any further Change is sent
**Then** it is refused with `booking_cancelled` and nothing changes (AD-29)
**And** Lisa decides in this story what the Manage page shows after all Seats were given up (EXPERIENCE.md Open Item 19), for example the Booking as cancelled with its history and no Changes offered

**Given** the AD-31 ledger rule
**When** a Booking has no split in its history
**Then** its charges minus its returns equal `total_ore` while it is active and 0 once all its Seats are given up, and a test checks this after partial and full Voucher Changes

**Given** a repeat of a successful Voucher Change with the same key
**When** it arrives
**Then** it writes nothing, issues no second Voucher, and returns the first outcome with the same email (AD-9)

**Given** the Booking list
**When** the Administrator opens a date with a Voucher Change
**Then** the Booking shows the history entry (Seats given up, when, Voucher value issued, never the code), and a cancelled Booking stays in the list with its time, the cause "Guest" and the remedy "Voucher", outside the Seats booked figure (FR-16)

**Given** the FR-21 retention rule
**When** Vouchers exist from a Booking
**Then** `retention_due(booking_id)` is the one predicate: past both 12 months after the Booking's session and the latest `expires_at` of the Vouchers from it, and the Booking list masking and the startup catch-up from Epic 2 use it (FR-21, AD-30)

**Given** the Manage page before the Cutoff
**When** the Guest chooses to give up Seats
**Then** a confirming step lets them pick how many and states what will happen (Seats given up, Voucher value, valid for one year, no money back) before anything changes, using the shared `ConfirmingStep` and `ChangeResult` components (FR-25, UX-DR40)

**Given** the API and e2e test layers
**When** `uv run pytest` runs
**Then** `tests/test_fr27_voucher_for_seats.py` covers partial and full Voucher Changes, value, code format and hashing, expiry date, the email and response shape, cancellation columns and the store CHECKs, ledger, `cutoff_passed`, `booking_changed`, `booking_cancelled` and repeats
**And** an e2e test gives up 1 of 2 Seats through the Manage page with the keyboard alone, sees the Voucher in the email on the result page, and axe reports no A or AA failure (FR-23)

### Story 4.4: Pay with a Voucher

As a Guest holding a Voucher,
I want to enter its code on Review and have it pay for all or part of a new Booking,
So that the credit I received is worth what I was promised.

**Acceptance Criteria:**

**Given** a Guest with a session on Review
**When** they send `POST /api/vouchers/quote {code, kind: 'seats', window_id, seats}`
**Then** it takes no lock, writes nothing and returns `{voucher_part_ore, card_part_ore}`, where the Voucher part is the lesser of the balance and the total (AD-30)
**And** an unknown, malformed, expired or used-up code returns `409 voucher_invalid` with no facts, and no response ever states a Voucher's balance or expiry; without a session the call is `401 no_session` (FR-28, AD-8, AD-30)

**Given** typed codes
**When** a code is submitted
**Then** input of at most 32 characters is normalised (upper case, hyphens and spaces removed, `I` and `L` → `1`, `O` → `0`) before hashing, and input that does not normalise to 16 Crockford characters is `voucher_invalid`, never a 422 (AD-30)

**Given** a booking request with `voucher_code` and the quoted `voucher_part_ore` (1 to the total)
**When** `POST /api/bookings` runs
**Then** `charge()` decides the card part (total minus the Voucher part) before the lock, and is not called when the Voucher covers the whole total (AD-13)
**And** after the lock the order is `outside_horizon`, `deadline_passed`, the Booking insert (capacity), then one statement `UPDATE vouchers SET balance_ore = balance_ore - :part WHERE code_hash = :h AND balance_ore >= :part AND expires_at > app_now() RETURNING id`; no row → `409 voucher_invalid` and nothing is written; nothing before the lock refuses (AD-30)
**And** a `payments` row `charge`/`voucher` with the `voucher_id` is written, plus a `charge`/`card` row for any card part, so that the charges add up to `total_ore` and a later refund can return each part the way it was paid (FR-28, AD-31)

**Given** a Booking takes at most one Voucher in v1
**When** a request carries a Voucher
**Then** it carries one code only, and the idempotency `request_hash` includes the Voucher part but never the code (AD-9, AD-30)

**Given** a Voucher worth NOK 500 used for a NOK 250 Booking
**When** the Booking is paid
**Then** NOK 250 stays on the Voucher until its expiry, and no code path pays a balance out in money (FR-28, AD-30)

**Given** an expired Voucher (clock moved past `expires_at`), a used-up Voucher, and an unknown code
**When** each is used to pay
**Then** each is refused with the same `voucher_invalid`, no Booking is created, no Seat is taken, nothing is charged and no email is sent (FR-28)

**Given** one Voucher and parallel bookings that together want more than its balance
**When** they run 100 times (FR-11 repetitions) in `tests/test_fr28_voucher.py`
**Then** `balance_ore` never goes below 0, the Voucher charges never exceed `value_ore`, every losing request gets `voucher_invalid` and writes nothing, and Window locks are always taken before the Voucher row is written (FR-28, AD-30)

**Given** Review in the Seat flow
**When** the page renders
**Then** a Voucher field (Text field with a Text link beside it, UX-DR39) sits between the Booking summary and the booking terms, always visible; applying a valid code shows the Voucher part in the Booking summary and updates the Pay label to the card part, for example "Pay NOK 250" (FR-6, FR-28)
**And** an invalid code shows one identical Field error and an Error summary entry for every cause, with the input kept (FR-23, UX-DR9, UX-DR12)
**And** Lisa decides in this story the wording of Pay and of the payment note when the Voucher covers the whole total (EXPERIENCE.md Open Item 23), and the Text link label

**Given** Review must stay in the first view
**When** the Voucher field is added
**Then** Pay still ends inside the first view at 1366×768 and the page has no horizontal scrolling at 1024, 1366 and 1920 px (FR-22, UX-DR24)

**Given** a Booking paid partly or wholly with a Voucher
**When** the confirmation page and email are produced
**Then** they state the total and how it was paid (Voucher part and card part), with the payment note wherever a card payment is mentioned, in wording Lisa accepts in this story (FR-6, FR-8)
**And** the Booking list shows the Booking's total as stored (AD-13)

**Given** a refusal after a Voucher was applied
**When** Review shows the Notice for `no_seat_free`, `deadline_passed` or `try_again`
**Then** the Voucher has not been spent, and choosing a nearest session keeps the code in the draft and quotes it again (UX-DR25, UX-DR26)

**Given** the README
**When** the examiner wants to test a Voucher
**Then** it says how to get one (give up a Seat on a sample Booking through its Manage link from the Outbox) and where the code appears (DR-2)
**And** the README's "Not delivered" section no longer lists SC3 or FR-25 to FR-28 (DR-2)

**Given** the API and e2e test layers
**When** `uv run pytest` runs
**Then** `tests/test_fr28_voucher.py` covers the quote, normalisation, full and partial payment, remainder, every `voucher_invalid` cause, the payment rows and the parallel spend
**And** an e2e test pays a Booking partly with a Voucher through Review with the keyboard alone, axe reports no A or AA failure on Review with the Voucher field, and the log search finds no Voucher code in any container's log (AD-19)

## Epic 5: A group books a whole sauna

A Guest chooses Private sauna, sees which Saunas can be booked whole on a date, with size, price and free sessions, and books one. Until 72 hours before the start, the Guest can cancel it for a refund or a Voucher, or move it. Seat bookings are counted around Private saunas so that no Seat is ever lost or sold twice, and the Administrator sees each session's Placement.

### Story 5.1: A Guest sees which saunas can be booked whole

As a Guest planning a visit with a group,
I want to see, for a date, which Saunas can be booked whole, with their size, price and free sessions,
So that I can choose a private sauna for my group before I commit to anything.

**Acceptance Criteria:**

**Given** the story starts
**When** Lisa is asked to choose the Whole-sauna price of each Sauna and which Saunas are Bookable whole (spine Deferred, EXPERIENCE.md Open Item 27, PRD §12 Q3)
**Then** her choice is written into `seeds/` as the values of a new nullable column `saunas.whole_price_ore`, filled by the seed only where it is NULL (AD-18, AD-23)
**And** a Sauna with a NULL price is not offered whole, and the choice and its date are recorded in the story file and the session log

**Given** the §4.9 migration runs on a database that already holds Seat bookings and slice `whole_bookings` rows
**When** it is applied
**Then** `bookings` gains `kind` (`seats` | `whole`) and `sauna_id`, `seats` becomes NULL for `kind = 'whole'`, and one CHECK ties the three columns (Seat booking: `seats` 1–10, `sauna_id` NULL; Whole-sauna booking: `sauna_id` set, `seats` NULL) (AD-23)
**And** existing rows become `kind = 'seats'`, a BEFORE UPDATE trigger refuses any change of `kind`, and `settings.cutoff_whole` is added with default 72 hours and `CHECK >= interval '2 hours'` (AD-4)
**And** `whole_bookings` gains `booking_id UNIQUE NOT NULL REFERENCES bookings`, rows without a Booking are deleted, and the migration takes its number at merge (AD-15)

**Given** the pairing rule of AD-23
**When** a `bookings` row of `kind = 'whole'` and its `whole_bookings` row are written, changed or deleted out of step (for example an active Whole-sauna booking without its capacity row, or a capacity row whose `window_id` or `sauna_id` differs from its Booking)
**Then** the deferred constraint triggers that call `check_whole_pair(booking_id)` refuse the transaction at COMMIT with `CONSTRAINT = 'whole_pairing'`, which `db` maps to a 500, never a refusal (AD-1)
**And** a bypass test for each case writes around the API and turns red if a trigger is removed, and each case has its entry in the harness's `MUTATIONS` (AD-2)

**Given** the slice's whole-booking endpoint and the slice tests that used it
**When** this story is merged
**Then** the endpoint is removed, slice tests that wrote `whole_bookings` call the test helper `raw_whole(pg, wid, sid)`, which inserts a paired `kind = 'whole'` Booking and its capacity row in one transaction, and every slice assertion stays (AD-21, AD-23)
**And** `window_booked_seats()` counts only active `kind = 'seats'` rows, and no other code sums `bookings.seats` (AD-23)

**Given** the SQL predicate `whole_bookable(wid, sid, ignore_booking DEFAULT NULL)`
**When** it judges a Sauna and Window
**Then** it is true only when the Sauna is Bookable whole with a `whole_price_ore`, is not Blocked, is not booked whole (ignoring the capacity row of `ignore_booking`), the Seats booked plus held fit within its Room ahead unless `mark_closed(wid, sid)`, and the Window has not started (`window_started(wid)`), or has no Seat booking, or `mark_closed(wid, sid)` (FR-29, AD-24)
**And** it never uses `sauna_open_for_seats` of the Sauna being judged, and it is the only statement of the store-enforced part of FR-29

**Given** `trg_check_whole` fires AFTER INSERT and AFTER `UPDATE OF window_id, sauna_id` on `whole_bookings`
**When** a test inserts or updates a capacity row around the API that `whole_bookable` refuses, including in a started Window with Seat bookings (H12) and a Sauna holding Seats (B2, B3)
**Then** the store refuses it with `CONSTRAINT = 'whole_bookable'` and nothing is written
**And** each bypass test (INSERT and UPDATE) turns red under its `MUTATIONS` entry (AD-2, AD-24)

**Given** a date with seed Saunas Rauha 7, Löyly 10, Kajo 12 and Lumo 15 in Fill order
**When** a client calls `GET /api/private-saunas?date=<Venue date>`
**Then** the response is `{saunas: [{id, name, capacity, whole_price_ore, windows: [{id, start, end, already_started}]}], horizon_end, horizon_days}` and lists only the pairs where `within_horizon`, the Booking deadline predicate and `whole_bookable(wid, sid)` all hold (FR-30, AD-24, AD-16)
**And** the request needs no session, holds no lock and writes nothing apart from `windows.ensure_generated()` (AD-4)

**Given** the catalogue examples, with Seats booked as raw rows or through `services.booking.create`
**When** the listing is read for that Window
**Then** `test_fr29_whole_sauna.py::test_b1` lists Lumo with 20 Seats booked at `[7,10,3,0]`; `::test_b2` does not list Kajo there; `::test_b3` does not list Rauha with 1 Seat booked; `::test_b7` lists Lumo in an empty Window; and `::test_h12` does not list Lumo in a started Window with 29 Seats booked at `[7,10,12,0]`
**And** each test asserts the exact set of Saunas listed for the Window, and a Sauna without a `whole_price_ore` is never listed

**Given** a Guest on Landing after this story
**When** the page renders
**Then** the rail holds two equal Booking choices, "Book seats" and directly under it "Book private sauna", in the Primary button's fill and edge, the label centred, the same size (Lisa 2026-11-25; replaces the Text link); each Sauna card shows its price under the size line; and the Seat statement in "The saunas" intro gains the group sentence that a group that wants to stay together should book a Private sauna (FR-1.7, FR-4, UX-DR41, UX-DR16)
**And** the Book seats rail shows the same group sentence, still within the Book seats first-view budget at 1366×768 (UX-DR22), and no Seat-flow page names a Sauna (FR-4)

**Given** a Guest opens the Private sauna page and picks a date
**When** the listing returns
**Then** the page shows one Sauna option per Sauna with its name, "Holds 12"-style size and price ("NOK …"), then its free sessions as Session rows, and offers the view by session as well, both built only by regrouping the one API response (UX-DR41, AD-24)
**And** the date control reuses the Date calendar from Book seats (typed or picked, horizon from the server, UX-DR17), the page uses only the shared components and the one stylesheet, and an empty result says so plainly with no urgency cue (NFR-9)

**Given** the Private sauna page in the e2e layer
**When** it is opened, used with the keyboard alone and checked with axe
**Then** axe reports no A or AA failure, the Sauna and session choices are radio groups in `fieldset`/`legend` with one tab stop each, the page title is "Private sauna – Saunalöyly", and focus moves to the `h1` on arrival (FR-23, UX-DR33, UX-DR35)
**And** there is no horizontal scroll at 1024, 1366 and 1920 px wide, and `test_fr21_privacy.py` asserts every request on the page goes to the stack's origin (FR-21, FR-22)

### Story 5.2: Book and pay for a Private sauna

As a Guest booking for a group,
I want to pick a Sauna and a session, enter my details, review and pay,
So that the whole Sauna is ours for that session and nobody else can book it or a Seat in it.

**Acceptance Criteria:**

**Given** a Guest has chosen a Sauna and a session on the Private sauna page
**When** they continue
**Then** the same Details, Review and Confirmation pages as the Seat flow are used, with the draft in `sessionStorage` slot `draft:whole` holding the Sauna, Window, name, email and the one `Idempotency-Key` made on reaching Review (AD-9, UX-DR26)
**And** Back, reload and a direct address behave as in the Seat flow: nothing entered is lost, and Details or Review with something missing goes to the earliest page that needs it

**Given** Review for a Private sauna
**When** it renders
**Then** the Booking summary shows the Sauna name, date, session and total in NOK incl. VAT, the Guest's name and email and the Venue facts, and never the Sauna's Capacity (AD-23, FR-5)
**And** the terms block shows the shared `content/terms-whole` text with "The sauna is not held while you pay.", Pay states the amount ("Pay NOK …") beside "Simulated payment: no money moves", and the Terms checkbox is never pre-ticked (FR-29, FR-6, UX-DR24, UX-DR41)

**Given** `POST /api/bookings` with `kind = 'whole'`, `window_id`, `sauna_id`, name, email and the key
**When** the Sauna is still bookable whole at payment
**Then** `services.whole.create` runs in one `db.run`: `charge()` decides before `lock_windows`, then the key read, `outside_horizon`, `deadline_passed`, the Booking inserted through `services.reference` (AD-20) with `total_ore = whole_price_ore` and `price_per_seat_ore` NULL, then its `whole_bookings` row, the card `payments` row, the Manage token through `services.manage.issue`, and the confirmation email through `services.outbox.send` (AD-3, AD-13, AD-23, AD-28, AD-12)
**And** `cutoff` is copied from `settings.cutoff_whole` (72 hours) onto the Booking, and the request carries no Hold (FR-29, AD-4)

**Given** the Sauna has been taken, Blocked or made unbookable while the Guest typed, or the Seats booked no longer fit its Room ahead
**When** Pay is submitted
**Then** FR-29 is judged again after the lock and the store refuses; `db` maps `whole_bookable`, `booked_within_capacity` and the `(window_id, sauna_id)` unique key to `409 sauna_unavailable`, and nothing is charged, written or emailed (FR-29, AD-24)
**And** the refusal order is `outside_horizon`, then `deadline_passed`, then `sauna_unavailable`, each tested, and Review shows a Notice that says nothing was charged, removes Pay, the payment note and the checkbox, takes focus, and links back to the Private sauna page for the same date (UX-DR25)

**Given** a successful Private sauna booking
**When** the Confirmation page and the email are read
**Then** both show the Booking reference, the Sauna name, the date and session, the total paid, the Guest's email, the Venue facts, the reception sentence, the Whole-sauna booking terms, the "Before you come" link and the Manage link line, and the page shows the email "Sent by email:" as stored (FR-8, FR-30, AD-12, AD-23, UX-DR27)
**And** the email's links start with the base URL (`https://` since Epic 3, FR-24), and the page opens only in the paying browser session

**Given** an empty Window with Seats left 44
**When** Lumo (15) is booked whole
**Then** Seats left for that Window becomes 29 at once on Book seats, in the listing and in the Administrator's Booking list (B7, FR-29, AD-5)
**And** Seat bookings in that Window are then judged on the reduced Seat capacity, and other Windows are unchanged (FR-13 E4)

**Given** a Guest with a Voucher on Review for a Private sauna
**When** they enter its code in the Voucher field
**Then** `POST /api/vouchers/quote` now also accepts `{code, kind: 'whole', window_id, sauna_id}` and quotes against the Sauna's `whole_price_ore`, the Voucher field from Story 4.4 is reused unchanged, and the Pay label shows the card part (FR-28, AD-30, UX-DR39)
**And** the Whole-sauna booking request carries `voucher_code` and `voucher_part_ore` and spends the Voucher after the lock exactly as in Story 4.4, writing a `charge`/`voucher` row and any `charge`/`card` row, so that Story 5.3's refund can return each part the way it was paid (FR-28, AD-31)

**Given** two parallel requests for the same Sauna and Window
**When** both press Pay
**Then** exactly one Booking is created and the other gets `409 sauna_unavailable`, is not charged and gets no email, in each of 100 repetitions (C1, FR-11 repetitions)
**And** after each run exactly one active `whole_bookings` row exists for the pair, and Seats left equals Seat capacity minus Seats booked

**Given** a repeated Pay with the same key from the same session (double click, reload, lost response)
**When** it reaches the server
**Then** it writes nothing and returns the first outcome with its stored email; any other known key is `409 invalid_key` (FR-6, AD-9)
**And** the request hash includes `kind` and `sauna_id`, so a key first used for one Sauna cannot book another

**Given** invalid input such as a missing or unknown `sauna_id`, a `seats` value sent with `kind = 'whole'`, an unknown extra field or a malformed name or email
**When** it is posted
**Then** it is refused with `422 invalid_input` (shape) or `409` (rule) as the code table says, with no Booking, payment, token or email (FR-18, AD-16)
**And** `api/errors.py` and the frontend mirror declare `sauna_unavailable` once

**Given** the Administrator's Booking list for that date
**When** it is loaded
**Then** the Whole-sauna booking appears under its session with its reference, name, email, the Sauna name in place of a Seat count, total and time of booking, and the session's Seat capacity, Seats booked and Seats left reflect it (FR-16, AD-23)
**And** stored text stays escaped

**Given** the AD-25 walk test
**When** it walks every Seat-flow response, page and email, and every `/api/manage/` response and Change email for Seat bookings, after Private saunas exist
**Then** it finds no Sauna name and no Placement anywhere (FR-4, AD-25)
**And** Sauna names still appear only in Venue facts and in `kind = 'whole'` responses

**Given** the Private sauna flow in the e2e layer
**When** a Guest books Kajo for a session with the keyboard alone
**Then** the flow completes, axe reports no A or AA failure on Review and Confirmation, and the page titles and focus follow UX-DR33 (FR-23)
**And** `test_fr21_privacy.py` covers the flow's pages, and the README names the Private sauna flow and its seed prices (DR-2)

### Story 5.3: Cancel or move a Private sauna

As a Guest who has booked a Private sauna,
I want to cancel it for a refund or a Voucher, or move it to another session, until 72 hours before the start,
So that a change of plans does not cost my group the money we paid.

**Acceptance Criteria:**

**Given** a Whole-sauna booking opened through its Manage link
**When** the Manage page loads
**Then** it shows the Booking through the AD-23 serializer (Sauna name, session, total, status, `version`, `change_allowed`, `cutoff_at`, history) and offers "Cancel" and "Move" as confirming steps built from Epic 4's Manage components (FR-25, AD-28, UX-DR40)
**And** the page read returns no email, Voucher code or Manage link, and the Seat routes `…/seats/move` and `…/seats/voucher` answer `404 not_found` for this Booking, as `…/whole/*` routes do for a Seat booking (AD-28)

**Given** Story 5.2
**When** this story's migration runs
**Then** the `booking_changes` `action` CHECK gains `cancel` with its AD-29 shape CHECK (`voucher_id` set only when the remedy is a Voucher; `seats`, Window and Sauna ids and `new_booking_id` NULL), and nothing else changes (AD-15, AD-29)

**Given** a Whole-sauna booking before its Cutoff (72 hours before the start, the Booking's own `cutoff`)
**When** the Guest confirms "Cancel" with the remedy `refund` (`POST /api/manage/{reference}/whole/cancel {remedy, version}` with a key)
**Then** in one transaction in AD-23's write order the Booking becomes `cancelled` with `cancelled_at`, `cancel_cause = 'guest'` and `cancel_remedy = 'refund'`, the capacity row is deleted, `booking_changes` gets a `cancel` row, `services.payment.refund()` writes one `refund`/`card` row for the card charges, and the cancellation email is sent (FR-33, AD-29, AD-31)
**And** Seats left in that Window rises at once by the Sauna's Capacity, and the Administrator list shows the Booking as cancelled with time, cause and remedy and does not count it (FR-16)

**Given** a Whole-sauna booking paid partly with a Voucher
**When** it is cancelled with the remedy `refund`
**Then** `refund()` returns the card part as one `refund`/`card` row and the Voucher part as one new Voucher of that sum, recorded as a `refund`/`voucher` row, whose last valid date is the earliest of the Vouchers used but never less than 30 days after `app_now()` (FR-28, AD-31)
**And** the email names the card refund with the payment note and carries the returned Voucher block (code, value, last valid date)

**Given** a Whole-sauna booking before its Cutoff
**When** the Guest confirms "Cancel" with the remedy `voucher`
**Then** one Voucher of the full `total_ore`, valid one year, is issued through `services.voucher.issue`, also when part was paid by Voucher, with a `refund`/`voucher` row and `cancel_remedy = 'voucher'`; no card refund row is written (FR-33, AD-30, AD-31)
**And** the Voucher code reaches the Guest only inside the cancellation email shown on the result page (FR-17, AD-29)

**Given** a Whole-sauna booking before its Cutoff
**When** the Guest confirms "Move" to another Window, keeping the Sauna or picking another one (`POST …/whole/move {window_id, sauna_id, version}`)
**Then** the move follows AD-3's Booking-scoped order; `bookings` is updated first and `whole_bookings` second, with `window_id` and `sauna_id` together; the reference, price and `entry_time` are kept; a `move` history row records both Windows and both Saunas; and a Change confirmation email (Sauna, new session, price) is sent (FR-33, AD-23, AD-29)
**And** the move list on the Manage page is the AD-24 listing query with `ignore_booking` set to this Booking

**Given** a move target where the Sauna is not available whole (FR-29), or a target Sauna whose `whole_price_ore` differs from the Booking's `total_ore`
**When** the move is confirmed
**Then** the first is refused with `409 sauna_unavailable` and the second with `409 price_differs`, the original Booking is untouched, and the page says why; for a different price it says the Guest can cancel and book again (FR-33, AD-23, AD-24)
**And** `same_target` (`change_invalid`), `outside_horizon` and `deadline_passed` for the target are refused in AD-29's order, each tested

**Given** a Whole-sauna booking whose Cutoff has passed
**When** the Guest opens the Manage page or posts a cancel or move
**Then** the page still shows the Booking, and every Change is refused with `409 cutoff_passed` carrying `cutoff_at`, with the reason on the page (FR-33, AD-16)
**And** tests move the clock through `clock.off` only, and the 72-hour edge is tested on both sides (NFR-11)

**Given** a stale tab or a cancelled Booking
**When** a Change is posted with an old `version`, or after the Booking was cancelled
**Then** the answer is `409 booking_changed` (with the current Booking) or `409 booking_cancelled`, nothing changes, and the Manage page reloads the Booking and opens a fresh step with a new key (AD-29, AD-9)
**And** a repeat with the same key returns the first outcome and its stored emails, and never a second refund or Voucher

**Given** the CHECK `seat_guest_refund_forbidden` and AD-31's "never money" rule
**When** a test tries to cancel a Seat booking with `guest` and `refund` around the API, or asks `refund()` for a Booking with a split in its history
**Then** the store refuses the first, and the second raises an internal error (500), as AD-31 and the spine's Deferred list say
**And** no code path turns a Voucher balance into a card refund (AD-30)

**Given** the ledger rule of AD-31
**When** any Whole-sauna booking is created, moved or cancelled with either remedy
**Then** for a Booking with no split, the charges minus the returns equal `total_ore` while it is active and 0 once it is cancelled with a remedy, asserted in this story's tests
**And** `test_fr33_whole_change.py` covers cancel with each remedy, move, and each refusal

**Given** the Manage cancel and move steps in the e2e layer
**When** they are used with the keyboard alone
**Then** each confirming step changes nothing until confirmed, the result page shows "Sent by email:" with the email as stored, axe reports no A or AA failure, and `X-Robots-Tag: noindex` and no referrer apply (FR-25, FR-23, AD-27, UX-DR40)
**And** the wording of the result pages and the Cutoff reason follows the decisions made for Open Items 19–22 in Epic 4

### Story 5.4: The Administrator sees where Seats are counted

As an Administrator,
I want to see, for each session, which Saunas are booked whole and how many Seats are counted in each Sauna,
So that I can check that Private saunas and Seat bookings fit together, and staff know which Saunas are private.

**Acceptance Criteria:**

**Given** the SQL function `placement(wid)`
**When** it is called for a Window
**Then** it returns one row per Sauna in Fill order, `(sauna_id, state, seats)`, with `state` in `open`, `whole`, `blocked` or `marked` and `seats` 0 unless `open`, placing booked Seats only, and it is the only computation of Placement (AD-25, AD-6)
**And** a brute-force Placement written in Python lives only in `tests/` as the reference, and `placement()` matches it on every example below

**Given** the catalogue examples of FR-31, set up through `services` or raw rows (Seat cancellations through FR-27's Voucher, since a Seat booking is cancelled only that way)
**When** `placement(wid)` and Seats left are read after each step
**Then** `test_fr31_placement.py` asserts A1 `[7,2,0,0]` and 35 left; A2 `[7,10,2,0]` and 25 left; A3 `[7,10,0,0]` with Kajo then listed as bookable whole; A4 `[7,10,3,0]`; A5 `[7,10,10,0]` with Seats moving forward from Lumo first, then Kajo; A8 `[7,10,4,0]`
**And** B4 (Rauha booked whole, Bookings of 10, 10, 10 and 7 fill Seat capacity 37, and 1 more is refused), B5 `[7,—,2,0]` with 25 left, and B6 `[7,10,6,0]` after cancelling Löyly's Whole-sauna booking at `[7,—,12,4]`

**Given** the Administrator API
**When** a signed-in Administrator calls `GET /api/admin/windows/{id}/placement` (or the Booking list response carries Placement per Window)
**Then** it returns each Sauna's name, state and Seats counted from `placement(wid)` (AD-25, FR-31)
**And** anonymous callers get 401 and non-Administrators 403, and no response outside `/api/admin/` carries Placement (AD-10, RB-1)

**Given** the Booking list page for a date
**When** it is loaded
**Then** each Session group shows a Placement line or small table listing the Saunas in Fill order with "booked whole" (and the Booking reference) or the Seats counted, in words and tabular figures, never by colour alone (FR-16, FR-31, UX-DR31)
**And** the Session group's figures still equal what Guests see, and the page passes axe and the keyboard check on the Administrator layout (FR-23)

**Given** the INV-1 to INV-5 checker in `tests/`
**When** it is run against `placement(wid)` after every example in this story
**Then** INV-1 (no Sauna over Capacity), INV-2 (Seats placed equal Seats booked), INV-3 (Whole-sauna-booked Sauna holds none), INV-4 (Blocked Sauna holds none, using raw Block rows) and INV-5 (no earlier open Sauna has room while a later one holds Seats) all hold (FR-31)
**And** the same checker is a shared helper that Story 5.5 reuses

**Given** the guest-facing API and pages
**When** the AD-25 walk test from Story 5.2 runs again
**Then** it still finds no Sauna name and no Placement outside `/api/admin/` and `kind = 'whole'` responses (FR-4, AD-25)
**And** the README says where the Administrator sees Placement (DR-2)

### Story 5.5: Placement and Private saunas hold under any sequence and any race

As Lisa, responsible for the capacity guarantee,
I want a model test that runs random sequences of every booking action, and parallel tests for the races between Seats and Private saunas,
So that I can show that no Seat is ever lost, counted twice or sold over a Private sauna, whatever order the requests come in.

**Acceptance Criteria:**

**Given** `tests/test_fr31_placement_model.py`
**When** it runs under `uv run pytest`
**Then** it holds one Hypothesis `RuleBasedStateMachine` whose rules call `services` in-process against the real PostgreSQL test database: Seat booking, Whole-sauna booking, Seat move of all and of some Seats (split), Voucher for some and for all Seats, FR-33 move and FR-33 cancel with each remedy, and an explicit clock rule, over at least two Windows (AD-26, FR-31)
**And** no test-only endpoint is added, and Seats are cancelled only through FR-27 and Whole-sauna bookings only through FR-33 (AD-14, AD-26)

**Given** the machine after every step
**When** its `@invariant`s run
**Then** they check INV-1 to INV-5 and Seats left by comparing `placement(wid)` with the brute-force reference from Story 5.4, for every Window touched (FR-31, AD-26)
**And** a further invariant checks AD-31's ledger: for every Booking with no split, charges minus returns equal `total_ore` while active and 0 once cancelled with a remedy

**Given** the machine's setup
**When** an example starts
**Then** an `@initialize` rule truncates the mutable tables with `RESTART IDENTITY`, reseeds and sets the clock, Windows lie far from every time edge, and all test switches read as off whatever the local file says (AD-26, AD-14)
**And** settings come from a Hypothesis profile, `default` small enough for every `uv run pytest` and `thorough` chosen with `HYPOTHESIS_PROFILE`, with `deadline=None`, and `.hypothesis/` is git-ignored

**Given** a Window at `[7,10,12,0]`
**When** Guest A books 1 Seat while Guest B books Lumo whole, in parallel through the API, 100 times
**Then** in every repetition exactly one succeeds: either `[7,10,12,1]` with B refused, or Lumo booked whole with A refused, never both (C2, FR-32)
**And** INV-1 to INV-5 and Seats left are asserted on `placement(wid)` after each repetition

**Given** a Window at `[7,10,2,0]` with 19 Seats booked
**When** 2 Seats counted in Rauha are given up for a Voucher while Kajo is requested whole, in parallel, 100 times
**Then** Kajo is accepted only when the give-up went first (`[7,10,0,0]`), and is refused otherwise (C3, FR-32)
**And** a Whole-sauna booking is never made over a Sauna holding Seats in any repetition

**Given** a Window at `[7,10,12,4]` with 33 Seats booked
**When** two Bookings give up 3 Seats each for Vouchers in parallel, 100 times
**Then** every run ends at `[7,10,10,0]`, with no Seat moved twice or lost (C4, FR-32)
**And** each Voucher's value equals the price paid for its 3 Seats

**Given** mixed parallel requests on one Window (Seat bookings, give-ups and Whole-sauna bookings)
**When** they run under any interleaving, 100 times
**Then** INV-1 to INV-5 hold after each completed request and at the end (C5, FR-32)
**And** Seats booked never exceed Seat capacity and Seats left is never negative (FR-10)

**Given** a Seat move from Window X to Window Y and a Whole-sauna booking (or an opposite Seat move) in Y, run in parallel, 100 times
**When** both finish
**Then** INV-1 to INV-5 hold in both Windows, and no Seat is lost or counted twice (FR-32)
**And** Windows are locked in id order, so no run deadlocks beyond `db.run`'s retries (AD-3)

**Given** the full test run
**When** `uv run pytest` finishes on Lisa's laptop
**Then** the model test and the group-C tests pass within the `default` profile, and their run time is recorded in the story file
**And** the README names the `thorough` profile and how to run it (DR-2), and SM-5 is noted as covered for groups A to C as built
**And** the README's "Not delivered" section no longer lists SC2, SC4 or FR-29 to FR-33 (DR-2)
