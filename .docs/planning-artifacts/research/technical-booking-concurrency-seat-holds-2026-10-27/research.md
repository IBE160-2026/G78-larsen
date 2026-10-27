---
title: 'technical research: booking concurrency, seat holds and seat moves'
type: 'technical'
topic: 'booking concurrency, seat holds and seat moves'
decision: 'Which concurrency, performance and consistency requirements can the PRD realistically state so architecture can choose a design'
source: 'native run'
status: complete
preset: 'quick'
validation: 'normal'
claims_verified: 1
claims_unverified: 4
created: '2026-10-27'
updated: '2026-10-27'
---

# technical research: booking concurrency, seat holds and seat moves

**Decision this research serves:** Which concurrency, performance and consistency requirements can the PRD realistically state so architecture can choose a design.

## Executive summary

**State the consistency requirements as hard, testable guarantees. State performance as a load-test target, not a number.**

- **Consistency is well supported.** PostgreSQL's own documentation backs a single atomic conditional update under Read Committed for "last seat" bookings: the losing request waits, re-checks capacity, and affects zero rows [1]. Serializable isolation is a documented backstop, but it requires the application to retry on SQLSTATE 40001 [1].
- **Moves are safe with consistent lock ordering.** PostgreSQL documents consistent lock ordering as the best defence against deadlocks, and the moving and the whole-sauna booking can both use it [2]. No source in this run applies this to booking systems; that step is inference.
- **Performance numbers could not be sourced.** The only throughput figures are low-confidence anecdotes [6][7]. Do not put TPS or latency figures in the PRD. Put them in a load-test acceptance target to be measured on the team's own hardware.
- **Biggest caveat:** every database finding is PostgreSQL-specific. The chosen database engine is not known to this research, and SQLite and MySQL were not covered.

## D1. No double-sale of the last seat

- **Mechanism.** Under Read Committed, an UPDATE that meets a row just changed by another transaction waits, then re-evaluates its WHERE clause against the new row version [1]. A conditional `UPDATE ... SET booked = booked + n WHERE booked + n <= capacity` therefore lets exactly one of two simultaneous requests win; the other affects 0 rows. The docs show this for simple per-row changes and do not name the booking pattern, so applying it to capacity is inference (confidence: medium).
- **Alternatives.** `SELECT ... FOR UPDATE` holds row locks to end of transaction and can deadlock when rows are touched in different order [2]. Repeatable Read and Serializable fail with 40001 under conflict, and the application must retry the whole transaction [1]. A 2026 conference talk argues Repeatable Read suits heavily contended rows poorly because of those retries [9] (low; slide text not parsed).
- **Do not hold the lock across payment.** A long-held row lock makes later writers queue behind it [2][10] (low-medium; secondary sources). The hold, not a row lock, must carry the guest through payment.
- **Throughput.** Published figures are anecdotes: about 245-248 TPS on a single contended pgbench row (old mailing-list post, hardware unknown) [6], and a hot-row wait profile with idle CPU [7]. Both low confidence, single source each. **No defensible number exists in this evidence.**

## D2. Seat hold for 10 minutes

- **Lazy expiry plus sweeper.** The one design write-up found filters on `expires_at > now()` at read time and adds a background sweeper; lag then only understates availability and does not oversell [5] (low; a secondary design write-up, not production evidence). Its figures (30 s sweeper, 60 s reclaim target) are design choices, not measurements [5].
- **Redis TTL keys** free holds without a cleanup job, but the expiry is not in durable records, so audit and extension are harder [8] (low; search snippet only).
- **Payment after expiry is the weak spot.** The design write-up does not address a payment confirming after the hold expired [5]. Stripe documents that webhooks can arrive more than once and out of order, so a callback handler must be idempotent [4] (high; vendor docs, primary for its own behaviour). That the handler must re-check hold validity in a transaction and refund when the seat was taken is **inference**; no source states it.
- **Expiry accuracy.** No measured drift was found. Using the database's `now()` as the single clock avoids app-server clock skew; this is unverified belief.

## D3. Moving seats without a whole-sauna booking sneaking in

- **Lock order.** PostgreSQL: the best defence against deadlocks is acquiring locks on multiple objects in a consistent order; row locks can also deadlock without explicit locking [2] (high).
- **Aggregate lock.** Advisory locks are application-defined, so every code path must use them; transaction-level ones release at commit or rollback [2] (high). A per-sauna lock is a viable aggregate lock (inference from [2]).
- **Serializable backstop.** The documented write-skew shape (a check over one set, an insert into another) is what Serializable catches with a 40001 [1]. A "sauna holds zero individual seats" check is that kind of predicate. Sequential scans coarsen the tracking and raise false failures, so keep the check indexed and the transaction short [1] (high; the booking application is inference).
- **Exclusion constraints** express "no overlapping ranges for the same resource" [3]; that they cannot express "at most N seats" or "room empty" is unverified belief.
- **Reasoned design (inference, no source):** one transaction locks the affected saunas' capacity rows in ascending id order; both the move and the whole-sauna booking use the same order; Serializable with retry as backstop.

## Cross-dimension insights

The three problems share one answer: **one short transaction, locks in a fixed order, retry on 40001/deadlock, and no lock held across the payment step.** That is why the 10-minute hold must be data (a row with `expires_at`), not a held lock. The same ordering rule covers the move and the whole-sauna booking.

## Contrary evidence

Red team was off for this run. Not assessed.

## Recommendations (for PRD input and the architecture spine)

1. **Require "bookings never exceed capacity under concurrent requests"**, and that the loser gets a clear "no seat free" answer and nothing is held. Verified by parallel automated tests, as the addendum already says. Basis: PostgreSQL docs [1] (high for the mechanism, medium for its application here).
2. **Require that a hold is stored, with an expiry, and ignored once expired even if cleanup has not run.** Basis: single weak source [5] plus reasoning (low).
3. **Require idempotent payment callbacks and a defined outcome when payment arrives after expiry** (no booking, simulated refund, as the addendum already says). Basis: Stripe docs [4] (high for duplicates and ordering); the full flow is inference.
4. **Require that a seat move is atomic and cannot interleave with a whole-sauna booking.** Leave the mechanism to architecture. Basis: PostgreSQL docs [1][2] (high for mechanisms, none for booking-specific proof).
5. **Do not state TPS or latency figures.** If the PRD needs one, phrase it as a load-test target set after measuring, and mark it unverified. Basis: no defensible source.
6. **Require retry handling for serialization failures and deadlocks**, with a bounded retry count and a clean error to the guest if it runs out. Basis: [1][2] (high).

## Open questions

| Question | What would answer it |
|---|---|
| Which database engine? Findings cover PostgreSQL only | Architecture decision; then a short run on SQLite (single writer) or MySQL (InnoDB) |
| Realistic single-row update rate | A measured spike on the team's own setup; a Cybertec post and the pgsql-hackers thread are the leads [6][7] |
| Real-world hold-expiry drift and the payment-after-expiry flow | A ticketing-company retrospective; none found. Stripe Checkout `expires_at` is a lead |
| Is the single-resource aggregate lock enough, or is a queue per sauna needed? | Not found in any source; decide in architecture and prove with the parallel tests |

## Source appendix

| [n] | Supports | Publisher | Pub date | Accessed | Confidence |
|---|---|---|---|---|---|
| [1] | Read Committed re-check, 40001 retry, predicate locks cannot deadlock, write skew | [PostgreSQL docs, transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html) | current (v18) | 2026-10-27 | high (spot-checked by lead) |
| [2] | Row locks, consistent lock order, advisory locks, deadlocks | [PostgreSQL docs, explicit locking](https://www.postgresql.org/docs/current/explicit-locking.html) | current (v18) | 2026-10-27 | high |
| [3] | Exclusion constraints | [PostgreSQL docs, constraints](https://www.postgresql.org/docs/current/ddl-constraints.html) | current | 2026-10-27 | high on definition |
| [4] | Webhook duplicates and ordering | [Stripe docs, webhooks](https://docs.stripe.com/webhooks) | current | 2026-10-27 | high |
| [5] | Lazy expiry plus sweeper design | [techinterview.org write-up](https://www.techinterview.org/post/3233469923/lld-inventory-reservation/) | n/a | 2026-10-27 | low |
| [6] | ~245-248 TPS on one contended row | [pgsql-hackers post](https://www.postgresql.org/message-id/CAHyXU0xwHARrTWmV7OQ1tYvm12eidq9mg3Uo1Hr%3DwX8wwj6-Bw%40mail.gmail.com) | unknown | 2026-10-27 | low |
| [7] | Hot-row wait profile | [Cybertec](https://www.cybertec-postgresql.com/en/wp-json/wp/v2/posts/130220) | unknown | 2026-10-27 | low |
| [8] | Redis TTL holds | [oneuptime.com](https://oneuptime.com/blog/post/2026-03-31-redis-booking-lock-system/markdown) | 2026-03-31 | 2026-10-27 | low |
| [9] | Repeatable Read vs contention | [PGConf.de 2026 slides](https://www.postgresql.eu/events/pgconfde2026/sessions/session/7418/slides/846/fixing-locks.pdf) | 2026 | 2026-10-27 | low |
| [10] | Long-held locks queue writers | [Netdata guide](https://www.netdata.cloud/guides/postgres/postgres-row-level-lock-contention/) | unknown | 2026-10-27 | low-medium |

## Staleness map

PostgreSQL documentation claims [1]-[3] are version-bound (freshness bar: 1 month for version claims); re-check them when the database version is chosen. Patterns [5][8] age on a 2-year bar, so no re-check is due before the end of 2028. Performance anecdotes [6][7] carry unknown dates and should be treated as stale until replaced by a measurement.
