---
review: adversarial
target: ../ARCHITECTURE-SPINE.md (uncommitted working-tree diff of 2026-11-19 that applies the fixes from validate-caddy-next-2026-11-19.md; touches Paradigm diagram, AD-10, AD-14, AD-17, AD-18, AD-19, AD-22, AD-27, Conventions, Stack, Structural Seed, Map, Deferred)
date: '2026-11-20'
lens: 'Two units one level down that each obey every AD to the letter yet still build incompatibly; plus: did each validate fix close its finding, and did a fix open a new contradiction'
inputs:
  - git diff of ARCHITECTURE-SPINE.md (working tree vs HEAD 2dc1a69)
  - ARCHITECTURE-SPINE.md (working copy, full read)
  - .memlog.md (last 6 entries, incl. Lisa's three decisions: CSP if time, focus to the fragment target, one noscript line)
  - reviews/validate-caddy-next-2026-11-19.md, review-rubric-caddy-next-2026-11-19.md, review-reconcile-prd-caddy-next-2026-11-19.md
  - reviews/review-adversarial-caddy-next-2026-11-19.md (style)
  - ux-designs/ux-booking-platform-2026-11-05/EXPERIENCE.md (focus, titles, "not available")
  - brownfield: docker-compose.yml, README.md, pyproject.toml, .python-version, src/booking_platform/__init__.py, app.py, db.py, tests/conftest.py
---

# Adversarial review: the validate fixes (Caddy + Next.js amendment)

## Verdict

**Most fixes landed and closed their findings. Not quite ready for the skeleton story.** H1 (switch file on a fresh clone) and H2 (headers on Caddy's redirect) are closed. `BP_ROOT=/app` fits with the `/app/config` mount. The `redirect_slashes` rule fits the slice's routes, since none ends in a slash. The compose-owned mode removes the placeholder problem.

There are two high findings, and both come from the fix text itself:

- The new focus rule says "not on the first document load". The new test and Lisa's decision both require focus on `/#before-you-come` when it is opened directly, which is a first document load.
- The proxy healthcheck runs "on its own site address". From FR-24 that address is the scheme-less `localhost:8443`. The healthcheck then fails, unless the FR-24 story changes a fourth compose line, which the "three lines" rule does not allow.

The medium findings sit on the seam the skeleton story writes: compose, the healthchecks, the backend Dockerfile, and the e2e fixture's compose calls. Each one is a value with two owners or no owner:

- the Caddy container's port variables;
- the e2e "database";
- the database address defaults;
- the e2e compose command prefix;
- the startup effects of a switch restart;
- the Dockerfile's copy list;
- `pg_isready` during the image's init;
- `server-api`'s catch-all.

None of the fixes below needs a new product decision.

| Severity | Count |
| --- | --- |
| Critical | 0 |
| High | 2 |
| Medium | 9 |
| Low | 8 |
| **Total** | **19** |

## Method

| # | Unit | Main ADs |
| --- | --- | --- |
| U1 | Core skeleton: `docker-compose.yml`, `Caddyfile`, backend `Dockerfile`, `.dockerignore`, reshaped slice fixture | AD-14, AD-15, AD-21, AD-22, AD-27 |
| U2 | Next.js shell: root layout (focus component, `<noscript>`), `lib/server-api.js`, error pages, frontend Dockerfile, `package.json` scripts | AD-17, Conventions |
| U3 | Landing page with "Before you come" and Venue facts | AD-16, AD-17 |
| U4 | API-layer harness (`tests/conftest.py`, session fixture) | Conventions Tests, AD-14, AD-22 |
| U5 | e2e fixture and tests (`tests/e2e/`, `test_fr21_privacy.py`) | AD-14, AD-19, AD-27, Conventions Tests |
| U6 | FR-24 story (three compose lines, HSTS, TLS part of the fixture, HT-1 to HT-4) | AD-22, AD-27 |
| U7 | Seed and startup (seed, `ensure_generated`, purges) and `create-admin` | AD-4, AD-18 |

---

## High

### 1. The focus rule skips the first document load, but the new test and Lisa's decision need focus on a direct `/#before-you-come`

- **Severity:** High (contradicts a product decision; the e2e test cannot pass against the component as specified)
- **Units:** U2 (root-layout focus component) vs U5 (Landing e2e test)
- **How they diverge:**
  - U2 follows AD-17 literally. It moves focus only "after each client navigation (not on the first document load)", so it does nothing when the email's or the browser bar's `/#before-you-come` loads the page.
  - The browser itself scrolls to the fragment on a first load but does not move focus. `document.activeElement` stays `body`.
  - U5 follows Conventions Tests: "`/#before-you-come`, opened directly and through the Confirmation link, shows and focuses the section". The direct case fails.
  - The memlog records Lisa's decision as "e2e test (direct link and Confirmation link both show and focus the section)", so the AD text is the side that is wrong.
  - The same AD sentence says "`/manage#t=…` … falls back to the `h1` after the fragment is removed", but `/manage#t=` is always a first document load (opened from an email), where the rule says nothing happens. The Accessibility convention ("then focus moves to the page heading, or to the fragment's target") has no first-load exception at all. That makes three readings of one behaviour.
  - A literal `document.querySelector(location.hash)` throws on `#t=<token>` (`=` is not valid in a selector), inside an effect in the root layout.
- **Evidence:** AD-17: "moves focus after each client navigation (not on the first document load): to the element the URL fragment names when it exists (`tabindex="-1"`, so `/#before-you-come` shows and focuses that section, FR-1.4, FR-8)". Conventions Tests: "opened directly and through the Confirmation link, shows and focuses the section."
- **Fix:** In AD-17 Titles and focus, replace the focus sentence with: "On the first document load, focus moves only when the URL fragment names an existing element, and then to that element. After each client navigation, focus moves to that element if it exists, otherwise to the page's `h1`. The target is found with `document.getElementById(decodeURIComponent(location.hash.slice(1)))`, never with a selector. `/manage#t=…` names no element, so the first load leaves focus alone, and the navigation to `/manage/[reference]` focuses its `h1`." Give the Accessibility convention the same wording. This only restates Lisa's decision, so no new decision is needed.

### 2. The proxy healthcheck "on its own site address" breaks at the FR-24 switch, or forces a fourth mode line

- **Severity:** High (the examiner's one command, `up --wait`, fails; the e2e run would catch it, but only by breaking the "three lines" rule)
- **Units:** U1 (skeleton writes the proxy healthcheck) vs U6 (FR-24 changes "those three lines together")
- **How they diverge:**
  - In the Core, U1 writes `wget -q --spider http://localhost:${HTTP_PORT:-8000}/`, or reuses `$SITE_ADDRESS`, as the spine says.
  - U6 changes only the three Modes lines. `SITE_ADDRESS` becomes `localhost:${HTTPS_PORT:-8443}`, with no scheme. A healthcheck built from it sends plain HTTP to the TLS port. Caddy answers `400 Client sent an HTTP request to an HTTPS server`, the proxy never becomes healthy, and `up --wait` exits non-zero.
  - A healthcheck still on `http://localhost:8000/` now gets Caddy's redirect. It passes only if busybox `wget` in `caddy:2.11` follows it and completes TLS against the internal CA.
  - Whichever variant U1 picks, U6 must touch a fourth compose line, which Modes and Build order do not allow.
  - The path is also open. `/` is Landing, which calls `server-api` (Venue facts) and so the backend. The proxy's health then depends on the frontend and the backend. The healthcheck generates API reads every interval, which may run `ensure_generated()` against "Healthcheck routes never write, run no catch-up". HT-2's "the fixture stops `frontend`" also turns the proxy unhealthy.
- **Evidence:** AD-27 Startup: "proxy `wget` on its own site address". Modes: "the FR-24 story changes those three lines together to `localhost:${HTTPS_PORT:-8443}`, …".
- **Fix:** In AD-27 Startup, replace the proxy part with: "proxy: `wget -q -O /dev/null http://127.0.0.1:2019/config/` (Caddy's admin endpoint, on by default and reachable only inside the container; the Caddyfile never sets `admin off`). The proxy healthcheck does not depend on the mode, and FR-24 does not touch it." Routing through Caddy is already proven by `up --wait` on the backend and the frontend plus the e2e routing test.

---

## Medium

### 3. Caddy's own placeholders (`{$HTTP_PORT}`, `{$HSTS_MAX_AGE}`) read the proxy container's environment, which the env file never reaches

- **Units:** U1 (proxy `environment:` holds only `SITE_ADDRESS`, as Modes lists) vs U5/U6 (e2e env file with `HTTP_PORT=18000`, `HTTPS_PORT=18443`)
- **How they diverge:** `--env-file` feeds only compose interpolation. Inside the proxy container, `{$HTTP_PORT:8000}` stays `8000`. Before FR-24 this does not matter, because the site address carries the port. From FR-24, the redirect server listens on container port 8000 while compose publishes `18000:18000`. HT-1 (`http://localhost:18000/x?y`) then gets a refused connection. The examiner's stack works only because its ports are the defaults.
- **Evidence:** Ports: "`HTTP_PORT` … come from the environment with those defaults, in both the Caddyfile and compose". Modes: "the proxy gets `SITE_ADDRESS: …`" and "An env file (e2e) therefore sets only ports, the database and `SWITCHES_DIR`."
- **Fix:** In AD-27 Modes, add: "The proxy's `environment:` also passes `HTTP_PORT: ${HTTP_PORT:-8000}` (and `HSTS_MAX_AGE` when set). These lines do not change with the mode."

### 4. The e2e env file "sets its own … database", but no variable names the database

- **Units:** U5 (e2e env file) vs U1 (compose hard-codes `POSTGRES_DB: booking` and `BP_DATABASE_URL: …@db:5432/booking`)
- **How they diverge:** U5 writes, for example, `POSTGRES_DB=booking_e2e` or `BP_DATABASE_URL=…/booking_e2e`. Neither reaches a container, because compose interpolates no such variable, and if one did, the db and the backend would disagree. The e2e fixture "moves the clock and seeds rows through `DB_PORT`" against a database name it has to guess.
- **Evidence:** AD-14 and Modes: env file "sets only ports, the database and `SWITCHES_DIR`". AD-27 Tests: "sets its own `HTTP_PORT`, `HTTPS_PORT`, `DB_PORT`, database and `SWITCHES_DIR`". AD-22: "compose sets `…@db:5432/booking`".
- **Fix:** Remove "database" from both sentences, and add: "The e2e project has its own db container and volume, so its database is `booking` too; the fixture connects to `127.0.0.1:<DB_PORT>/booking`."

### 5. A switch change restarts the backend, and startup re-runs the seed, Window generation and purges inside an e2e test

- **Units:** U5 (fixture: "rewriting the file there and running `… restart backend`"; "moves the clock and seeds rows through `DB_PORT`") vs U7 (AD-18: "startup applies `seeds/` in every environment"; sample Bookings through `services.booking.create`; AD-8/AD-28 purges at startup)
- **How they diverge:** An e2e test does the following:
  1. truncates or replaces rows through `DB_PORT` to build its scenario, for example fills a Window;
  2. moves `clock.off`;
  3. switches `payment = "fail"` and restarts the backend.

  At that restart the seed puts back the absent sample Bookings and Saunas, which changes Seats left mid-test. A seed Booking refused by capacity aborts startup, so the backend never becomes healthy and the fixture hangs. A moved clock also purges sessions and grants at startup, which ends the browser's session in the middle of a flow. Each unit is correct on its own.
- **Fix:** In AD-27 Tests, add: "The e2e fixture never deletes seed-owned rows. It adds its own Windows and rows beside the seed's. A test that needs switches sets them before it seeds its own rows and before it moves the clock, and any restart happens only at those points."

### 6. Two defaults own the database address, and neither follows `DB_PORT`

- **Units:** U1 (compose publishes `127.0.0.1:${DB_PORT}`) vs U4 (brownfield `tests/conftest.py`: `BP_TEST_ADMIN_URL` default `postgresql://postgres:booking@localhost:55432/postgres`) vs AD-22 (`BP_DATABASE_URL` default `…@127.0.0.1:55432/booking_dev`) vs brownfield `db.py`/README (`…@localhost:55432/booking`)
- **How they diverge:**
  - A developer sets `DB_PORT=55433` in `.env` because 55432 is taken. The session fixture's `docker compose up -d --wait db` honours it, but neither URL default does, so the tests report "not reachable".
  - `localhost` and `127.0.0.1` are mixed while the db is bound to `127.0.0.1` only. On Windows, `localhost` resolves to `::1` first, which costs a failed connect per new connection. The `pg` fixture opens one per test.
  - AD-22 now says `config.py` is "the only reader" of `BP_TEST_MUTATE` and `BP_TEST_ADMIN_URL`, but only the test harness uses them (`mutate()`, the admin URL). Either the harness imports `booking_platform.config` just to read its own variables, or it keeps reading them and breaks the rule.
- **Fix:**
  - In AD-22, write: "Both defaults use `127.0.0.1`. The harness derives its admin URL from `BP_DATABASE_URL` by swapping the database for `postgres`, so `BP_TEST_ADMIN_URL` is dropped. A different `DB_PORT` needs a matching `BP_DATABASE_URL` (README)."
  - Make the rule "`config.py` is the only reader of the `BP_*` variables the application uses; `tests/` reads `BP_TEST_MUTATE` itself".

### 7. The frontend healthcheck route is unnamed, and `localhost` on Alpine can miss Next.js bound to `0.0.0.0`

- **Units:** U2 (frontend image: `HOSTNAME=0.0.0.0`, IPv4 only) vs U1 (compose healthcheck: busybox `wget -q --spider` "on a route that calls no API") vs U3 (a later page story that adds Venue facts to that route)
- **How they diverge:**
  - Docker's `/etc/hosts` lists `::1 localhost`. busybox `wget` connects to the first address only, so `http://localhost:3000/…` can be refused while the server is up. The frontend then never becomes healthy, and with it the proxy and `up --wait`.
  - "A route that calls no API" is chosen by U1, say `/terms`. U3 later shows the Cutoff on Terms through `server-api`, and the healthcheck quietly starts calling the backend.
- **Fix:** In AD-27 Startup, write: "frontend: `wget -q --spider http://127.0.0.1:3000/privacy`". Use whichever static route Lisa's page list allows; the e2e layer asserts that this route renders with the backend stopped.

### 8. `server-api` "never throws" swallows Next.js's own control-flow errors

- **Units:** U2 (`lib/server-api.js` wraps `fetch` in a catch-all, per AD-17) vs U2 (frontend image runs `next build` with no backend reachable)
- **How they diverge:** Next.js signals "this route is dynamic" (a `no-store` fetch during prerender), `notFound()` and `redirect()` by throwing. A catch-all turns those signals into "unavailable". Depending on the Next.js version, the build may then prerender Landing statically with the "unavailable" Notice baked into the image, and the examiner never sees the Venue facts. A `notFound()` inside the try block also stops working. This needs one `next build` to confirm.
- **Fix:** In AD-17 Server calls, add: "The catch calls `unstable_rethrow(err)` first. Every page that uses `server-api` is dynamic: it awaits `connection()` before the call. The `next build` route table shows these routes as dynamic (`ƒ`), and the skeleton story checks this."

### 9. The backend Dockerfile's named copy list cannot build the project, and `exec` cannot find `booking-platform`

- **Units:** U1 (Dockerfile "copies named paths, never the whole context"; Seed: "copies `migrations/`, `seeds/`, `content/`, `config/` to `/app`") vs `pyproject.toml` (`readme = "README.md"`, `uv_build`) vs U7 (README: `docker compose exec backend booking-platform create-admin`)
- **How they diverge:**
  - `uv sync --locked` builds the project with `uv_build`, which needs `pyproject.toml`, `uv.lock`, `src/` and the `README.md` that `pyproject.toml` names. Copying only the listed folders fails the build on the missing readme.
  - "Started from the image's virtual environment" can be met with `CMD ["/app/.venv/bin/booking-platform"]` alone. `docker compose exec backend booking-platform …` then fails with "executable file not found".
- **Fix:** In the Structural Seed Dockerfile line, write: "copies `pyproject.toml`, `uv.lock`, `README.md`, `.python-version`, `src/` and the four folders; sets `ENV PATH=/app/.venv/bin:$PATH`, `UV_PYTHON_DOWNLOADS=never` and `BP_ROOT=/app`."

### 10. The e2e fixture's compose calls have no single prefix, so the AD-19 log search can read the wrong project

- **Units:** U5 (fixture runs `up`, `restart`, `stop`/`start` for HT-2, `cp` for the root, and `logs`) vs AD-19 (the e2e runs "search `docker compose logs`")
- **How they diverge:** AD-19 spells the command without `-p booking_e2e`. Run that way, it searches the default project's logs, which hold neither the e2e password nor the e2e Manage token, so the test passes even if a secret leaked. AD-14 spells the restart with `-p` but without `--env-file`. A "wait for health" done with `up --wait` and no env file would recreate the e2e containers on the default ports, where they clash with the examiner's stack.
- **Fix:** In AD-27 Tests, add: "Every compose call in the e2e layer goes through one helper, `docker compose -p booking_e2e --env-file <its file> …`, including `logs`, `restart`, `stop`, `start` and `cp`. Waiting after a restart is `up --wait` through the same helper." In AD-19, write "`docker compose -p booking_e2e logs`".

### 11. `pg_isready` passes during the postgres image's init phase, before TCP is open

- **Units:** U1 (db healthcheck `pg_isready`) vs AD-27 ("the backend migrates only after PostgreSQL is ready")
- **How they diverge:** On a fresh volume, which is the examiner's first run and every e2e run after `down -v`, the `postgres` entrypoint runs a temporary server with TCP off while it creates the `booking` database. A bare `pg_isready` checks the Unix socket and reports ready. The backend then connects to `db:5432`, is refused, and its startup migration fails. Whether this happens depends on the healthcheck interval U1 picks; a short interval, chosen to make `up --wait` fast, makes it likely.
- **Fix:** In AD-27 Startup, write: "db `pg_isready -h 127.0.0.1 -U postgres -d booking`".

---

## Low

### 12. The error pages cannot set their title "through Next.js `metadata`"

- **Units:** U2 (`app/error.js` and `global-error.js` must be client components; a client page that shows the not-found component after an API 404) vs the Accessibility convention ("Every route sets its page title through Next.js `metadata`")
- **Divergence:** `metadata` exports work only in server components. `error.js` and `global-error.js` then have no title, or keep the title of the failed page. A Manage page that shows "This page is not available." keeps the title "Manage booking – Saunalöyly", against EXPERIENCE ("A page's title is its heading followed by ' – Saunalöyly'").
- **Fix:** In AD-17 Error pages, add: "The error components and the shared not-available component set the title with React's `<title>` element, from their heading."

### 13. The header matchers still use `/api/*` after the entry matcher became `path /api /api/*`

- **Units:** U1 (Caddyfile headers) vs AD-10 (bare `/api` returns the JSON 404)
- **Divergence:** `Cache-Control: no-store on /api/*` misses `/api`, and `X-Robots-Tag on /api/manage/*` misses `/api/manage`. The Paradigm and Seed diagrams still label the route `/api/*`.
- **Fix:** Use the named matcher `path /api /api/*` for `Cache-Control`, and `path /api/manage /api/manage/*` for `X-Robots-Tag`.

### 14. The Caddyfile default `{$SITE_ADDRESS:http://localhost:8000}` is a second owner of the mode

- **Units:** U1 (Caddyfile) vs U6 (compose owns the mode)
- **Divergence:** After FR-24, compose says HTTPS but the Caddyfile still defaults to HTTP. A proxy started without the compose line (a second compose file, or `caddy run` on the host) serves plain HTTP with the HSTS line, against "HSTS is never sent over HTTP". `{$HTTP_PORT:8000}` repeats compose's default as well.
- **Fix:** Use `{$SITE_ADDRESS}` with no default, so Caddy refuses to start without it. Compose and Railway always set it.

### 15. A slash variant is a 404 in compose but a redirect in dev, and Starlette's defaults are not the envelope

- **Units:** U2 (`next dev` rewrites) vs AD-10 (slash variant is the JSON 404)
- **Divergence:**
  - Next.js applies its trailing-slash 308 before `rewrites()`. In dev, `/api/x/` redirects to `/api/x` and answers 200, while compose answers the JSON 404. That is the dev/compose drift AD-17 says it prevents.
  - With `redirect_slashes=False`, Starlette's own 404 body is `{"detail":"Not Found"}`, not the envelope. A wrong method gets `405`, which the Conventions' status list does not contain.
- **Fix:**
  - In AD-10, add: "An exception handler turns Starlette's 404 and 405 into `404 not_found` in the envelope."
  - In AD-17 Dev, add `skipTrailingSlashRedirect: true` in development, or record the dev difference as accepted.

### 16. The e2e switch directory can be unreadable to the backend, and then switches are silently off

- **Units:** U5 (`SWITCHES_DIR` = a pytest temp dir, mode `0700` on Linux and macOS) vs AD-14 ("a path that is not a regular file means all switches off")
- **Divergence:** A non-root backend user cannot read the mounted file. If `config` treats that as "missing", the `payment = "fail"` test runs with payments succeeding and fails for a misleading reason. Docker Desktop on Windows hides this.
- **Fix:**
  - In AD-14, add: "A file that exists but cannot be read or parsed stops startup with one line naming it."
  - In the fixture, use `chmod 0755` on the directory and `0644` on the file.

### 17. Windows shells: npm script env prefixes and the `create-admin` prompt

- **Units:** U2 (`package.json` scripts) and U7 (`create-admin`) vs Lisa's Windows machine (`next dev`, README) and AD-19
- **Divergence:**
  - `"dev": "NEXT_TELEMETRY_DISABLED=1 next dev …"` fails under `cmd.exe`, npm's default script shell on Windows.
  - A `cp`-based `predev` content copy fails the same way.
  - Under Git Bash, `docker compose exec` without a TTY breaks a `getpass` prompt. If `create-admin` takes the password as an argument instead, it ends up in shell history, against AD-19.
- **Fix:**
  - In AD-17, add: "`predev`/`prebuild` and the telemetry variable are set by a small Node script, never by shell syntax."
  - In AD-18, add: "`create-admin` prompts for the password (never an argument); the README shows the command for PowerShell."

### 18. Only `booking-platform dev` creates `booking_dev`, but other local commands use the same default

- **Units:** U7 (`uv run booking-platform create-admin` "against `booking_dev`"; plain `uv run booking-platform`) vs AD-22 ("`booking-platform dev` creates `booking_dev` …")
- **Divergence:** A fresh developer who runs `create-admin`, or the brownfield README's `uv run booking-platform`, before `dev` gets "database booking_dev does not exist". The brownfield README and `db.py` still say the default is `booking` on port 8000.
- **Fix:** In AD-22, write: "Every local command creates `booking_dev` when the URL is the default and the database is missing." The skeleton story rewrites the README's "Kom i gang" section.

### 19. "Carries only `Location`" overstates Caddy's redirect

- **Units:** U6 (HT-1) vs AD-27 Headers
- **Divergence:** Caddy's automatic redirect also sends `Server: Caddy` and `Content-Length: 0`, and possibly `Connection: close`. An HT-1 written to the Headers sentence ("carries only `Location`") fails. The test sentence itself ("carries no `Strict-Transport-Security`") is correct.
- **Fix:** In AD-27 Headers, write: "…carries `Location` and none of the site's headers; HSTS is never sent over HTTP."

---

## Did each fix close its finding?

| Validate ID | Closed? | Note |
| --- | --- | --- |
| H1 switch file on a fresh clone | Yes | Directory mount at `/app/config` is consistent with `BP_ROOT=/app` and with the Dockerfile copying `config/`; the mount shadows the image copy, which only Railway uses. The validate's suggested regression test (start from a copy without the file) was not added. See #16 for permissions. |
| H2 headers on the automatic redirect | Yes | HT-1/HT-2 now test the right responses. Wording: #19. |
| M1 mode split, placeholders | Mostly | Mode lives in compose; Railway literal. Caddy's container env: #3. Caddyfile default: #14. |
| M2 Core-era e2e fixture | Yes | `base_url` from the fixture, HTTP before FR-24. |
| M3 e2e switch file | Yes, with new seams | Mechanism exists; command prefix #10; restart side effects #5; permissions #16. |
| M4 bare `/api` | Routing yes | Headers not: #13. |
| M5 `booking_dev` | Partly | Only `dev` creates it: #18; address defaults: #6. |
| M6 db for `uv run pytest` | Yes | Session fixture starts it; port ownership: #6. |
| M7 base path | Yes | `BP_ROOT`; Dockerfile copy list: #9. |
| M8 `.dockerignore` | Yes | |
| M9 slash redirect | Backend yes | Dev and Starlette defaults: #15. |
| M10 README cookie limit | Yes | |
| M11 browser-side FR-21, CSP | Yes | `test_fr21_privacy.py`; CSP deferred as Lisa decided. |
| M12 focus vs fragment | No | First-load contradiction: #1. |
| M13 error pages, throwing fetch | Partly | Catch-all: #8; titles: #12. |
| M14 scaffold assets | Yes | |
| M15 `create-admin` in compose | Yes | PATH: #9; prompt: #17. |
| L8 healthchecks, backend image | Partly | Proxy: #2; frontend: #7; db: #11. |
| reconcile L6 `<noscript>` | Yes | One line in the root layout, tested in e2e. |

## Checked and consistent

- **`redirect_slashes` against the slice.** No slice route (`/health`, `/windows`, `/windows/{id}`, `/holds`, `/bookings`, `/whole-bookings`, `/blocks`, `/blocks/{id}`, `/marks`, `/settings`) ends in a slash, so the rule breaks no kept test once AD-21 adds `/api`.
- **Compose-owned mode vs the e2e env file.** `SITE_ADDRESS`, `BP_HTTPS` and `BP_BASE_URL` are all interpolated from the same port variables, so an env file with ports only keeps them in step (apart from #3).
- **`BP_BASE_URL` before and after FR-24.** AD-8's same-origin check, AD-12 links and the e2e `base_url` all follow `HTTP_PORT` or `HTTPS_PORT`.
- **API layer vs `BP_DATABASE_URL` default.** The brownfield harness passes `BP_DATABASE_URL` explicitly to its uvicorn subprocess, so the new `booking_dev` default does not leak into `booking_test`.
- **Backend healthcheck vs image.** `python:3.12-slim` has `python` and `urllib`. A Debian `localhost` lookup tries both families, and uvicorn listens on `0.0.0.0` (`BP_HOST`).
- **CSP deferral.** It matches Lisa's decision and its revisit point. `test_fr21_privacy.py` covers "no third-party request" on the Core pages and Manage meanwhile; the Private sauna page joins it in §4.9.
- **`<noscript>` and the placeholder rule.** Without JavaScript, a page shows its heading, the neutral placeholder and the one line, which is what Lisa decided.
