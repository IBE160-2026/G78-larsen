---
review: tech-currency
target: ARCHITECTURE-SPINE.md, uncommitted diff of 2026-11-19 (fixes from validate-caddy-next-2026-11-19): AD-10, AD-14, AD-17, AD-18, AD-19, AD-22, AD-27; Conventions Styling, Accessibility, Tests; Stack; Structural Seed; Deferred
reviewed: 2026-11-19
method: FastAPI 0.162.0 and Starlette 1.10.0 source in the project venv (fastapi/applications.py, fastapi/routing.py `_IncludedRouter`, starlette/routing.py), plus two TestClient probes run with the venv's Python (redirect_slashes on app vs router; which HTTPException handler catches router 404s). Caddy v2.11.9 source at the tag (caddyconfig/caddyfile/parse.go `replaceEnvVars`; modules/caddyhttp/app.go `Start`; server.go `ServeHTTP`) and caddyserver.com docs (request matchers). caddy-docker `2.11/alpine/Dockerfile`; docker-library `python 3.12/slim-trixie/Dockerfile`; nodejs/docker-node `24/alpine3.24/Dockerfile`. Docker docs (compose interpolation, services volumes and depends_on, up, down, restart, stop, build context) and docker/compose source (pkg/compose/stop.go, restart.go). Next.js docs (error.js, not-found.js, telemetry) and Next.js v16.4.6 source (telemetry/storage.ts, cli/next-dev.ts, create-next-app templates via the GitHub API). react.dev (hydrateRoot). uv docs (Docker guide), GitHub tags and releases for astral-sh/uv, ghcr.io package page. npm registry (axe-core). Versions already verified in review-tech-currency-caddy-next-2026-11-19.md (Caddy 2.11.9, Next 16.4.6, React 19.3.1, Node 24/26, Playwright) were not re-checked. No live probe of Caddy, compose or Next.js: the Docker daemon was not running and `frontend/` does not exist yet.
---

# Review: technology currency of the validate fixes

## Verdict

**Sound; one Medium fix before the FR-24 story, the rest is wording.** The new claims hold against the source and docs: `redirect_slashes=False` on the app stops every slash redirect (probed), `{$SITE_ADDRESS:http://localhost:8000}` is a valid default (split on the first colon), `protocols h1 h2` stops both HTTP/3 and `Alt-Svc`, the compose interpolation, bind-mount, `--wait`, `restart`, `stop` and `down -v` semantics are as described, `global-error.js` must bring its own `<html>`, `<body>` and styles, and axe-core 4.14.1 is the npm `latest`.

The one Medium item: the proxy healthcheck "busybox `wget` on its own site address" fails once the site is `https://localhost:8443`, because Alpine's busybox wget verifies certificates and the container does not trust Caddy's internal root (`skip_install_trust`). `up --wait` would then fail in the FR-24 story (F-1). The Low items are a missing exception-handler detail for the JSON 404 (F-2), the Caddyfile matcher syntax (F-3, F-4), a compose variable that must be passed into the proxy container (F-5), and three toolchain details (F-6 to F-8).

| Severity | Count |
| --- | --- |
| High | 0 |
| Medium | 1 |
| Low | 7 |
| Info | 5 |

## What was verified (no action needed)

| Claim (spine) | Evidence | Result |
| --- | --- | --- |
| `redirect_slashes=False` exists on the app and on `APIRouter` (AD-10) | `fastapi/applications.py` l.396 and `fastapi/routing.py` l.2447 both take it; the app passes it to its root `APIRouter` (applications.py l.983). The redirect branch is in `APIRouter.app` (routing.py l.2828) | OK |
| Setting it on the app is enough; a slash variant is a 404 | Probe (FastAPI 0.162.0, Starlette 1.10.0): app `True`, router `False` → `/api/admin/bookings/` 307, `/api/health/` 307; app `False`, router `True` → all 404. Included routers are `_IncludedRouter` wrappers (routing.py l.1645) that only report a match; the redirect check runs only in the top router. The router-level flag has no effect (F-12) | OK |
| The backend never builds an absolute URL from the request | The only place that does is the slash redirect (`RedirectResponse(url=str(URL(scope=redirect_scope)))`, routing.py ~l.2855), which `redirect_slashes=False` removes | OK |
| `docs_url=None`, `openapi_url=None` turn off `/docs` and `/openapi.json` | Probe: `/docs`, `/openapi.json` and `/redoc` all 404 | OK |
| `{$SITE_ADDRESS:http://localhost:8000}` and `{$HTTP_PORT:8000}` | `parse.go` `replaceEnvVars` (~l.66-105): `strings.SplitN(envString, ":", 2)`, so a default may contain colons; runs on the raw bytes before tokenizing, so it works in site addresses. Default applies only when the variable is **unset** (`!found`); set-but-empty gives an empty value. Compose always sets `SITE_ADDRESS`, so this does not bite | OK |
| `path /api /api/*` matches `/api` and `/api/x` but not `/apix` | Matcher docs: "Path matching is an exact match by default", "`/foo/*` will not match `/foo` or `/foobar`", multiple paths are OR'ed, matching is case-insensitive | OK (syntax: F-3) |
| `servers { protocols h1 h2 }` stops HTTP/3 and `Alt-Svc` | `app.go` `Start`: HTTP/3 starts only when `h3ok := protocolsUnique["h3"]` and TLS is on. `server.go` ~l.355: `Alt-Svc` is set only `if s.h3server != nil`. Default list is `h1 h2 h3` | OK |
| `header` without `defer` reaches Caddy's 502; the HTTP→HTTPS redirect is served apart from the site and carries no HSTS | Verified at the tag in the earlier review (headers.go l.91-105, server.go l.739-792, autohttps.go). Stopping `frontend` makes the upstream unresolvable, which `reverse_proxy` answers with 502 | OK (see F-9) |
| Access log off; `log_credentials` unset keeps `Cookie`, `Set-Cookie`, `Authorization` redacted in error logs | Verified in the earlier review (`marshalers.go` l.51-54, `log` directive docs) | OK |
| busybox `wget` in `caddy:2.11` | caddy-docker `2.11/alpine/Dockerfile`: `FROM alpine:3.24`, `apk add ca-certificates curl libcap mailcap`. Busybox `wget` and also `curl` are present. `ENV XDG_DATA_HOME=/data`; the Dockerfile declares no `VOLUME`, so the named volume `caddy_data` is what keeps the root across recreation | OK (see F-1) |
| `/data` holds the CA; `down` keeps it, `down -v` removes it | Earlier review (`ca.go` l.411-415). `down` docs: by default removes containers and networks; `-v` "Remove named volumes declared in the volumes section … and anonymous volumes". Named volumes are prefixed by the project, so `booking_e2e` has its own `caddy_data` | OK |
| `${VAR:-default}` in `environment` and in bind-mount sources | Interpolation docs: "any values in a Compose file can be interpolated"; `:-` uses the default when unset **or empty** | OK |
| `${SWITCHES_DIR:-./config}` mounted read-only as a directory | Services docs: relative paths resolve from the compose file's directory; short syntax "creates a directory at the source path on the host if it doesn't exist" (so a missing `config/` would be created, not fail; see F-13). Mounting the directory rather than the file means a rewritten file is seen after a restart | OK |
| `docker compose -p booking_e2e restart backend` re-reads the switch file; then wait for health | restart docs: changes to compose config and environment "are not updated after restarting" (the mount stays, the file content is new, which is what is wanted). No `--wait` option, so the fixture must poll, as the spine says. `restart.go`: dependents are included only via `depends_on … restart: true`, which the spine does not use | OK |
| HT-2 stops `frontend` for a Caddy 502 | `stop.go`: only the named services are stopped, not their dependents, so the proxy stays up | OK |
| `docker compose up -d --wait db` is a no-op when db already runs | up docs: `--wait` "Wait for services to be running\|healthy. Implies detached mode"; existing containers are recreated only when their config or image changed | OK |
| `.dockerignore` `**/node_modules`, `**/.next` | Build-context docs: "`**` … matches any number of directories (including zero)". A bare `.venv` matches only at the root, which is where it is | OK |
| `python:3.12-slim` has no curl or wget; the healthcheck uses `urllib.request` | docker-library `3.12/slim-trixie/Dockerfile`: runtime installs only `ca-certificates netbase tzdata`; `wget` is a build dependency removed by `apt-mark auto` + `purge --auto-remove` | OK |
| `node:24-alpine` has busybox `wget` | docker-node `24/alpine3.24/Dockerfile`: `FROM alpine:3.24`; every `apk del` removes only `.build-deps*` groups, never busybox | OK (see F-7) |
| `app/global-error.js` must include `<html>`/`<body>` and import its own CSS | error.js docs (lastUpdated 2026-10-15): "Global error UI must define its own `<html>` and `<body>` tags, global styles, fonts, or other dependencies"; "global-error and the built-in 500 page … do not include your global styles". Also shown in development since v15.2.0 | OK (see F-11) |
| `app/error.js` and `app/not-found.js` | error.js must be a Client Component; it does not wrap the root layout ("use global-error.js"). Since v16.3.0 the stable prop is `retry` (`reset` still exists). not-found docs: the root `app/not-found.js` "handle[s] any unmatched URLs for your whole application"; `global-not-found.js` is only needed for several root layouts | OK |
| Next.js's route announcer stays | Earlier review (`app-router-announcer.tsx`); the accessibility docs still list `document.title`, then `h1`, then pathname. No documented switch to turn it off, so keeping it and testing for double announcements is the right call | OK |
| Browser state read only in effects | react.dev hydrateRoot, "Handling different client and server content": two-pass render with state set in `useEffect`; browser-only APIs in render are a listed cause of mismatches | OK |
| create-next-app scaffold assets | create-next-app v16.4.6 `templates/app/js`: `app/favicon.ico`, `app/globals.css`, `app/page.module.css`, and `public/` with `file.svg`, `globe.svg`, `next.svg`, `vercel.svg`, `window.svg`. No `app/icon.*` (harmless to list) | OK (see F-10) |
| `COPY --from=ghcr.io/astral-sh/uv:<ver> /uv /uvx /bin/` | uv Docker guide: exactly this pattern, and "it is best practice to pin to a specific uv version" | OK (see F-8) |
| axe-core 4.14.1 | npm `axe-core/latest` → 4.14.1 | OK |

## Findings

### F-1 [Medium] The proxy healthcheck with busybox `wget` fails once the site is HTTPS

- **Claim (AD-27 Startup):** "proxy `wget` on its own site address", unchanged across the FR-24 switch; `skip_install_trust` is set (AD-27 Modes).
- **Evidence:** from FR-24 the site address is `localhost:8443`, so the check fetches `https://localhost:8443/` (or `http://localhost:8000/`, which redirects there and busybox `wget` follows). Alpine's busybox `wget` verifies certificates through `ssl_client` since busybox 1.28.3-r2 (CVE-2018-1000500 fix). Caddy's internal root is not in the container's trust store, because `skip_install_trust` stops Caddy installing it. The check fails, the proxy never becomes healthy, and `up --build --wait` fails in the FR-24 story. Not probed live (no Docker daemon).
- **Fix (AD-27 Startup):** make the check independent of the mode and of trust. The `caddy:2.11` image also ships `curl`, so either `curl -fsS -o /dev/null http://localhost:${HTTP_PORT}/` without `-L` (200 in the Core, 308 from FR-24; `-f` fails only on ≥ 400), or, to check the HTTPS site itself, `curl -fsS --cacert /data/caddy/pki/authorities/local/root.crt https://localhost:${HTTPS_PORT}/`, which is a fourth line to switch in FR-24. The first keeps the "three compose lines" rule.

### F-2 [Low] The JSON 404 for unknown paths needs a handler on Starlette's `HTTPException`

- **Claim (AD-10):** "Any unknown `/api` or `/api/*` path returns the JSON 404 envelope … a slash variant is the JSON 404." Conventions: envelope `{"detail": {"error": "<code>", …}}`.
- **Evidence:** probe: a handler registered for `fastapi.HTTPException` does not see router 404/405s; they return `{"detail":"Not Found"}`, which has no `error` key. A handler for `starlette.exceptions.HTTPException` catches them (`/api`, `/api/x`, `/api/health/` → `{"detail":{"error":"not_found"}}`; it also catches 405). The current `src/booking_platform/app.py` registers no such handler.
- **Fix (AD-10):** add "one exception handler on `starlette.exceptions.HTTPException` turns router 404 and 405 into the envelope (`not_found`, `method_not_allowed`)", and let the `/api` and `/api/x` e2e test assert the `error` key.

### F-3 [Low] `handle` takes one inline path; two paths need a named matcher

- **Claim (AD-27 Entry):** "One `handle` with the matcher `path /api /api/*`".
- **Evidence:** matcher docs: the inline form is a single path token that starts with `/`; every multi-path example uses a named matcher (`@assets path /js/* /css/*`). `handle path /api /api/*` is not valid syntax.
- **Fix (AD-27 Entry):** "`@api path /api /api/*` and one `handle @api`". The path matcher is case-insensitive, so `/API/x` also reaches the backend, which is harmless.

### F-4 [Low] `Cache-Control: no-store` covers `/api/*` but not the bare `/api` the backend now answers

- **Claim (AD-27 Headers):** "`Cache-Control: no-store` on `/api/*`", while Entry now routes `/api` and `/api/*`.
- **Evidence:** `/api/*` does not match `/api` (matcher docs). The bare `/api` 404 envelope would go out without `no-store`.
- **Fix (AD-27 Headers):** apply the header with the same `@api` matcher as the route (F-3), and include `/api` in HT-2's header assertions.

### F-5 [Low] Compose must pass the port variables into the proxy container

- **Claim (AD-27 Ports, Modes):** "`HTTP_PORT` … come from the environment with those defaults, in both the Caddyfile and compose"; "an env file (e2e) therefore sets only ports, the database and `SWITCHES_DIR`"; the Caddyfile reads `http_port {$HTTP_PORT:8000}`.
- **Evidence:** interpolation docs: substitution from `.env` / `--env-file` "is a Docker Compose CLI feature"; values reach a container only through `environment` (or `env_file`). Without it, the e2e proxy keeps `http_port 8000` while compose publishes the e2e port, and HT-1's `Location` names the wrong port.
- **Fix (AD-27 Ports):** "the proxy's `environment` lists `HTTP_PORT: ${HTTP_PORT:-8000}` (and `HSTS_MAX_AGE` if used); `SITE_ADDRESS` already carries the HTTPS port."

### F-6 [Low] How `next dev` sets `NEXT_TELEMETRY_DISABLED` is not said, and the POSIX form fails on Windows

- **Claim (AD-17 One origin):** "Builds and `next dev` set `NEXT_TELEMETRY_DISABLED=1`."
- **Evidence:** Next v16.4.6 `telemetry/storage.ts` ~l.70 reads `process.env.NEXT_TELEMETRY_DISABLED` once, in the `Telemetry` constructor; `cli/next-dev.ts` builds one in the parent CLI process (~l.188), which takes `initialEnv`, so a `.env` file is not a reliable switch for it. npm runs scripts with `cmd.exe` on Windows, where `"dev": "NEXT_TELEMETRY_DISABLED=1 next dev …"` is an error. The Dockerfile `ENV` is fine for builds.
- **Fix (AD-17):** name the mechanism, for example a two-line `frontend/scripts/dev.mjs` that sets `process.env.NEXT_TELEMETRY_DISABLED = '1'` and spawns `next dev -H 127.0.0.1`, or `cross-env` as a dev dependency. `next telemetry disable` is per machine and does not cover the examiner.

### F-7 [Low] The frontend healthcheck should name `127.0.0.1`, not `localhost`

- **Claim (AD-27 Startup):** "frontend busybox `wget -q --spider` on a route that calls no API".
- **Evidence:** the standalone server binds `HOSTNAME=0.0.0.0` (IPv4 only, earlier review F-6). Docker's `/etc/hosts` also maps `localhost` to `::1`, and busybox `wget` does not fall back to the next address, so `http://localhost:3000/` can get "connection refused". Not probed live.
- **Fix (AD-27 Startup):** `wget -q --spider http://127.0.0.1:3000/<route>`. The proxy check (F-1) can keep `localhost`, because Caddy listens on all interfaces and the site needs `Host: localhost`.

### F-8 [Low] "The pinned 0.12.x" names no tag, and uv 0.13 is current

- **Claim (Stack):** "Backend image `python:3.12-slim`, with uv copied from `ghcr.io/astral-sh/uv` at the pinned 0.12.x"; uv / uv_build 0.12.x.
- **Evidence:** GitHub tags: the 0.12 line ends at `0.12.24`; `0.13.0` follows, and `0.13.9` (2026-11-17) is latest on PyPI and in the uv Docker guide's examples. The local uv is 0.12.6, and `pyproject.toml` pins `uv_build>=0.12.6,<0.13.0`. The ghcr.io package page lists 136 pages of tags; the 0.12 tags were not on the first page, so their presence rests on uv publishing one image per release.
- **Fix (Stack):** write the exact tag, for example `ghcr.io/astral-sh/uv:0.12.24` (or the local 0.12.6), and note "0.13.9 out on 2026-11-19; move together with `uv_build` when the lockfile is next updated", as for Playwright.

### F-9 [Info] The automatic redirect also carries `Server: Caddy`

- **Claim (AD-27 Headers):** the redirect "carries only `Location`".
- **Evidence:** `server.go` `ServeHTTP` sets `h["Server"] = serverHeader` ("Caddy") on every response, the redirect server included; Go adds `Date` and `Content-Length`.
- **Fix:** say "carries `Location` and none of the site's headers"; HT-1 asserts the absence of `Strict-Transport-Security`, not an exact header set.

### F-10 [Info] The scaffold also brings `page.module.css` and `globals.css`

- **Evidence:** the `app` template adds `app/page.module.css` (a CSS Module, which the Styling convention forbids) and `app/globals.css` (the convention's file is `styles.css`). The `--empty` template (`app-empty`) has no `public/` folder at all.
- **Fix (AD-17 Scaffold assets):** add those two files to the delete list, or scaffold with `create-next-app --empty`.

### F-11 [Info] `global-error.js` cannot export `metadata`

- **Evidence:** error.js docs: "`metadata` and `generateMetadata` exports are not supported in `global-error.jsx`. As an alternative, you can use the React `<title>` component." It is also shown in development since v15.2.0, and `retry` is the stable prop since v16.3.0.
- **Fix:** if the "please try again" page needs a title, render `<title>` inside it.

### F-12 [Info] The router-level `redirect_slashes=False` is redundant

- **Evidence:** probe in the verified table: only the app's flag has any effect in FastAPI 0.162.0.
- **Fix:** none required; "The app sets `redirect_slashes=False`" is enough and avoids a rule the code cannot check.

### F-13 [Info] `config/` does not exist yet

- **Evidence:** the repository has no `config/` folder today. If compose ran before the example is committed, the short bind syntax would create an empty `config/` on the host rather than fail.
- **Fix:** the skeleton story commits `config/test-switches.example.toml` in the same PR that adds the mount.

## Not checked live

The Docker daemon was not running and `frontend/` does not exist, so F-1, F-7 and the Caddy items rest on source and docs, not on a probe. The FastAPI items (F-2, F-12, the verified rows) were probed with TestClient in the project venv. The FR-24 story should run the proxy healthcheck once by hand (`docker compose exec proxy …`) before relying on `up --wait`.
