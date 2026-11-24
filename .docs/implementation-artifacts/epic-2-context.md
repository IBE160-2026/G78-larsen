# Epic 2 Context: The Administrator sees who is coming

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Give Saunalöyly's staff a safe back office and finish the Core. The Administrator signs in with a throttled, hashed password, sees every session (Window) of a chosen day with Seat capacity, Seats booked, Seats left and every Booking, and reads every simulated email in the Outbox exactly as sent. Anonymous visitors and Guests get nothing from any Administrator address or endpoint. The epic ends with "Core done": the examiner can start the platform, sign in and run every test from a fresh clone by following the README alone, and the automated and manual accessibility passes cover every Core page. Epic 3 (HTTPS) follows.

## Stories

- Story 2.1: Administrator signs in and out
- Story 2.2: Booking list for a chosen day
- Story 2.3: Outbox
- Story 2.4: Core done: the examiner can run, sign in and check everything

## Requirements & Constraints

- **Seeded login:** `admin@saunaloyly.example` with a documented local test password (in `seeds/` and the README); a restart never overwrites the hash. Accounts and password changes go only through the seed or `booking-platform create-admin`, which prompts twice without echo and never takes the password as an argument or env var. No response ever contains a password or hash.
- **One answer for every failure:** wrong password, unknown email and throttled email all get the same `401`, the same code and "Wrong email or password". Unknown emails are verified against a dummy hash so timing reveals nothing.
- **Throttle:** 5 failures in a row per lower-cased email (known or unknown) lock it for 15 minutes, even for the right password; a success resets the count; parallel wrong attempts are all counted.
- **Passwords:** salted slow hashes only (same password gives different hashes). Minimum 15 characters, at least 64 allowed, any characters, no composition rules; refused if on the common list or equal to the email (case-insensitive). Paste and password managers work.
- **Access:** role checked server-side on every Administrator request. Anonymous callers, including a Guest's booking-flow session, get `401` and learn nothing, not even a count. Sign-out revokes the session; the old token then gets `401`.
- **Booking list:** figures equal what Guests see for the same Window; a new Booking shows on the next load; stored text is always rendered escaped; a malformed date or unknown query field gets `422 invalid_input`.
- **Outbox:** every email newest first with time, recipient, subject and full body as stored; links are plain text, absolute and start with `BP_BASE_URL` (`http://localhost:8000` in the Core). A Booking's confirmation body equals the Confirmation page's "Sent by email:" block. HTML or script in a body shows as text with line breaks kept. Guests see an email only on the page of the action that sent it.
- **Retention:** past retention (more than 12 months after the end of the Booking's Window), name and email are masked on read in the Booking list, and linked Outbox emails have recipient and body masked. Reads never write; the next startup's catch-up anonymises the Booking and clears its emails' recipient and body. Emails not linked to a Booking are unaffected. Tested by moving the clock through `clock.off`.
- **Logs:** the test password, session tokens and request bodies never appear in compose logs.
- **Accessibility and layout:** WCAG 2.2 AA (1.4.10 Reflow is the only known gap), keyboard-only operation, no horizontal scroll at 1024, 1366 and 1920 px.
- **Core done:** final copy and images on every Core page, SC1, SC9 without HTTPS and the laptop part of SC10 pass, `main` is green, and the README's "Not delivered" list is true on the day it is merged. Tests are part of done in every story and all run with `uv run pytest`.

## Technical Decisions

- **Schema (2.1 migration):** only `accounts(id, email UNIQUE, password_hash, role)`, nullable FK `sessions.account_id`, and `sign_in_throttle(email_lower PK, failures, locked_until)` with no FK to `accounts`.
- **Hashing:** Argon2id via `argon2-cffi` defaults (PHC format), rehashed at sign-in when parameters change. `services.auth.check_password_rules(password, email)` is the single rule function for seed, `create-admin` and later sign-up; the common list is `src/booking_platform/data/common-passwords.txt`.
- **Throttle transaction:** one `db.run(work)` per attempt; upsert and lock the throttle row `FOR UPDATE` before deciding, and return (not raise) a refusal from `work` so the count commits. Time from `app_now()`.
- **Sessions:** opening Sign-in calls `POST /api/session`; no other Administrator page load creates a session. `POST /api/admin/sign-in` rotates the token on the same `sessions` row, sets the Administrator role and an 8 h sliding lifetime. `POST /api/admin/sign-out` deletes the row and clears the cookie. Both fall under the CSRF rule (no same-origin `Origin`/`Sec-Fetch-Site` gives `403 cross_origin`).
- **Router:** all Administrator endpoints on the one `/api/admin/` router; its dependency resolves the caller via `sessions.account_id` and role. Anonymous gets `401`, non-Administrator `403`, neither changes anything. The test fixture's Administrator session comes from a real sign-in with the seeded account.
- **Booking list API:** `GET /api/admin/bookings?date=YYYY-MM-DD` returns every Window starting on that Venue date in time order (including empty ones) with `start`, `end`, `seat_capacity`, `seats_booked`, `seats_left` taken only from `window_open_capacity()`, `window_booked_seats()` and `seats_left()`; Bookings oldest first with reference, name, email, Seats, `total_ore`, `created_at`. No lock, no write apart from `ensure_generated()`. The page's default date is the API's `today`, never the browser clock.
- **Outbox API:** `GET /api/admin/outbox` reads `outbox_emails` newest first, no lock, no write; only `/api/admin/` lists it. `services.outbox.send` stays the only sender, inside the action's transaction; bodies are plain text built in `services`, with links from `BP_BASE_URL`.
- **Retention:** `retention_due(booking_id)` is the one SQL predicate (built in 2.2, reused by the Outbox read via `outbox_emails.booking_id`). Epic 4 adds the Voucher `expires_at` clause. `services/catchup.py` does the startup anonymisation, one function per effect; no background jobs.
- **Conventions:** refusal codes declared once in `api/errors.py` and mirrored in `frontend/lib/`; error envelope `{"detail": {"error": ..., ...}}`. Money "NOK 500" from integer øre; times `dd.mm.yyyy HH:MM` Europe/Oslo. Browser calls only through `lib/api.js`; all styling in the one `app/styles.css`. Shared components in `frontend/components/` (Administrator bar new; Error summary, Notice, Text field, Email-as-sent reused).
- **Tests:** API: `tests/test_fr15_sign_in.py`, `test_fr19_passwords.py`, `test_fr16_booking_list.py`, `test_fr17_outbox.py`. E2E: `tests/e2e/test_fr15_sign_in.py`, `test_fr16_booking_list.py`, `test_fr17_outbox.py`, `test_fr23_accessibility.py`, `test_fr23_keyboard_and_zoom.py`; Story 2.4 extends `test_fr21_privacy.py`. Keyboard steps go through `tests/e2e/a11y.py` (`press`, `tab_to`, `tab_order`, `zoomed`, `check_axe`, `no_horizontal_scroll`).

## UX & Interaction Patterns

- **Shell:** full-width Administrator bar (`bar` fill, `on-bar` text, weight 600), no rail, one column up to `spacing.page-max`. On Sign-in the bar shows the name only; elsewhere it holds Booking list, Outbox, Sign out.
- **Sign-in:** bar, heading, email, password, "Sign in", in that order. Every refusal shows an Error summary with "Wrong email or password" and no Field error. Anonymous visits to any Administrator address, Back after sign-out, and the next action after expiry all lead to Sign-in; copy never uses the word "session" for this.
- **Booking list (dense layout, revised 2026-11-21):** date Text field (default today) with "Previous day"/"Next day" Text links. One group per session in time order, rule above. Session time in `session-time-selected` (Source Sans 3, 600, 18 px, text family, not a heading font); capacity, booked and left on the same line in `body-sm` tabular figures. A session with no Bookings says "No bookings" on that same line, so it is one line. Booking table: header in `label`, rows in `body-sm`, 1 px `border` lines, 2 px vertical cell padding, indented `spacing.4` under the session header, numbers right-aligned in tabular figures. A full session gets an `unavailable` header with "Sold out" and "Seats left 0" in weight 600 (not colour alone). Failed read: Notice with "please try again". No search feature; reception uses the browser's find. UI copy says "session" for a Window.
- **Outbox:** bar, heading "Outbox", one always-open entry per email, newest first: the Email-as-sent block (`surface`, 1 px `border`, `spacing.5` padding) with time, recipient and subject in `label` above the body in `small`, line breaks kept, links as plain text. Masked values show as masked. Empty: "No emails".
- **Titles and focus:** "Sign in – Saunalöyly", "Booking list – Saunalöyly", "Outbox – Saunalöyly", prefixed "Error: " while an Error summary shows; focus moves to the `h1` after navigation.
- **Manual passes (2.4):** confirm, not repeat, the automated checks: keyboard only, 200 % zoom at 1366×768 and 1920×1080 (screenshots in `test-results/zoom/`), the Book seats tab order, and NVDA + Chrome on Book seats, Review and Confirmation. Recorded in `tests/manual/core-accessibility.md`.

## Cross-Story Dependencies

- **Epic 1 only:** reuses the `/api/admin/` router, sessions, the outbox service, the Window functions, the e2e fixture, `a11y.py`, the shared components and the stylesheet.
- **2.1 first:** switches the Administrator test fixture to real sign-in; until 2.2 lands, the post-sign-in address shows only the bar and a heading.
- **2.2 → 2.3:** 2.2 builds `retention_due`, the masked list read and the startup catch-up (which already clears Outbox recipient and body); 2.3 reuses the same predicate for the Outbox read.
- **2.4 last:** depends on 2.1–2.3 and every Epic 1 page; finalises the README (install, compose and dev commands, test login, sample Bookings, Outbox, `create-admin`, test switches, folders, security section, "Not delivered" list) and the `ASSETS.md` check, and runs and logs the fresh-clone check.
- **Later epics:** Epic 3 (HTTPS) and Epics 4–5 shorten "Not delivered", extend the Booking list (status, history, Whole-sauna bookings, Placement) and add the Voucher clause to retention.
