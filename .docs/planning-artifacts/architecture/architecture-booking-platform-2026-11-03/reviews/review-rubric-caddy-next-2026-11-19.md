---
review-of: ARCHITECTURE-SPINE.md (architecture-booking-platform-2026-11-03, status final, updated 2026-11-19)
lens: rubric walker (good-spine checklist), focus on the Caddy + Next.js amendment (commit d946422 and the gate fixes recorded in .memlog.md on 2026-11-19): Design Paradigm, AD-17, AD-27, AD-22, AD-21, AD-14, AD-8, AD-10, AD-12, Conventions, Stack, Structural Seed, capability map, Deferred
reviewed: 2026-11-19
inputs: ARCHITECTURE-SPINE.md; .memlog.md (entries from "Update run started 2026-11-19 (coaching path)" to the end); git show d946422 (spine diff); reviews/review-adversarial-caddy-next-2026-11-19.md; reviews/review-tech-currency-caddy-next-2026-11-19.md; ../technology.md (proxy, frontend, compose rows); PRD FR-24, NFR-1, NFR-2, NFR-6, §8.2, SM-4; EXPERIENCE.md (route table, lines 20, 46, 290, 619); docker-compose.yml; README.md; .gitignore; pyproject.toml; src/booking_platform/__init__.py, app.py; tests/conftest.py
spine-edited: no
---

# Review: Caddy + Next.js amendment against the good-spine rubric

## Verdict

The amendment is coherent and most gate fixes landed: Caddy is the only entry, the browser makes every session call through relative `/api`, the server components carry no cookie, the base URL now follows the origin the browser uses, and the old design (Vite, react-router, `tls.py`, `cryptography`, two uvicorn listeners, port 5173) is gone from the spine text. But the operational envelope is still the weak part. **Two high findings would break a first run.** First, the examiner's compose file mounts a git-ignored switch file that does not exist on a fresh clone. Second, HT-2 expects headers on Caddy's automatic redirect, and that redirect never carries them. Nine medium findings are seams where the skeleton story, the FR-24 story and the e2e fixture will each pick a different value: the mode variables, the Core-era e2e fixture, the switch file in the e2e stack, the bare `/api` route, `booking_dev`, the database the API test layer needs, the base path for repository-root folders, `.dockerignore` patterns, and Starlette's slash redirect behind Caddy. Fix the two highs and the mediums M1 to M7 before the skeleton story is written. The rest can be fixed in the stories that touch them.

| Severity | Count |
| --- | --- |
| Critical | 0 |
| High | 2 |
| Medium | 9 |
| Low | 13 |
| **Total** | **24** |

## Findings at a glance

| ID | Sev | Location | Finding |
| --- | --- | --- | --- |
| H1 | high | AD-14, Structural Seed | Compose mounts `config/test-switches.toml`, which is git-ignored and missing on a fresh clone; Docker then makes a directory there, or refuses to start |
| H2 | high | AD-27 Headers, HT-2 | The spine says the headers reach "Caddy's own redirects", and HT-2 tests them on a redirect, but Caddy's automatic HTTPS redirect carries none of the site's headers |
| M1 | medium | AD-27 Modes, AD-22, AD-27 Tests | The mode is split over `SITE_ADDRESS`, `BP_HTTPS` and `BP_BASE_URL`. Its values are written with Caddy placeholders that never expand, and the e2e env file sets neither `SITE_ADDRESS` nor `BP_HTTPS` |
| M2 | medium | AD-27 Tests, Structural Seed, Conventions Tests | The e2e layer is described only in its HTTPS form. The Core-era fixture (no root, no TLS) is not defined |
| M3 | medium | AD-14 vs AD-27 Tests | No mechanism mounts the e2e layer's temporary switch file into the container, or changes switches during a run |
| M4 | medium | AD-27 Entry, AD-10 | `handle /api/*` does not match a bare `/api`, yet the spine says the bare path goes "through the same route" |
| M5 | medium | Structural Seed dev row, AD-22 | `booking_dev` is never created, and AD-22 does not state the default database URL (the brownfield default is `booking`) |
| M6 | medium | Structural Seed commands, Conventions Tests | `uv run pytest` needs the default project's db on `DB_PORT`, but the README commands never start it (SM-4) |
| M7 | medium | AD-12, AD-15, AD-18, Seed tree | There is no single base path that the backend uses to find repository-root `migrations/`, `seeds/` and `content/` in dev, in the API layer and in the image |
| M8 | medium | AD-17 Image | The `.dockerignore` entries are names, not patterns. A literal `node_modules` misses `frontend/node_modules` and `frontend/.next` |
| M9 | medium | AD-27 Backend side, AD-10 | Starlette's slash redirect builds `http://localhost:8443/...` behind Caddy, so it works in dev and the API layer and breaks only over HTTPS |
| L1 | low | Structural Seed diagram vs AD-22 | `backend: uv run booking-platform` contradicts "no `uv run` at runtime" |
| L2 | low | Design Paradigm diagram, Seed diagram, examiner row, Commands | Each shows only the FR-24 end state (`https :8443`), while the Core floor serves `http://localhost:8000` |
| L3 | low | AD-22 | The host and port variables are not named, and neither are "the test variables already in use" |
| L4 | low | AD-27 Entry | "The database port is published ... for dev and tests only", but one compose file serves both, and dev and the API layer need the port |
| L5 | low | AD-27, Seed tree | No named volume for Caddy's `/data`, so the root changes after `down` and the README's "warns once" breaks |
| L6 | low | AD-27 | Host and redirect edge cases: `127.0.0.1` is not served, the 308 can be cached, and HTTP/3 is advertised on a UDP port that is not published |
| L7 | low | AD-27 README | The README bullet omits the localhost Secure-cookie limit that PRD FR-24 requires the README to state |
| L8 | low | Stack, AD-27 Startup | The backend base image and the uv source are not named, the healthcheck commands are not named, and the proxy has no healthcheck |
| L9 | low | Stack | Tech-currency F-12 is half applied: Playwright is noted, axe-core 4.14.1 is not |
| L10 | low | Capability map | The FR-5–9, FR-15–17 and FR-29–33 rows omit `frontend/` and AD-17 |
| L11 | low | AD-17, AD-9 | Reads of `sessionStorage` and `location` during render in server-rendered client components are not bound (adversarial #23 is only half applied) |
| L12 | low | Structural Seed, Deferred | Local operations are not stated: reset, logs, and what survives `down` and `down -v` |
| L13 | low | EXPERIENCE.md (companion) | It still says "SPA" and `/confirmation/:reference` (lines 46, 290, 619); the memlog question is still open |

## Gate-fix check

Gate fixes in the memlog that landed consistently: the site address without `https_port`, no `tls` line, `skip_install_trust`, ports from `HTTP_PORT`, `HTTPS_PORT` and `DB_PORT` bound to `127.0.0.1`, `depends_on: service_healthy`, `/docs` and `/openapi.json` off, `BP_BASE_URL` always set to the browser's origin with the `https://` start check, `403 cross_origin` in AD-16, `tests/client.py` sending `Origin`, the Next.js prohibitions (`app/api`, `route.js`, Server Actions, `middleware.js`, `proxy.js`), dev-only rewrites that keep `/api`, browser-only listings, `today` in the listings, `metadata` in a server `page.js`, `content/` as JSON copied by `predev`/`prebuild`, the `with-docker` image, no `next/font` or `next/image`, telemetry off, the Strict Mode guard on `/manage`, `X-Forwarded-For` deferred, `/manage/[reference]`, and the two-layer test map. No leftover reference to Vite, react-router, `frontend/src`, `tls.py`, `cryptography`, `certs/`, port 5173 or two listeners remains in the spine.

Gate fixes that are half applied or contradict another part: the tech-currency claim about headers on redirects (H2), `SITE_ADDRESS` holding `{$PORT}` despite tech-currency F-3 (M1), the bare `/api` (M4), the backend half of adversarial #4 (M7), the `.dockerignore` patterns of adversarial #5 (M8), the switch file per layer for e2e (M3), tech-currency F-7 (healthcheck commands, duplicate `docker compose build`; L8, M2), F-12 (L9), F-13 (L6), F-15 (L6) and F-17 (L5).

---

## High

### H1. The examiner's compose stack mounts a file that a fresh clone does not have (AD-14)

- **Evidence.** AD-14: "the switch file's path is `BP_TEST_SWITCHES` (default `config/test-switches.toml`, git-ignored) ... A missing file means all switches off." and "The examiner's compose stack mounts `config/test-switches.toml` read-only, so the examiner uses a switch only by editing that file". The Structural Seed tree: "`config/  # test-switches.example.toml (the real file is git-ignored)`". The README commands are only `docker compose up --build --wait`, with no copy step.
- **Why units diverge.** On a fresh clone the source of that bind mount does not exist. With compose's short syntax, Docker creates a *directory* at `config/test-switches.toml` on the host and mounts it. With the long syntax (`type: bind`), `up` fails with "bind source path does not exist". The skeleton story's author chooses one of these without knowing it matters:
  - If `config` tests the path with `exists()`, it opens a directory and the backend dies at startup. `--wait` then fails on the examiner's first run (NFR-1, SM-4).
  - If `config` uses `is_file()`, the stack starts, but the stray directory stays in the working tree. The examiner can then never create the file that AD-14 tells them to edit.

  The developer machine always has the file, so the gap shows only on the clean-clone check during the freeze.
- **Suggested spine fix.** AD-14, replace the mount sentence with: "The compose `backend` mounts the `config/` directory (which always exists, because it holds the committed example) read-only at `/app/config`, and sets `BP_TEST_SWITCHES=/app/config/test-switches.toml`. A missing file means all switches off, and `config` treats anything that is not a regular file as missing. The README tells the examiner to copy `test-switches.example.toml` to `test-switches.toml` to use a switch, then run `docker compose restart backend`."

### H2. HT-2 checks headers on a response that Caddy builds without them (AD-27 Headers)

- **Evidence.** AD-27 Headers: "`header` directives without `defer` add to every response, including Caddy's own redirects and errors". HT-2: "the headers on a page, a 404 envelope, a static asset and a Caddy redirect". AD-27 Modes: "its automatic HTTPS redirects every request on the global `http_port`". The tech-currency review (verified table, `header` row) found the opposite at the v2.11.9 source: "The automatic HTTP→HTTPS redirect is served by a separate server and carries none of them, which is correct (RFC 6797 §7.2: no HSTS over HTTP)". The gate fix took "headers without defer" from that review but kept "including Caddy's own redirects".
- **Why units diverge.** The FR-24 story writes HT-2 exactly as the spine says, and it is red. There are two ways out, and each breaks another rule:
  - Write an explicit `http://localhost:{$HTTP_PORT}` site with `redir` and the headers. That replaces the automatic redirect AD-27 Modes names, and it sends HSTS over HTTP unless the snippet is split.
  - Drop the redirect case from HT-2, which makes the test weaker than the spine says.

  The Core skeleton (which has no redirect) and the FR-24 story will also disagree on whether the headers snippet is one block or two.
- **Suggested spine fix.** AD-27 Headers, replace "including Caddy's own redirects and errors" with "including Caddy's own errors (there is no `handle_errors`). Caddy's automatic HTTP→HTTPS redirect is served apart from the site and carries only `Location`; HSTS is never sent over HTTP." HT-2: "the headers on a page, a 404 envelope, a static asset and a Caddy-generated 502 (the fixture stops `frontend`); the HT-1 redirect carries no `Strict-Transport-Security`." If Lisa wants `Referrer-Policy` on the redirect too, that needs an explicit HTTP site block (her decision; it costs one snippet split).

---

## Medium

### M1. The mode switch is split over three variables whose values do not expand (AD-27 Modes, AD-22, AD-27 Tests)

- **Evidence.** AD-27 Modes: "the site address comes from `{$SITE_ADDRESS}`. The Core skeleton uses `http://localhost:{$HTTP_PORT}` ... From the FR-24 story it is `localhost:{$HTTPS_PORT}` ... Railway sets `SITE_ADDRESS=http://:{$PORT}`". Build order: "The FR-24 story switches `SITE_ADDRESS`, `BP_HTTPS` and `BP_BASE_URL` together". AD-27 Tests: the e2e env file "sets its own `HTTP_PORT`, `HTTPS_PORT`, `DB_PORT`, database, `BP_BASE_URL` and `BP_TEST_SWITCHES`". Tech-currency F-3: "Env placeholders `{$VAR:default}` are substituted once, at parse time, and values are not expanded again, so `SITE_ADDRESS` cannot contain `{$PORT}`."
- **Why units diverge.**
  - **Placeholder syntax.** The values are written in Caddy placeholder syntax. A compose author who copies them literally (`SITE_ADDRESS: localhost:{$HTTPS_PORT}`) gets a Caddyfile parse error. One who uses compose interpolation (`localhost:${HTTPS_PORT:-8443}`) gets a working stack.
  - **The e2e env file.** It names neither `SITE_ADDRESS` nor `BP_HTTPS`. If compose hard-codes either, the e2e stack runs on its own ports while Caddy still serves the default address or `BP_HTTPS` disagrees with `BP_BASE_URL`.
  - **No default.** The Caddyfile has no default for `{$SITE_ADDRESS}`, so `caddy run` outside compose fails or picks whatever the author wrote.
  - **Railway.** The Railway value as written cannot work. It is untested in v1, so nobody will notice until deployment.
- **Suggested spine fix.** AD-27 Modes: "Compose computes `SITE_ADDRESS` by interpolation: `http://localhost:${HTTP_PORT:-8000}` before FR-24, `localhost:${HTTPS_PORT:-8443}` from it on. The Caddyfile writes `{$SITE_ADDRESS:http://localhost:8000}`. `BP_BASE_URL` and `BP_HTTPS` are derived in compose from the same port variables, so an env file sets only ports, database and switch path." Railway: "the Railway service sets `SITE_ADDRESS` to `http://:` followed by its port as a literal value (no nested placeholder); untested in v1 (Deferred)." Alternatively, use one `HTTPS=on|off` variable that compose turns into all three; either is a technical refinement, not a product choice.

### M2. The e2e layer is specified only in its FR-24 form (AD-27 Tests, Structural Seed, Conventions)

- **Evidence.** AD-27 Tests: the fixture "copies Caddy's root out of the proxy (`/data/caddy/pki/authorities/local/root.crt` ...) and verifies with an `ssl.SSLContext` loaded from it; Playwright uses `ignore_https_errors`." Seed: "test, e2e layer | ... | Caddy on the e2e ports, HTTPS". The Conventions say the e2e layer proves "pages, keyboard and axe (FR-1 to FR-8, FR-15 to FR-17, FR-22, FR-23 ...)", which are Core requirements, and AD-27 Build order keeps Caddy on plain HTTP until FR-24. The Conventions also say "The e2e fixture builds the images with `docker compose build`", while AD-27 says "runs `up --build --wait`".
- **Why units diverge.** The first Core page story builds the e2e fixture against an HTTP-only stack. There is no root to copy and no HTTPS port to verify. That author either writes the root copy anyway (it fails, because Caddy never made a CA) or leaves it out and hard-codes `http://localhost:<port>` in tests. The FR-24 story then has to reshape every e2e test, and the spine assigns that reshape to nobody. Two build commands in two places invite two fixtures.
- **Suggested spine fix.** AD-27 Tests, add: "Before FR-24 the fixture runs the same project over HTTP: `base_url = BP_BASE_URL` from the env file, no root copy, no TLS context. The FR-24 story adds the root copy (retried until the file exists) and the HTTPS context. Every e2e test takes its URL from the fixture's `base_url`, never a literal." Conventions Tests: drop "builds the images with `docker compose build`" (the fixture's `up --build` builds them).

### M3. The e2e stack cannot see its own switch file (AD-14 vs AD-27 Tests)

- **Evidence.** AD-14: "each test layer writes its own temporary file and points `BP_TEST_SWITCHES` at it, never at the working tree's file". AD-27 Tests: the e2e env file sets `BP_TEST_SWITCHES`. The file is "read once at startup".
- **Why units diverge.** In the e2e layer the backend runs in a container. A host temporary path in `BP_TEST_SWITCHES` means nothing inside it unless something mounts it, and the only mount the spine names is the examiner's `config/` file (H1). The e2e author can add a compose override file, make the mount source a variable, or give up and write the working-tree file, which AD-14 forbids. The FR-7 failed-payment page and the FR-14 `try_again` notice (e2e, per the layer map) need a switch changed during the run, and nothing says how, so tests that change switches will each invent a restart.
- **Suggested spine fix.** AD-14: "Compose mounts `${SWITCHES_DIR:-./config}` read-only at `/app/config` (H1). The e2e fixture sets `SWITCHES_DIR` to a temporary directory, writes `test-switches.toml` there, and changes a switch by rewriting that file and running `docker compose -p booking_e2e restart backend`, then waiting for health."

### M4. A bare `/api` does not match `handle /api/*` (AD-27 Entry, AD-10)

- **Evidence.** AD-27 Entry: "One `handle /api/*` sends requests, with the path unchanged, to `{$BACKEND_UPSTREAM:backend:8000}`; a bare `/api` gets the backend's JSON 404 through the same route." In Caddy, the path matcher `/api/*` is a prefix match on `/api/`, so `/api` falls to the final `handle` and reaches Next.js, which answers with an HTML 404 page.
- **Why units diverge.** The Caddyfile author writes exactly "one `handle /api/*`". An e2e or AD-10 test author who trusts the second half of the sentence asserts a JSON envelope for `/api` and gets HTML. One of them "fixes" the other: either `handle /api*`, which also catches `/apiary`, or a second matcher. Adversarial #3 proposed `handle /api` plus `handle /api/*`; the gate fix shortened it to a claim that does not hold.
- **Suggested spine fix.** AD-27 Entry: "One `handle` with the matcher `path /api /api/*` sends requests, with the path unchanged, to the backend." Add `GET /api` to the e2e layer's routing check.

### M5. The dev database `booking_dev` is never created, and the default URL is unstated (Structural Seed, AD-22)

- **Evidence.** Seed: "dev | `booking_dev` in the compose db | `uv run booking-platform dev` (127.0.0.1:8001, `--reload`)". AD-22 lists "the database URL" with no default. In the brownfield, the README says "Standard database-URL er `postgresql://postgres:booking@localhost:55432/booking`", and `docker-compose.yml` sets `POSTGRES_DB: booking`, so only `booking` exists. The slice test fixture creates `booking_test` itself through the admin URL.
- **Why units diverge.** The skeleton story keeps the brownfield default (`booking`), so dev and the examiner share one database, which the gate fix meant to prevent. Or it switches the default to `booking_dev`, and the first `uv run booking-platform dev` fails because the database does not exist. Someone then adds a `docker-entrypoint-initdb.d` script, which runs only on an empty volume and so never on an existing developer volume. Someone else makes `dev` create the database.
- **Suggested spine fix.** AD-22: "`BP_DATABASE_URL` defaults to `postgresql://postgres:booking@127.0.0.1:${DB_PORT:-55432}/booking_dev`; compose sets `.../booking` for its backend." AD-15 or the dev row: "`booking-platform dev` creates `booking_dev` through the server's `postgres` database if it is missing (as the test fixture does for `booking_test`)."

### M6. `uv run pytest` silently needs the default project's database (Seed commands, Conventions Tests; SM-4)

- **Evidence.** Seed Commands: "`uv run pytest` runs every test; it starts its own backend and its own compose stack." Seed table: "test, API layer | `booking_test` in the compose db". Brownfield `tests/conftest.py`: `ADMIN_URL ... localhost:55432/postgres`, and on failure `pytest.exit("... Start it with: docker compose up -d db")`. The e2e project has "its own db container" on its own `DB_PORT`.
- **Why units diverge.** On a fresh clone the examiner follows the three commands: `docker compose up --build --wait` (now running, so 55432 is up), then the test preparation, then `uv run pytest`. That works only if the examiner stack is still running. An examiner who stopped it, or a CI-like clean run, gets the "not reachable" exit from the API layer while the e2e layer starts its own stack. One story will make the API layer use the e2e project's db, and another will add `docker compose up -d db` to the README. SM-4 ("all its tests pass, by following the README alone") depends on which one happens.
- **Suggested spine fix.** Pick one and write it into Conventions Tests and the Commands: either "the API layer uses the e2e project's db server (started by the session fixture before either layer), in database `booking_test`", or "the README runs `docker compose up -d db` before `uv run pytest`, and the API layer uses the default project's db". The first keeps "one command runs all tests" (NFR-6). This is a technical choice, not a product one.

### M7. The backend has no single base path for repository-root folders (AD-12, AD-15, AD-18, Seed tree)

- **Evidence.** The Seed tree puts `migrations/`, `seeds/`, `content/` and `config/` at the repository root, outside `src/booking_platform/`. AD-15's runner reads `migrations/`, AD-18 applies `seeds/`, AD-12 says "`services` reads the same files" from `content/`, and AD-14 reads `config/`. The tree only says "`Dockerfile  # backend image, uv sync --locked`". Adversarial #4 proposed one `config.paths.ROOT` (or `BP_ROOT`) and named copies in the Dockerfile. The memlog's gate fixes record only the frontend half ("content/ as JSON copied into frontend/content"). The brownfield keeps `schema.sql` inside the package, so this move is new.
- **Why units diverge.** The skeleton story's migration runner finds `migrations/` from `Path(__file__).parents[2]`. That works in dev, and in the image only if `uv sync` installs the project in editable mode. The seed story uses the working directory. The outbox story uses a third path. The backend Dockerfile copies whatever the first story needed. A `uv sync --no-editable` or a changed `WORKDIR` later breaks some of them but not others.
- **Suggested spine fix.** AD-22: "`config.paths.ROOT` is the only base for `migrations/`, `seeds/`, `content/` and `config/`: `BP_ROOT` if set, else the repository root found from the package location. The backend Dockerfile copies those four folders to `/app` and sets `BP_ROOT=/app`."

### M8. The `.dockerignore` entries are names, not patterns (AD-17 Image)

- **Evidence.** AD-17 Image: "A root `.dockerignore` keeps `node_modules`, `.venv`, `.next`, `config/test-switches.toml` and `.logs/` out of every build context." The frontend image uses "the repository root as build context". Docker matches `.dockerignore` lines from the context root, so `node_modules` excludes only `./node_modules`, not `frontend/node_modules`; the same goes for `.next`.
- **Why units diverge.** The README's own test-preparation step (`npm --prefix frontend ci`) fills `frontend/node_modules` with Windows binaries. A frontend Dockerfile that copies `frontend/` after `npm ci`, as the `with-docker` layout does with `COPY . .`, overwrites the Linux modules, and `next build` fails on the examiner's machine but not on a fresh clone. This is adversarial #5 coming back through the literal wording.
- **Suggested spine fix.** AD-17 Image: "`.dockerignore` lists `**/node_modules`, `**/.next`, `.venv`, `.git`, `.logs`, `.docs`, `config/test-switches.toml` and `frontend/content`; each Dockerfile copies named paths, never the whole context."

### M9. Starlette's slash redirect points at `http://` behind Caddy (AD-27 Backend side, AD-10)

- **Evidence.** AD-27 Backend side: "No v1 rule reads an `X-Forwarded-*` header." The backend runs one uvicorn process behind Caddy (AD-22), and uvicorn trusts forwarded headers only from `127.0.0.1` by default, so the scope's scheme is `http`. FastAPI routers have `redirect_slashes=True` by default, and Starlette builds the 307 `Location` from the scope's scheme and the `Host` header that Caddy passes through (`localhost:8443`).
- **Why units diverge.** An API story declares `@router.get("/")` on a prefixed router, which serves `/api/admin/bookings/`. The frontend story calls `/api/admin/bookings`. In dev (HTTP) and in the API layer (HTTP), the 307 works. Behind Caddy with HTTPS, the browser follows it to `http://localhost:8443/...`, which is plain HTTP on the TLS port, and Caddy answers 400. Only the e2e layer after FR-24 shows the failure, and by then the cause is far from the change.
- **Suggested spine fix.** AD-10: "The FastAPI app and every router set `redirect_slashes=False`, and paths have no trailing slash. An unknown variant is the JSON 404 envelope. The backend never builds an absolute URL from the request (AD-12 links come from `BP_BASE_URL`)."

---

## Low

### L1. The Seed diagram starts the backend with `uv run` (Structural Seed vs AD-22)

- **Evidence.** Seed diagram: "`BE["backend: uv run booking-platform :8000 (internal)"]`". AD-22: "started from the image's virtual environment (no `uv run` at runtime)".
- **Fix.** The diagram: "backend: booking-platform from the image's venv, :8000 (internal)".

### L2. The diagrams and the examiner row show only the FR-24 end state (Design Paradigm, Structural Seed)

- **Evidence.** Design Paradigm: "`B[Browser] -->|"HTTPS :8443"| PX`". Seed: "proxy: Caddy on 127.0.0.1, HTTPS :8443, HTTP :8000 redirects"; examiner row "Caddy, `https://localhost:8443`"; Commands: "`docker compose up --build --wait` starts the platform at `https://localhost:8443`." AD-27 Build order keeps the Core on `http://localhost:8000`, and the README already says this correctly.
- **Why it matters.** The Core floor (PRD §10.1) may ship without FR-24. A story that writes the README from the Seed writes an address where nothing listens.
- **Fix.** Label both states: "Core: `http://localhost:8000`; from FR-24: `https://localhost:8443` (HTTP :8000 redirects)".

### L3. AD-22 names some variables but not all

- **Evidence.** "host and port (default `127.0.0.1:8001` for dev; `0.0.0.0:8000` inside the container)", "`BP_TEST_SWITCHES` (AD-14) and the test variables already in use". Only `BP_DATABASE_URL`, `BP_TEST_MUTATE` and `BP_TEST_ADMIN_URL` exist in the brownfield.
- **Fix.** Name them (`BP_DATABASE_URL`, `BP_HOST`, `BP_PORT`, `BP_TEST_MUTATE`, `BP_TEST_ADMIN_URL`), so the backend Dockerfile, compose and `config.py` use the same names.

### L4. "DB port for dev and tests only" has no mechanism (AD-27 Entry)

- **Evidence.** "The database port is published as `127.0.0.1:${DB_PORT}` for dev and tests only." There is one `docker-compose.yml`. Dev (`booking_dev`) and the API layer (`booking_test`) use the default project's db.
- **Fix.** "The database port is always published on `127.0.0.1:${DB_PORT}`; the examiner does not need it." Or name an override file. Either way, say which.

### L5. Caddy's data has no named volume (AD-27, Seed tree)

- **Evidence.** The README bullet: "the browser warns once; how to copy Caddy's root (`docker compose cp proxy:/data/caddy/...`)". The official image declares `/data` as an anonymous volume. After `docker compose down`, the next `up` gets a new one and a new root (tech-currency F-17).
- **Fix.** AD-27: "compose mounts the named volume `caddy_data` at `/data`"; README: "after `down -v`, copy and import the root again".

### L6. Host and redirect edge cases are not stated (AD-27)

- **Evidence.** Caddy serves only `localhost`. `https://127.0.0.1:8443` fails the TLS handshake, and before FR-24 `http://127.0.0.1:8000` matches no site and gets an empty response (tech-currency F-13). Dev uses `127.0.0.1:3000`, so a developer who carries that habit to the stack sees a blank page. The automatic redirect is a 308, which browsers may cache for `http://localhost:8000` across the Core-to-FR-24 switch. HTTP/3 is advertised (`Alt-Svc`) on a UDP port compose does not publish (F-15). The old design set `no-store` on its redirect; the new one says nothing.
- **Fix.** README: "use `localhost`, not `127.0.0.1`". AD-27: either `servers { protocols h1 h2 }` or publish the UDP port, and HT-2 ignores `Alt-Svc`.

### L7. The README bullet omits the localhost cookie limit (AD-27 README vs PRD FR-24)

- **Evidence.** PRD FR-24: "On `localhost`, browsers send Secure cookies over plain HTTP anyway ... The README states this limit." AD-27 Known limits states it, but the AD-27 README bullet does not list it. The old AD-27 had "the README states the deviation".
- **Fix.** Add "the localhost Secure-cookie and HSTS limits (Known limits)" to the README bullet.

### L8. Images and healthchecks are named only in part (Stack, AD-27 Startup)

- **Evidence.** The Stack names `node:24-alpine`, `caddy:2.11` and `postgres:18`, but not the backend base image or how uv gets into it. AD-27 Startup: "db, backend and frontend have healthchecks (`pg_isready`, `/api/health`, the frontend's `/`)", with no tool (a slim Python image has no `curl`). The proxy has no healthcheck, and `--wait` then counts it ready before Caddy has made its root, which the e2e root copy depends on (tech-currency F-7).
- **Fix.** The Stack gets a backend image row (for example `python:3.12-slim` plus the uv image at the pinned version). AD-27 Startup names the commands (`python -c "urllib.request.urlopen(...)"`, busybox `wget`) and adds a proxy healthcheck.

### L9. Tech-currency F-12 is half applied (Stack)

- **Evidence.** "pytest-playwright / playwright | 0.10.0 / 1.64.1 (1.65.2 out on 2026-11-19; take it when the lockfile is next updated)" and "axe-core | 4.14.0". The review found axe-core 4.14.1 (published 2026-11-16).
- **Fix.** "axe-core | 4.14.1 (or latest at lock time)".

### L10. Three capability rows omit the frontend (Capability map)

- **Evidence.** "FR-5 to FR-9 Book and pay | `services/booking.py` ... | AD-3, AD-8, AD-9, AD-12, AD-13, AD-20". "FR-15 to FR-17 Admin sign-in, list, Outbox | `api/admin.py`, `services/auth.py`". "FR-29 to FR-33 Whole-sauna booking | `services/whole.py` ...". Each needs pages: Details, Review and Confirmation; Sign-in, the Booking list and Outbox; Private sauna and the Manage Whole-sauna steps. AD-17 binds "FR-1 to FR-23 pages".
- **Fix.** Add `frontend/app` and AD-17 to those three rows (FR-1–4 and FR-25–28 already have them).

### L11. Browser-only state during server rendering is not bound (AD-17, AD-9)

- **Evidence.** AD-9: "The key lives with the draft in `sessionStorage` (`draft:seats`, `draft:whole`)". AD-17 puts the booking pages in client components, and Next.js renders those on the server too. Only `/manage` got the Strict Mode guard (AD-28). Adversarial #23's "read only inside effects" was not taken.
- **Why it matters.** The Review and Manage-step authors will each choose between a `useState` initializer (which throws on the server, or causes a hydration mismatch if guarded) and an effect.
- **Fix.** AD-17: "`sessionStorage`, `location` and `history` are read only inside effects; until mounted, a page renders its heading and a neutral placeholder."

### L12. Local operations are not stated (Structural Seed, Deferred)

- **Evidence.** Deferred puts "backups and monitoring" out of scope for production. Nothing says, for the local stack, how the examiner resets data (`docker compose down -v`, which also wipes Caddy's root, L5), where logs are read (`docker compose logs backend proxy`), or what survives a plain `down` (the database volume, and Caddy's data only after L5).
- **Fix.** Add one line to the Seed Commands: reset, logs, and what persists.

### L13. The companion EXPERIENCE.md is still partly SPA-era (EXPERIENCE.md)

- **Evidence.** Line 20 is updated ("Next.js (React) behind Caddy"), but line 46 still has "Route `/confirmation/:reference` (AD-12)", and lines 290 and 619 still say "the SPA". AD-12 now says `/confirmation/[reference]`. The memlog still lists "EXPERIENCE.md still says React SPA" as an open question for Lisa.
- **Fix.** Not a spine change. Offer Lisa the three wording edits along with the open PRD/README questions.

---

## Checked and consistent

- **AD-8 versus the base URL.** In every environment the browser's `Origin` equals `BP_BASE_URL`:
  - dev `http://127.0.0.1:3000`, through the rewrite, which keeps `Origin`;
  - the API layer `http://127.0.0.1:<port>`, through `tests/client.py`;
  - Core compose `http://localhost:8000`;
  - FR-24 `https://localhost:8443`.

  `config` refuses `BP_HTTPS` on with a non-`https://` base URL, and `403 cross_origin` is in AD-16.
- **Server-side calls.** `lib/server-api.js` sends no cookie, makes no write, holds no Seats left, and fetches with `no-store`. Landing, Terms and Privacy set no cookie (FR-21). The listings come only from the browser, so a cached Seats left cannot appear.
- **Ports.** Dev (3000, 8001) and the examiner stack (8000, 8443, 55432) no longer collide. The e2e project takes its own ports, and the container ports equal the host ports, so the redirect names the right port.
- **Startup order.** `depends_on: service_healthy` puts migrate after PostgreSQL is ready, and the frontend after the backend.
- **The Deferred list.** Railway, production TLS and `X-Forwarded-For` for FR-35 are deferred without letting two v1 units diverge (apart from the untested Railway value in M1).
- **Brownfield.** AD-10 (`/health` → `/api/health`), AD-15 (`schema.sql` → `0001`), AD-21 (slice tests kept, reshaped to `tests/client.py`) and AD-22 (dev port 8000 → 8001) each state their migration from the slice. `docker-compose.yml` and the README still describe the slice, which is correct until the skeleton story.
- **PRD alignment.** NFR-1 is already amended ("Docker runs the whole platform ... with one command"). §8.2 (frontend JavaScript) is kept by AD-17's "Not adopted" list.
