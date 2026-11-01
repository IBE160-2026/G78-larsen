---
title: "Backcasting from 15 December 2026"
created: 2026-11-01
status: decided by Lisa on 2026-11-01 (PRD §8.2, §12 Q6 and Q17)
inputs: prd.md §8.2, §10.1, §10.3, §12 Q6 and Q17; brainstorm-intent.md; sensorveiledning-kravsporing.md
---

# Backcasting from 15 December 2026

The brainstorm of 2026-10-27 proposed a build order but never tested it backwards. This document does that.

**Decided by Lisa on 2026-11-01:** feature cutoff Friday 11 December, freeze 12–15 December, and building may run to 4 December. The tables below show the plan with those dates. The PRD (§8.2, §12 Q17) and its addendum I carry them.

## The finished state, Tuesday 15 December

- A fresh clone starts from the README alone, and one command runs all tests, which pass (SM-4, NFR-1, NFR-6).
- The Core is done: every Core page is final and passes FR-22 and FR-23, and SM-1 to SM-3 pass.
- DR-1 to DR-5 are complete. What was not built is listed as not delivered (DR-2).
- Everything beyond the Core is whatever the steps below leave room for.

## Working backwards

Weekdays checked. Dates marked "assumption" are not confirmed.

| Date | What must be true | What that needs before it |
|---|---|---|
| Tue 15 Dec | Delivered. The delivery time on the day is not in the repo, so plan to finish on the evening of 14 Dec. | A passed clean-clone check |
| Mon 14 Dec | Clean-clone check done: every README command run on a fresh clone. This is also the spare day. | README final on 13 Dec |
| Sat 12 – Sun 13 Dec | **Freeze work:** DR-1 compiled from the session logs, DR-3 asset register, DR-2 list of what is not delivered, NFR-8 dependency audit, secrets scan of the git history (DR-5), final full test run with 100 race repetitions (FR-11) | `main` green and no feature code since 11 Dec |
| Fri 11 Dec | **Feature cutoff:** the last pull request is merged, `main` is green | Started stories are finished |
| Wed 9 – Fri 11 Dec | Buffer after the 8 Dec exam. No committed stories. Only if the Core is stable, one small If-time item (HTTPS) | Core done on 1 Dec |
| Tue 8 Dec | Exam. 5–7 Dec is exam reading with no building | |
| Fri 4 Dec | Last building day. The Core must be done; spare days 2–4 Dec go to If-time 1 and 2 only if the Core is done earlier | Core done by 1 Dec |
| Tue 1 Dec | **Core done (target)** | Backend Core complete by about 24 Nov, leaving 25 Nov – 1 Dec for the frontend pages, final copy, images and accessibility |
| Tue 17 Nov | Window B starts. Skeleton running; UX documents ready before the first frontend story | Skeleton merged by 8 Nov; `bmad-ux` run on 17–19 Nov at the latest |
| Sun 8 Nov | Walking skeleton merged: one Guest books Seats through the API, the data store refuses over-capacity writes, the parallel test harness runs against the real database | Architecture and the first stories, written by 5 Nov |
| Mon 16 Nov | Exam. 9–15 Nov is exam reading (assumption) | |
| Mon 2 – Thu 5 Nov | Architecture (Q3, Q4, Q5, Q14), the planning depth (Q17), the first stories, readiness check | Q4 and Q17 decided on 2 Nov |
| **Sun 1 Nov (today)** | **The first move:** decide Q17 (planning depth) and Q4 (database engine) | |

## What the backcast shows

### 1. Planning is behind the plan, so window A is short
The plan was PRD and architecture in days 1–8 (to about 3 Nov). The PRD took until 1 Nov, and architecture, UX, epics and sprint planning have not started. First code is realistic on 5–6 Nov, which leaves **3–4 coding days** before exam reading. The skeleton by 8 Nov holds only if three things are true:

- the architecture covers the Core decisions only (PRD §10.3);
- UX is not a gate for the backend skeleton (kravsporing: UX "before frontend", not before backend);
- only the skeleton stories are written first, and the remaining Core stories are written at the start of window B.

### 2. Tests in every story: build the heavy test harness first
NFR-6 is confirmed (2026-10-30), and the backcast agrees with it: a freeze that must also write tests would not fit. Two consequences:

- The parallel capacity test against the real database (FR-11, no mocks) is the expensive test. Its harness goes into the **skeleton story**, not a later one. This ties to Q4: the engine must support it from day one.
- The freeze is for verification and documentation only. No feature code, and no test-writing that a story should have carried.

### 3. The freeze was too long (decided 2026-11-01)
With tests in every story, the freeze work is about **2.5–3 working days** (my estimate: README and clean-clone check, DR-1, DR-3, DR-2, audit, secrets scan, final run). Seven days was more than twice that.

Shortening the freeze only helps if 9–11 Dec is used. After an exam on 8 Dec, and with frontend and testing named as the likeliest overruns, those days are more likely buffer than building. That is fine, as long as no story is *committed* to them.

**Decided:** feature cutoff Fri 11 Dec; freeze Sat 12 – Tue 15 Dec (4 days: about 3 of work and 1 spare). Rule for the freeze: only documentation and fixes for failing tests are accepted.

### 4. Scope: the likely outcome is the Core plus HTTPS
Window B is now 18 days (17 Nov – 4 Dec), since building may run to 4 Dec. With about 12 Core stories (my estimate; epics are not written yet) and 2–3 done in window A, about 9–10 remain. The Core fills most of window B. Then:

- **If-time 1 (HTTPS)** is small and fits 2–4 Dec or the buffer of 9–11 Dec.
- **If-time 2 (Change Seats or take a Voucher, FR-25 to FR-28, SC3)** is about 4–5 stories. It fits only if the Core is done by about 27 Nov. If it starts later, it eats the buffer, which should stay free for overruns.
- **If-time 3 to 6** are not reachable.

Two consequences for decisions:

- **Q6 can close for now.** The order of items 3 to 6 does not matter before sprint planning. Decide it when If-time 2 is merged.
- **SC3 is inside the teacher's suggested minimum (SC1 to SC4 with an Administrator view), and the Core is narrower than that** (PRD §10.1 note). If If-time 2 is not reached, the delivery is below the teacher's minimum on SC3 and SC2/SC4 as well. This is allowed, but DR-2 must say so, and Lisa should choose it knowingly.

## Checkpoints (go / no-go)

Each checkpoint re-runs this backcast with real velocity. The token budget per story (DR-1, Q17) gives the data.

| Date | Test | If it fails |
|---|---|---|
| Sun 8 Nov | Skeleton merged and the race test runs | Core stories move into window B. Drop If-time 2 from the plan |
| Tue 24 Nov | Backend Core complete | No If-time item except HTTPS |
| Fri 27 Nov | Core done, so that If-time 2 can fit | Plan only HTTPS after the Core |
| Fri 4 Dec | Core done, the latest | 9–11 Dec goes to the Core. HTTPS is dropped. Report SC9 without HTTPS |
| Fri 11 Dec | Cutoff: `main` green | Whatever is not merged is listed as not delivered |

## Assumptions to confirm

1. 5–7 Dec is full exam reading (building may run to 4 Dec, Lisa 2026-11-01), and 9–15 Nov likewise. If 9–15 Nov reading is shorter, window A grows.
2. About 12 Core stories. Replace with the real count when the epics exist.
3. Hours per day are unknown. The backcast sets milestones, not hours.
4. The time of delivery on 15 Dec is not in the repo.
5. The 2.5–3 days of freeze work is my estimate.

## What the Administrator has in Core plus HTTPS

Read-only, and nothing else (PRD §4.4, §7, §9):

- sign-in and sign-out, with hashed passwords, sign-in throttling and role checks (FR-15, FR-19, FR-20);
- the booking list, grouped by date and Window, with totals (FR-16);
- the Outbox, with every email sent (FR-17).

There are no editing screens. Windows, Capacity, prices and the Settings come from seed data. The screens for them are If-time 7 (FR-38 to FR-42, the last part of v1), so they are not reachable. The Administrator also cannot cancel or change a Booking: Administrator cancellation of a single Booking is not in the sources (PRD §12 Q7).

The teacher's suggested minimum asked for "an Administrator view" with SC1 to SC4. The booking list meets that part.

## Decisions

Decided by Lisa on 2026-11-01:
1. **Freeze:** cutoff 11 Dec, freeze 12–15 Dec. In PRD §8.2 and Q17.
2. **Building** may run to 4 Dec.
3. **Scope:** the Core plus HTTPS is accepted as the likely v1, because the Administrator sign-in, booking list and Outbox are in the Core. SC2 to SC4 are reported as not delivered (DR-2) if If-time 2 is not reached. The order of items 3 to 6 is decided when If-time 2 is merged. PRD Q6 is closed.
