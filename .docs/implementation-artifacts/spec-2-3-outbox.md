---
title: 'Story 2.3: Outbox'
type: 'feature'
created: '2026-11-21'
status: 'done'
baseline_commit: '88ac5e027c927059a046388dd3955ba4060828e3'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/planning-artifacts/epics.md'
  - '{project-root}/.docs/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Administrator bar links to `/admin/outbox`, but there is no page or endpoint behind it, so nobody can read the simulated emails (FR-17), and nothing masks an email's recipient and body once its Booking is past retention (FR-21) the way the Booking list masks name and email.

**Approach:** Build Story 2.3 as written in `.docs/planning-artifacts/epics.md` (L909–952): a read-only `GET /api/admin/outbox` that masks by `retention_due` in SQL, the Outbox page reusing Email as sent, and their tests. No migration.

## Boundaries & Constraints

**Always:**
- `GET /api/admin/outbox` (guarded router, no query parameters; any query field gets `422 invalid_input`) answers `{"emails": [...]}`: every `outbox_emails` row, newest first (`created_at DESC, id DESC`), each with `id`, `created_at` (Venue-tz ISO, tz from `wq.horizon`), `recipient`, `subject`, `body` exactly as stored.
- One `db.run` of one SELECT. No lock, no write, no `ensure_generated()`.
- Masked read, same mechanism as the Booking list: when `booking_id IS NOT NULL AND retention_due(booking_id)`, `recipient` and `body` are replaced by the masked values (see Decisions) by SQL `CASE`, never by writing. `subject` is never masked. Emails with no `booking_id` are never masked. `retention_due` stays the only retention predicate; `services/catchup.py` is unchanged.
- The Outbox entry reuses `components/EmailAsSent.js`, extended so it can show a heading and header lines above the same `.email-body` block. The Confirmation page's markup and text stay the same.
- Page copy in `lib/copy.js`, browser calls only through `lib/api.js`, styling only in `app/styles.css`, keyboard steps in e2e only through `a11y.press`/`a11y.tab_to`. Stored text is rendered as React text, never as HTML.

**Never:** Add a migration or edit `0001`–`0009`. Change what the catch-up writes. Add paging, search, filters, expand/collapse or resend. Show the Outbox anywhere outside `/api/admin/`.

**Decisions (Lisa, 2026-11-21):**
- Scope: the mockup `key-booking-list.html` and DESIGN.md front-matter fix are split off to `deferred-work.md`. The story stays whole (about 2050 tokens).
- Masked values: the API masks `recipient` and `body` to `''`, the same values the catch-up stores, so a read is identical before and after the next startup. The page shows "To Anonymised" for an empty recipient and "Removed after 12 months." in the body block for an empty body.

**Decisions (planning, confirmed at approval):**
- Entry layout: `section` labelled by an `h2` with the subject in `label`, then "Sent dd.mm.yyyy HH:MM" and "To {recipient}" in `label`, then the body in the `.email-body` block. Copy: heading "Outbox", empty "No emails", failed read "The outbox could not be loaded, please try again." Title "Outbox – Saunalöyly".
- 401 on the read sends the page to Sign-in, as in `BookingList.js`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error Handling |
|---|---|---|---|
| Guest-flow Booking | Booking via `POST` flow, then read | its confirmation is first; body equals the Confirmation response's email body; every link starts with `BP_BASE_URL` | — |
| Order | several emails | newest first, ties by `id` desc | — |
| Empty | no rows | `{"emails": []}`; page "No emails" | — |
| Bad query | `?foo=1` | `422 invalid_input` | — |
| Anonymous / Guest session | no cookie, or a booking session | `401 not_signed_in`, no count | page goes to Sign-in |
| Retention | clock at 12 months + 1 s after the Window end | linked email masked, unlinked email and subject unchanged, rows and `xmin` unchanged | — |
| After catch-up | same clock, `catchup.run()` | read gives the same masked values | — |
| Masked on the page | entry with `''` recipient and body | "To Anonymised", body block "Removed after 12 months." | — |
| Hostile body | raw row with `<script>alert(1)</script>` and `<b>x</b>` on two lines | shown as text, line breaks kept, no dialog | — |
| Failed read | `5xx` or network error | — | Notice with the failed copy |

</frozen-after-approval>

## Code Map

- `migrations/0006_bookings_pay.sql:75-82` -- `outbox_emails(id, created_at DEFAULT app_now(), recipient, subject, body, booking_id FK)`; read only.
- `src/booking_platform/db/booking_list.py:24-35` -- pattern for the masked SELECT (`CASE WHEN retention_due(...)`, named params). New `db/outbox.py` with `all_emails(c)`.
- `src/booking_platform/db/retention.py:10-23` -- `ANONYMISED_*` constants and `clear_emails` (writes `''`). Put any new masked constant here.
- `src/booking_platform/services/booking_list.py:19-40` -- shape to follow (tz from `wq.horizon(c)[3]`, `.astimezone(tz).isoformat()`). Add `listing()` to existing `services/outbox.py` (keep `link`, `send`, `of_booking` unchanged).
- `src/booking_platform/api/admin.py:46` -- add `GET /outbox` beside `/bookings`; `api/schemas.py:17` `Strict` for an empty `OutboxQuery` so extra fields give 422.
- `frontend/components/EmailAsSent.js` -- extend with optional `heading` and `lines`; default renders today's "Sent by email:" output. `components/Confirmation.js:92-94` unchanged.
- `frontend/components/BookingList.js:114-140,189` -- fetch/`live`/401/Notice pattern for new `components/Outbox.js`. `components/AdminBar.js:19-22` already has the Outbox link (`current="outbox"`). `app/admin/bookings/page.js` -- template for new `app/admin/outbox/page.js` (`metadata.title` "Outbox", no Suspense needed).
- `frontend/lib/dates.js:96` `dottedTime`; `lib/copy.js:136-170` `ADMIN`, `BOOKING_LIST` -- add `OUTBOX`. `app/styles.css:1076-1095` -- email styles; add `.outbox-entry` spacing only.
- `tests/test_fr16_booking_list.py:27-53` -- `book_seats`, `written(pg)` (counts and `xmin`) to reuse for the no-write check; `:182,190` 401 tests. `tests/test_fr08_confirmation.py:28` `expected_body`.
- `tests/test_fr21_retention.py:23-94` -- `LIMIT`/`PAST`, `rows(pg)`, `booked`, catch-up test; add the Outbox masking cases here.
- `tests/e2e/admin.py`, `tests/e2e/guest.py`, `tests/e2e/a11y.py`, `tests/e2e/test_fr16_booking_list.py:162-200` -- sign-in, booking, hostile raw row, `page.route` failure and 401 patterns.

## Tasks & Acceptance

**Execution:**
- [x] `src/booking_platform/db/outbox.py`, `services/outbox.py`, `api/schemas.py`, `api/admin.py` -- the masked read and route -- FR-17, FR-21, AD-4, AD-12
- [x] `tests/test_fr17_outbox.py` -- matrix rows except retention and page rows; a read writes nothing (`written(pg)`) -- FR-17, FR-20, FR-8
- [x] `tests/test_fr21_retention.py` -- retention and after-catch-up rows; one day before the limit nothing is masked -- FR-21
- [x] `frontend/components/EmailAsSent.js`, `components/Outbox.js`, `app/admin/outbox/page.js`, `lib/copy.js`, `app/styles.css` -- the page -- UX-DR14, UX-DR32, UX-DR33
- [x] `tests/e2e/test_fr17_outbox.py` -- sign in, book in the browser, reach the Outbox from the bar by keyboard alone, find that confirmation (reference in body, recipient, "Sent" time); hostile raw row as text with no dialog; failed-read Notice, "No emails" and a masked entry via `page.route`; title; axe A/AA; no horizontal scroll at 1024/1366/1920 -- FR-17, FR-22, FR-23

**Acceptance Criteria:**
- Given `uv run pytest`, then every test passes, including those of Stories 1.1–2.2.
- Given `npm --prefix frontend run build`, then it succeeds.
- Given the Confirmation page after a booking, then its "Sent by email:" block looks and reads as before.

## Implementation Notes

- The Outbox read is one SELECT: the Venue time zone comes with each row (`CROSS JOIN settings`, `settings.venue_tz`), not from `wq.horizon`. Whether an email is masked is computed once per row (`CROSS JOIN LATERAL ... AS due`), so `recipient` and `body` are always masked together even though `retention_due` reads the clock.
- The masked value lives once as `retention.CLEARED = ''`; `clear_emails` keeps its literal SQL unchanged, so the catch-up writes exactly what it wrote before.
- `EmailAsSent` takes optional `heading`, `lines`, `id` and `className`; with none of them it renders the Confirmation block as before.
- The e2e reaches the Outbox link with Shift+Tab from the focused `h1` (the bar comes before it), each step through `a11y.press`.

## Spec Change Log

## Review Triage Log

| # | Source | Location | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|---|---|
| 1 | edge-case, blind | `db/outbox.py` | `retention_due()` evaluated separately for recipient and body | low | `retention_due` and `app_now` are VOLATILE (`clock_timestamp()`), so the two CASEs can disagree at the exact limit and return a half-masked row; computing the flag once per row is a direct correction | patch |
| 2 | edge-case, blind | `services/outbox.py`, `api/admin.py` | "One SELECT" docstrings, but `wq.horizon` is a second SELECT | low | `listing()` runs `wq.horizon(c)` then `all_emails(c)`: two statements, against the frozen "One `db.run` of one SELECT"; reading `venue_tz` in the same SELECT is trivial | patch |
| 3 | edge-case, blind | `components/EmailAsSent.js` | `key={line}` duplicates on equal lines | low | today's two lines can never be equal, but the component is now shared; keying by index is a direct correction | patch |
| 4 | blind | `tests/e2e/test_fr17_outbox.py` | hostile text never in the subject, now rendered as the `h2` | low | the raw row's subject is plain "Hostile raw row"; putting markup in it is a one-line test change | patch |
| 5 | edge-case, blind | `components/Outbox.js` | an unmasked `''` recipient/body shows as "Anonymised"/"Removed" | low | `send` always gets a Guest email and a built body; only a hand-written raw row can be empty, and the frozen Decisions define `''` as the masked display; an explicit flag adds public surface | reject |
| 6 | edge-case | `components/Outbox.js` | 200 without `emails` leaves a blank page | false | `listing()` always returns `{"emails": [...]}`; no path produces another 200 shape | reject |
| 7 | edge-case | `services/outbox.py` | no `settings` row gives a 500 | false | `settings` is the seeded single-row table every service already reads the same way (`booking_list`) | reject |
| 8 | blind | `components/EmailAsSent.js`, `styles.css` | no `<time>`, label margin also hits the `h2` | false | the spacing applies to every label line in the entry by design; the spec's layout has the time in `label`, no harm named | reject |
| 9 | blind | `tests/e2e/test_fr17_outbox.py` | "Marit Solberg" booked with `ingrid@example.com` | low | the helper fixes the email; the API test already pins the recipient to the booking's email; fix adds a helper parameter for no user-facing gain | reject |
| 10 | blind | `tests/e2e/test_fr17_outbox.py` | docstring says "as the Confirmation showed" but compares the API response | false | `booked["emails"]` is the Confirmation response the page renders; the matrix row is worded the same way | reject |
| 11 | blind | `tests/test_fr21_retention.py` | dict keyed by subject makes the subject check hollow | false | each expected subject is looked up exactly and found, which is what proves subjects are unchanged; subjects are unique by reference | reject |
| 12 | blind | tests | half-masked rows untested | false | masking uses one condition for both fields (after #1 a single evaluation), and the catch-up clears both together; no path yields one empty field | reject |
| 13 | blind | `components/Outbox.js` | no loading state or retry | false | the spec prescribes the `BookingList.js` fetch/`live`/Notice pattern, which has the same behaviour; no expansion is in scope | reject |
| 14 | verification-gap | — | no gaps | — | every changed behaviour has a failing-on-regression test | — |

## Verification

**Commands:**
- `uv run pytest -q` -- expected: all pass
- `npm --prefix frontend run build` -- expected: success
