---
title: 'Story 1.2: The platform starts with one command and shows its Terms and Privacy notice'
type: 'feature'
created: '2026-11-20'
status: 'done'
baseline_commit: '7c0f36ead6d13b2f617ec4acb1472f3e758ed2f2'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/planning-artifacts/epics.md'
  - '{project-root}/.docs/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Only the backend and db run today. There is no compose stack, Caddy, frontend, shared stylesheet, components or e2e/a11y harness, and Guests cannot read the Terms or the Privacy notice (FR-5, FR-21).

**Approach:** Build Story 1.2 in `.docs/planning-artifacts/epics.md` (L429–501) exactly as its ACs list. That means the four-service compose stack behind Caddy (AD-27), the backend and frontend images (AD-22, AD-17), the Next.js scaffold with the shared homes (`styles.css`, fonts, `lib/`, `components/`), the root layout with its focus mover and error pages, the Terms and Privacy pages copied from the mockups, the e2e fixture and a11y helper, `ASSETS.md` and the README.

## Boundaries & Constraints

**Always:**
- Copy text verbatim from `mockups/key-terms.html` and `mockups/key-privacy.html`. Each page uses `h1` for its heading and `h2` for its sections, and the rail shows the Wordmark only. These pages never call the API.
- Caddy alone sets `Referrer-Policy` and `Cache-Control`. The backend and frontend set no security or cache headers themselves.
- Only `frontend/app/styles.css` styles the site: no `style` props, `<style>`, CSS Modules, `next/font` or `next/image`. Corners are square, there are no shadows, and the site is light mode only.
- Every keyboard step in an e2e test goes through `a11y.press` / `a11y.tab_to`. E2e tests use `base_url` and never a literal URL.
- The existing API tests and the root `tests/conftest.py` keep working unchanged in meaning.

**Never:**
- Build the Landing content, seed, `content/*.json` or the Notice variants beyond "please try again" (those belong to Story 1.3 and later). Never add HTTPS (Story 3.1).
- Add `app/api/`, `route.js`, Server Actions, `middleware.js`, `proxy.js`, TypeScript, Tailwind, ESLint or a UI library.
- Make any third-party request at runtime, including fonts and analytics.
- Use `uv run` inside the backend image, or set `--workers`.

**Decisions (made in planning):**
- **Fonts:** Finlandica and Source Sans 3 come from `github.com/google/fonts` (OFL) as variable fonts, converted once to `.woff2` with fonttools. The output keeps `tnum` and ö.
- **`next build` dynamic check:** no route uses `server-api.js` yet. The record shows `next build` output with every route static, and the "lists server-api routes as dynamic" check moves to Story 1.3, the first user. The issues.md item stays open for that part only.
- **Branch:** `story/1-2-compose-terms-privacy`.
- **Landing stub (human, 2026-11-20):** until Story 1.3, `/` is a minimal stub with the Wordmark as `h1` and Text links to Terms and Privacy. It makes no API call, and Story 1.3 replaces it.
- **Scope (human, 2026-11-20):** the story stays whole even though the spec is about 2400 tokens.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected |
|---|---|---|
| Stack up | `docker compose up --build --wait` | four services healthy; `http://localhost:8000/privacy` 200 |
| API through Caddy | `GET /api/health` | 200, `Cache-Control: no-store`, `Referrer-Policy: no-referrer` |
| Unknown API path | `/api`, `/api/x`, `/api/x/` | JSON `404 {"detail":{"error":"not_found"}}`, no redirect |
| Unknown page | `/nope` | 404 page "This page is not available." with a link to Landing |
| Backend stopped | `compose stop backend`, `GET /privacy` | page renders |
| No JS | any page | `<noscript>` "This booking page needs JavaScript." |
| Asset missing from register | file in `frontend/public/` without a row in `ASSETS.md` | `test_dr3_assets` fails and names the file |

</frozen-after-approval>

## Code Map

- `docker-compose.yml` -- db service only (healthcheck over TCP, named volume `dbdata`). Add proxy, backend and frontend. Keep the db block and the `docker compose up -d --wait db` workflow that `tests/conftest.py::_compose_db` uses.
- `src/booking_platform/config.py` -- reads `BP_HOST`, `BP_PORT` and `BP_ROOT`, and `paths.CONFIG = ROOT/config`. The image sets `BP_HOST=0.0.0.0`, `BP_PORT=8000` and `BP_ROOT=/app`. No code change needed.
- `src/booking_platform/__init__.py` -- `booking-platform serve` is the entry point, so the image's CMD is `booking-platform serve` (the venv is on `PATH`).
- `src/booking_platform/api/public.py` `/api/health` and `api/errors.py` -- already answer the JSON 404 for `/api` and `/api/x/` (Story 1.1). Do not change them.
- `tests/conftest.py` -- session fixtures `database` and `backend`, and the Windows `taskkill` pattern. The e2e conftest must not depend on these fixtures and must not change them.
- `ASSETS.md` -- the images table exists, and "## Fonts" says "Not added yet". Replace that line with font rows. The images move to `frontend/public/` only in Story 1.3, so this story adds only the fonts there.
- `README.md` (Norwegian) -- update "Kom i gang", "Tester", "Mappestruktur" and the status table.
- `.gitignore` -- already ignores `node_modules/` and `.next/`. Add `frontend/content/`.
- `.docs/planning-artifacts/ux-designs/ux-booking-platform-2026-11-05/DESIGN.md` (front matter L6–136) -- every token for `styles.css`. Mockup shell CSS to reuse: `.vp{grid 320px minmax(0,1fr); max-width 1320px}`, `.stick{sticky; padding 32px 40px}`, `.main{padding 24px 56px 48px}`, `.col{max-width 640px}`.
- Pinned versions (spine): `python:3.12-slim`, `ghcr.io/astral-sh/uv:0.12.24`, `caddy:2.11`, `node:24-alpine`, Next 16.4.6, React 19.3.1, axe-core 4.14.1, pytest-playwright 0.10.0.

## Tasks & Acceptance

**Execution:**
- [x] `Dockerfile`, `.dockerignore` -- root backend image and ignore list as the ACs list -- AD-22, AD-17
- [x] `Caddyfile` -- global options, `{$SITE_ADDRESS}`, `@api` to `{$BACKEND_UPSTREAM:backend:8000}`, the rest to `{$FRONTEND_UPSTREAM:frontend:3000}`, header directives -- AD-27
- [x] `docker-compose.yml` -- proxy, backend, frontend and db with healthchecks, `depends_on: service_healthy`, the Core env, the `${SWITCHES_DIR:-./config}:/app/config:ro` mount and `caddy_data` -- AD-27, AD-14
- [x] `frontend/` scaffold -- `package.json` + lock (Next, React, axe-core), `scripts/run-next.mjs` (sets `NEXT_TELEMETRY_DISABLED=1`, copies `../content` when it exists), `next.config.mjs`, `jsconfig.json`, `Dockerfile` -- AD-17
- [x] `frontend/app/styles.css`, `frontend/public/fonts/*.woff2` -- every token as a custom property, `@font-face`, shell and breakpoint, 3 px focus ring -- UX-DR1/2/3/34/36
- [x] `frontend/lib/api.js`, `frontend/lib/server-api.js` -- as AC4 lists (`ApiError` carries `status`, `code`, `facts`)
- [x] `frontend/components/{GuestShell,Rail,Wordmark,TextLink,Notice,FocusMover}.js` -- shared components; FocusMover is the one client component for focus and the "Error: " title prefix
- [x] `frontend/app/{layout,not-found,error,global-error}.js`, `app/terms/page.js`, `app/privacy/page.js` and `app/page.js` (the Landing stub) -- `lang="en"`, `<noscript>`, and `metadata` titles in the form "<h1> – Saunalöyly" -- UX-DR28/29/33
- [x] `tests/e2e/conftest.py`, `tests/e2e/a11y.py` -- compose helper, temp env file plus switches dir, `base_url`, and the a11y API as the ACs list
- [x] `tests/e2e/test_stack_routing.py`, `tests/e2e/test_fr21_privacy.py`, `tests/e2e/test_fr22_terms_privacy_a11y.py`, `tests/test_dr3_assets.py` -- one test per matrix row and per AC
- [x] `pyproject.toml` -- add `pytest-playwright` to the dev group; `uv lock`
- [x] `ASSETS.md`, `README.md`, `.gitignore` -- font rows, commands and local operations -- DR-2, DR-3

**Acceptance Criteria:**
- Given a fresh clone, when `npm --prefix frontend ci`, `uv run playwright install chromium` and `uv run pytest` run, then every test passes, the old API tests included.
- Given the repo, when grepping `frontend/`, then no `fetch(` appears outside `lib/`, no `style=` or `<style` appears, and no stylesheet other than `app/styles.css` exists.
- Given the story record, then it contains the live output of the healthchecks, `caddy adapt`, `curl -i http://localhost:8000/` and the `next build` route list.

## Implementation Notes

**Live record (2026-11-20, Docker 29.9.3, Compose v5.7.0, Windows 11).** Run against the dev stack after `docker compose up --build --wait` (all four services built and healthy in about 35 s on a warm cache).

Healthchecks (`docker inspect`, status | last exit code | test):

```text
proxy: healthy | 0 | ["CMD","wget","-q","-O","/dev/null","http://127.0.0.1:2019/config/"]
backend: healthy | 0 | ["CMD","python","-c","import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"]
frontend: healthy | 0 | ["CMD","wget","-q","--spider","http://127.0.0.1:3000/privacy"]
db: healthy | 0 | ["CMD","pg_isready","-h","127.0.0.1","-U","postgres","-d","booking"]
```

`docker compose exec proxy caddy adapt --config /etc/caddy/Caddyfile` (valid JSON, no warnings):

```json
{"apps":{"http":{"http_port":8000,"servers":{"srv0":{"listen":[":8000"],"routes":[{"match":[{"host":["localhost"]}],"handle":[{"handler":"subroute","routes":[{"handle":[{"handler":"headers","response":{"set":{"Cache-Control":["no-store"]}}}],"match":[{"path":["/api","/api/*"]}]},{"handle":[{"handler":"headers","response":{"set":{"X-Robots-Tag":["noindex"]}}}],"match":[{"path":["/manage*","/api/manage","/api/manage/*"]}]},{"handle":[{"handler":"headers","response":{"set":{"Referrer-Policy":["no-referrer"]}}}]},{"group":"group2","handle":[{"handler":"subroute","routes":[{"handle":[{"handler":"reverse_proxy","upstreams":[{"dial":"backend:8000"}]}]}]}],"match":[{"path":["/api","/api/*"]}]},{"group":"group2","handle":[{"handler":"subroute","routes":[{"handle":[{"handler":"reverse_proxy","headers":{"response":{"delete":["Cache-Control"]}},"upstreams":[{"dial":"frontend:3000"}]}]}]}]}]}],"terminal":true}],"protocols":["h1","h2"]}}},"pki":{"certificate_authorities":{"local":{"install_trust":false}}}}}
```

`curl -i http://localhost:8000/` (headers):

```text
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Etag: "16u22x8w0h84xu"
Referrer-Policy: no-referrer
Vary: rsc, next-router-state-tree, next-router-prefetch, next-router-segment-prefetch, Accept-Encoding
Via: 1.1 Caddy
X-Nextjs-Cache: HIT
```

`curl -i` on `/api/health`, `/api`, `/api/x` and `/api/x/`: 200 `{"ok":true}`, then three times 404 `{"detail":{"error":"not_found"}}` with no `Location`; every one with `Cache-Control: no-store` and `Referrer-Policy: no-referrer`. `/nope`: 404 with "This page is not available.".

`npm --prefix frontend run build` route list (every route static, as decided; the server-api dynamic check moves to Story 1.3):

```text
Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /privacy
└ ○ /terms

○  (Static)  prerendered as static content
```

`uv run pytest -q`: 184 passed in 135 s (the old API tests, `test_dr3_assets.py` and 38 e2e tests against `booking_e2e`, torn down with `down -v`).

**Choices made while building (not in the ACs):**
- Next.js adds its own `Cache-Control` to pages and assets (`s-maxage=31536000`, `private, no-cache, no-store…`). To keep "Caddy alone sets `Cache-Control`", the frontend's `reverse_proxy` drops it with `header_down -Cache-Control`. Pages then carry only `ETag`. Story 1.3+ pages that must never be cached rely on that (browsers do not heuristically cache without `Last-Modified`/`Expires`); revisit if a page needs an explicit `no-store`.
- HTTPS_PORT is written to the e2e env file but not published, since nothing listens on it before FR-24 ("never add HTTPS").
- The shell puts `main` before the rail in the source (rail last in tab order, EXPERIENCE.md Accessibility Floor) and places them with `grid-column`. The rail is a `<header>` (banner landmark).
- Copy not given verbatim anywhere: the error pages' heading "Something went wrong", the Notice "The page could not be shown, please try again." and the link "Go to the Saunalöyly start page". The not-found title drops the heading's full stop: "This page is not available – Saunalöyly".
- The root layout has only the title template, no default, because a default `metadata` title wins over the error pages' React `<title>`. Landing sets `{absolute: 'Saunalöyly'}`.
- Fonts: full variable fonts (no subsetting), so `tnum` and ö are kept by construction. Source Sans 3 has no `tnum` feature but its default figures are tabular (all digits 472 units wide). OFL texts are in `frontend/font-licenses/` (outside `public/`).
- `seeds/` and `content/` are copied into the images "if present" with a bracket glob (`se[e]ds/`, `conten[t]/`) beside an always-present file, because `COPY` fails on a missing path.
- `tests/e2e/` is a package (`__init__.py`): otherwise its `conftest.py` shadows the root `conftest` that the API tests import by name. Tests reach the compose helper through `stack.compose(...)`.
- External link (datatilsynet.no) is "followed" with `a11y.press` while Playwright answers the request with 204, so the test makes no third-party request.
- `next dev` writes `frontend/AGENTS.md` when it detects an AI agent; it was removed and is not part of the change.

## Spec Change Log

## Review Triage Log

Pass 1 (blind-hunter BH, edge-case-hunter EC, verification-gap VG):

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| VG1/BH2b/EC19 | Nothing checks that non-`/api` responses carry no `Cache-Control` | medium | `test_every_site_response_carries_caddys_headers` asserts `cache-control` only for `/api` paths | patch |
| VG2 | `X-Robots-Tag: noindex` on `/manage*` / `/api/manage*` untested | medium | no hit for `x-robots`/`noindex` in `tests/` | patch |
| BH3 | `Set-Cookie` check in `test_fr21_privacy.py` cannot fail | medium | Playwright's `Response.headers` omits cookie-related headers (docstring, `_generated.py` L22282); needs `all_headers()` | patch |
| VG4 | First-load "focus stays on body" test asserts before hydration | medium | `page.goto` then an immediate `evaluate`; no wait for the effect | patch |
| EC1/BH5b | FocusMover focuses the h1 on first load under Strict Mode in `next dev` | low | App Router dev runs effects twice and keeps refs; `firstLoad` is false on the second run | patch |
| BH4 | FR-21 and axe checks skip `/` and the 404 page | low | `PAGES` lists `/terms` and `/privacy` only; adding two entries is a direct fix | patch |
| BH8/VG-o2 | `lib/api.js` STATUS mirror of `api/errors.py` has no drift check | medium | both tables match today (13 codes); nothing compares them, so a new backend code silently diverges | patch |
| BH7b | `.dockerignore` lets local `__pycache__` into the backend image | low | `COPY src/` copies the tree; one ignore line fixes it | patch |
| BH11 | README env table lacks `HTTP_PORT`, `DB_PORT`, `SWITCHES_DIR`, `API_INTERNAL_URL` | low | compose and `server-api.js` read them; the table lists only `BP_*` | patch |
| VG3/BH4b | Error pages (`error.js`, `global-error.js`, TryAgain) never rendered by a test | medium | no route can fail yet; needs a failing `server-api` page or switch (Story 1.3) | defer |
| EC2 | Hash-only or query-only client navigation moves no focus | medium | effect depends on `pathname` only; no same-page fragment link exists before Story 1.3 Landing | defer |
| BH1 | Caddy sets no `X-Content-Type-Options`, frame guard or CSP | medium | AD-27 enumerates the header set; adding headers is an architecture decision, not this diff's defect | defer |
| VG5 | Landing stub title "Saunalöyly" untested | low | stub is replaced in Story 1.3, whose tests pin Landing's title | defer |
| VG-o1 | "Error: " title prefix has no consumer or test | low | first observable with the first form's Error summary | defer |
| BH2 | Stripping `Cache-Control` loses long caching of hashed `/_next/static` assets | low | local platform; assets revalidate by ETag | reject |
| BH5c/EC3 | MutationObserver watches the whole document | low | one `querySelector` per mutation on small pages; no named harm | reject |
| BH6 | `error.js` ignores `reset`/`error`, no retry button | false | UX-DR29 specifies the Notice and a link, no retry control; Next logs render errors itself | reject |
| BH7 | Backend image runs as root | low | local-only stack; adding a user is more than a direct fix | reject |
| BH8b/EC5/EC6 | `api()` has no timeout; AbortError becomes `unavailable`; 2xx non-JSON returns null | low | no caller exists yet; the backend always answers JSON | reject |
| BH9 | Legal facts (NOK 250, 24 h, address) hard-coded | false | spec requires the mockup text verbatim; `content/` arrives in Story 1.3 | reject |
| BH10 | E2e layer has no opt-out; `pytest.exit` aborts the API tests too | low | the AC makes `uv run pytest` run both; both layers need Docker | reject |
| BH10b | 200 % zoom test does not check clipping | low | 1.4.10 is the accepted gap; axe and tab order pass | reject |
| BH12 | No favicon, `/favicon.ico` 404s | false | "no logo and no favicon" is decided (DESIGN.md, AD-17) | reject |
| BH13 | Patch omits licence texts, spec and lockfiles | false | excluded on purpose when staging the review diff; the files exist | reject |
| EC4 | `TextLink` treats `//host` as a site path | low | no caller passes one | reject |
| EC7 | `API_INTERNAL_URL` with a trailing slash | low | set only by compose, without a slash | reject |
| EC8/EC9 | `run-next.mjs` keeps a stale `frontend/content`; no `error` handler on spawn | low | `content/` does not exist yet; a missing `next` fails loudly anyway | reject |
| EC10 | `@manage path /manage*` also matches `/managers` | false | the matcher is AD-27's verbatim | reject |
| EC11 | `127.0.0.1:PORT` gets an empty 200 | false | AD-27 sets the site address to `localhost`; README says so | reject |
| EC12/EC21 | Shell keeps a 320 px rail below 1024 px | false | UX-DR36: the rail stays to 1024 px; the narrow layout is FR-51, later | reject |
| EC13/EC14 | Port race in `_free_ports`; Ctrl-C during `up` leaves the project | low | rare; the next run reuses the project name and recreates it | reject |
| EC15/EC16/EC17 | Missing axe file message; `tab_order` on body; mockup class parse | low | test-helper ergonomics; mockups are fixed files | reject |
| EC18 | Fragment first-load test does not check the focus ring | low | the ring is checked after every key press; adding it to a programmatic focus is uncertain in Chromium | reject |
| EC20 | Proxy healthcheck probes admin, not the site | false | AD-27 specifies the admin `:2019` check | reject |

## Design Notes

E2e compose helper, so that every call has one shape and nothing touches the dev project:

```python
def compose(*args, check=True):
    return subprocess.run(["docker", "compose", "-p", "booking_e2e", "--env-file", str(ENV_FILE), *args],
                          cwd=ROOT, capture_output=True, text=True, check=check, timeout=900)
```

The e2e fixture picks free host ports for `HTTP_PORT`, `HTTPS_PORT` and `DB_PORT`, so it never collides with the dev stack on 8000/55432.

## Verification

**Commands:**
- `docker compose up --build --wait` -- expected: four services healthy
- `docker compose exec proxy caddy adapt --config /etc/caddy/Caddyfile` -- expected: valid JSON
- `curl -i http://localhost:8000/privacy` and `curl -i http://localhost:8000/api/x/` -- expected: 200 page with `Referrer-Policy`; JSON 404 with `Cache-Control: no-store`
- `npm --prefix frontend run build` -- expected: route list printed
- `uv run pytest -q` -- expected: all pass
