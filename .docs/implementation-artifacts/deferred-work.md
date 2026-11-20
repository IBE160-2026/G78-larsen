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
