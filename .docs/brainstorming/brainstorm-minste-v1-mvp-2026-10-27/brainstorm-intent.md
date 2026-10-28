---
title: "Brainstorm intent: smallest v1 that surely finishes"
source: .memlog.md (same folder)
created: 2026-10-27
status: input for bmad-prd and bmad-architecture
---

# Brainstorm intent: smallest v1 that surely finishes

Marking: **[user]** = decided by Lisa in the session; **[proposal]** = suggested by the coach and not yet confirmed.

## Context and constraints

- One person, 27.10.2026 to 15.12.2026 (about 7 weeks). The teacher rates the schedule risk as high.
- Two other exams compete for time: 16.11.2026 and 08.12.2026 [user].
- Claude tokens and long-running tasks are a real limit [user].
- Frontend/design and extensive testing are the likeliest overruns [user].
- Planning (PRD and architecture) takes 7-8 days of the first 12; coding starts after, as tokens allow [user].

## MVP (the one feature: individual seats)

Book individual seats end to end [user]:

- Time windows, capacity and prices live in the database [user]; seeded by script or config, no admin screens for them [proposal].
- Guest flow: pick date, number of seats, time window, then book and pay [user]. One booking page and one confirmation page; native date picker; time windows as a list with free seats [proposal].
- Guest is a free-text name plus email, no account [user: name kept minimal; proposal: no account].
- Simulated payment is instant [user].
- Confirmation with a booking reference by email [user]; the email is an outbox table, also shown on the confirmation page [proposal].
- The database enforces "never two bookings on the last seat" [user]: booked seats in a window can never exceed capacity. Booking is atomic in one transaction, with a concurrency test (two guests, last seat) [proposal, follows from user decision].
- Admin: password login and a simple booking list [user]; one seeded admin account, hashed password, session cookie, role check tested as guest and unauthenticated [proposal].
- Server-side input validation, hashed passwords and role-based access, each with an automated test [brief, criterion 9; HTTPS see open items].

## If time (order is a proposal)

1. Cancel individual seats up to 12 hours before start, capacity restored, refund simulated and no voucher at first. Then change as cancel plus new booking. Voucher last.
2. Whole-sauna booking, which needs seats placed in specific saunas and the rule that a whole sauna is bookable only when no individual seats are placed in it.
3. "My booking" lookup by reference plus email.
4. 10-minute seat hold [user: postponed].
5. Guest accounts.
6. Step 2 from the brief: gift cards, door codes.

## Build order

1. Planning, days 1-8: PRD derived from the brief and limited to the MVP; architecture limited to decisions that must be consistent (database engine, booking transaction, API shape); epics and stories for the MVP only [proposal].
2. Database engine decision, schema and the capacity invariant [proposal].
3. Walking skeleton: a thin booking from time window to confirmation, so an interruption always leaves a running app [proposal].
4. Complete the MVP, with tests written inside each story as part of "done" [proposal]. Window 17.11 to about 1.12.
5. Admin list and login [user].
6. Freeze 9.12-15.12: tests, README (test users, sample data, frontend start), AI-use documentation, no new features [proposal].

Time windows: 27.10 to about 8.11 (skeleton and core rule), 17.11 to about 1.12 (finish MVP), 9.12 to 15.12 (freeze). Dates for the first two are estimates assuming about a week of exam reading before each exam.

## Mitigations for the named risks

- **Tokens:** small stories with acceptance criteria taken from the brief, a token budget per story logged in the session log as evidence of AI steering (counts 30% of part 1), mechanical tasks at lower effort [user: tokens can be an advantage; rest proposal].
- **Frontend/design:** one stylesheet with a Finnish-inspired palette and typography, mobile first, no design system [proposal].
- **Testing:** depth on concurrency, capacity, validation and criterion 1; breadth only for the rest [proposal].

## Open decisions

- HTTPS (redirect and secure cookie settings): core or if-time. Deferred by the user.
- Database engine: SQLite or PostgreSQL. The concurrency research covers only PostgreSQL, and the reviewer must be able to run the app locally without own infrastructure.
- Whether the schema carries a sauna per seat from day one, so whole-sauna booking later is an extension and not a rewrite. Decide in architecture.
- Backcasting from 15.12 was not run; the build order has not been tested backwards.
