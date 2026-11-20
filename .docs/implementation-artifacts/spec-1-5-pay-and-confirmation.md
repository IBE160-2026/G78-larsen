---
title: 'Story 1.5: A Guest pays and gets a confirmation'
type: 'feature'
created: '2026-11-20'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/planning-artifacts/epics.md'
  - '{project-root}/.docs/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `POST /api/bookings` takes a free-text `guest`, stores no name, email, reference, price or payment, sends nothing and has no one-time key; Details, Review and Confirmation do not exist. A Guest cannot pay or get a confirmation (FR-5, FR-6, FR-8).

**Approach:** Build Story 1.5 in `.docs/planning-artifacts/epics.md` (L632–705) as its ACs list: migration `0006`, `services.{payment,reference,outbox}`, the new booking and confirmation endpoints with AD-9 keys, `content/`, the confirmation email, the seed Bookings, the three pages, and the API and e2e tests the ACs name. Also carry the three open points from Story 1.1/1.4 below.

## Boundaries & Constraints

**Always:**
- One `db.run`: `charge()` decided before `lock_windows`; after the lock the key is read first, then `ensure_open_for_booking`, Holds deleted, the Booking inserted through `services.reference`, the `payments` row, then `outbox.send()`, then the key row. Only a success stores a key.
- `request_hash` = SHA-256 of canonical `{endpoint, window_id, seats}` — never name or email. A known key from the same session, endpoint and hash returns the first outcome (Booking as it is now + the emails read by id) with nothing written; any other known key is `409 invalid_key`.
- Prices and totals shown anywhere come from the stored `price_per_seat_ore` / `total_ore` (except the pre-payment total, as on Book seats). No Sauna name or id in any Seat-flow response, page or email. Stored text rendered only as text (React escaping; no `dangerouslySetInnerHTML`).
- Copy verbatim from EXPERIENCE.md and `mockups/key-confirmation.html`; booking terms and the reception sentence only from `content/`. Keyboard steps in e2e go through `a11y.press` / `a11y.tab_to`. Only `styles.css`, no `style` props.
- Existing API tests keep their assertions; only their request shape changes to `{window_id, seats, name, email}` + `Idempotency-Key` (AD-21).

**Never:**
- Build Story 1.6: the Review refusal Notices and Nearest sessions on Review, the specific payment-failed/`invalid_key` copy, `test_fr11`, `test_fr12`. Until then any refusal on Review shows the "please try again" Notice with Pay kept.
- Edit migrations `0001`–`0005`. Delete Booking rows. Add a Manage link, Voucher or Hold UI.

**Decisions:**
- **Migration `0006_bookings_pay.sql`** (next free number; AD-7's "0002" is corrected in the spine): `bookings` gains `reference text UNIQUE` (`^[0-9A-HJKMNP-TV-Z]{8}$`), `name` (1–100 chars), `email` (1–254), `price_per_seat_ore int >= 0`, `total_ore int` (`= seats × price_per_seat_ore`), `session_id bigint REFERENCES sessions ON DELETE SET NULL`, `status text DEFAULT 'active' CHECK IN ('active','cancelled')`, `entry_time timestamptz DEFAULT app_now()`; all NOT NULL except `session_id`. Legacy rows are backfilled (reference = `lpad(upper(to_hex(id)),8,'0')`, name = trimmed `guest` or `'Guest'`, email `'unknown@example.invalid'`, price from `settings`, `entry_time = created_at`); then `guest` is dropped. `window_booked_seats()` counts `status = 'active'` only; `a_lock_bookings` and `t_bookings` are recreated (same names) on `INSERT OR DELETE OR UPDATE OF window_id, seats, status`. New tables `payments`, `outbox_emails(id, created_at, recipient, subject, body, booking_id)`, `idempotency_keys(key uuid UNIQUE, session_id … ON DELETE CASCADE, endpoint, request_hash bytea, booking_id, created_at)` exactly as AD-9/12/13 (no `change_id`, `voucher_id` columns yet).
- **Refusal map (`db/refusals.py`):** `bookings_session_id_fkey`, `holds_session_id_fkey` and `idempotency_keys_session_id_fkey` → `no_session` (401), so a sign-out racing a write is no longer `404 not_found`. New codes in `api/errors.py` and `lib/api.js`: `invalid_key` 409, `payment_pending` 409, `payment_failed` 409.
- **`charge()`:** reads the `payment` switch only for runs made for an HTTP request (`config.in_request`), like `force_conflict`; `ok` → card charge, `fail` → `payment_failed`, `hold` → `payment_pending`, both raised before anything is written. The seed always charges `ok`.
- **Endpoint shapes:** `POST /api/bookings` → 201 `{booking, emails}` (also on a repeat). `GET /api/bookings/{reference}/confirmation` → `{booking, emails}`; another session, no session, or an unknown or malformed reference → the same `404 not_found`. `booking` = `{reference, date, start, end, seats, price_per_seat_ore, total_ore, name, email, status}`; `emails` = `[{subject, body}]`.
- **Email:** subject `Booking confirmed: <reference>`; body exactly the line layout of `key-confirmation.html` L89–112 with `<BP_BASE_URL>/#before-you-come` (`config.links.before_you_come`).
- **Frontend routes:** `/book-seats/details`, `/book-seats/review`, `/confirmation/[reference]`. Draft `draft:seats` = `{date, seats, window_id, name, email, key}`; the key is made on reaching Review if absent; after success the draft is `{reference}` only, and Details/Review then `router.replace` to Confirmation. Book seats with a `{reference}`-only draft starts a fresh draft. Details without a chosen session → Book seats; Review without name or email → Details (no error).
- **Seed Bookings:** `seeds/bookings.json`, applied after `ensure_generated()` at startup through `services.booking.create` under one fixed seed session (`expires_at = 'infinity'`) with fixed keys; an entry whose key already exists is skipped, so a restart (any day) creates no duplicates. **List (Lisa, 2026-11-20)**, offsets from the Venue date at first start, all `@example.com`: +1 day 14:30, 2 Seats (Ingrid Berg); +2 days 17:30, 42 of 44 (Ola Nordmann 10, Kari Hansen 10, Per Johansen 10, Liv Olsen 10, Aino Virtanen 2); +3 days 19:00, full (Jonas Lie 10, Siri Dahl 10, Erik Moe 10, Nora Bakke 10, Mikko Laine 4); +5 days 10:00, 4 Seats (Olav Strand). Nothing today, so the result never depends on the start time. The e2e tests pick a day without seed Bookings.
- **Carried from 1.4 (Lisa, 2026-11-20):** the two Notice texts ("The session you chose no longer has room for N seats. Choose another session." and "The sessions could not be loaded, please try again.") are approved; `nearest` in `GET /api/windows` comes only when both `date` and `seats` are given and no Window on the date has room — the current code is right.
- **Scope (Lisa, 2026-11-20):** the story stays whole even though the spec is about 3300 tokens.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected |
|---|---|---|
| Pay | session, Window with room, 2 Seats, valid name/email, new key | 201; one Booking (reference 8 Crockford chars, total 50000), one card `payments` row, one Outbox email, one key row; Seats left −2 |
| Repeat | same key, session, body | 201 same `booking` and `emails`; still one of each row |
| Repeat, other name | same key and Window/Seats, other name | first outcome (name not in hash) |
| Other request | same key, other Seats or Window | 409 `invalid_key`, nothing written |
| Other session | key known from another session | 409 `invalid_key` |
| No key / malformed key | missing or non-UUID header | 422 `invalid_input` |
| Invalid input | Seats 0/−1/1.5/"x"/11; Window unknown or malformed; missing field; extra field; `window_ids` list; name ""/101 chars; email ""/255 chars/no `@` | 422 (unknown Window: 404 `not_found`); no Booking, payment, email or key |
| Script name | `<script>alert(1)</script>` | stored as given; JSON and pages show it as text |
| Confirmation | paying session / other session / unknown ref / lower-case ref | 200 / 404 / 404 / 404, same body for all 404s |
| Logout race | session row deleted between resolve and insert | 401 `no_session` (FK map) |
| Seed restart | backend started twice, also on a later day | sample Bookings exist once |

</frozen-after-approval>

## Code Map

- `migrations/0001_core.sql` L21–24 `bookings`, L82 `window_booked_seats`, L236/L242 `a_lock_bookings`/`t_bookings` -- replaced in 0006, never edited (pinned by `tests/test_dr4_migrations.py`).
- `migrations/0002_sessions.sql` -- `sessions`; `holds.session_id` FK `holds_session_id_fkey`.
- `src/booking_platform/db/__init__.py` -- `run` (READ COMMITTED, 5 retries, `_force_conflict` seam L58), `lock_windows` L102, `statement`.
- `src/booking_platform/db/refusals.py` L28–47 -- `MAP`, `code_for` (`*_fkey` → `not_found`): add the three session FKs first.
- `src/booking_platform/db/seats.py` L77 `delete_holds`, L89 `insert_booking` -- replace the insert with the reference insert (`ON CONFLICT (reference) DO NOTHING RETURNING id`); add `db/bookings.py` for keys, payments, outbox, confirmation read.
- `src/booking_platform/services/booking.py` L12 `book` -- becomes `create(session_id, window_id, seats, name, email, key)`; `services/windows.py:162` `ensure_open_for_booking` reused.
- `src/booking_platform/api/public.py` L60 `POST /api/bookings`, `api/schemas.py:150` `BookingIn`, `api/deps.py` `require_session`/`current_session`, `api/errors.py` L17–32 `STATUS` (mirror enforced by `tests/test_fr14_status_mirror.py`).
- `src/booking_platform/config.py` -- `Switches.payment` L98 exists; add `paths.CONTENT` and `links` (`before_you_come = "/#before-you-come"`); `base_url`, `in_request` exist.
- `src/booking_platform/services/seed.py:51` `apply`, `app.py` lifespan -- seed Bookings after `windows.ensure_generated()`.
- `db/venue.py:16` `venue_facts`, `services/venue.py:85` -- price and Venue identity for the email.
- `tests/conftest.py` -- `world` L192 TRUNCATE list gains `payments`, `outbox_emails`, `idempotency_keys`; `MUTATIONS` L59 (`notriggers` drops `t_bookings`: keep the name); `start_backend(switches=…)` L132; `tests/client.py::api_client`.
- Existing callers of `POST /api/bookings`: `test_application_rules`, `test_fr10_through_the_api`, `test_fr14_retry`, `test_fr14_switches`, `test_fr18_csrf`, `test_fr2_input`, `test_fr21_sessions`; `test_fr10_bypass` inserts raw rows (needs the new NOT NULL columns).
- `frontend/lib/{api,draft,copy,venue-format,server-api}.js`, `components/{BookSeats(DETAILS L28),ErrorSummary,FieldError,FocusMover,GuestShell,Notice,NotAvailable,PrimaryButton,TextLink,TryAgain,Wordmark}.js` -- reuse; `frontend/scripts/run-next.mjs` already copies `../content` (satisfies predev/prebuild); `.gitignore` already has `frontend/content/`. Check both Dockerfiles copy `content/`.
- `.docs/.../ux-designs/.../mockups/key-{details,review,confirmation}.html`, EXPERIENCE.md L175–206, L316–368 -- layout and copy.

## Tasks & Acceptance

**Execution:**
- [ ] `migrations/0006_bookings_pay.sql` -- columns, backfill, triggers, three tables -- AD-7, AD-9, AD-12, AD-13
- [ ] `content/{terms-seats,reception}.json`, `config.py`, `services/{payment,reference,outbox,content}.py`, `services/booking.py`, `db/{bookings,seats,refusals}.py`, `api/{public,schemas,errors}.py` -- create, repeat, confirmation read, email body -- FR-5, FR-6, FR-8, FR-9, AD-20
- [ ] `seeds/bookings.json`, `services/seed.py`, `app.py`, `backend Dockerfile`/`frontend/Dockerfile` -- seed Bookings; `content/` in both images -- AD-18
- [ ] `tests/conftest.py` and the existing booking callers -- new request shape and TRUNCATE list
- [ ] `tests/test_fr06_payment.py`, `test_fr08_confirmation.py`, `test_fr18_validation.py`, `test_fr04_no_sauna.py`, `test_dr5_seed_bookings.py`, `test_dr4_migrations.py`, `test_fr21_sessions.py` (FK → `no_session`) -- the matrix rows
- [ ] `frontend/app/book-seats/{details,review}/page.js`, `app/confirmation/[reference]/page.js`, `components/{Details,Review,Confirmation,BookingSummary,EmailAsSent,ReferenceDisplay,TermsCheckbox}.js`, `lib/{api,draft,copy}.js`, `BookSeats.js`, `app/styles.css` -- the three pages -- FR-5, FR-6, FR-8, UX-DR5/6/9/10/14/23/24/26/27
- [ ] `tests/e2e/test_fr05_book_and_pay.py`, `tests/e2e/test_fr21_privacy.py` -- keyboard flow, titles, axe, Pay in first view, widths, script name as text, Confirmation in another browser
- [ ] `ARCHITECTURE-SPINE.md` AD-7 ("migration `0006`"), `README.md` status, `.logs/lisa-larsen/issues.md` (close the three carried points)

**Acceptance Criteria:**
- Given `uv run pytest`, then every test passes, Stories 1.1–1.4 included.
- Given `npm --prefix frontend run build`, then `/book-seats/details`, `/book-seats/review` and `/confirmation/[reference]` build without error.
- Given a paid Booking, when Back, `/book-seats/details` or `/book-seats/review` is opened, then Confirmation shows and no second payment is possible.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run pytest -q` -- expected: all pass
- `npm --prefix frontend run build` -- expected: success, the three new routes listed
- `docker compose up --build --wait`, then book 2 seats in the browser -- expected: Confirmation with reference and the email as sent
