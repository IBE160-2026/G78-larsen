- source_spec: `.docs/implementation-artifacts/spec-1-1-capacity-slice-backend-structure.md`
  summary: Test the RequestGuard middleware's 500 fallback (JSON envelope, log by exception type only) for an exception no handler catches.
  evidence: No test reaches the `except Exception` branch in `app.py`; it needs a test-only fault seam that does not exist yet (verification-gap VG4).
- source_spec: `.docs/implementation-artifacts/spec-1-1-capacity-slice-backend-structure.md`
  summary: Test migration 0002 on a legacy database that holds Windows and text-session Holds, and two migrate() runs at once.
  evidence: `test_a_legacy_database_counts_as_having_0001` uses an empty database and runners are always sequential; revisit when a migration must touch real data (verification-gap VG5).
