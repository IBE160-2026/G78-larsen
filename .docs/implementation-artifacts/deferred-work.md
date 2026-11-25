- source_spec: `.docs/implementation-artifacts/spec-1-1-capacity-slice-backend-structure.md`
  summary: Test the RequestGuard middleware's 500 fallback (JSON envelope, log by exception type only) for an exception no handler catches.
  evidence: No test reaches the `except Exception` branch in `app.py`; it needs a test-only fault seam that does not exist yet (verification-gap VG4).
- source_spec: `.docs/implementation-artifacts/spec-1-1-capacity-slice-backend-structure.md`
  summary: Test migration 0002 on a legacy database that holds Windows and text-session Holds, and two migrate() runs at once.
  evidence: `test_a_legacy_database_counts_as_having_0001` uses an empty database and runners are always sequential; revisit when a migration must touch real data (verification-gap VG5).
- source_spec: `.docs/implementation-artifacts/spec-1-2-compose-stack-terms-privacy.md`
  summary: Render the error boundary (`app/error.js`, `app/global-error.js`, TryAgain) in an e2e test and assert the "please try again" Notice, its title and that Next's default error page never shows.
  evidence: No route can fail on purpose in Story 1.2; Story 1.3's first `server-api.js` page (or a test switch) gives a reachable failure (verification-gap VG3).
- source_spec: `.docs/implementation-artifacts/spec-1-2-compose-stack-terms-privacy.md`
  summary: Make FocusMover also react to hash-only and query-only client navigation (fragment target, else h1).
  evidence: Its effect depends on `pathname` only; the first same-page fragment link (Landing's "Before you come", Story 1.3) would move no focus (edge-case EC2).
- source_spec: `.docs/implementation-artifacts/spec-1-2-compose-stack-terms-privacy.md`
  summary: Decide in the architecture whether Caddy should also send `X-Content-Type-Options: nosniff`, a frame guard and a `Content-Security-Policy` (`default-src 'self'`).
  evidence: AD-27 enumerates the header set and has none of these; a CSP would let the browser enforce FR-21's same-origin rule (blind-hunter BH1).
- source_spec: `.docs/implementation-artifacts/spec-1-2-compose-stack-terms-privacy.md`
  summary: Pin Landing's page title "Saunalöyly" and the "Error: " title prefix in e2e tests when Landing (Story 1.3) and the first form with an Error summary arrive.
  evidence: Neither has a test today; the stub is temporary and no page renders `[data-error-summary]` yet (verification-gap VG5, VG other 1).
- source_spec: `.docs/implementation-artifacts/spec-1-3-landing-page-venue.md`
  summary: Decide whether the seed may insert a seeded Sauna again after the store deleted it, before Sauna administration is built.
  evidence: `seed_sauna` inserts any absent seeded id at every start (literal AD-18), and `test_fresh_start_restart_and_a_value_the_store_owns` pins it; an Administrator could never retire a seeded Sauna (blind-hunter, edge-case, verification-gap).
- source_spec: `.docs/implementation-artifacts/spec-1-3-landing-page-venue.md`
  summary: Test `frontend/lib/venue-format.js` for a price with øre (25050, 25005), whole hours (120) and minutes only (45) when an Administrator story lets price and Session length change.
  evidence: Only 25000 and 90 are checked end to end, and the frontend has no unit-test runner (verification-gap VG2).
- source_spec: `.docs/implementation-artifacts/spec-1-4-book-seats-date-seats-session.md`
  summary: Add a test that `seed.apply()` checks the schedule's daylight-saving rule against the store's `settings.venue_tz`, not the Europe/Oslo default.
  evidence: Every schedule test uses the default zone, so reverting `apply` to `load(directory)` passes the suite; it matters once an Administrator can change `venue_tz`.
- source_spec: `.docs/implementation-artifacts/spec-1-5-pay-and-confirmation.md`
  summary: Test the sample-Booking seed's skip paths (an entry with no Window at its time, and one the store refuses) so startup continues and logs one "sample booking N skipped" line.
  evidence: `services/seed.py:apply_bookings` handles both, but the shipped seed always matches the shipped schedule, so no test reaches them; it matters once the schedule or seed is Administrator-editable.
- source_spec: `.docs/implementation-artifacts/spec-1-5-pay-and-confirmation.md`
  summary: E2e-test Review's refusal path (Notice shown, Pay re-enabled, the draft key unchanged; after 401 a new session and a successful retry).
  evidence: `frontend/components/Review.js` `pay()` catch branch has no test; Story 1.6 replaces the refusal Notices, so the test belongs there (a Playwright `page.route` stub returning 409 suffices).
  status: done (Story 1.6, `tests/e2e/test_fr11_refusals.py`: every refusal state on Review against the real stack, including `401 no_session` with a successful retry under the same key).
- source_spec: `.docs/implementation-artifacts/spec-1-6-refusals-charged-nothing.md`
  summary: E2e-test Review's fallback to the listing's `nearest` (other dates) when the refused session's date has no other session with room, and that choosing one reloads Review for that date.
  evidence: Unverified (maybe-false, medium if true): every refusal in `tests/e2e/test_fr11_refusals.py` uses a date with eight empty Windows, so the fallback branch in `Review.js` `nearestSessions` never runs; settle by filling the date's other seven Windows in the seats-taken test.
- source_spec: `.docs/implementation-artifacts/spec-2-1-admin-sign-in-out.md`
  summary: Bound the cost of sign-in: the Argon2id verify (64 MiB, t=3) runs inside the `db.run` transaction while holding the throttle row lock and a pool connection, so a burst of sign-ins can starve the pool.
  evidence: `services/auth.py` `sign_in` `work`; prescribed by the Story 2.1 intent (AD-11). Options: a verify semaphore, or verify outside the transaction with a re-check of the lock.
- source_spec: `.docs/implementation-artifacts/spec-2-1-admin-sign-in-out.md`
  summary: E2e-test that an Administrator page restored from the back/forward cache after sign-out re-checks `GET /api/admin/me` (`AdminGuard` `pageshow`) and goes to Sign-in.
  evidence: The current Back step returns to the first Sign-in entry (sign-out uses `router.replace`), so no Administrator page is restored and the `pageshow` listener never runs in a test.
- source_spec: none
  summary: Update mockups/key-booking-list.html to the denser Booking list style in DESIGN.md (commit 1541485) and fix DESIGN.md front matter, which still lists heading-md for the session group.
  evidence: Split from the Story 2.3 Outbox intent (2026-11-21); independently shippable design-doc work, not part of the Outbox.
- source_spec: none
  summary: Story 2.4 part B — rewrite the README in the order the story lists (tools, compose, dev, tests, test login and sample Bookings, Outbox, create-admin and switches, folders), add the security and "Not delivered" sections, run the fresh-clone check, add `tests/manual/core-accessibility.md` with Lisa's manual passes (keyboard, 200 % zoom, tab order, NVDA), and record "Core done" in the session log.
  evidence: Split from the Story 2.4 intent (2026-11-21, Lisa chose "A first"); independently shippable docs and manual work that needs Lisa at the laptop; Story 2.4 stays in progress until it is done.
- source_spec: `.docs/implementation-artifacts/spec-2-4-core-done-automated-checks.md`
  summary: Make the other keyboard flows that change the Seat number and then Tab to a Session (`test_fr02_book_seats.py:139`, `test_fr05_book_and_pay.py:57`) wait on the `/api/windows?…seats=N` response instead of `networkidle`.
  evidence: Unverified (maybe-false, medium if true): the same pattern failed 1 in 5 runs in the new zoom test (focus lost when the rows were replaced after Tab reached them); the older tests have not been seen failing.
- source_spec: `.docs/implementation-artifacts/spec-3-1-serve-website-api-https-only.md`
  summary: `tests/test_fr15_sign_in.py::test_five_failures_lock_the_email_for_15_minutes_even_with_the_right_password` is flaky under load.
  evidence: Failed twice on 2026-11-24 (once beside a parallel e2e run, once just after it), then passed 6 of 6 alone; likely the `14:59 < locked_until - now` window, since `now` is read after five Argon2 sign-ins. Story 3.1 touches no backend or API-layer test file.
- source_spec: `.docs/implementation-artifacts/spec-3-1-serve-website-api-https-only.md`
  summary: `tests/e2e/test_fr17_outbox.py::test_a_401_on_the_read_goes_to_sign_in` timed out once (30 s, still on `/admin/bookings`) in a full e2e run.
  evidence: 161 of 162 passed in that run; the file re-run with `test_fr24_https.py` gave 12 passed. A second full e2e run is needed to tell flakiness from an HTTPS-related cause.
- source_spec: `.docs/implementation-artifacts/spec-4-1-manage-link-opens-booking.md`
  summary: `change_allowed` and `manage_token_valid` (migration 0010) ignore `bookings.status`, so a cancelled Booking with a live token would open and show "You can change this booking until …".
  evidence: Unverified (medium if true): no code sets `status = 'cancelled'` yet (only the CHECK in 0006). Settle it when the first cancellation path is built (Epic 5): either revoke the token on cancel or add `status = 'active'` to the predicates, and give the Manage page a cancelled state.
- source_spec: `.docs/implementation-artifacts/spec-4-1-manage-link-opens-booking.md`
  summary: `db.manage.samples_without_token` re-issues a token and a "Manage your booking" email on every restart for any sample whose token was revoked without a replacement.
  evidence: Unverified (medium if true): today only `manage.issue` revokes, and it inserts a replacement in the same transaction. Settle it when Story 4.2 or Epic 5 adds a revoke without replacement: limit the query to Bookings that never had a token.
- source_spec: `.docs/implementation-artifacts/spec-4-3-give-up-seats-for-a-voucher.md`
  summary: The voucher step's own "Valid until" rule (29 February -> 28 February in `GiveUpSeats.js` `lastValidDate`) has no test; consider returning `last_valid_date` from the API instead of recomputing it in the browser.
  evidence: Backend rule is tested with a 29 Feb clock, but the e2e runs at the real clock and the frontend has no unit runner; settled by a test with the stack clock on 29 Feb or by removing the browser computation.
- source_spec: `.docs/implementation-artifacts/spec-4-4-pay-with-a-voucher.md`
  summary: Seats paid with a Voucher can be given up (Story 4.3) for a new Voucher at full value with a fresh one-year expiry, so a near-expiry Voucher can be renewed indefinitely by booking and giving up.
  evidence: 4.3 values the give-up at the stored price per Seat and issues `app_now() + 1 year`; Lisa decides whether the voucher-paid share should keep the spent Voucher's expiry (FR-27/AD-30 policy).
