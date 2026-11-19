---
review: adversarial
target: ../ARCHITECTURE-SPINE.md (amendment of 2026-11-19 for Caddy + Next.js: Design Paradigm, AD-17, AD-27 rewritten; AD-4, AD-8, AD-10, AD-12, AD-14, AD-21, AD-22, Conventions, Stack, Structural Seed, Map, Deferred amended)
date: '2026-11-19'
lens: 'Two units one level down (stories or developers) that each obey every AD to the letter yet still build incompatibly because of the Caddy + Next.js change'
inputs:
  - ARCHITECTURE-SPINE.md (working copy, uncommitted, 2026-11-19 21:18)
  - .memlog.md (last 10 entries: Update run for Caddy + Next.js)
  - ../technology.md (proxy and frontend rows only)
  - prds/prd-booking-platform-2026-10-29/prd.md (§7, §8, NFR-1, NFR-2, FR-8, FR-21 to FR-25, §13)
  - prds/prd-booking-platform-2026-10-29/addendum.md (2026-11-19 change rows)
  - ux-designs/ux-booking-platform-2026-11-05/EXPERIENCE.md (route table, Booking draft, Accessibility Floor, open items)
  - README.md, docker-compose.yml, .gitignore, tests/conftest.py, src/booking_platform/app.py and db.py (slice)
---

# Adversarial review: Caddy as the only entry and Next.js behind it (AD-17, AD-27)

## Verdict

**Not ready to slice into stories.** The direction is coherent. Caddy owns TLS and headers, the browser does every session call through relative `/api`, and server components never carry a cookie. None of the holes lets capacity be exceeded or a token leak. But the rewrite moved several facts from one process (where one developer owned them) to four containers, two test layers and three environments, and in each case the spine says *what* without saying *which value where*. The worst one breaks the Core floor itself: AD-22 sets the compose base URL to `https://localhost:8443` unconditionally, while AD-27 runs the Core stack on `http://localhost:8000` until FR-24. AD-8's same-origin check then refuses every write, starting with `POST /api/session`, so Book seats never works.

Seven high findings are about the same seam: the `/api` prefix, `content/`, the Docker build context, test switches, e2e ports and startup readiness. Each is a place where the skeleton story, the FR-24 story and the test fixture will each pick a different value. The medium findings are mostly Next.js App Router facts the spine does not yet bind: `metadata` only works in server components, the Router Cache serves stale Seats left on Back, `next/font` and `next/image` add a second stylesheet, and there is no Venue "today" for the calendar. There are also some HTTPS guarantees the old AD-27 had and the new one dropped.

| Severity | Count |
| --- | --- |
| Critical | 1 |
| High | 7 |
| Medium | 11 |
| Low | 5 |
| **Total** | **24** |

## Method

Units one level down:

| # | Unit | Main ADs |
| --- | --- | --- |
| U1 | Core skeleton: compose (proxy, backend, frontend, db), Caddyfile in plain-HTTP mode, backend Dockerfile, reshaped slice fixture | AD-21, AD-22, AD-27, AD-15, AD-18 |
| U2 | Next.js app shell: `next.config.js`, root layout, `lib/api.js`, `lib/server-api.js`, frontend Dockerfile | AD-17, AD-12, Conventions |
| U3 | Core Guest pages: Landing, Book seats, Details, Review, Confirmation, Terms, Privacy | AD-4, AD-5, AD-8, AD-9, AD-16, AD-17 |
| U4 | Administrator pages: Sign-in, Booking list, Outbox | AD-8, AD-10, AD-17 |
| U5 | API-layer tests: slice tests, FR-11 races, RB-4/RB-5, AD-26 machine | Conventions (Tests), AD-14, AD-26 |
| U6 | e2e layer: compose fixture, axe, browser flows | AD-27 (Tests), Conventions |
| U7 | FR-24 story: Caddy `tls internal`, redirect, headers, `BP_HTTPS`, HT-1 to HT-4, README | AD-27, AD-8, AD-12, AD-22 |
| U8 | §4.8 Manage pages: `/manage`, `/manage/[reference]` | AD-28, AD-17, AD-27 |

Each finding names two units that each satisfy every AD as written, shows how they still collide, and gives the exact rule text to add. "Replace" means replace the quoted sentence in the spine; "Add" means add a bullet to the named AD or row.

---

## Critical

### 1. The compose base URL is `https://localhost:8443` before the stack serves HTTPS, so every Core write is refused

- **Severity:** Critical (breaks the Core floor, PRD §10.1 "Floor if the build falls short")
- **Units:** U1 (skeleton) vs U3 (Book seats) and U7 (FR-24)
- **Scenario:** AD-22 says, without qualification, "the base URL (default `http://127.0.0.1:3000` …; compose sets `https://localhost:8443`)". Only `BP_HTTPS` is qualified with "once the FR-24 story merges". U1 follows AD-22 and writes `BP_BASE_URL: https://localhost:8443` into `docker-compose.yml`. U1 also follows AD-27's build order: Caddy on plain HTTP at `:8000`. The examiner opens `http://localhost:8000`, and Book seats calls `POST /api/session` with `Origin: http://localhost:8000`. AD-8 compares that with the base URL's origin (`https://localhost:8443`) and refuses it. No Guest can book. The seeded emails also link to `https://localhost:8443`, where nothing listens. AD-27's build order says the FR-24 story "sets `BP_HTTPS` and the base URL", which contradicts AD-22. If FR-24 never ships, the Core floor is broken. If it does ship, the Core-era e2e tests were written against a stack that could not book.
- **Fix:**
  - AD-22, replace the base-URL bullet with: "the base URL `BP_BASE_URL` (default `http://127.0.0.1:3000`, the dev frontend). Compose sets it to the origin Caddy serves: `http://localhost:${HTTP_PORT}` until the FR-24 story merges, and `https://localhost:${HTTPS_PORT}` from then on, changed in the same PR as `BP_HTTPS`."
  - AD-22, add: "`config` refuses to start, with one line naming `BP_BASE_URL`, when the base URL has a path, a query or a fragment, or when `BP_HTTPS` is on and the base URL is not `https://`."
  - AD-27 Build order, append: "Before FR-24, the platform's only origin is `http://localhost:${HTTP_PORT}`, and AD-8's same-origin check compares with it."

---

## High

### 2. The API test layer has no Origin, and AD-8 refuses every write it sends

- **Severity:** High
- **Units:** U5 (API-layer fixture and tests) vs the AD-8 CSRF dependency (U1)
- **Scenario:** Conventions: "API, concurrency and bypass tests start the backend themselves with uv over HTTP". The Structural Seed calls this "uvicorn subprocess on a free port, HTTP … direct". The fixture sets no `BP_BASE_URL`, so the backend's base URL is the default `http://127.0.0.1:3000`. httpx sends neither `Origin` nor `Sec-Fetch-Site`. AD-8 says a state-changing request without `Origin` must carry `Sec-Fetch-Site: same-origin`, so every `POST` in the slice tests, the FR-11 races and RB-4/RB-5 is refused. One developer then "fixes" this by adding a test bypass to the CSRF check, which AD-21 forbids ("no rule is loosened"). Another adds `Origin: http://127.0.0.1:3000` by hand in some tests. The FR-11 races written by a third developer fail at random depending on which client helper they use.
- **Fix:** Conventions, Tests, add: "The API-layer fixture starts the backend with `BP_BASE_URL=http://127.0.0.1:<port>` (its own port) and `BP_HTTPS` off. Every httpx client in the API layer is made by one helper, `tests/client.py::api_client(base)`, which sets `Origin: <base>` on every request. `tests/test_fr18_csrf.py` sends the same `POST` without `Origin` and `Sec-Fetch-Site`, with a foreign `Origin`, and with `Origin: null`, and asserts `403 cross_origin` and no row written. No setting or switch turns the same-origin check off." Add `cross_origin` (403) to AD-16's code table.

### 3. The `/api` prefix contract differs across Caddy, `next dev` and the Next app

- **Severity:** High
- **Units:** U1 (Caddyfile) vs U2 (`next.config.js`) vs backend routers (AD-10)
- **Scenario:** Four places route `/api`, and each rule allows a variant that breaks another:
  - AD-27 says Caddy "routes `/api/*` … to `backend:8000`". `technology.md` comes from a project whose Caddyfile a developer may copy with `handle_path /api/*`, which strips the prefix. AD-10 mounts every route under `/api`, so every API call becomes a 404.
  - AD-17 and the Conventions say `next dev` "rewrites `/api/:path*` to `http://127.0.0.1:8000`". Written literally as `destination: 'http://127.0.0.1:8000/:path*'`, this also strips `/api`. It works for nothing in dev, while compose works.
  - Caddy's `/api/*` matcher does not match the bare path `/api`, so it goes to Next.js and comes back as an HTML 404. AD-10 says an unknown `/api` path "never [returns] a page".
  - AD-17 forbids only Route Handlers "that write, judge a rule or read a cookie". A read-only `frontend/app/api/venue/route.js` is allowed. Next.js checks its own routes before `rewrites()`, so in dev it answers; in compose, Caddy sends the same path to FastAPI, which returns 404.
  - `rewrites()` is not limited to development unless the code says so. In the standalone image, a request that reaches Next.js on `/api…` is proxied to `127.0.0.1:8000` inside the frontend container and fails with a 500.
  - Next.js 16 calls middleware `proxy.js`. AD-17 forbids "middleware", and a developer can argue that `proxy.js` is not covered.
- **Fix:**
  - AD-27 Entry, replace the routing sentence with: "The Caddyfile routes with `handle` (never `handle_path`, never `uri strip_prefix`): `handle /api` and `handle /api/*`, `handle /docs` and `handle /openapi.json` go to the backend with the path unchanged, and a final `handle` goes to the frontend."
  - AD-17 Dev, replace with: "`next.config.js` returns `[{ source: '/api/:path*', destination: 'http://127.0.0.1:8000/api/:path*' }]` from `rewrites()` only when `process.env.NODE_ENV === 'development'`, and `[]` otherwise. The path keeps its `/api` prefix."
  - AD-17 Framework, replace the last sentence with: "`frontend/app/` has no `api/` folder, no `route.js` files, no Server Actions (`'use server'`) and no `middleware.js` or `proxy.js`."
  - AD-10, add: "`GET /api` (no trailing slash) is also the JSON 404 envelope."

### 4. `content/` cannot be both read by the Next standalone build and found by the backend image as written

- **Severity:** High
- **Units:** U2 (frontend Dockerfile, `next.config.js`) vs U1 (backend Dockerfile) vs the story that writes the terms (U3, `services.outbox`)
- **Scenario:** AD-12 says "both the frontend build and `services` read it from there. The frontend image is built with the repository root as its context." Nothing fixes how Next.js reaches a folder outside `frontend/`:
  - Next 16 builds with Turbopack. Turbopack does not resolve files outside its root, and it infers that root from the nearest lockfile, which is `frontend/package-lock.json`. `import terms from '../../content/terms-seats.json'` then fails `next build`.
  - Another developer instead reads the file with `fs.readFileSync(path.join(process.cwd(), '../content/…'))` in a server component. That works in `next dev`. But `output: 'standalone'` copies only traced files under `outputFileTracingRoot`, so in compose the page throws at runtime.
  - If someone then sets `outputFileTracingRoot` to the repository root, the standalone server moves to `.next/standalone/frontend/server.js`, and the Dockerfile's `CMD ["node", "server.js"]` no longer starts it.
  - The file format is open too. A Markdown file shows `**` in a plain-text email (AD-12 Format), and a plain `.txt` cannot be imported by Next.js without a loader.
  - The backend side has the same gap. The Structural Seed puts `migrations/`, `seeds/` and `content/` at the repository root, outside the package. The backend image (`uv sync --locked`) only works if the Dockerfile copies them, and if the code finds them from the same base path in dev, in the API layer and in the container.
- **Fix:**
  - AD-12 Shared text, replace the last two sentences with: "Each shared text is `content/<name>.json` of the form `{"paragraphs": ["…", "…"]}`: plain UTF-8 sentences, no markup. `services` reads it with `json.load`; emails join paragraphs with a blank line, and pages render each as `<p>`. The frontend imports it as a JSON module at build time and never reads `content/` with `fs`. `frontend/next.config.js` sets `turbopack.root` and `outputFileTracingRoot` both to `path.join(__dirname, '..')`. The frontend image is built with the repository root as context, copies `content/` and `frontend/`, and starts with `node frontend/server.js` from the standalone output."
  - AD-15/AD-18, add: "`config.paths.ROOT` is the one base path for `migrations/`, `seeds/`, `content/` and `config/`: `BP_ROOT` if set, otherwise the repository root found from the package location. The backend Dockerfile sets `WORKDIR /app`, copies those four folders to `/app/`, and sets `BP_ROOT=/app`."

### 5. A repository-root build context without `.dockerignore` puts Windows `node_modules`, `.venv` and the local test-switch file into the images

- **Severity:** High (NFR-1 on the examiner's Windows laptop)
- **Units:** U6 (README: `npm --prefix frontend ci` once, for axe) vs U2 and U1 (Dockerfiles with repository-root context)
- **Scenario:** The README tells the examiner to run `npm --prefix frontend ci` on the host, so `frontend/node_modules` holds Windows binaries (`@next/swc-win32-x64-msvc`). The frontend Dockerfile runs `npm ci` in Linux and then, as is usual, `COPY frontend/ ./frontend/`. The host `node_modules` overwrites the Linux one, and `next build` then fails to load SWC for linux-musl, or tries to download a WASM fallback. The backend Dockerfile's `COPY . .` does the same with the host `.venv` (Windows `Scripts/` layout). It also bakes `config/test-switches.toml` into the image, where AD-14 meant it to be mounted. Each Dockerfile is correct on a fresh clone and broken after the README's own test-preparation step.
- **Fix:** Structural Seed tree, add `.dockerignore`. AD-27 (or a new Conventions row "Images"): "`.dockerignore` at the repository root excludes `**/node_modules`, `**/.next`, `.venv`, `.git`, `.logs`, `.docs`, `.hypothesis`, `.pytest_cache`, `test-results`, `config/test-switches.toml` and `caddy_data`. Each Dockerfile copies named paths only, never `COPY . .`."

### 6. One test-switch file in the working tree drives the examiner stack, the e2e stack and the API layer

- **Severity:** High
- **Units:** U5 (API-layer tests for FR-7 and FR-14) vs U6 (e2e tests for the failed-payment and `try_again` pages) vs U1 (compose mounts `config/`)
- **Scenario:** AD-14 says the switch file is `config/test-switches.toml`, read once at startup, and that "in compose, `config/` is mounted read-only into the backend". The e2e project uses the same compose file, so it mounts the same folder. U5 writes `payment = "fail"` into `config/test-switches.toml` and starts its backend. U6 needs `payment = "hold"` for the `409 payment_pending` page, writes the same file, and restarts the e2e backend. Both run in one `uv run pytest`, so each sees the other's value. A crashed run leaves the file behind, and the examiner's next `docker compose up` serves a platform where every payment fails. AD-14 gives no variable to point a backend at another file. AD-22's "the test variables already in use" names none.
- **Fix:** AD-14, replace "In compose, `config/` is mounted read-only into the backend." with: "`config` reads the file named by `BP_TEST_SWITCHES` (default `config/test-switches.toml` under `config.paths.ROOT`); a missing file means all switches off. The examiner's `docker-compose.yml` mounts no switch file. The API-layer fixture writes a temporary file per backend it starts and passes its path. The e2e fixture uses `docker-compose.e2e.yml`, which mounts a temporary folder read-only at `/switches` and sets `BP_TEST_SWITCHES=/switches/test-switches.toml`. A test that needs other switches rewrites that temporary file and runs `docker compose -p booking_e2e restart backend`, then waits for health. Tests never write `config/test-switches.toml`."

### 7. The e2e project's "own host ports" break Caddy's redirect, the base URL, the clock and the examiner's stack

- **Severity:** High
- **Units:** U6 (e2e fixture) vs U7 (Caddyfile, HT-1) vs U1 (compose file)
- **Scenario:** AD-27 says the e2e fixture runs the compose stack "under its own project name, host ports and database". It also says Caddy's "`http_port 8000` and `https_port 8443` are published as the same host ports". These two rules collide in five ways:
  - **Redirect target.** If U6 maps host `18443` to container `8443`, Caddy's redirect still sends `http://localhost:18000/x` to `https://localhost:8443/x`. That is the examiner's stack, or nothing. HT-1 passes or fails depending on what else is running.
  - **Base URL.** Nothing says the e2e `BP_BASE_URL` follows the e2e port, so HT-4 and AD-8 compare with `:8443`.
  - **Clock and data.** AD-4 says "tests move the clock only by writing `clock.off` directly", and HT-1 must show "nothing changes". Both need the e2e database, but the only published database port is `127.0.0.1:55432`, which is the examiner's.
  - **Which database the API layer uses.** "`uv run pytest` … starts its own backend and its own compose stack", but the API layer still connects to `localhost:55432` (slice `conftest.py`). The examiner who has not run `docker compose up` first gets "The PostgreSQL container is not reachable".
  - **Leftovers and timing.** The e2e volume outlives the run, so the next run starts on an old database. Caddy's root is created only when Caddy first issues a certificate, so `docker compose cp` right after `--wait` can fail.
- **Fix:**
  - AD-27 Local HTTPS, replace the port sentence with: "Caddy's global `http_port {$HTTP_PORT:8000}` and `https_port {$HTTPS_PORT:8443}` are published as `127.0.0.1:${HTTP_PORT}:${HTTP_PORT}` and `127.0.0.1:${HTTPS_PORT}:${HTTPS_PORT}`: the container port always equals the host port, so the redirect names the right port. The database is published as `127.0.0.1:${DB_PORT:-55432}:5432`."
  - AD-27 Tests, replace the first sentence with: "The pytest session fixture picks free ports, writes them with `BP_BASE_URL=https://localhost:<HTTPS_PORT>` (plain `http://localhost:<HTTP_PORT>` before FR-24) into a temporary env file, runs `docker compose -p booking_e2e --env-file <it> -f docker-compose.yml -f docker-compose.e2e.yml down -v`, then `up --build --wait`, and runs `down -v` again at the end. The API layer uses the same project's database server (`DB_PORT`), in its own database `booking_test`, so `uv run pytest` needs only Docker running. The fixture retries `docker compose cp proxy:/data/caddy/pki/authorities/local/root.crt` for up to 30 s. e2e tests write `clock.off` through `127.0.0.1:<DB_PORT>`, database `booking`. Every e2e test takes its URL from the fixture's `base_url`, never a literal."

### 8. Nothing orders startup, so the examiner's first `docker compose up --build` can leave the backend dead behind Caddy

- **Severity:** High (NFR-1, SM-4)
- **Units:** U1 (compose) vs the backend lifespan (AD-15, AD-18) vs U6 (`--wait`)
- **Scenario:** The slice's lifespan calls `db.migrate()` first, which connects directly to PostgreSQL. On a first start, `postgres:18` is still initialising its volume, so the connection fails, the lifespan raises and uvicorn exits. Caddy then answers 502 forever, and Next's server components fail too, since they call `API_INTERNAL_URL` for Venue facts. `docker compose up --wait` (U6) waits only for healthchecks, and none is defined, so the e2e tests start before migrations and the seed finish. Inside the container the spine also leaves four start details open, and each one can stop the backend or the frontend from being reached:
  - **Backend host:** AD-22 says `0.0.0.0:8000` inside the container, but not which variable sets it.
  - **Backend start command:** the Structural Seed's `uv run booking-platform` re-syncs at every start and may need the network.
  - **Next.js listen address:** the standalone `server.js` listens on `$HOSTNAME`, which Docker sets to the container id.
  - **Healthcheck tools:** the healthcheck tool is unstated (`python:slim` has no `curl`).
- **Fix:** AD-27, add **Startup:** "`db` has a healthcheck (`pg_isready -U postgres`). `backend` `depends_on: db: condition: service_healthy`, sets `BP_HOST=0.0.0.0`, runs `.venv/bin/booking-platform` (never `uv run` at runtime), has `restart: unless-stopped`, and has a healthcheck `python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"`. `/api/health` answers 200 only after migrations, seed and catch-up. `frontend` `depends_on: backend: condition: service_healthy`, sets `HOSTNAME=0.0.0.0` and `PORT=3000`, and has a healthcheck with busybox `wget -q -O- http://127.0.0.1:3000/`. `proxy` `depends_on` both healthy. The e2e fixture uses `up --wait`, which then means ready."

---

## Medium

### 9. The dev setup collides with the examiner stack on port 8000 and shares its `booking` database

- **Severity:** Medium
- **Units:** dev workflow (Structural Seed "dev" row) vs U1 (compose publishes Caddy's HTTP port 8000)
- **Scenario:** Dev runs `uv run booking-platform dev` on `127.0.0.1:8000`, against "`booking` in compose". The README's only start command is now `docker compose up --build`, which also starts Caddy on host port 8000. Then either the dev backend cannot bind, or, on Windows, binds `127.0.0.1:8000` beside Docker's `0.0.0.0:8000`, and `http://127.0.0.1:8000` reaches whichever one the OS picks. Even with `docker compose up -d db` only, the dev backend on a feature branch applies migration `0009` to the same `booking` database the compose backend (older image) then starts against. In dev, `next dev` without `-H` prints `http://localhost:3000`; a developer who follows it has `Origin: http://localhost:3000` ≠ base URL `http://127.0.0.1:3000`, so every write is refused, and cookies set on one host are not sent to the other.
- **Fix:**
  - Change Caddy's default `HTTP_PORT` to `8080` everywhere (AD-27, README `curl -i http://localhost:8080/`), so 8000 stays the dev backend's.
  - Structural Seed dev row: "Database: `booking_dev` in the compose `db` service, started with `docker compose up -d db`; dev never uses the examiner's `booking` database. `BP_DATABASE_URL` default points at `booking_dev`."
  - AD-17 Dev: "`frontend/package.json` `dev` script is exactly `next dev -H 127.0.0.1 -p 3000`; the README opens `http://127.0.0.1:3000`, never `localhost:3000`."

### 10. Window listings from server components show stale Seats left and split the listing code

- **Severity:** Medium
- **Units:** U3 (Book seats as a server component calling `server-api` with `?date=&seats=`) vs U3' (Book seats as a client component calling `lib/api.js`)
- **Scenario:** AD-17 lets `server-api.js` fetch "Window listings" with `no-store`, and it lets the browser fetch anything through `api.js`. Book seats changes date and Seats on the client and keeps the draft in `sessionStorage`. One developer renders listings on the server from search params. Another fetches them in the browser. Both are legal, so error handling for the same listing exists twice, and AD-16's code mapping exists in `server-api.js` too. And `no-store` covers only the fetch. The App Router's client Router Cache always reuses the RSC payload on browser Back/Forward, so Back from Details shows the Seats left from before, which AD-17 says it prevents ("a cached Seats left").
- **Fix:** AD-17 Server calls, replace the parenthesis with: "(Venue facts: Saunas, prices, Window schedule, contact; never anything that shows Seats left, `already_started` or a horizon)". Add: "Window listings and Private sauna listings are fetched only in the browser through `lib/api.js`, when the page mounts and whenever its inputs change, so Back and Forward always read them again. `server-api.js` throws on any non-2xx and the page shows its generic error; it does not map codes."

### 11. No Venue "today" in any response, so the calendar and the Booking list read a forbidden clock

- **Severity:** Medium
- **Units:** U3 (Book seats calendar: first month and first bookable day) and U4 (Booking list: "a Text field defaulting to today", EXPERIENCE.md) vs AD-4
- **Scenario:** AD-4 now forbids both the browser clock and the Next.js server clock. AD-16 sends `already_started`, `horizon_end` and `horizon_days`, but not the start of the horizon, so neither page can know "today" in Venue time without a clock. U3 uses `new Date()` in a server component ("that is not the browser clock"). U4 uses it in the browser. e2e tests move `clock.off` to 2026-12-01, while the Next.js server and Chromium still think it is 19 November. The calendar opens on the wrong month, and the Booking list defaults to a date with no Windows. The first render also differs between server and browser at midnight, so React reports a hydration mismatch. `Intl.DateTimeFormat` without a fixed locale and hour cycle can also format differently in Node's ICU and Chrome's (for example the narrow no-break space before "PM").
- **Fix:**
  - AD-16 Time facts, replace the second sentence with: "Each Window listing, the Private sauna listing and every Administrator day view carry `today` (the Venue date of `app_now()`), `horizon_end` and `horizon_days`; each Window carries `already_started`."
  - AD-4 Clock, add: "The frontend never calls `Date.now()` or `new Date()` without an argument, on the server or in the browser; ESLint `no-restricted-syntax` enforces it in `frontend/`."
  - Conventions, Time: "…formats with `Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Oslo', hourCycle: 'h23', … })`."

### 12. "Every route sets its page title through Next.js `metadata`" cannot hold for client pages or the "Error:" title

- **Severity:** Medium (FR-23, WCAG 2.4.2 and 2.4.3)
- **Units:** U3 (Review, Confirmation as client pages) vs U2 (root layout focus handling) vs EXPERIENCE.md Accessibility Floor
- **Scenario:** Next.js accepts `metadata` and `generateMetadata` only from server components. U3 writes `'use client'` at the top of `app/book/review/page.js`, because the page reads `sessionStorage` and calls `api.js`, and then cannot export `metadata`. The build fails, or the title is silently missing. EXPERIENCE.md also requires "Error: " in front of the title while an Error summary shows. That title is client state, so it needs `document.title`, which the Convention ("through metadata") forbids. Focus is open too. The App Router keeps layouts mounted, so a focus effect in a layout never runs on navigation, while one in each page runs on first load too. Next's built-in route announcer already reads the new title, so moving focus to the heading makes screen readers announce the change twice. Nobody says whether a query change (`/admin/bookings?date=`) is a "route change".
- **Fix:** Conventions, Accessibility, replace with:
  - "Every `page.js` is a server component that exports `metadata` with `title` = the page heading + ' – Saunalöyly' (Landing: 'Saunalöyly') and renders one client component for the page body. `generateMetadata` never fetches."
  - "`components/useErrorTitle.js` is the only code that writes `document.title`: while an Error summary is shown it sets 'Error: ' + the metadata title, and restores it when the summary goes."
  - "`components/RouteFocus.js`, rendered once in the root layout, moves focus to the page's `<h1 tabindex="-1">` when `usePathname()` changes, never on first load and never on a query-string change alone."
  - "The Next route announcer stays on."

### 13. HT-3 drops the PRD's "the HTTP listener never reads a cookie", and an unnamed HTTP host is not covered

- **Severity:** Medium (spine contradicts PRD FR-24 as amended today)
- **Units:** U7 (HT tests) vs PRD FR-24 (commit 8f4f284) and addendum row FR-24
- **Scenario:** PRD FR-24 now reads: "the local test checks the cookie attributes and that the HTTP listener never reads a cookie." The new HT-3 checks only the attributes. The old byte-for-byte clause ("answers the same with and without a `Cookie` header") was dropped with the uvicorn listener. U7 writes HT-3 to the spine, and the PRD's acceptance line has no test. Caddy redirects only the site names it serves. `http://127.0.0.1:8080/` (or any `Host` other than `localhost`) either gets Caddy's catch-all redirect to `https://127.0.0.1:…`, where no certificate exists, or gets an empty response. FR-24 "a plain-HTTP request … is redirected to HTTPS" is then untested for the most common alternative address.
- **Fix:**
  - AD-27 Tests, HT-3, append: "…and Caddy's HTTP port answers a request with a `Cookie` header exactly as without one (status, `Location` and every header except `Date`)."
  - HT-1, append: "…for `Host: localhost` and for `Host: 127.0.0.1`. The Caddyfile has an `http://` catch-all site on `{$HTTP_PORT}` that redirects every host to `{$BP_BASE_URL}{uri}` with 308."
  - The addendum row FR-24 should name Caddy instead of "the HTTP listener", or leave it generic ("the HTTP port").

### 14. The rewrite lost two HTTPS guarantees: the https base-URL check and headers on Caddy's own errors

- **Severity:** Medium
- **Units:** U7 (Caddyfile headers, HT-2, HT-4) vs U1 (compose env)
- **Scenario:**
  - The old AD-27 refused to start when HTTPS was on and the base URL was not `https://`. That check is gone (see finding 1 for the rule text). HT-4 only compares links with "the stack's base URL", so a compose override `BP_BASE_URL=http://localhost:8443` with `BP_HTTPS` on passes HT-4 while every email link is `http://`. PRD FR-24 says every link starts with `https://`.
  - AD-27 says Caddy adds the headers "to every response from either service, error responses included". But the `header` directive in a site block does not apply to responses that Caddy itself generates in `handle_errors`. For example, the 502 while the backend starts carries no HSTS, `no-store` or `noindex`.
- **Fix:**
  - AD-27 Tests, HT-4, replace with: "every Outbox link starts with `https://` and with the stack's base URL."
  - AD-27 Headers, add: "The headers are one Caddyfile snippet `(headers)`, imported in the site block and in its `handle_errors` block. HT-2 also checks a Caddy-generated error (the e2e fixture stops `backend` and requests `/api/health`)."

### 15. `/docs` routed through Caddy loads Swagger UI from a CDN (FR-21)

- **Severity:** Medium
- **Units:** U1 (Caddyfile copied from `technology.md`: `/api/*`, `/docs`, `/openapi.json`) vs FR-21 "No request goes to a third party"
- **Scenario:** FastAPI's default `/docs` page loads `swagger-ui-bundle.js` and CSS from `cdn.jsdelivr.net` and a favicon from `fastapi.tiangolo.com`. AD-27 now makes it public on the platform's only origin. The FR-21 test (no third-party request) passes on the Guest pages, while the examiner who opens `/docs` sees exactly such requests. `/redoc` is not routed, so it falls through to Next.js as a 404 page.
- **Fix:** AD-27 Entry: "Caddy routes `/api/*` and `/api` only. FastAPI is created with `docs_url=None, redoc_url=None, openapi_url='/api/openapi.json'`. If interactive docs are wanted, Swagger UI is served from self-hosted assets at `/api/docs` (`get_swagger_ui_html` with local `swagger_js_url`/`swagger_css_url`), and the e2e FR-21 test also opens it." Remove "`/docs` and `/openapi.json`" from AD-27 and the Design Paradigm's proxy row.

### 16. "The only service with a public port" binds Caddy to every interface

- **Severity:** Medium (SC9; regression from the old design's loopback-only listeners)
- **Units:** U1 (compose `ports: ["8443:8443", "8000:8000"]`) vs AD-27 ("The database port is published on `127.0.0.1` only")
- **Scenario:** Compose's short `ports` syntax publishes on `0.0.0.0`. With the spine as written, the examiner's stack, with a seeded Administrator whose password the README prints, is reachable from the café network. The old AD-27 bound `127.0.0.1` and `::1` only.
- **Fix:** Covered by finding 7's port text (`127.0.0.1:` prefix on every published port). Add to AD-27 Entry: "Every published port is bound to `127.0.0.1`; nothing listens on other interfaces. 'Public' means reachable from the host's browser."

### 17. Next.js idioms for fonts, images and CSS break "one stylesheet" and "self-hosted in `frontend/public/`"

- **Severity:** Medium (FR-22, DR-3)
- **Units:** U2 (root layout with `next/font/local`) vs U3 (Landing images with `next/image`) vs Conventions, Styling
- **Scenario:** In Next.js the idiomatic way to self-host Finlandica is `next/font/local`. It generates its own `@font-face` CSS chunk and hashed class names: a second stylesheet, and fonts copied out of `public/`. That conflicts with the `ASSETS.md` paths. `next/image` writes inline `style` attributes, serves images from `/_next/image` (with `sharp` in the standalone image), and needs `width` and `height` props. A third developer uses a CSS Module for one component. Each follows "React components use PascalCase files" and imports `styles.css` once, but the page then has three styling sources.
- **Fix:** Conventions, Styling, append: "Fonts are `@font-face` rules in `styles.css` pointing to `/fonts/*.woff2` in `frontend/public/fonts/`; `next/font` is not used. Images are plain `<img>` from `frontend/public/images/` with `width`, `height` and `alt`; `next/image` is not used, and `images.unoptimized` is `true`. No CSS Modules, `style` props, `styled-jsx` or other CSS files. `tests/e2e/test_fr22_one_stylesheet.py` asserts each Core page loads exactly one stylesheet and only same-origin font and image URLs."

### 18. The two test layers have no coverage map: the real-browser write path, Caddy routing and the Manage fragment flow fall between them

- **Severity:** Medium
- **Units:** U5 vs U6
- **Scenario:** Conventions split the layers by kind: API, concurrency and bypass in one; browser, axe and HTTPS in the other. They do not say which requirements each layer must prove, so each layer's author assumes the other covers it:
  - **AD-8 with a real browser:** the API layer adds `Origin` by hand (finding 2), so only an e2e test that books through Chromium shows that the browser's real `Origin`, passed through Caddy, matches `BP_BASE_URL`. Finding 1 hides here.
  - **AD-10 through Caddy:** an unknown `/api/x` returns the JSON 404 envelope only if Caddy routes it to the backend (finding 3). The API layer never passes through Caddy.
  - **FR-25 and AD-28 end to end:** these are the fragment read, `history.replaceState`, `POST /api/manage/open`, no token in any Caddy or uvicorn log line, and `Referrer-Policy` on the Manage HTML. RB-4 and RB-5 run in the API layer only.
  - **FR-7, FR-14 and FR-22 error pages:** these are the page states for the failed payment and `try_again`, plus axe on them. They need switches in the e2e stack (finding 6).
  - **Duplicate cookie checks:** any API-layer cookie-attribute test asserts no `Secure` (`BP_HTTPS` off), while HT-3 asserts `Secure`. Two tests for one rule with opposite expectations invite someone to "fix" one.
- **Fix:** Conventions, Tests, add **Layer map:**
  - "API layer: every rule and refusal, FR-10 to FR-14 races, RB-1 to RB-6, AD-26, CSRF refusals (finding 2), and cookie `HttpOnly`, `SameSite=Strict` and `Path=/`, never `Secure`."
  - "e2e layer, one test each:
    - a full Seat booking in Chromium (Landing → Confirmation), asserting the confirmation email in the page;
    - `GET /api/nope` and `GET /api` return the JSON envelope through Caddy;
    - the Manage link flow (§4.8): the address bar has no `#t=` after load, the Manage page shows the Booking, and the backend logs contain no token (`docker compose logs backend proxy`);
    - the FR-7 failed-payment page and the FR-14 `try_again` notice, each with axe;
    - HT-1 to HT-4."
  - "No requirement is tested in both layers with different expectations."

### 19. "Environment variables switch the same Caddyfile" has no mechanism, and three stories need one

- **Severity:** Medium
- **Units:** U1 (Core: plain HTTP on `:8000`) vs U7 (FR-24: `tls internal`) vs the Deferred Railway mode
- **Scenario:** `tls internal` cannot be turned off with a placeholder. A site address without a scheme turns automatic HTTPS on. U1 writes `http://localhost:8000 { … }` (or `auto_https off`). U7 rewrites the site block. Railway would need `:{$PORT}` with no TLS at all. Three authors write three mode mechanisms, and the headers and routes get copied into each. A copied block that misses `handle /api` is finding 3 again.
- **Fix:** AD-27, add **Modes:** "The `Caddyfile` holds the global options, the `(headers)` and `(routes)` snippets, and one line `import caddy/{$CADDY_MODE:local-https}.caddy`. `caddy/local-http.caddy` (Core, before FR-24) is `http://localhost:{$HTTP_PORT} { import routes }`. `caddy/local-https.caddy` is `localhost { tls internal; import headers; import routes }` plus the HTTP catch-all of finding 13. `caddy/railway.caddy` is `:{$PORT} { import headers; import routes }` with `auto_https off`, and adds no HSTS, because Railway terminates TLS. The FR-24 story only changes `CADDY_MODE` and `BP_HTTPS` in compose." Also add global option `skip_install_trust` (see finding 24).

---

## Low

### 20. PRD NFR-1, the NFR-1 assumption and the README still describe "Docker runs the data store; one command each"

- **Severity:** Low
- **Units:** U7 (README section of AD-27) vs PRD §5 and §13 vs README.md
- **Scenario:** PRD NFR-1 says "Docker runs the PostgreSQL data store as a container", and the assumption (also in §13) says "one command each to start the data store, the backend and the frontend". The spine's examiner flow is one `docker compose up --build`, and the tests need Node (`npm ci`) and Docker. The README lists uv, Git and Docker (no Node), starts with `docker compose up -d db` and `uv run booking-platform` on `http://127.0.0.1:8000`, and says frontend Node.js "bestemmes i arkitekturfasen". The current `docker-compose.yml` publishes `55432` on all interfaces. None of these is wrong for today's slice, but U1 and U7 will each edit the README to their own state, and the PRD will contradict both.
- **Fix:**
  - PRD NFR-1, replace the Docker sentence and the assumption with: "Docker runs the whole platform (proxy, backend, frontend, data store) with one command from the README; uv and Node.js are needed only to run the tests and for development (Lisa, 2026-11-19). `[ASSUMPTION: one command to start the platform and one to run all tests]`." Update §13 the same way.
  - Spine, AD-21: "The skeleton story rewrites README 'Forutsetninger', 'Kom i gang' and 'Tester' to the Structural Seed commands (with Node.js in the prerequisites); the FR-24 story changes only the address and adds the certificate paragraph."

### 21. Stale references to the SPA and React Router remain in the spine and in its companion EXPERIENCE.md

- **Severity:** Low
- **Units:** U8 (`/manage/[reference]`) and U3 vs the documents they read
- **Scenario:** In the spine:
  - AD-28 Open still says "goes to `/manage/:reference`" (React Router syntax), while AD-12 now uses `/confirmation/[reference]`.
  - AD-19 covers only "the uvicorn access log". It is silent on the Next.js server and on Caddy's error log; Caddy redacts `Cookie` unless `log_credentials` is set.

  EXPERIENCE.md, which Conventions cite for titles and focus, still says "React SPA" (line 20), "the SPA" (lines 290, 366, 367, 619), "the site is an SPA" (open item 15) and "Route `/confirmation/:reference`" (line 46). Its open item 15 (JavaScript reliance) has changed: server components can now render Landing, Terms and Privacy without JavaScript, but the booking flow still cannot.
- **Fix:**
  - AD-28 Open: "…The frontend then goes to `/manage/[reference]`."
  - AD-19, append: "Caddy's access log stays off and `log_credentials` is never set; the Next.js server logs no request URLs or headers."
  - Raise an EXPERIENCE.md update: replace "React SPA" with "Next.js App Router frontend (AD-17)", "the SPA" with "the frontend", `:reference` with `[reference]`, and restate open item 15 for server-rendered static pages.

### 22. "No rule reads an `X-Forwarded-*` header" makes the later per-source-address limits impossible behind Caddy

- **Severity:** Low (shape-only for FR-34, FR-35, but the spine's own test is "a choice made now would otherwise force a rewrite")
- **Units:** AD-27 Backend side vs FR-34 (resend limit "per source address", If-time 4) and FR-35 (Holds per source address)
- **Scenario:** Behind Caddy, every request reaches uvicorn from the proxy's container address. The only source address is `X-Forwarded-For`, which AD-27 forbids reading. The Deferred entry says only "cannot be tested meaningfully on localhost".
- **Fix:** Deferred, Holds per source address, append: "Behind Caddy the client address exists only in the `X-Forwarded-For` that Caddy sets. The If-time 4/5 story adds one function `api.client_address(request)`, which trusts that header only from the proxy's address (uvicorn `--forwarded-allow-ips` set to the compose network), and amends AD-27's 'No rule reads an `X-Forwarded-*` header' to name that one exception."

### 23. Browser-only state in App Router pages: SSR of `sessionStorage` reads and double effects on `/manage` and Book seats

- **Severity:** Low
- **Units:** U3 (Review restores the draft in a `useState` initializer) vs U2 (client components are still server-rendered); U8 (`/manage` effect) under React StrictMode in dev
- **Scenario:**
  - Client components are still rendered on the Next.js server. Reading `sessionStorage` during render throws there, or, if guarded with `typeof window`, renders a different tree on the server and in the browser, which React reports as a hydration mismatch.
  - In dev, StrictMode runs effects twice. The `/manage` effect's first run calls `history.replaceState` to remove `#t=`, so the second run finds no token and shows "This page is not available" while the first run is still opening the Booking.
  - Book seats' effect sends two `POST /api/session` without a cookie, which creates two anonymous rows.

  None of this shows in compose (production build), so it surfaces as "works in e2e, broken in dev".
- **Fix:** AD-17, add **Browser state:** "`sessionStorage`, `location.hash` and `history` are read only inside effects, never during render; a page that depends on them renders its heading and a neutral placeholder until mounted. The `/manage` page and the session call each read or send once per page instance, guarded by a `useRef`."

### 24. `next build` telemetry and Caddy's trust-store install are outgoing or host-touching actions nobody switched off

- **Severity:** Low (NFR-1 "no external services", FR-21 spirit)
- **Units:** U2 (frontend Dockerfile) vs U7 (Caddy global options)
- **Scenario:** By default, `next build` and `next dev` send anonymous telemetry to Vercel. That happens on the examiner's machine and in every e2e image build. Caddy with `tls internal` tries to install its root into the trust store of the system it runs on. In the container that only logs a warning, but if a developer runs `caddy run` on the host, it prompts to change the host's trust store, which the README calls optional.
- **Fix:**
  - AD-17: "The frontend Dockerfile and the `dev` script set `NEXT_TELEMETRY_DISABLED=1`."
  - AD-27 Local HTTPS: "Global options include `skip_install_trust`; the README's optional import is the only way the root reaches a trust store."

---

## Checked and consistent

These were checked and not raised:

- **Session creation on Book seats.** AD-8 creates the session from the browser only (Book seats, Sign-in, `/manage`). Server components carry no cookie, and Next.js sets none itself, so Landing, Terms and Privacy stay cookie-free (FR-21). Prefetching Book seats runs no effects, so it creates no session.
- **The Manage token.** A URL fragment never reaches Next.js, Caddy or uvicorn. `Referrer-Policy: no-referrer` on every Caddy response covers the Manage HTML.
- **CSRF and `no-referrer`.** `fetch()` is in mode `cors`, so a same-origin `POST` still sends the real `Origin` even under `Referrer-Policy: no-referrer`. A future plain HTML form `POST` would send `Origin: null` and be refused, which is the safe direction.
- **Hypothesis machine.** The AD-26 machine runs in-process against the API layer's database and does not depend on the proxy.
- **FR-11 races.** These stay in the API layer, against real PostgreSQL through the real API process (NFR-6).
- **Time zone data.** `Intl` in Europe/Oslo: `node:24-alpine` ships full ICU.
