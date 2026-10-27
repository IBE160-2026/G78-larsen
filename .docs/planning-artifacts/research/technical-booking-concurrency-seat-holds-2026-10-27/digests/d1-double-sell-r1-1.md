# D1 double-sell + perf numbers, round 1, assistant 1
Budget used: 3 searches, 2 fetches (1 failed). Evidence thin on numbers. Access date for all: 2026-10-27.

| # | claim | source | publisher | pub_date | confidence | class |
|---|---|---|---|---|---|---|
| 1 | Under Read Committed, an UPDATE that hits a row another transaction just changed waits, then re-evaluates WHERE against the new row version. Basis for atomic conditional UPDATE (`SET booked=booked+n WHERE booked+n<=capacity`); loser affects 0 rows. Docs show simple per-row cases only, not the booking pattern. | https://www.postgresql.org/docs/current/transaction-iso.html | PostgreSQL Global Development Group | current docs (v18) | high | pattern |
| 2 | Repeatable Read / Serializable fail with "could not serialize access due to concurrent update" or SQLSTATE 40001; app must retry the whole transaction. Predicate locks never block, so cannot deadlock. Docs advise short transactions, limited connections, no explicit SELECT FOR UPDATE where Serializable already protects. | same | PostgreSQL | current | high | pattern |
| 3 | SELECT FOR UPDATE locks returned rows; concurrent lockers wait then see the updated row; locks last to end of transaction. Row locks can deadlock when two transactions touch the same rows in different order. | https://www.postgresql.org/docs/current/explicit-locking.html | PostgreSQL | current (v18) | high (search snippet only, page not fetched) | pattern |
| 4 | Older docs (v11): SELECT FOR UPDATE marks rows as locked, which causes disk writes. | https://www.postgresql.org/docs/11/explicit-locking.html | PostgreSQL | v11 docs | med (snippet, old version) | performance-claim |
| 5 | pgbench scale 1 (all clients contend on one branch row): ~245-248 TPS, several times higher at larger scales; attributed to near-linear serialization on the single row. Single-hardware anecdote. | https://www.postgresql.org/message-id/CAHyXU0xwHARrTWmV7OQ1tYvm12eidq9mg3Uo1Hr%3DwX8wwj6-Bw%40mail.gmail.com | pgsql-hackers | unknown, probably old | low | performance-number |
| 6 | When clients far outnumber contended rows, waiters wake together after each commit, one wins, TPS drops sharply. 7.2-era thread, may be improved since. | https://www.postgrespro.com/list/id/3C232938.53486E4B@tm.ee | pgsql-hackers mirror | ~2001 | low | failure-claim |
| 7 | Cybertec hot-row benchmark: ~75% of wait time on transaction-ID locks, ~20% on tuple locks, CPU mostly idle. Snippet only. | https://www.cybertec-postgresql.com/en/wp-json/wp/v2/posts/130220 | Cybertec | unknown | low | performance-number |
| 8 | 2026 PGConf.de talk: Repeatable Read poorly suited to heavily contended rows because of retries; Read Committed waits then applies the update. From a search summary; PDF not parsed. | https://www.postgresql.eu/events/pgconfde2026/sessions/session/7418/slides/846/fixing-locks.pdf | PGConf.de 2026 | 2026 | low | pattern |
| 9 | Blog: per-user counter hit contention at tens of jobs/s; a separate counters table later became a bottleneck; claims 25,000 durable updates/s without contention on Aurora PG 9.6. Old, vendor-specific, single source. | https://medium.com/@timanovsky/ultra-fast-asynchronous-counters-in-postgres-44c5477303c3 | Medium (individual author) | unknown | low | performance-number |
| 10 | A long-held row lock (e.g. a transaction waiting on app logic or a payment call) makes later writers to that row queue behind it. Two secondary sources agree (Netdata guides and one other). | https://www.netdata.cloud/guides/postgres/postgres-row-level-lock-contention/ | Netdata | unknown | low-med | failure-claim |

## Assistant's implications (reasoning, not evidence)
- Single-statement atomic conditional UPDATE under Read Committed resolves conflict by row waiting; no app retry needed.
- With Serializable / Repeatable Read the PRD must require retry on 40001 and 40P01 (deadlock).
- Keep the transaction short; do not hold the row lock across the simulated payment call.
- No defensible numeric TPS/latency requirement could be sourced. Any figure should be a load-test acceptance target on the team's own hardware, labelled unverified until measured.

## Leads
- Cybertec hot-row post (fetch actual blog URL for method/numbers).
- pgsql-hackers pgbench scale-1 thread (date, hardware).
- PGConf.de 2026 "fixing locks" slides (saved PDF at tool-results/webfetch-1793109947837-4oxqfh.pdf, untrusted).
- PostgreSQL advisory locks and SKIP LOCKED docs.
- SQLite (single-writer, WAL, busy timeout) and MySQL InnoDB locking docs.

## Not found
- Any published single-row updates/s figure from a production engineering blog or paper.
- Measured comparisons for optimistic locking/version columns, per-seat rows vs counters, advisory locks, Redis/distributed locks (not searched within budget).
- Whether the old hot-row pain points (2001 thread, Aurora 9.6 post) have since been fixed.
- Any SQLite or MySQL source.
