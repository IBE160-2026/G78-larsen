---
title: 'Story 2.4 (part B): Core done — README, fresh clone, manual passes'
type: 'chore'
created: '2026-11-21'
status: 'ready-for-dev'
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
- [ ] `README.md` -- rewrite per Always; security and "Not delivered" sections -- DR-2, DR-5, FR-21, AD-14/18/27
- [ ] fresh clone in a new temp folder -- run the README word for word; fix README/code for each failure; note commands and results for the log -- NFR-1, SM-4
- [ ] `tests/manual/core-accessibility.md` -- checklist with the four rows; HALT for Lisa's results, then fill them in -- FR-23, DR-1
- [ ] `.docs/sensorveiledning-kravsporing.md` -- rows 3 and 6 -- DR-1, DR-2
- [ ] session log (sesjonslogg) -- fresh-clone record; "Core is done" or the exact list of what is missing -- §10.1

**Acceptance Criteria:**
- Given the fresh clone, when the README is followed, then stack, Landing, a booking, sign-in, Booking list and Outbox work and `uv run pytest` passes.
- Given `uv run pytest` and `npm --prefix frontend run build` in the repo, then both pass.
- Given the README, then its security section and the privacy notice do not contradict each other, and "Not delivered" is true on merge day.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run pytest -q` -- expected: all pass (fresh clone and repo)
- `npm --prefix frontend run build` -- expected: success

**Manual checks (if no CLI):**
- Every fenced command in the README appears in the fresh-clone record.
