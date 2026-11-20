# Epic 1 Context: A Guest finds a session and books seats

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Deliver the complete Guest Seat-booking flow for Saunalöyly on the spine's architecture: a Guest opens the Landing page, picks a date, 1–10 Seats and a session (Window) with true Seats left and one total, enters name and email, accepts the terms, pays with a Simulated payment and gets a Confirmation page plus the email as sent. However many Guests pay at once, no Seat is sold twice, and a loser gets a clear message, the nearest sessions with room and no charge. The epic starts by reshaping the existing capacity slice onto the layered backend and compose stack without loosening any rule. It also creates the shared homes that every later epic reuses: stylesheet and tokens, `frontend/components/`, `frontend/lib/`, `content/`, shared services and test fixtures.

## Stories

- Story 1.1: The capacity slice runs on the spine's backend structure
- Story 1.2: The platform starts with one command and shows its Terms and Privacy notice
- Story 1.3: The Landing page presents the Venue
- Story 1.4: A Guest picks a date, a number of seats and a session
- Story 1.5: A Guest pays and gets a confirmation
- Story 1.6: A Guest who cannot get the seats is told why and charged nothing

## Requirements & Constraints

- **Capacity integrity:** never sell more Seats than are left, even when the application is bypassed (the store refuses it). In the last-Seat race exactly one request wins, tested with 100 repetitions per run against real PostgreSQL. Requests are all or nothing. Losers get no charge, no email and no stored key.
- **Seats, not Saunas:** no Seat-flow page, response or email shows a Sauna name or id. Windows are Venue-wide, never overlap (back-to-back is allowed), and keep their local clock times across DST. A Window starting or ending in a skipped or repeated hour is refused.
- **Payment:** simulated, with no credentials or external service. A one-time idempotency key per Review means a repeat returns the first outcome and never charges twice. A failed payment creates nothing. "Simulated payment: no money moves" appears on Pay and in every payment email.
- **Validation (server-side):** Seats must be an integer from 1 to 10 and no more than are left. The date or Window must be inside the Booking horizon (4 weeks) and before its deadline. Name is 1–100 characters, email is valid and at most 254. Unknown fields are rejected and only one Window is allowed per Booking. Stored text is only ever shown escaped. Seed data is validated like Administrator input.
- **Privacy:** Guests give name and email only. Only strictly necessary cookies are used, and the session cookie is set only from Book seats (not on Landing, Terms or Privacy). No third-party requests. Secrets, tokens and request bodies never appear in logs. The confirmation opens only in the paying browser session. A guessed reference gets the same 404 as an unknown one.
- **Honest UI:** no countdowns, false scarcity, pre-ticked options or hidden fees. English only, Europe/Oslo time.
- **Laptop layout and accessibility:** WCAG 2.2 AA, with 1.4.10 Reflow as the one known gap. No horizontal scroll at 1024, 1366 and 1920 px. Book seats and Pay are in the first view at 1366×768. Pages are usable with the keyboard alone, with a visible focus ring at all times.
- **Tests are part of done in every story**, and all of them run with `uv run pytest`.

## Technical Decisions

- **Layers:** dependencies run one way, `api` → `services` → `db`, and `config.py` is a leaf that every layer may import. SQL lives only in `db/` and `migrations/`. Every refusal is `services.errors.Refused(code, **facts)`. Store errors are mapped by constraint name, and an unmapped one is a 500 that never leaks store text.
- **Errors:** `api/errors.py` is the single code → status table, and the frontend mirrors it in one place in `frontend/lib/`. The envelope is `{"detail": {"error", "message"?, …facts}}`. A shape error is `422 invalid_input` with `fields`, a rule refusal is 409 (`no_seat_free` with `seats_left`, `outside_horizon`, `deadline_passed`, `invalid_key`, `payment_pending`), a lost or missing session is `401 no_session`, and running out of retries is `503 try_again`.
- **Capacity in PostgreSQL:** counters, a `CHECK` constraint, recompute triggers and deferred verification. Any change that affects capacity needs lock and recompute triggers, a bypass test and a `MUTATIONS` entry in the test harness. Seats left comes only from `seats_left()`, `window_booked_seats()` and `window_open_capacity()`.
- **Transactions:** one user action is one `db.run(work)` at READ COMMITTED. Before the first write, `lock_windows(c, ids)` locks Windows in id order. Only `db.run` retries 40001 and 40P01, a bounded number of times.
- **Time:** time rules read `app_now()` after the lock, and each rule is one SQL predicate (`booking_deadline`, `within_horizon`, `venue_date`, `window_started`). Never cast timestamptz to a date without `AT TIME ZONE settings.venue_tz`. There are no background jobs, and GETs never write, with two exceptions: `windows.ensure_generated()` and the session touch. Tests move the clock only through `clock.off`.
- **Sessions:** a `sessions` table stores the SHA-256 hash of a 256-bit token. The cookie is HttpOnly, `SameSite=Strict` and `Path=/` (`Secure` only when `BP_HTTPS` is on), and an anonymous session lasts 24 h, sliding. Sessions are created only by `POST /api/session`. A cross-origin write is refused with `403 cross_origin`.
- **Idempotency:** every confirming request carries an `Idempotency-Key`. Only successes are stored. `request_hash` covers only the fields that decide the outcome, never name or email.
- **Money:** amounts are integer øre in `*_ore` fields. The Booking stores `price_per_seat_ore` and `total_ore`, which are always shown and never recomputed. `services.payment.charge()` decides before the lock and writes after it.
- **Reference and email:** the Booking reference is 8 upper-case Crockford base32 characters, created by `services.reference` with `ON CONFLICT DO NOTHING` and at most 5 tries. Email is sent only by `services.outbox.send()` inside the action's transaction. Bodies are plain text, and links are absolute, built from `BP_BASE_URL`. Text shared by pages and emails lives once in `content/*.json`.
- **Migrations, seed and config:** schema changes go in numbered plain SQL files `migrations/NNNN_name.sql`, which are never edited after merge. `seeds/` is applied idempotently at every start and never overwrites. `config.py` is the only reader of the `BP_*` variables. Test switches are read once at startup from a TOML file at two fixed points: `payment.charge` (`ok | fail | hold`) and `db.run` (`force_conflict`).
- **API:** everything lives under `/api`, and admin endpoints are on one `/api/admin/` router. Unknown paths and 405s answer the JSON `404 not_found` envelope. `redirect_slashes=False` is set, and `/docs` and `/openapi.json` are off. Endpoints: `GET /api/venue`, `GET /api/windows?date=&seats=`, `POST /api/bookings`, `GET /api/bookings/{reference}/confirmation`.
- **Frontend:** Next.js App Router in plain JavaScript with `output: 'standalone'`. It has no `app/api/`, route handlers, Server Actions or middleware. `lib/api.js` is the only browser fetch caller. `lib/server-api.js` is the only server-side caller, used for public GETs only (`no-store`, no cookie, never throws). There is one stylesheet, `app/styles.css`, which holds the design tokens. There is no UI library, TypeScript, Tailwind, CSS Modules, `style` props, `next/font` or `next/image`. Fonts are self-hosted, and every file in `public/` is listed in `ASSETS.md`.
- **Stack:** Caddy is the only published port (`127.0.0.1:8000`, HTTP in the Core), routing `/api` and `/api/*` to the backend; compose runs proxy, backend, frontend and db with healthchecks and `up --wait`.
- **Tests:** files are named `tests/test_fr<NN>_<topic>.py`. The API layer goes through `tests/client.py::api_client` against `booking_test`. The e2e layer (`tests/e2e/`) runs the `booking_e2e` compose project with Playwright and axe-core, and every keyboard step goes through `tests/e2e/a11y.py`.
- **Traceability:** each story gets branch `story/1-<n>-<short-name>` and one PR, with FR numbers in commit messages. Lisa merges each PR with a normal merge commit.

## UX & Interaction Patterns

- **Guest shell:** a sticky 320 px rail plus a main column, centred up to 1320 px. The one breakpoint is `max-width: 1199px`, where multi-column parts stack. Pages use square corners, no shadows and light mode only.
- **Shared components:** primary button (one per page, at least 48 px, "Processing" while busy and ignores a second press), Text link, Wordmark, Rail, Notice (neutral, never shown as an error), Error summary (takes focus and adds the "Error: " title prefix), Field error and Nearest sessions (up to three links). Date, Seat and Session choices are radio groups with one tab stop and arrow-key movement.
- **Focus and titles:** each page title is "<heading> – Saunalöyly". After navigation, focus goes to the `h1` or to a fragment target such as `/#before-you-come`.
- **Copy:** "session" means a Window to the Guest, never a browser session; specified copy is used verbatim; nothing is pre-selected and "Continue booking" is always enabled.
- **Booking draft:** `sessionStorage` key `draft:seats` holds the choices, name, email and idempotency key, and survives a reload. After payment it holds only the reference, so Back can never reach a page that can pay again.
- **Review refusals:** the Guest stays on Review with input kept. A Notice takes focus and offers the nearest sessions. Pay, the payment note and the checkbox are removed for the refused session.

## Cross-Story Dependencies

- Stories build strictly in order. 1.1 (backend structure) underpins all of them. 1.2 creates the compose stack, frontend scaffold, shared frontend homes and the e2e/a11y fixtures. 1.3 adds the seed, Venue facts and the Notice component. 1.4 adds the Window listing, time predicates, the session cookie and the draft, which 1.5 consumes. 1.6 builds on 1.5's booking endpoint and on 1.4's nearest-Windows listing.
- Epic 1's tests get an Administrator session from a fixture, so they do not wait for Epic 2 (Administrator sign-in).
- Later epics reuse this epic's shared homes, and Epic 2's "Core done" story re-checks the README, ASSETS.md and the accessibility passes across all of them. Leave room for the narrow layout planned for later: no fixed widths.
