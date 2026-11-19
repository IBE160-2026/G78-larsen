---
review: tech-currency
target: ARCHITECTURE-SPINE.md, 2026-11-19 amendment for Caddy and Next.js (AD-17, AD-22, AD-27; Conventions Dev proxy, Tests, Styling, Accessibility; Stack; Structural Seed)
reviewed: 2026-11-19
method: Caddy v2.11.9 source read at the release tag (modules/caddyhttp/autohttps.go, server.go, reverseproxy/reverseproxy.go, headers/headers.go, marshalers.go; modules/caddypki/ca.go, certificates.go; modules/caddytls/internalissuer.go; caddyconfig/httpcaddyfile/httptype.go, tlsapp.go; certmagic handshake.go) and caddyserver.com docs (global options, header, log). Next.js v16.4.6 source at the tag (examples/with-docker/Dockerfile, build/utils.ts standalone server template, router-utils/proxy-request.ts, layout-router.tsx, app-router-announcer.tsx) and nextjs.org docs (output, fetch, cacheComponents, generateMetadata, turbopack, allowedDevOrigins, reactStrictMode, environment variables, proxy). Docker docs (compose up). Registries: GitHub releases (Caddy), Docker Hub tags (caddy, node), npm (next, react, react-dom, axe-core), PyPI (playwright, pytest-playwright), nodejs.org/dist/index.json. FastAPI 0.162.0 source in the project venv (openapi/docs.py). No live probe of Caddy or Next.js was possible: the Docker daemon was not running, and downloading and running the Caddy binary was refused by the session's permission policy. Every Caddy finding below therefore rests on the source at the v2.11.9 tag, quoted by file and line.
---

# Review: technology currency of the Caddy and Next.js amendment

## Verdict

**Needs one fix before the FR-24 story; otherwise sound.** The versions are current (Caddy 2.11.9 and `caddy:2.11` from 2026-11-16, Next.js 16.4.6, React 19.3.1, Node 24 and 26 LTS), and most behaviour the spine relies on holds: `localhost` gets Caddy's internal CA, the server sends leaf plus intermediate, `header` set without `defer` reaches proxied responses and Caddy's own 502s, access logs are off without a `log` directive, `cache: 'no-store'` is still the right control in Next 16, and `NEXT_PUBLIC_*` is inlined at build.

One claim is wrong and would fail HT-1 on the first run: with global `https_port 8443`, Caddy's automatic redirect drops the port and sends `http://localhost:8000/x` to `https://localhost/x` (port 443). `https_port` is "for internal use only" in Caddy. The site address must carry the port instead (F-1). Three Medium items follow from the same Caddyfile and from Next 16's build: the e2e stack cannot use other host ports unless Caddy's ports move with them (F-2), the Railway switch as written is a Caddyfile error (F-3), and reading the repo-root `content/` needs more than the Docker build context (F-4).

| Severity | Count |
| --- | --- |
| High | 1 |
| Medium | 3 |
| Low | 8 |
| Info | 6 |

## What was verified (no action needed)

| Claim (spine) | Evidence | Result |
| --- | --- | --- |
| Caddy 2.11.9, image `caddy:2.11` (Stack, AD-27) | GitHub: v2.11.9 published 2026-11-05 (latest; 2.11.8 on 11-04). Docker Hub: `caddy:2.11` and `caddy:2.11.9` updated 2026-11-16. The 2.11.9 breaking changes are in FastCGI and `client_auth`, neither used here | OK |
| Site `localhost` uses the internal CA | `tlsapp.go` and `autohttps.go` (~l.760-780): internal-only names such as `localhost` get an automation policy with the `internal` issuer even without `tls internal`. So `tls internal` is redundant for `localhost` (and harmful in Railway mode, F-3) | OK (see F-3) |
| Root at `/data/caddy/pki/authorities/local/root.crt` in the `caddy_data` volume | `ca.go` l.411-415: storage key `pki/authorities/<id>/root.crt`, CA id `local`; the official image sets `XDG_DATA_HOME=/data`, so storage is `/data/caddy/` | OK |
| Root, intermediate and leaf lifetimes | `ca.go` l.475-476: root `24h × 30 × 12 × 10` = 3600 days (~9.9 years), intermediate 7 days; `internalissuer.go` l.200: leaf 12 h. The global options docs: intermediate "must be less than the lifetime of the root cert (`3600d` or 10 years)", default `7d` | OK (see F-17) |
| Python `ssl` verifying against the root alone | `internalissuer.go` l.118-140 and `ca.go` l.244-250: the leaf is signed by the intermediate signer and the whole returned chain (leaf + intermediate) is PEM-encoded into the certificate Caddy serves. A client that trusts only `root.crt` can therefore build the chain; the short-lived intermediate never needs to be copied. Project Python is 3.12, so 3.13's `VERIFY_X509_STRICT` does not apply yet; the smallstep default root/intermediate templates set CA basic constraints, and Go sets SKI/AKI | OK |
| No name constraints on the root | `certificates.go` l.27: root built from `x509util.DefaultRootTemplate`, no `NameConstraints` set | OK |
| `header` applies to responses from `reverse_proxy` and to Caddy-generated errors | `headers.go` l.91-105: without `defer`/`require` the ops change `w.Header()` at once. `server.go` l.739-792: with no `handle_errors`, Caddy writes the error status on the same writer, so headers set earlier stay on a Caddy 502/504. Deferred ops do not ("deferred changes do not take effect if an error occurs later", `headers.go` l.37). The automatic HTTP→HTTPS redirect is served by a separate server and carries none of them, which is correct (RFC 6797 §7.2: no HSTS over HTTP) | OK (see F-11) |
| Access log off by default | `log` directive docs: "When configured, by default all requests to the site will be logged"; nothing logs access without it. Error logs still exist and include request headers with `Cookie`/`Authorization` redacted unless `log_credentials` is set (`marshalers.go` l.51-54) | OK |
| `{$HSTS_MAX_AGE:3600}` | Caddyfile env placeholder with default, substituted at parse time | OK |
| Next.js 16.4.6, React/React DOM 19.3.1 (Stack) | npm: `next` latest 16.4.6 (2026-11-09), engines `node >=20.9.0`, peer `react ^18.2.0 \|\| ^19.0.0`; `react`/`react-dom` 19.3.1 (2026-10-14) are latest | OK |
| `node:24-alpine`; "24 LTS or 26 LTS" | nodejs.org index: v24.22.3 (Krypton, LTS) and v26.13.1 (Lithium, LTS) on 2026-11-10; Docker Hub `node:24-alpine` updated 2026-11-11 | OK (see F-18) |
| `output: 'standalone'`, `server.js` | Next docs (output): standalone writes `.next/standalone/server.js`; the server reads `PORT` and `HOSTNAME`. Template `build/utils.ts` l.1612-1613: `parseInt(process.env.PORT) \|\| 3000`, `process.env.HOSTNAME \|\| '0.0.0.0'` | OK (see F-6) |
| `cache: 'no-store'` on server GETs | Next 16 fetch docs: default `auto no cache` "will fetch once during `next build` because the route will be statically prerendered"; `no-store` "fetches the resource from the remote server on every request, even if Request-time APIs are not detected". `cacheComponents` is opt-in (top-level flag since 16.0.0). So `no-store` is still the correct control, and it also keeps `next build` from calling the backend | OK (see F-16) |
| `NEXT_PUBLIC_*` is baked at build | Env-vars guide: public variables are inlined "during `next build`" and "will be frozen with the value evaluated at build time". Server-only `API_INTERNAL_URL` is read at request time in dynamic rendering | OK |
| `rewrites` to `http://127.0.0.1:8000` | `proxy-request.ts` l.32-37: Next's rewrite proxy uses `changeOrigin: true` (the backend sees `Host: 127.0.0.1:8000`) and forwards other headers, including `Origin` and `Sec-Fetch-Site`; 30 s proxy timeout. AD-8 never compares with `Host`, so the CSRF rule works in dev | OK (see F-9) |
| `metadata` for titles | generateMetadata docs: `metadata` export in `page.js`/`layout.js`, `title.template` with a required `title.default` | OK (see F-5) |
| Playwright `ignore_https_errors` | Verified in the 2026-11-19 §4.7/§4.8 review (Playwright 1.64.1, Chromium 156, Firefox 157); unchanged in 1.65 | OK |
| `docker compose up --build --wait` | Compose docs: `--wait` "Wait for services to be running\|healthy. Implies detached mode." | OK (see F-7) |
| DB port on `127.0.0.1` only | Compose short syntax `"127.0.0.1:55432:5432"` binds the host side to loopback. The current `docker-compose.yml` still has `"55432:5432"` (all interfaces), so the story must change it | OK (see F-2) |

## Findings

### F-1 [High] `https_port 8443` makes the automatic redirect drop the port

- **Claim (AD-27 Local HTTPS):** "the site is `localhost` with `tls internal`, and Caddy's global `http_port 8000` and `https_port 8443` are published as the same host ports. Caddy's automatic HTTPS redirects every HTTP request on :8000 to `https://localhost:8443` with the same path and query." The Structural Seed and README line repeat it.
- **Evidence:** Caddy 2.11.9 `modules/caddyhttp/autohttps.go`, `makeRedirRoute` (l.544-575):

  ```go
  redirTo := "https://{http.request.host}"
  // ... we can't change the standard HTTPS port externally, so that
  // config parameter is for internal use only ...
  if redirToPort != uint(app.httpPort()) &&
      redirToPort != uint(app.httpsPort()) &&
      redirToPort != DefaultHTTPPort &&
      redirToPort != DefaultHTTPSPort {
      redirTo += ":" + strconv.Itoa(int(redirToPort))
  }
  redirTo += "{http.request.uri}"
  ```

  With site `localhost` and `https_port 8443`, the site listens on 8443, `redirToPort` is 8443 = `httpsPort()`, and no port is appended. `{http.request.host}` is the host without port. So `GET http://localhost:8000/api/x?a=1` gets `308 Location: https://localhost/api/x?a=1`, which goes to port 443, where nothing listens. The global options docs say the same: `https_port` is "for internal use only; does not change the HTTPS port for clients" (likewise `http_port`). HT-1 ("HTTP is redirected to `https://`") would fail, and the README's `curl -i http://localhost:8000/` would show the wrong `Location`. The 308 status and the kept path and query are right.
- **Fix (AD-27 Local HTTPS, Structural Seed):** put the port in the site address and leave `https_port` at its default (443), so 8443 ≠ `httpsPort()` and the port is appended:

  ```caddyfile
  {
  	http_port {$HTTP_PORT:8000}
  	skip_install_trust
  }
  {$SITE_ADDRESS:localhost:8443} {
  	# headers, handle /api/* …, reverse_proxy … (no tls directive, see F-3)
  }
  ```

  Then `http://localhost:8000/x?y` → `308 https://localhost:8443/x?y` (`redirToPort` 8443 differs from 8000, 443 and 80). Reword AD-27: "the site address is `localhost:8443`; the global `http_port 8000` is the redirect listener; `https_port` is not set." HT-1 should assert the exact `Location` (`https://localhost:<port>/path?query`), not only the scheme, and the FR-24 story should run `caddy adapt` once and look at the generated `Location`.

### F-2 [Medium] Host ports must equal Caddy's own ports, so the e2e stack needs them from the environment

- **Claim (AD-27 Tests, Structural Seed):** the e2e fixture runs `docker compose -p booking_e2e … up --build --wait` with "its own project name, host ports and database". AD-27 also says Caddy's ports "are published as the same host ports". The db is `127.0.0.1:55432`.
- **Evidence:** the redirect `Location` is built from Caddy's own listener port (F-1), and the base URL that AD-8's same-origin check and AD-12's links use is `https://localhost:8443`. If the e2e project maps, say, host 18443 → container 8443, every redirect and every email link points at 8443, the dev stack (or nothing). Two projects that publish the same fixed host ports (8000, 8443, 55432) also cannot run at the same time. The current `docker-compose.yml` hard-codes `"55432:5432"` on all interfaces.
- **Fix (AD-27 Entry and Tests, AD-22):** one set of env variables drives both sides of every published port, with the dev values as defaults: `HTTP_PORT`/`HTTPS_PORT` in the Caddyfile (`http_port {$HTTP_PORT:8000}`, site `localhost:{$HTTPS_PORT:8443}`) and in compose (`"${HTTPS_PORT:-8443}:${HTTPS_PORT:-8443}"`, the same for HTTP), `DB_PORT` (`"127.0.0.1:${DB_PORT:-55432}:5432"`), and `BP_BASE_URL=https://localhost:${HTTPS_PORT:-8443}`. The e2e fixture sets all four. Say in AD-27 that a container port always equals its host port.

### F-3 [Medium] The Railway switch as written is a Caddyfile error

- **Claim (AD-27 Railway mode, Deferred):** "environment variables switch the same Caddyfile to plain HTTP on Railway's port, with `BACKEND_UPSTREAM` and `FRONTEND_UPSTREAM` as upstreams", while the site block has `tls internal`.
- **Evidence:** `caddyconfig/httpcaddyfile/httptype.go` l.1186-1190: a site on an HTTP listener that carries TLS connection policies fails with "server listening on … is HTTP, but attempts to configure TLS connection policies". A `tls` directive cannot be switched off by an env variable inside the block. It is not needed locally: `localhost` gets the internal issuer by itself (`tlsapp.go` l.414-494, `autohttps.go` l.760-780). Env placeholders `{$VAR:default}` are substituted once, at parse time, and values are not expanded again, so `SITE_ADDRESS` cannot contain `{$PORT}`.
- **Fix (AD-27):** drop `tls internal` (state that `localhost` uses Caddy's internal CA automatically). Make the address `{$SITE_ADDRESS:localhost:8443}` and the upstreams `{$BACKEND_UPSTREAM:backend:8000}` and `{$FRONTEND_UPSTREAM:frontend:3000}`. Railway sets `SITE_ADDRESS=http://:<port>` with that port also given as `PORT`. Because deployment is Deferred, the spine only needs to fix the shape; when Railway is done, check whether its private network needs the backend and frontend to bind `::` as well as `0.0.0.0`.

### F-4 [Medium] Reading repo-root `content/` needs more than the Docker build context

- **Claim (AD-12 Shared text):** "both the frontend build and `services` read it from there. The frontend image is built with the repository root as its context, so it can read `content/`."
- **Evidence:** the build context only decides which files exist in the builder stage. Next 16 builds with Turbopack, and the turbopack docs say "Files outside of the project root are not resolved". The root is inferred from the lockfile, so it would be `frontend/` (`package-lock.json`). An `import` of `../content/terms-seats.md` fails. A runtime `fs` read from a dynamic route works in dev but not in the standalone image. The output docs say that for tracing "the project directory is used … any files outside of that folder will not be included" unless `outputFileTracingRoot` is set. Setting it to the repo root moves `server.js` to `.next/standalone/frontend/server.js`, and setting `turbopack.root` to the repo root makes Turbopack watch the whole repo (`.venv`, `.git`). The docs warn against "too broad of a root directory".
- **Fix (AD-12):** name one mechanism. The simplest: a `prebuild`/`predev` npm script copies `../content` to `frontend/content/` (git-ignored), and pages read it at build time from server components. In the Dockerfile, `COPY content ./content` sits beside `frontend/`, and `.next/standalone` does not need it when only statically rendered or build-time code reads it. If a dynamic route (for example Review with Seats left) needs the text, either pass it from a static parent or add `outputFileTracingIncludes: {'/*': ['./content/**/*']}`. Add a root `.dockerignore`, or the BuildKit `frontend/Dockerfile.dockerignore`, that keeps `.venv`, `node_modules`, `.git` and `.logs` out of the repo-root context.

### F-5 [Low] `metadata` works only in Server Components, and Next.js does not move focus

- **Claim (Conventions, Accessibility):** "Every route sets its page title through Next.js `metadata` …, then focus moves to the page heading." AD-17 puts every session-bound page in client components; AD-28 makes `/manage` "a client component".
- **Evidence:** generateMetadata docs: "The `metadata` object and `generateMetadata` function exports are **only supported in Server Components**". The recommended pattern is a server `page.js` that exports `metadata` and renders the client component. On navigation Next.js only scrolls: `layout-router.tsx` calls `scrollIntoView()` (l.229, l.254) and never `focus()`. Its route announcer (`app-router-announcer.tsx` l.49-52) reads `document.title`, falling back to the first `h1`, into an `aria-live` region. A `generateMetadata` that awaits data may be streamed into `<body>` after the first UI (Streaming metadata).
- **Fix (Conventions, Accessibility):** "every `page.js` is a Server Component exporting a static `metadata.title` (root layout: `title.template` + `title.default`); client logic lives in a child component. Focus is moved by one client component in the root layout that, on `usePathname()` change, focuses the page's `h1` (`tabIndex={-1}`)." Avoid async `generateMetadata` for titles.

### F-6 [Low] The standalone image needs `HOSTNAME=0.0.0.0` and the static folders copied

- **Claim (AD-17, Structural Seed):** "built with `output: 'standalone'` and run as its own service", "frontend: Next.js standalone :3000 (internal)".
- **Evidence:** the standalone server binds `process.env.HOSTNAME || '0.0.0.0'` (`build/utils.ts` l.1613). Docker sets `HOSTNAME` to the container id in every container, so without an override the server binds only the container's own address. Caddy still reaches it, but a healthcheck on `127.0.0.1:3000` fails (F-7). The output docs: the minimal `server.js` "does not copy the `public` or `.next/static` folders by default". The official `examples/with-docker/Dockerfile` (v16.4.6) sets `ENV PORT=3000`, `ENV HOSTNAME="0.0.0.0"`, copies `public` and `.next/static` next to `server.js`, and runs `USER node`. Without the copy, the self-hosted fonts and images (Styling convention) and every `/_next/static` asset return 404, which also breaks HT-2's "static asset".
- **Fix (AD-17 or Structural Seed):** "the frontend image follows Next's `with-docker` example: `ENV HOSTNAME=0.0.0.0 PORT=3000`, `public/` and `.next/static` copied beside `server.js`, `USER node`, `CMD ["node", "server.js"]`." Optionally add `NEXT_TELEMETRY_DISABLED=1` so `next build` makes no outside call.

### F-7 [Low] `--wait` waits only for the healthchecks that exist

- **Claim (AD-27 Tests):** the fixture runs `up --build --wait` and then copies the root and starts testing. The Tests convention also says "The e2e fixture builds the images with `docker compose build`".
- **Evidence:** compose docs: `--wait` waits for services to be "running\|healthy". A service without a healthcheck counts as ready as soon as it runs, so a backend that is still migrating and seeding, or a Next server that is still starting, passes `--wait`. A container that exits makes `--wait` fail, which is useful.
- **Fix (AD-27 Tests, `docker-compose.yml`):** give every service a healthcheck. db: `pg_isready -U postgres`. backend: `python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"` (no curl in a slim Python image). frontend: `wget -qO- http://127.0.0.1:3000/` (busybox `wget` is in `node:24-alpine`; needs F-6's `HOSTNAME`). proxy: `wget -qO- http://127.0.0.1:2019/config/` (the admin API, on by default inside the container). Use `depends_on: {condition: service_healthy}` for backend → db and proxy → backend/frontend. Drop the separate `docker compose build` from the Tests convention, since `--build` already builds, or say the fixture does one or the other.

### F-8 [Low] The `/manage` fragment exchange runs twice in development

- **Claim (AD-28 Open):** the client route `/manage` "reads `#t=`, removes the fragment with `history.replaceState`, and sends `POST /api/manage/open {token}`".
- **Evidence:** reactStrictMode docs: "Since Next.js 13.5.1, Strict Mode is `true` by default with `app` router". In development React mounts, unmounts and mounts again, so an effect that reads the hash runs twice. The first run removes the fragment, and the second finds none. If "no token" is shown as the not-found state, `next dev` shows an error for every valid link. A client component is also prerendered on the server, where `window` does not exist, so the hash can only be read in an effect.
- **Fix (AD-28 Open):** "read `location.hash` inside `useEffect`, once, guarded by a `useRef` flag (refs survive Strict Mode's re-mount), and only then call `replaceState` and `POST`."

### F-9 [Low] `next dev` must be started on `127.0.0.1`, or Next 16 blocks its own dev assets

- **Claim (AD-17 Dev, Conventions Dev proxy, Structural Seed):** "`next dev` on `127.0.0.1:3000`", entry `http://127.0.0.1:3000`, via `npm --prefix frontend run dev`.
- **Evidence:** allowedDevOrigins docs: "Next.js blocks cross-origin requests to dev-only assets and endpoints during development by default". The server allows "`localhost`, its subdomains, and the hostname it was started with". Opening `http://127.0.0.1:3000` against a server started with the default host breaks HMR and dev endpoints.
- **Fix (Conventions, Dev proxy):** "the `dev` script is `next dev -H 127.0.0.1 -p 3000`; the rewrite exists only when `phase === PHASE_DEVELOPMENT_SERVER` (`next.config.js` exports a function of `phase`)". That makes "in development only" mechanical, and nothing about it ends up in the standalone `routes-manifest`.

### F-10 [Low] `/docs` through Caddy loads Swagger UI from a CDN

- **Claim (AD-27 Entry, AD-17 One origin):** Caddy routes `/docs` and `/openapi.json` to the backend; "No page or server call talks to any other origin (FR-21)".
- **Evidence:** FastAPI 0.162.0 `fastapi/openapi/docs.py` l.79, l.92, l.100: the default Swagger UI page loads `https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js`, its CSS, and a favicon from `fastapi.tiangolo.com`. `/docs` is a page on the platform origin that talks to two other origins.
- **Fix (AD-27 Entry):** leave `/docs` out of the Caddy routes (the developer reaches it on `127.0.0.1:8000` in dev). Alternatively, serve Swagger UI from self-hosted files (`swagger_js_url`/`swagger_css_url`), listed in `ASSETS.md`. `/openapi.json` alone is harmless.

### F-11 [Low] The headers must stay immediate; `defer` loses them on Caddy errors, and immediate ones duplicate an upstream value

- **Claim (AD-27 Headers):** "Caddy adds to every response from either service, error responses included … The backend and the frontend set none of these themselves."
- **Evidence:** the claim holds only if the header ops are immediate (see the verified table). The `header` docs' own proxy example says "enabling `defer` is necessary to ensure the header is set *after* the proxy writes its headers", and `>`, `-`, `?` and the `match` subdirective turn `defer` on. Deferred ops are not applied when Caddy itself produces the error (`headers.go` l.37). Immediate ops have their own trap: `reverseproxy.go` l.1341 copies upstream headers with `copyHeader` → `dst.Add`, so a header that both Caddy and the upstream set appears twice (for example two `Cache-Control` lines on `/api/*` if the backend ever sets one).
- **Fix (AD-27 Headers):** "header ops are plain `header <field> <value>` (no `defer`, `>`, `-`, `?` or `match`), so they also reach Caddy's 502/504; because they are added before the proxy, the backend and the frontend never set these fields." HT-2 can assert exactly one value of each field, and add a request with the frontend stopped to cover a Caddy-generated 502.

### F-12 [Low] Stack: two newer patch/minor releases

- **Claim (Stack):** `pytest-playwright / playwright` 0.10.0 / 1.64.1; `axe-core` 4.14.0.
- **Evidence:** PyPI: `playwright` 1.65.2 uploaded 2026-11-14 (pytest-playwright 0.10.0 needs `playwright>=1.18`, still latest). npm: `axe-core` 4.14.1 (changelog 2026-11-12, published 2026-11-16), bug fixes only (`aria-valid-attr-value`, `target-size`, `heading-order` among them). Neither is in `uv.lock` or a `package-lock.json` yet.
- **Fix (Stack):** list `playwright 1.65.2` and `axe-core 4.14.1` or write "latest at lock time", as for hypothesis.

### F-13 [Info] Non-`localhost` hosts fail in the browser, not with a page

- **Claim (AD-27 One origin):** "only `localhost` is served".
- **Evidence:** `https://127.0.0.1:8443`: browsers send no SNI for an IP. certmagic then looks up the connection's local IP (`handshake.go` l.941), which in the container is the bridge address, finds nothing and fails the handshake ("no certificate available"), so the browser shows a TLS protocol error. `http://127.0.0.1:8000`: Caddy appends a catch-all redirect without a Host matcher (`autohttps.go` l.401-403) to `https://127.0.0.1` on `https_port`, so 443 after F-1, which is refused. Over TLS with SNI `localhost` but another `Host` header, no route matches and Caddy answers an empty 200 without the AD-27 headers. Browsers never do that.
- **Fix (README):** say "use `localhost`, not `127.0.0.1`". Optionally add `http://127.0.0.1:{$HTTP_PORT:8000} { redir https://localhost:{$HTTPS_PORT:8443}{uri} 308 }`.

### F-14 [Info] `skip_install_trust` keeps Caddy out of the container's trust store

- **Evidence:** global options: `skip_install_trust` "Skips the attempts to install the local CA's root into the system trust store". Without it, Caddy tries at first start inside the container (`pki.go` l.94). This is noise at best, and it has no value since the browser runs on the host.
- **Fix:** add `skip_install_trust` to the global block (it is in the F-1 sketch).

### F-15 [Info] HTTP/3 is advertised on a UDP port compose does not publish

- **Evidence:** Caddy serves h1, h2 and h3 by default and sends `Alt-Svc: h3=":8443"`. Compose publishes `8443` as TCP only, so browsers try QUIC, time out and fall back.
- **Fix:** either publish `"${HTTPS_PORT}:${HTTPS_PORT}/udp"`, or set `servers { protocols h1 h2 }` in the global block. Either way, HT-2 should ignore `Alt-Svc`.

### F-16 [Info] State that `cacheComponents` stays off

- **Evidence:** the `no-store` rule is right under Next 16's default (verified table). With `cacheComponents: true`, data is "dynamic by default". An uncached fetch outside `<Suspense>` then becomes a build error, and the route segment configs change. In development, the HMR cache also serves `no-store` fetches across hot reloads (fetch docs, Troubleshooting), so Seats left can look stale after an edit until a reload.
- **Fix (AD-17 Server calls):** add "`cacheComponents` is not enabled". `server-api.js` may also `await connection()` before its first read, which the env-vars guide gives as the request-time marker.

### F-17 [Info] Wiping `caddy_data` makes a new root

- **Evidence:** the root lives only in the `caddy_data` volume (3600 days). `docker compose down -v` deletes it, and the next start generates a new root, so a previously imported root no longer matches and the browser warns again.
- **Fix (README):** one line: "after `docker compose down -v`, copy and import the root again (or remove the old one)".

### F-18 [Info] Next 16 terminology: `proxy.js` (formerly middleware) and Server Functions

- **Evidence:** the proxy docs: "The `middleware` file convention is deprecated and has been renamed to `proxy`" (v16.0.0). The docs also call Server Actions "Server Functions". Node 26 is now LTS (Lithium), and Node 24 has gone from active to maintenance LTS. `node:24-alpine` is still supported until 2028.
- **Fix (AD-17 Framework):** "There are no Route Handlers, Server Functions (Server Actions) or `proxy.js` (formerly middleware)". This also avoids two things called "proxy" in one spine.

## Not checked live

The Docker daemon was not running and the session would not allow downloading and running the Caddy binary, so F-1, F-3 and F-13 rest on reading the v2.11.9 source, not on a probe. The first FR-24 story should confirm F-1 with `caddy adapt --config Caddyfile` and one `curl -si http://localhost:8000/x?y=1` against the stack before writing HT-1.
