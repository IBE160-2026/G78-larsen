---
id: SPEC-4-1-manage-link
companions:
  - brownfield.md
  - ../../planning-artifacts/architecture/architecture-booking-platform-2026-11-03/ARCHITECTURE-SPINE.md
  - ../../planning-artifacts/ux-designs/ux-booking-platform-2026-11-05/EXPERIENCE.md
  - ../../planning-artifacts/ux-designs/ux-booking-platform-2026-11-05/DESIGN.md
sources:
  - ../../planning-artifacts/epics.md
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Story 4.1: The Manage link opens the Booking

## Why

Opportunity, first step of Epic 4 (PRD §4.8, If time 2): a Guest with a Seat booking can today only read the confirmation. Epic 4 lets them move Seats or take a Voucher without an account or staff help, and every Change in 4.2–4.4 (and Epic 5) goes through the Manage link. This story builds that door — token, grant, read and page — and nothing behind it. HTTPS (Epic 3) is done, so links can now be sent. Read the spine's AD-28 in full before building; the AD numbers below point into it.

**Terminology:** *session* means the browser's `sessions` row; the sauna time slot is the *Window*.

## Capabilities

- **CAP-1**
  - **intent:** The store holds Manage tokens, grants, each Booking's own Cutoff and a version, and judges the Cutoff with one predicate.
  - **success:** Migration `0010` adds `access_tokens(id, purpose, booking_id, token_hash bytea UNIQUE, created_at, revoked_at)` (`purpose` CHECK `'manage'`, unique partial index `access_tokens_one_manage` on unrevoked manage tokens per Booking); `manage_grants(session_id, token_id, last_used_at)` UNIQUE `(session_id, token_id)`, `ON DELETE CASCADE` from `sessions`; `settings.cutoff_seats interval` default 12 h, `CHECK >= interval '2 hours'`; `bookings.cutoff interval NOT NULL` filled from `cutoff_seats` for existing rows; `bookings.version int NOT NULL DEFAULT 0`; SQL `change_allowed(booking_id)` = `app_now() < lower(during) - cutoff`. `test_dr4_migrations.py` still passes.
- **CAP-2**
  - **intent:** Paying for a Seat booking issues its Manage link and emails it.
  - **success:** `services.booking.create` copies `cutoff_seats` into the Booking and calls `services.manage.issue(c, booking_id)` in the same transaction; the stored hash is SHA-256 of a `secrets.token_urlsafe(32)` token; the confirmation email (stored and shown "Sent by email:" on Confirmation) contains `<BP_BASE_URL>/manage#t=<token>` starting with `https://` in the compose stack.
- **CAP-3**
  - **intent:** The examiner finds a working sample Manage link without booking first.
  - **success:** At startup the seed issues a token, through `services.manage.issue`, for each sample Booking with no unrevoked manage token, with an Outbox email carrying its link; a second start issues nothing. README says where the sample link is in the Outbox and that it works until its Window ends (DR-2).
- **CAP-4**
  - **intent:** Opening the link gives this browser access to that Booking only, with the token gone from the address bar.
  - **success:** `/manage` client component reads `#t=` once (Strict-Mode-safe), calls `history.replaceState` to drop it, sends `POST /api/manage/open {token}` via `lib/api.js`; the call creates or reuses the session cookie, checks the token, upserts the grant and returns `{reference}`; the browser lands on `/manage/[reference]` with focus on the `h1` (AD-17, UX-DR33).
- **CAP-5**
  - **intent:** Nobody can tell a bad link or a foreign reference from one that never existed.
  - **success:** Unknown, malformed, revoked, or Window-ended tokens → `POST /api/manage/open` answers `404 not_found`, identical to a never-issued token; the page shows "This page is not available." with a link to Landing (`NotAvailable`). `GET /api/manage/{reference}` for another existing Booking or a non-existent reference gives the same `404 not_found`, with or without a session (RB-4, RB-5).
- **CAP-6**
  - **intent:** A granted session can read its Booking, and the read reveals nothing beyond the Booking.
  - **success:** Every route under `/api/manage/{reference}/` sits on one router whose dependency checks `manage_grant_valid(session_id, booking_id)` (last use < 30 min ago, token unrevoked, before the Window ends), then touches `last_used_at` in one autocommit statement. `GET /api/manage/{reference}` writes nothing else and returns the AD-23 serializer (`kind`, `seats`, `sauna: null`, `window`, `total_ore`, `status`) + `version`, `change_allowed`, `cutoff_at`, `history: []`. A test walks the response and finds no Outbox body, Voucher code, Manage link or Sauna name.
- **CAP-7**
  - **intent:** Access fades when unused and is restored by the email link.
  - **success:** With `clock.off` moved > 30 min past last use, the read answers `404 not_found`; opening the email link again restores it. Signing out an Administrator session in the same browser deletes its grants by cascade. Startup purges grants of expired sessions and of tokens whose Window has ended.
- **CAP-8**
  - **intent:** The Manage page shows the Booking and whether it can still be changed.
  - **success:** Before the Cutoff: reference, date, Window, Seats, total paid, and until when Changes are possible (`cutoff_at` in Venue time); loading changes nothing. After the Cutoff: same Booking plus the approved reason text (Constraints). `ManageBookingSummary`, `ConfirmingStep` and `ChangeResult` ("Sent by email:") live in `frontend/components/`.
- **CAP-9**
  - **intent:** Terms everywhere state the §4.8 change rule instead of "no changes".
  - **success:** `content/terms-seats.json` (and its `frontend/content/` mirror), Terms "Changes and refunds", Review, Confirmation and the confirmation email carry the approved statement and no longer "A booking cannot be changed or refunded."; Review still shows Pay in the first view at 1366×768 (UX-DR24); tests asserting the old text are updated.
- **CAP-10**
  - **intent:** The Manage pages leak nothing and are accessible.
  - **success:** e2e: `/manage`, `/manage/<reference>`, `/api/manage/open`, `/api/manage/<reference>` carry `X-Robots-Tag: noindex` and `Referrer-Policy: no-referrer` from Caddy; `test_fr21_privacy.py` sees no request off the stack origin from the Manage page; `docker compose -p booking_e2e logs` does not contain the issued token; axe reports no A/AA failure on the Manage page and on "This page is not available."; keyboard-only works and no horizontal scroll at 1024, 1366, 1920 px.

## Constraints

- Token never in a path, query, log line, or any table except as its hash (AD-19, AD-12). Only `services.manage` writes `access_tokens`; `issue` locks the Booking `FOR NO KEY UPDATE`, revokes any unrevoked manage token, then inserts (AD-28).
- One SQL predicate each: `change_allowed` (Cutoff), `manage_grant_valid` (access). Validity is judged by join, never stored (AD-4).
- GETs write nothing except the grant/session touch, one autocommit statement outside any action transaction (AD-4).
- Manage routes never answer `401 no_session`; every refusal is plain `404 not_found` (AD-28 Access, AD-16). `POST /api/manage/open` passes the same-origin CSRF check (AD-8); it is the only page load besides Book seats and Sign-in that sets the session cookie (FR-21).
- `bookings.version` stays out of AD-7's trigger column list. Migration number is `0010` (AD-15).
- No token is issued for Bookings created before this migration, except seed samples (AD-28).
- Approved copy (Lisa, 2026-11-24):
  - after the Window ends: "This page is not available." (Open Item 21);
  - after the Cutoff: "This booking can no longer be changed. Changes are possible until 12 hours before the session starts, and that was {long date} at {HH:MM}." — code `cutoff_passed` with fact `cutoff_at` added to `api/errors.py` and the frontend mirror (Open Item 22, AD-16);
  - change statement: "Up to 12 hours before the session starts, you can move some or all seats to another session, or give them up for a voucher. Money is not refunded." It ships in full in 4.1, before moving (4.2) and Vouchers (4.3) exist;
  - "12 hours" is fixed copy: Administrators cannot change `cutoff_seats` in v1, so it matches every Booking's stored `cutoff`.
- `ConfirmingStep` and `ChangeResult` are created in 4.1 but first used in 4.2; 4.1 renders no Change action.
- Seat pages and emails never name a Sauna (FR-4, AD-25). Caddy alone sets the headers; the Caddyfile `@manage` matcher already exists (AD-27).
- Tests: new `tests/test_fr25_manage_link.py` (hashing and length, email link format, seed tokens, open with valid/unknown/revoked/expired, grant expiry, RB-4, RB-5, read fields and absences) plus e2e Manage tests; every earlier test still passes.

## Non-goals

- No Change actions: moving Seats (4.2), Voucher (4.3–4.4), history rows and `booking_changes` come later; `history` is always `[]` here.
- No new-link-on-request / My booking (FR-34) and no token for pre-existing non-seed Bookings.
- No Whole-sauna Manage routes or `cutoff_whole` (Epic 5).
- No Administrator view of Changes in the Booking list.
- Open Items 19–20 (page after a Voucher, after a Venue cancellation) stay undecided.

## Success signal

- In the compose stack, the examiner opens a seed Manage link from the Outbox over `https://localhost:8443`, lands on the Booking with the token gone from the URL, a guessed reference shows "This page is not available.", and `uv run pytest` (API + e2e) is green including `test_fr25_manage_link.py`.
