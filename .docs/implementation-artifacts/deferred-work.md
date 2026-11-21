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
