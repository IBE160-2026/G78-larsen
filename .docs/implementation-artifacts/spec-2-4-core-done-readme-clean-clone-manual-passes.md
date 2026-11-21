---
title: 'Story 2.4 (part B): Core done — README, fresh clone, manual passes'
type: 'chore'
created: '2026-11-21'
status: 'in-review'
baseline_commit: '9e1598a9d680c26d818233fb6135d03f4e14bac2'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/planning-artifacts/epics.md'
  - '{project-root}/.docs/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Story 2.4 stays in progress: the README is a story-by-story status log, not the examiner's run guide DR-2 asks for (no security section, no "Not delivered" list, Outbox and sample Bookings hard to find); no fresh clone has been run from it (NFR-1, SM-4); the FR-23 manual passes are not recorded (no `tests/manual/`); and no session log says the Core is done.

**Approach:** Build part B of Story 2.4 (`.docs/planning-artifacts/epics.md` L962–988, L1002–1009, L1023–1026): rewrite the README's run sections in the story's order with the security and "Not delivered" sections, run a fresh clone of `main` from it and fix what fails, add `tests/manual/core-accessibility.md` with Lisa's manual results, and record Core done (or what is missing) in the session log.

## Boundaries & Constraints

**Always:**
- README run sections in this order: tools (uv, Node.js, Docker; Git to clone); `docker compose up --build --wait` → `http://localhost:8000` (`localhost`, not `127.0.0.1`); dev commands (`uv run booking-platform dev`, `npm --prefix frontend run dev`, `http://127.0.0.1:3000`); the two preparation commands and `uv run pytest`; Administrator test login, the 12 seeded sample Bookings (days after first start: +1 14:30, +2 17:30 with 2 left, +3 19:00 full, +5 10:00) and `/admin/bookings`; the Outbox at `/admin/outbox`, which holds every email incl. those Guests never see on a page; `create-admin` (sh and PowerShell), test switches (copy, edit, `docker compose restart backend`), `docker compose logs`, `down`, `down -v`; folders for seeds, tests, `tests/manual/` and `.docs/`.
- Every README command is one actually run in this story (fresh clone run included).
- Security section: Argon2id hashing; server-side role check on every request; no third-party requests (fonts self-hosted, `/docs` off); no request bodies, headers, cookies or secrets in logs (AD-19); HTTPS not yet on (Epic 3), backend/frontend only on the internal network; Manage-link tokens will be stored only as hashes once §4.8 is built. Must not contradict `frontend/app/privacy/page.js`.
- "Not delivered": HTTPS (FR-24), SC2–SC8, FR-25 to FR-51, WCAG 1.4.10 Reflow until FR-51; plus the mobile part of SC10.
- Fresh clone: `git clone` of `origin/main` into a new folder outside the repo, so compose gets its own project, volumes and `booking_dev`; no `config/test-switches.toml`. Checks: stack starts, Landing loads, a Seat booking completes, Administrator signs in, Booking list and Outbox show it, `uv run pytest` passes after the two preparation commands. Every step that fails as written is fixed in README or code here.
- `tests/manual/core-accessibility.md`: one row per check (keyboard only; 200 % zoom 1366×768 and 1920×1080 + `test-results/zoom/` screenshots; Book seats tab order vs `tab_order`; NVDA + Chrome on Book seats, Review, Confirmation) with date, browser (+ screen reader), outcome and covering automated test. A failure is fixed here or recorded in `.logs/lisa-larsen/issues.md` with its WCAG criterion.
- Known from part A, for the zoom row: at 683 px the email on Review wraps mid-word; the rail stays mostly empty (1.4.10 territory).

**Decisions (Lisa, 2026-11-21):**
- README stays in Norwegian (the website stays English; commands, paths and UI names as written).
- Lisa runs the manual passes during implementation: the agent writes the checklist, pauses, then records Lisa's reported results.
- The agent runs the fresh clone on this laptop: `docker compose down` (no `-v`) of the running `g78-larsen` stack first so port 8000 is free; the session log says the agent ran it, with every command and result. Restart the `g78-larsen` stack afterwards.

**Never:** Change product behaviour except to fix a fresh-clone or manual-pass failure. Remove or weaken tests. Add a dependency. Commit secrets or `config/test-switches.toml`. Claim a manual result Lisa did not report.

</frozen-after-approval>

## Code Map

- `README.md` -- rewrite run sections; keep course header, members, "Plan- og prosessdokumentasjon" and "Prosess"; replace the long status table with a short status + "Not delivered". Keep the env-variable tables.
- `frontend/app/privacy/page.js:16-83` -- one cookie (on Book seats), nothing from other companies, hashed passwords, 12-month retention; README must agree (Administrator sign-in reuses `bp_session`).
- `seeds/admin.json`, `seeds/bookings.json`, `src/booking_platform/services/seed.py:11-14` -- login and sample Bookings, created once relative to first start.
- `config/test-switches.example.toml` -- `payment` (ok/fail/hold), `force_conflict`.
- `src/booking_platform/api/errors.py:51-71`, `app.py:89` -- log lines hold codes, method and path only.
- `.docs/sensorveiledning-kravsporing.md:11,14` -- point row 3 to the manual checklist; row 6 status to the new README and the fresh-clone run (drop `.env.example`).
- `.docs/implementation-artifacts/sprint-status.yaml` -- `2-4-…` to done only if Core done is logged.
- `.claude/skills/sesjonslogg` -- the session log carries the fresh-clone record and the Core-done statement.

## Tasks & Acceptance

**Execution:**
- [x] `README.md` -- rewrite per Always; security and "Not delivered" sections -- DR-2, DR-5, FR-21, AD-14/18/27
- [x] fresh clone in a new temp folder -- run the README word for word; fix README/code for each failure; note commands and results for the log -- NFR-1, SM-4
- [ ] `tests/manual/core-accessibility.md` -- checklist with the four rows; HALT for Lisa's results, then fill them in -- FR-23, DR-1
- [x] `.docs/sensorveiledning-kravsporing.md` -- rows 3 and 6 -- DR-1, DR-2
- [ ] session log (sesjonslogg) -- fresh-clone record; "Core is done" or the exact list of what is missing -- §10.1

**Acceptance Criteria:**
- Given the fresh clone, when the README is followed, then stack, Landing, a booking, sign-in, Booking list and Outbox work and `uv run pytest` passes.
- Given `uv run pytest` and `npm --prefix frontend run build` in the repo, then both pass.
- Given the README, then its security section and the privacy notice do not contradict each other, and "Not delivered" is true on merge day.

## Implementation Notes

- Implemented inline (not by a dispatched subagent): the spec pauses for Lisa's manual passes and stops/starts her local stack.
- Fresh clone (2026-11-21, run by the agent): `docker compose down` of `g78-larsen`; `git clone https://github.com/IBE160-2026/G78-larsen.git g78-fresh-clone` in the session scratchpad at `7aa4e14` (= `origin/main`). The folder is named `g78-fresh-clone`, not `G78-larsen`, so compose gets its own project and volumes; otherwise every command as in the README.
  - `docker compose up --build --wait` -- all four healthy in 33 s.
  - Browser script (Playwright, clicks) on `http://localhost:8000`: Landing with "Before you come"; Book seats (2 seats) → Details → Review → Pay → Confirmation `7JVM8BCA`; anonymous `/admin/bookings` → Sign-in; sign-in with the test login; Booking list shows the booking; Outbox shows the email with the reference; tomorrow's sample booking (Ingrid Berg) in the Booking list.
  - `docker compose ps` (4 healthy), `docker compose logs backend proxy` (no test password or guest email in them).
  - Test switches: `cp` (also run in PowerShell), `payment = "fail"`, `docker compose restart backend` → `POST /api/bookings` gives `409 payment_failed`; file removed and backend restarted. `git status` stays clean (file git-ignored).
  - `docker compose exec backend booking-platform create-admin`: without a TTY it answers "cancelled, nothing written"; with `-T` and piped input it prints "created", exit 0. The interactive run and `uv run booking-platform create-admin` (Windows `getpass` reads the console only) need Lisa at a terminal.
  - `docker compose down`; `uv sync`; `docker compose up -d --wait db`; `uv run booking-platform dev` (`/api/health` ok); `npm --prefix frontend ci`; `npm --prefix frontend run dev` (`/`, `/book-seats`, `/api/venue` 200 on port 3000).
  - `uv run playwright install chromium`; `uv run pytest -q` -- 536 passed in 12 min 34 s.
  - `docker compose down -v` (clone project only).
- The README's commands were written before the run and run from it; the clone's code is `origin/main`, and this story changes no code, so the code under test is the one that will be merged. The README file inside the clone was the old one.
- Added after the run and verified separately: `uv run booking-platform dev` against `booking_dev` while the `g78-larsen` stack runs (`/api/health` ok on both; `booking`, `booking_dev` and `booking_test` in one `db`).
- README fixes found by the run: compose (`booking`) and dev (`booking_dev`) do not share a database; `cp` works in PowerShell; test run takes 10–15 minutes; log lines hold method, path, status and error code.
- Repo: `npm --prefix frontend run build` passes.

## Spec Change Log

## Review Triage Log

| # | Source | Finding | Verdict | Route | Evidence / action |
|---|---|---|---|---|---|
| 1 | blind, edge | Fresh clone ran the old README file | low | patch | Commands came from the new README; code identical (docs-only diff). Notes say so; coexistence claim added later was run separately |
| 2 | blind | Spec `in-review` while manual-pass and session-log tasks are open | false | reject | Workflow sets the status; open tasks wait on Lisa (HALT) and the session log, written at session end. Fix would edit the spec |
| 3 | blind, edge | Kravsporing row 6 cites a session log not yet written | low | reject | The log is written at the end of this session (sesjonslogg), before commit |
| 4 | blind | Kravsporing row 3 status still says "Ingen tester" | low | patch | Status column updated with the test count and layers |
| 5 | blind, edge | README says manual results exist; Reflow called the only known gap | medium | patch | Wording now: checklist and results in `tests/manual/`; Reflow the only gap the automated tests know |
| 6 | blind | Checklist rows 2 and 4 omit Administrator pages | false | reject | Rows are as the frozen intent lists them (FR-23 AC) |
| 7 | blind, edge | Row 1 misses the Outbox keyboard test | low | patch | Added `test_fr17_outbox.py::test_the_confirmation_of_a_browser_booking_from_the_bar_with_the_keyboard_alone` |
| 8 | blind, edge | Interactive `create-admin` commands not run as written | medium | patch + human | README says to run it in a real terminal; Lisa runs the three commands (pending, see Implementation Notes) |
| 9 | blind, edge | Dropped `BP_TEST_MUTATE`, FR-10 direct writes, password-not-overwritten, dev sign-in URL, `/api/health` | medium | patch | Re-added each in one line; `serve` left out (not run) |
| 10 | blind | "SC9 levert uten HTTPS" under "Ikke levert" reads as a contradiction | low | patch | Reworded: SC9's HTTPS part is missing |
| 11 | blind | FR-25..51 called wholly unbuilt | medium | patch | FR-35, FR-36, FR-40, FR-41 exist in the store with tests (`services/holds.py`, `services/blocks.py`); README says so |
| 12 | blind | 19:00 row has no seat count | low | patch | "5 (44 av 44 plasser)" (seeds/bookings.json sums to 44) |
| 13 | blind | Security claims `/docs` off and admin redirect cite no test | low | patch | Cite `tests/test_fr20_access.py:84` and `tests/e2e/test_fr15_sign_in.py:101` |
| 14 | edge | README never says how to turn test switches off | medium | patch | Delete the file and restart backend |
| 15 | edge | Re-running `cp` overwrites edited switches | low | patch | Same sentence: `cp` only the first time |
| 16 | edge | `down -v` also removes `booking_dev` | low | patch | One sentence under `down -v` |
| 17 | verification-gap | No gaps (docs-only diff) | -- | -- | -- |

## Verification

**Commands:**
- `uv run pytest -q` -- expected: all pass (fresh clone and repo)
- `npm --prefix frontend run build` -- expected: success

**Manual checks (if no CLI):**
- Every fenced command in the README appears in the fresh-clone record.
