# Digest impl-r1-1 (angle: implementation)

Accessed 2026-10-28. Format: claim | source URL | publisher | pub_date | accessed | confidence | class

## Findings

- SQLite transactions are DEFERRED by default; a deferred transaction starts only at first database access (SELECT starts a read tx, a write statement starts a write tx) | https://www.sqlite.org/lang_transaction.html | sqlite.org | n/d (living doc) | 2026-10-28 | high | pattern
- BEGIN IMMEDIATE starts a write transaction up front and "might fail with SQLITE_BUSY if another write transaction is already active on another connection". It fails at BEGIN, before any work is done | same | sqlite.org | n/d | 2026-10-28 | high | pattern
- Deferred read-then-write: if a read tx is open and another connection has modified (or is modifying) the database, the upgrade to write fails with SQLITE_BUSY. Check-then-insert (is the sauna empty? then insert whole booking) under DEFERRED is therefore exposed to BUSY mid-transaction. The doc's remedy is BEGIN IMMEDIATE | same | sqlite.org | n/d | 2026-10-28 | high | failure-claim (single source, but official doc)
- SQLite allows many simultaneous readers but only one write transaction. A reader keeps a snapshot of the database from before concurrent changes | same | sqlite.org | n/d | 2026-10-28 | high | pattern
- In WAL mode EXCLUSIVE and IMMEDIATE are the same. COMMIT can also return SQLITE_BUSY, and the transaction stays active so the COMMIT can be retried | same | sqlite.org | n/d | 2026-10-28 | high | version-compat
- INFERENCE: with BEGIN IMMEDIATE around the whole "check emptiness, place, move seats" unit, writers are serialized. That gives serializable behaviour for these rules without row locks, and a retry/busy_timeout policy is all that is needed. It is the minimal-effort design for a single-user local app. (The WAL page itself was not read; the busy_timeout detail is not sourced.)
- PostgreSQL SERIALIZABLE "emulates serial transaction execution"; applications "must be prepared to retry transactions due to serialization failures" (SQLSTATE 40001). Retry the whole transaction | https://www.postgresql.org/docs/current/transaction-iso.html | postgresql.org | n/d (current docs) | 2026-10-28 | high | pattern
- PostgreSQL docs' write-skew example (on-call doctors: two transactions each read a count, update different rows, invariant breaks under Repeatable Read) is structurally the same as "two guests check the sauna is empty and book different rows". Serializable aborts one of them | same | postgresql.org | n/d | 2026-10-28 | high | failure-claim (official doc example)
- Under Serializable, unique violations can appear even after an explicit "not present" check. Serializable predicate locks do not block and cannot cause deadlock | same | postgresql.org | n/d | 2026-10-28 | medium | pattern
- PostgreSQL: an exclusion constraint with a range type, `EXCLUDE USING GIST (during WITH &&)`, forbids overlapping rows. Combined with a scalar via btree_gist, `EXCLUDE USING GIST (room WITH =, during WITH &&)` forbids overlap per room only | https://www.postgresql.org/docs/current/rangetypes.html | postgresql.org | n/d (PG18 docs) | 2026-10-28 | high | pattern
- INFERENCE: the exclusion constraint covers only "no overlap among rows of the same kind". "Whole booking cannot overlap a seat-group in the same sauna" is a cross-kind rule. It needs either one table with a `kind` column plus a conditional or partial scheme, or a serializable check or trigger. It does not follow directly from the sourced example. SQLite has no exclusion constraints (INFERENCE from the absence of any mention in the pages read; not verified), so app-level checks inside BEGIN IMMEDIATE would be the equivalent.
- Hypothesis (Python) stateful testing generates whole sequences of actions (`RuleBasedStateMachine`), with `@invariant` checked after each rule and a minimal reproducing program printed on failure. It is called "model-based testing" elsewhere | https://hypothesis-test-zhd.readthedocs.io/en/latest/stateful.html (found via search snippet only, mirror, not fetched) | readthedocs mirror of Hypothesis docs | n/d | 2026-10-28 | medium | pattern
- INFERENCE (invariants to assert after every action): per sauna, placed seats <= capacity. Sum of placed seats over all saunas = sum of booked seats per window. A whole-booked sauna in a window has zero individual seats. No placed seats in a blocked sauna during a block. After a cancel, no earlier sauna is non-full while a later one holds seats (compaction / fill-order). A model-based test would compare the DB against an in-memory reference model.

## Leads worth chasing
- Q1 (store placement vs derive from counts): no practitioner source found. A targeted search (for example "bin packing booking recompute on read" or Stack Overflow / dba.stackexchange threads on "derived vs stored allocation") is needed.
- INFERENCE worth testing: deriving placement from per-window counts means "move seats on cancel" becomes automatic (pure function of counts and capacities). Whole-bookings and blocks do not fit a pure count model, though, and window overlap makes derivation order-dependent. This needs a design decision in the PRD.
- SQLite https://www.sqlite.org/wal.html and the busy_timeout pragma docs, for exact BUSY behaviour in WAL.
- SQLite triggers (RAISE(ABORT)) docs for enforcing cross-row overlap checks.
- Hypothesis official docs (hypothesis.readthedocs.io) and `fast-check` model-based testing for a JS stack. Which language stack is used is unknown here.
- Fixed standard slots vs free windows: with fixed slots, "overlap" reduces to equality of slot id, so a UNIQUE or partial-unique constraint works in both SQLite and PostgreSQL. INFERENCE only, no source retrieved. Worth a source.

## What I looked for and could not find
- Practitioner reports (blogs, forums) on stored vs derived seat placement. The one search returned only Microsoft Dynamics booking-vs-assignment docs, which are tangential (derive-once, not derive-on-read).
- A source naming "fixed slots vs freely overlapping windows" as a known modelling decision.
- Deterministic concurrency-test techniques for SQLite or PostgreSQL (two connections, interleaved steps). Not searched, budget.
- Row-lock ordering (SELECT ... FOR UPDATE in fixed order) docs for PostgreSQL. Not fetched, so the deadlock-avoidance claim is unsourced.
