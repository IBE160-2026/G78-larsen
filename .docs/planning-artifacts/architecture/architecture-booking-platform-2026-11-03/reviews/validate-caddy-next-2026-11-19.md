---
report: validate (reviewer gate, standalone)
target: ../ARCHITECTURE-SPINE.md (status final, updated 2026-11-19), Caddy + Next.js amendment (commit d946422)
date: '2026-11-19'
lenses run now: rubric walker, reconcile PRD
lenses run earlier: adversarial, tech-currency (reviews/*-caddy-next-2026-11-19.md; their fixes were applied 2026-11-19)
spine-edited: no
---

# Validate: Caddy + Next.js amendment

## Verdict

**The amendment is coherent and matches the PRD's intent, but it is not ready for the skeleton story.** The two highs break the examiner's first run on a fresh clone (H1) and make HT-2 impossible to pass as written (H2). Both lenses found H1 independently. No critical findings. No leftover references to the old design (Vite, react-router, `tls.py`, `cryptography`, two uvicorn listeners, port 5173) remain. NFR-2 is not contradicted: the PRD asks for one API, not one server.

Lint (`lint_spine.py`): 7 low, all false positives (`{reference}`, `{token}`, `{card_ore}` are path templates and field names).

| Severity | Rubric | Reconcile PRD | Combined (deduplicated) |
| --- | --- | --- | --- |
| Critical | 0 | 0 | 0 |
| High | 2 | 1 | **2** |
| Medium | 9 | 6 | **15** |
| Low | 13 | 13 | **22** |

Overlaps merged: rubric H1 = reconcile H1; rubric H2 = reconcile L7 (raised to high); rubric L7 = reconcile M1 (raised to medium); rubric L5 = reconcile L9; rubric L1 = reconcile L12; rubric L13 = reconcile's EXPERIENCE.md list.

## High

| ID | Where | Finding | Suggested fix |
| --- | --- | --- | --- |
| H1 | AD-14 (line 206), Structural Seed | Compose mounts `config/test-switches.toml`, which is git-ignored and missing on a fresh clone. Docker creates a directory at that path (the backend then fails at startup and a stray folder is left), or refuses to start. Breaks NFR-1, SM-4, the Glossary "Test switch … off by default" and DR-5. | Mount the `./config` **directory** read-only; `BP_TEST_SWITCHES` defaults to `test-switches.toml` inside it; any path that is not a regular file counts as missing. The e2e fixture mounts its own temp dir through one compose variable. README: edit, then `docker compose restart backend`. Test: start from a copy without the file. |
| H2 | AD-27 Headers (line 353), HT-2 (line 358) | The spine says headers reach "Caddy's own redirects", and HT-2 tests them on a redirect. Caddy's automatic HTTP→HTTPS redirect is served by a separate server and carries none of them (verified in the tech-currency review; also correct per RFC 6797 §7.2). | Drop "including Caddy's own redirects". HT-2 tests a Next.js page, an API 404 envelope, a static asset and a Caddy-generated HTTPS error (backend stopped). HT-1 asserts only `Location` on the redirect. |

## Medium

| ID | Source | Where | Finding |
| --- | --- | --- | --- |
| M1 | rubric M1 | AD-27 Modes, AD-22 | Mode split over `SITE_ADDRESS`, `BP_HTTPS`, `BP_BASE_URL`; values use Caddy placeholders that never expand (incl. Railway `{$PORT}`); e2e env file sets neither `SITE_ADDRESS` nor `BP_HTTPS` |
| M2 | rubric M2 | AD-27 Tests, Seed | e2e layer described only in its HTTPS form; Core-era fixture (no root, no TLS) undefined |
| M3 | rubric M3 | AD-14 vs AD-27 Tests | No mechanism mounts the e2e layer's temporary switch file into the container (ties to H1) |
| M4 | rubric M4 | AD-27 Entry, AD-10 | `handle /api/*` does not match a bare `/api` |
| M5 | rubric M5 | Seed dev row, AD-22 | `booking_dev` is never created; default database URL not stated |
| M6 | rubric M6 | Seed commands | `uv run pytest` needs the default project's db on `DB_PORT`, but the README never starts it (SM-4) |
| M7 | rubric M7 | AD-12, AD-15, AD-18 | No single base path for repo-root `migrations/`, `seeds/`, `content/` in dev, API layer and image (half of adversarial #4) |
| M8 | rubric M8 | AD-17 Image | `.dockerignore` entries are names, not `**/` patterns; misses `frontend/node_modules`, `frontend/.next` |
| M9 | rubric M9 | AD-27, AD-10 | Starlette's slash redirect builds `http://localhost:8443/...` behind Caddy |
| M10 | reconcile M1 + rubric L7 | AD-27 README | README bullet dropped the FR-24 localhost Secure-cookie limit the PRD requires the README to state |
| M11 | reconcile M2 | Conventions, test layers | Browser-side FR-21 checks (no cookie on Landing, no third-party request, FR-25 Manage) have no test layer; CSP optional (needs Lisa's decision) |
| M12 | reconcile M3 | AD-17 Titles and focus | Focus-to-`h1` after navigation defeats the direct link to "Before you come" (FR-1.4, FR-8); needs Lisa's decision as an exception to EXPERIENCE |
| M13 | reconcile M4 | AD-17 | Next.js default 404/error pages and a throwing `server-api` fetch break FR-22 and EXPERIENCE "This page is not available." |
| M14 | reconcile M5 | AD-17 / Conventions Styling | `create-next-app` adds favicon and Next/Vercel logos; contradicts DR-3 and EXPERIENCE Open Item 9 (no favicon) |
| M15 | reconcile M6 | AD-18 | `uv run booking-platform create-admin` does not reach the examiner's compose database (FR-15); password change not covered |

## Low (22)

From the rubric: L1 Seed diagram `uv run booking-platform` vs "no `uv run` at runtime" (also reconcile L12, healthchecks never write); L2 diagrams show only the FR-24 end state; L3 host/port and test variables not named in AD-22; L4 DB port "dev and tests only" in one compose file; L5 no named volume for Caddy `/data` (also reconcile L9); L6 `127.0.0.1` not served, cached 308, HTTP/3 on unpublished UDP; L8 backend base image, healthcheck commands, proxy healthcheck; L9 axe-core version not pinned (tech-currency F-12 half applied); L10 capability map rows omit `frontend/` and AD-17; L11 `sessionStorage`/`location` reads during server render (adversarial #23 half applied); L12 local operations (reset, logs, `down` vs `down -v`); L13 EXPERIENCE.md still says SPA and `/confirmation/:reference`.

From reconcile PRD: L1 TLS ends at Caddy, so §4.7 "never travel unencrypted" is literally too strong; README security section; L2 NFR-1 "one more command"/"nothing else" vs two preparation commands and Playwright's Chromium; L3 build-time downloads and dev telemetry; L4 CSS Modules, `styled-jsx`, `style` props not forbidden (FR-22); L5 Next.js route announcer plus focus move may double-announce; L6 no-script behaviour (needs Lisa's decision); L8 logs of Caddy and Next.js containers (FR-21); L10 dependency audit does not cover images (NFR-8); L11 Railway mode untested in v1; L13 capability map rows for FR-18..21 and NFR-1.

## Source updates (spine right, source stale)

PRD and addendum, 9 sentences: §4.7 "never travel unencrypted"; FR-24 "HTTP listener" sentence; NFR-1 ×3 ("no … external services", "installs … nothing else", "One more command runs all tests"); DR-2 first bullet; Glossary Test switch ("only by editing that file" → plus restart); addendum §M.1 "What the examiner installs"; addendum §M.2 Q4 second consequence. Exact quotes and suggested wording: `review-reconcile-prd-caddy-next-2026-11-19.md`, section "PRD sentences to update".

EXPERIENCE.md, 3 places: Confirmation route `/confirmation/:reference`; State Patterns "the SPA"; Emails "base URL … not set yet".

## Recommended next step

An Update run on the spine: fix H1, H2 and M1–M7 (the operational seam) before the skeleton story; M10–M15 in the same run, with Lisa deciding M11 (CSP), M12 (focus exception) and reconcile L6 (no-script). The remaining lows can land in the stories that touch them. Then update the 9 PRD/addendum sentences and EXPERIENCE.md.

## Full reviews

- `review-rubric-caddy-next-2026-11-19.md`
- `review-reconcile-prd-caddy-next-2026-11-19.md`
- earlier: `review-adversarial-caddy-next-2026-11-19.md`, `review-tech-currency-caddy-next-2026-11-19.md`
