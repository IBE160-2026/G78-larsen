# D2 hold + D3 move, round 1, assistant 2
5 sources read (PG docs x3, Stripe, one design write-up). Access date for all: 2026-10-27. Snippets were used for orientation only unless marked.

## Q2: temporary hold
| # | claim | source | publisher | pub_date | confidence | class |
|---|---|---|---|---|---|---|
| 1 | Lazy expiry: availability queries filter `expires_at > NOW()`, so an expired hold is ignored at read time before any cleanup runs. | https://www.techinterview.org/post/3233469923/lld-inventory-reservation/ | techinterview.org (design write-up) | n/a | low (secondary, no production evidence) | pattern |
| 2 | Write-up's design: `expires_at` column, 300 s TTL, extensions capped at 30 min total, sweeper every 30 s in batches of max 500; reclaim target 60 s after expiry, alert at 120 s sweeper lag. Design choices, not measurements. | same | techinterview.org | n/a | low | pattern / performance-number (unsourced) |
| 3 | Sweeper lag is conservative: understates availability but does not oversell, provided reads also check `expires_at`. Write-up's reasoning, not independently evidenced. | same | techinterview.org | n/a | low | pattern |
| 4 | The write-up does NOT address a payment confirming after expiry or racing the sweeper. | same | techinterview.org | n/a | high (verified absence in this source) | failure-claim |
| 5 | Redis TTL keys (`SET hold:... EX 300`) free abandoned holds without a cleanup job; trade-off: expiry not in durable records, audit and extension harder. From search-result summaries, not fetched. | https://oneuptime.com/blog/post/2026-03-31-redis-booking-lock-system/markdown | oneuptime.com | 2026-03-31 | low (snippet only) | pattern |
| 6 | Stripe webhooks may deliver the same event more than once; dedupe by recorded event IDs. Sometimes two distinct Event objects exist; then use `data.object` id plus `event.type`. | https://docs.stripe.com/webhooks | Stripe (official docs) | current | high | pattern |
| 7 | Stripe does not guarantee events arrive in generated order. Manual resend up to 15 days (Dashboard) / 30 days (CLI); does not cancel automatic retries. Vendor docs, primary for its own behaviour. Page fetched in Spanish; paraphrased, matches English URL. | https://docs.stripe.com/webhooks | Stripe | current | high | pattern / failure-claim |
| 8 | UNVERIFIED BELIEF (assistant inference): a late or duplicate payment callback must be handled idempotently and re-check hold validity in a transaction; if expired and slot taken, refund. No retrieved source states this flow. | none | n/a | n/a | unverified | pattern |

## Q3: atomic move and whole-room booking
| # | claim | source | publisher | pub_date | confidence | class |
|---|---|---|---|---|---|---|
| 9 | "The best defense against deadlocks is generally to avoid them by being certain that all applications using a database acquire locks on multiple objects in a consistent order." Also take most restrictive mode first; otherwise retry transactions aborted by deadlock. | https://www.postgresql.org/docs/current/explicit-locking.html | PostgreSQL (PG 18.6 docs) | current | high | pattern |
| 10 | Row-level locks can deadlock even without explicit locking; PG aborts one transaction on detection, unpredictable which. Locks wait indefinitely if no deadlock detected; do not hold transactions open across user input. | same | PostgreSQL | current | high | failure-claim |
| 11 | `SELECT ... FOR UPDATE` locks rows against modification by others. Under REPEATABLE READ/SERIALIZABLE it errors if the row changed since transaction start. Row locks block only writers and lockers, not plain reads. | same | PostgreSQL | current | high | pattern |
| 12 | Advisory locks are application-defined, not system-enforced, so every code path must use them. Transaction-level ones auto-release at commit/rollback; session-level survive rollback. `LIMIT` with `pg_advisory_lock` can leave dangling locks. A per-sauna advisory lock is a viable aggregate lock. | same | PostgreSQL | current | high | pattern / failure-claim |
| 13 | SERIALIZABLE (SSI) guarantees a result of some serial order. Docs' example (sum over one class inserted into the other) is the classic write-skew shape: under REPEATABLE READ both commit, under SERIALIZABLE one fails with SQLSTATE 40001. | https://www.postgresql.org/docs/current/transaction-iso.html | PostgreSQL | current | high | pattern / failure-claim |
| 14 | Applications must retry the whole transaction on 40001 and must not rely on results read in an aborted transaction. | same | PostgreSQL | current | high | pattern |
| 15 | SSI predicate locks (SIReadLock) never block, so cannot deadlock. May be coarsened (tuple to page to relation) under memory pressure; a sequential scan takes a relation-level lock. Both raise false-positive failures. Use indexes, short transactions, READ ONLY where possible. Relevant to a "zero individual bookings" check (count/exists over bookings is exactly the tracked predicate). | same | PostgreSQL | current | high | pattern / performance (qualitative) |
| 16 | Overlapping SERIALIZABLE inserts can raise unique violations even after an existence check; docs recommend all such transactions do the existence check first. | same | PostgreSQL | current | high | failure-claim |
| 17 | Before PG 9.1, SERIALIZABLE gave REPEATABLE READ behaviour; pre-9.1 advice that serializable doesn't prevent write skew is stale. | same | PostgreSQL | current | high | version |
| 18 | Exclusion constraints (`EXCLUDE USING gist`) enforce a pairwise rule; can express "no overlapping ranges for the same resource". Page does not state they cannot express "at most N seats" or "room empty"; that limitation is the assistant's inference (unverified belief). | https://www.postgresql.org/docs/current/ddl-constraints.html | PostgreSQL | current | high on definition, low on capacity limitation | pattern |

## Assistant's reasoned implication (inference, no source)
Lock the affected sauna rows (or one capacity row per sauna) in ascending ID order within one transaction. The move (A to B) and the whole-room booking both lock in the same order. SERIALIZABLE as backstop with retry on 40001 and deadlock. Follows from 9, 11, 13-15; no retrieved source states it as a booking recipe.

## Expiry accuracy
No source gave measured drift. Only numbers are the write-up's unsourced design targets (30 s sweeper, 60 s reclaim, 120 s alert). Using DB `now()` as the only clock avoids app-server skew: unverified belief.

## Leads
- Postgres wiki SSI page, Cahill/Ports papers (false-positive rates).
- `SELECT ... FOR UPDATE SKIP LOCKED` for sweeper concurrency.
- Redis docs on key-expiry accuracy (lazy plus active sampling).
- Stripe Checkout Session `expires_at` / `checkout.session.expired` for the payment-after-expiry flow.
- Multigranularity (intent) locking literature (Gray et al.), not retrieved.

## Not found
- Production retrospective from a ticketing company (Ticketmaster, Eventbrite) on hold expiry with measured drift or failure numbers.
- Primary source on the "payment completes after hold expired and seat sold" compensation flow.
- Source on clock-skew incidents in hold systems.
- Source for queue / single-writer-per-resource, or multigranularity locking applied to booking.
- Two-source corroboration of any failure claim beyond the PG docs; claims 1-3 and 5 rest on single weak secondary sources.
