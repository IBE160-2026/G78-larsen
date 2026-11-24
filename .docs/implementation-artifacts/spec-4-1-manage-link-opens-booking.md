---
title: 'Story 4.1: The Manage link opens the Booking'
type: 'feature'
created: '2026-11-24'
status: 'done'
baseline_commit: 'b7e6956844365935a4a98f0daf045e6140adc21b'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/specs/spec-4-1-manage-link/SPEC.md'
  - '{project-root}/.docs/specs/spec-4-1-manage-link/brownfield.md'
  - '{project-root}/.docs/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A Guest with a Seat booking can only read the confirmation. Every Change in Epic 4 and Epic 5 needs a way into the Booking without an account, and none exists.

**Approach:** Build CAP-1 to CAP-10 of `.docs/specs/spec-4-1-manage-link/SPEC.md` (the canonical contract) in one PR. Migration `0010` adds hashed link tokens, per-session grants, a Cutoff copied onto each Booking and `version`. Paying and the seed issue a link, emailed as `<base>/manage#t=<token>`. `/manage` swaps the fragment for a grant, and `/manage/[reference]` reads the Booking through one grant-checked router. Terms everywhere carry the approved change statement. No Change action is built.

## Boundaries & Constraints

**Always:**
- Everything in SPEC.md's Constraints, including the approved copy (verbatim) and AD-28's issue order.
- `manage_grant_valid` is one SQL function, and the dependency checks it and touches `last_used_at` in **one** autocommit `UPDATE … WHERE manage_grant_valid(…) RETURNING` (`db.statement`). No row means `404 not_found`, and that holds without a session as well.
- `POST /api/manage/open` accepts any JSON string `token`. A token that is too long (over 200 characters), malformed, unknown, revoked or past its Window is `404 not_found` and never `422`. A non-JSON body or a missing field stays `422` (shape). With a valid token it returns `{reference}` and sets the cookie only when a new session was created.
- The read serializer: `{reference, kind: "seats", seats, sauna: null, window: {id, date, start, end}, total_ore, status, version, change_allowed, cutoff_at, history: []}`. Times are ISO strings in Venue time, and `change_allowed` comes from the SQL predicate. Name and email are left out. No Python clock is used.
- `bookings.cutoff` gets the column default `seat_cutoff()`, a SQL function that reads `settings.cutoff_seats`. That way the existing raw test inserts keep working, and `insert_booking` still passes the value explicitly.
- `cutoff_passed` (409, fact `cutoff_at`) is added to `api/errors.py` and `lib/api.js` STATUS. Its copy goes in `lib/copy.js`.
- The confirmation email gets a "Manage your booking" line with the link, placed just before "Before you come". The seed's own email for an existing sample has the subject `Manage your booking: <ref>` and carries the reference, the session, the link and the change statement, and no Sauna.
- Manage page copy (Lisa, 2026-11-24): `h1` and title "Manage booking"; before the Cutoff the line "You can change this booking until {long date} at {HH:MM}."; labels from `SUMMARY` (Date, Session, Seats, Total) plus "Booking reference".
- README (Norwegian): in the Outbox section, say where the sample link is and that it works until its session ends (DR-2). Update the Status line, and the "Manage-lenker finnes ikke ennå" line under Sikkerhet.

**Never:** Build Change routes or actions, `booking_changes`, Vouchers, My booking, Whole-sauna Manage or `cutoff_whole`. Put the token in a path, query, log, cookie or any table except as a hash. Set headers outside Caddy. Return `401` from a Manage route. Edit migrations `0001`–`0009`. Add a dependency. Weaken an existing test (apart from replacing the old terms sentence).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Open, valid | `#t=<token>`, no cookie | Cookie set, grant row, `{reference}`; URL without fragment; `/manage/<ref>` with `h1` focused | — |
| Open, bad | unknown / revoked / Window ended / 500-char / `"x"` | `404 not_found`, same body | No grant; a session is created only on success |
| Open again | same token, same browser | Grant upserted (one row), `last_used_at` = now | — |
| Read, foreign or unknown ref | grant for A, GET B or `ZZZZZZZZ`; or no cookie | `404 not_found` for all | Nothing written |
| Grant idle | `clock.off` +31 min | `404`; opening the link again restores it | — |
| Before or after Cutoff | `app_now()` vs `lower(during) - cutoff` | `change_allowed` true or false; the page shows the until-text or the approved reason | — |
| Sign-out | Administrator signs out in a browser that has a grant | Grants deleted by cascade | — |
| Restart | seed samples already have tokens | No new token, no new email | — |

</frozen-after-approval>

## Code Map

- `migrations/0010_manage_links.sql` (new) -- tables, the partial unique index, settings and bookings columns (backfill `cutoff`, then `SET NOT NULL`), `seat_cutoff()`, `change_allowed(bid bigint)`, `manage_grant_valid(sid bigint, bid bigint)` (all VOLATILE because of `app_now()`). `manage_grants.token_id` FK `access_tokens ON DELETE CASCADE`. Do not touch the `a_lock_bookings`/`t_bookings` column lists.
- `src/booking_platform/db/manage.py` (new) -- SQL: lock the Booking `FOR NO KEY UPDATE`, revoke, insert the hash; find a token by hash + validity; upsert the grant; check-and-touch; the read row; the purge; samples missing a token.
- `src/booking_platform/services/manage.py` (new) -- `issue(c, booking_id) -> token`, `link(token)`, `open(session_token_cookie, token)`, `grant(session, reference) -> booking_id`, `read(booking_id)`, `purge()`. Reuse `sessions.token_hash`, `sessions.open_session` and `reference.is_reference`.
- `src/booking_platform/services/booking.py:79-111,116-144` -- the email gains the link (update its docstring). `create` calls `manage.issue` after the insert and before building the email. `long_date` is reused for the seed email.
- `src/booking_platform/db/seats.py:55` `insert_booking` -- add `cutoff` = `(SELECT cutoff_seats FROM settings)`.
- `src/booking_platform/services/seed.py:188` `apply_bookings` -- after the loop, call `manage.issue` and send the email for each known sample key whose Booking has no unrevoked token and whose Window has not ended.
- `src/booking_platform/app.py` lifespan -- after `sessions.purge_expired()`, `manage.purge()`, and log the count.
- `src/booking_platform/config.py:35` `links` -- `manage = "/manage"`.
- `src/booking_platform/api/manage.py` (new) -- `open_router` (`POST /api/manage/open`) and `router` (`prefix="/api/manage/{reference}"`, dependency `require_grant`) with `GET ""`. Both use `redirect_slashes=False`. Register them in `app.create_app`. Schema `ManageOpenIn` goes in `api/schemas.py`.
- `src/booking_platform/api/errors.py`, `frontend/lib/api.js` -- add `cutoff_passed: 409`.
- `content/terms-seats.json` -- replace the second paragraph with the change statement. `frontend/content/` is a git-ignored copy that the predev/prebuild script makes, so do not edit it by hand.
- `frontend/app/terms/page.js:50-51` -- the change statement.
- `frontend/app/manage/page.js`, `frontend/app/manage/[reference]/page.js` (new) -- Server Components with `metadata` that render client children.
- `frontend/components/ManageOpen.js`, `ManageBooking.js`, `ManageBookingSummary.js`, `ConfirmingStep.js`, `ChangeResult.js` (new) -- follow `Confirmation.js`: `NotAvailable` on 404, `Notice` on failure, no `h1` until loaded. `ChangeResult` wraps `EmailAsSent`. `ConfirmingStep` is a minimal heading/summary/confirm-button shell and is not rendered.
- `frontend/lib/copy.js` -- `MANAGE` (heading, untilText, cutoffPassed(longDate, time), loadFailed).
- `tests/test_fr08_confirmation.py:48`, `tests/e2e/test_fr05_book_and_pay.py:23` -- replace the old sentence and match the link line with a regex.
- `tests/e2e/test_fr21_privacy.py` -- add a Manage page test. The log search (L184) also asserts that the issued token is absent.
- Reuse: `tests/conftest.py` `world`/`api`/`admin`/`set_clock`/`raw_booking`; `tests/e2e/admin.db_url`, `a11y.check_axe`/`no_horizontal_scroll`/`tab_to`, `guest.book_in_browser`.

## Tasks & Acceptance

**Execution:**
- [x] `migrations/0010_manage_links.sql` -- CAP-1 schema and predicates -- the store owns validity.
- [x] `src/booking_platform/db/manage.py`, `services/manage.py`, `config.py`, `db/seats.py` -- token, grant, read, purge -- the only writer of `access_tokens`.
- [x] `services/booking.py` -- issue in `create` and put the link in the email -- CAP-2.
- [x] `services/seed.py`, `app.py` -- issue for samples, purge at startup -- CAP-3, CAP-7.
- [x] `api/manage.py`, `api/schemas.py`, `api/errors.py`, `app.py` -- routes and the grant dependency -- CAP-4 to CAP-6.
- [x] `content/terms-seats.json`, `frontend/app/terms/page.js` -- the change statement -- CAP-9.
- [x] `frontend/lib/api.js`, `lib/copy.js`, `app/manage/**`, the 5 components -- the pages -- CAP-4, CAP-5, CAP-8.
- [x] `tests/test_fr25_manage_link.py` -- the full list in SPEC.md Constraints/Tests plus every row of the I/O matrix; for the absence check, walk the JSON for `token`, `@`, the Outbox body, `manage#t=` and the Sauna names.
- [x] `tests/test_fr08_confirmation.py`, `tests/e2e/test_fr05_book_and_pay.py` -- the new terms text and the link.
- [x] `tests/e2e/test_fr25_manage.py`, `tests/e2e/test_fr21_privacy.py` -- CAP-10: the sample link from the Outbox works over HTTPS; the fragment is gone and the `h1` is focused; a guessed reference shows NotAvailable; headers; axe; keyboard; widths; no token in `compose logs`; Review's Pay is in the first view at 1366×768.
- [x] `README.md` -- the sample link, Status, Sikkerhet.

**Acceptance Criteria:**
- Given a fresh compose stack, when the examiner opens a sample Manage link from the Outbox over `https://localhost:8443`, then the Booking shows with the token gone from the URL, and a guessed `/manage/<ref>` shows "This page is not available.".
- Given a booking paid in the browser, when its Confirmation loads, then "Sent by email:" shows `https://…/manage#t=…` and the new change statement, and no page says "A booking cannot be changed or refunded.".
- Given the change, when `uv run pytest` runs (API + e2e), then everything is green, including `test_dr4_migrations.py` and `test_fr25_manage_link.py`.

## Implementation Notes

## Spec Change Log

## Review Triage Log

| # | Source | Finding | Verdict | Evidence | Route |
|---|--------|---------|---------|----------|-------|
| 1 | verification-gap | Non-404 failure of the Manage read/open (Notice "could not be loaded") untested | medium | Pre-verified: no `page.route` stub on `/api/manage` in tests; other pages test this path | patch |
| 2 | edge-case, blind | `replaceState` before the POST, so "please try again" cannot be retried by reload | low | Real, but only on a 5xx/network failure; reopening the email link works; Design Notes order is deliberate (token off the URL at once); fix needs new unapproved copy or a retry flow | reject |
| 3 | edge-case, blind | Orphan session if the token turns invalid between `valid_token` and `upsert_grant` | low | Real race window of milliseconds (revocation/Window end in between); the orphan session is anonymous and expires; fix restructures `open_session` transactions | reject |
| 4 | edge-case, blind | `change_allowed`/`manage_token_valid` ignore `status = 'cancelled'` | maybe-false | No code path sets `cancelled` today (only the CHECK in 0006); would be medium once cancellation exists (Epic 5) | defer |
| 5 | edge-case, blind | `ConfirmingStep` hard-codes `id="confirming-step-heading"` | low | Two instances would duplicate the id; direct fix with `useId()` | patch |
| 6 | blind | Terms promise Changes that are not built yet | false | The frozen Intent decides it: "Terms everywhere carry the approved change statement. No Change action is built." | reject |
| 7 | blind | "12 hours" is fixed copy while `cutoff_seats` is a setting | false | Copy is approved verbatim in SPEC.md; no route or UI changes `cutoff_seats` in v1 | reject |
| 8 | blind | `ManageOpen` failed state has no h1 | low | Real: the `failed` Notice on `/manage` has no heading, unlike `ManageBooking`'s failed state; direct fix | patch |
| 9 | blind | `change_statement()` takes paragraph `[1]` by position | false | A reorder would be caught: `test_the_seed_gives_every_sample_a_link_once` asserts `CHANGE_STATEMENT in body` | reject |
| 10 | blind | `seed.manage_email` unpacks a positional tuple | low | Developer-only; a column change breaks the seed test loudly; fix (named rows) is more than a direct correction | reject |
| 11 | blind | `samples_without_token` would re-issue after a future revocation | maybe-false | Today only `issue` revokes, and it inserts a replacement in the same transaction; would be medium if Story 4.2/Epic 5 revoke a sample's token without replacement | defer |
| 12 | blind | Purge skips grants via revoked tokens and idle grants | low | Such grants are already invalid by `manage_grant_valid`; only table growth on a long-running local stack; fix adds conditions | reject |
| 13 | blind | Sensor guide `.docs/sensorveiledning-kravsporing.md` has no FR-25 entry | low | Real doc lag; outside the Code Map; noted as an open item for Lisa instead of editing the examiner's guide unasked | reject |
| 14 | blind | Seed Manage email is thin / has no mockup | false | Matches the frozen constraint: reference, session, link, change statement, no Sauna | reject |
| 15 | blind | `.summary + .notice` is a site-wide selector | low | No other page renders a Notice right after a summary (Confirmation, Review checked); no current effect | reject |
| 16 | blind | README "bookingens økt" is ambiguous next to browser sessions | low | Real ambiguity in the same paragraph; direct wording fix | patch |
| 17 | blind | e2e sample depends on the stack's start date | false | The e2e stack runs `up --build` and ends with `down -v`, so the seed is always fresh | reject |

## Design Notes

The Strict-Mode-safe open: a `useRef` flag set before the read, so the second effect run sees it and does nothing. The flow reads `location.hash`, then calls `history.replaceState(null, '', '/manage')`, then `api('/api/manage/open', {method: 'POST', body: {token}})`, then `router.replace('/manage/' + reference)`. No fragment or a 404 renders `NotAvailable`. FocusMover's MutationObserver path focuses the `h1` once the read renders it.

## Verification

**Commands:**
- `uv run pytest tests --ignore=tests/e2e` -- expected: all pass.
- `uv run pytest tests/e2e` -- expected: all pass (the compose stack builds itself).
- `npm --prefix frontend run lint` (if defined) and `npm --prefix frontend run build` -- expected: no errors; `/manage` and `/manage/[reference]` build.
