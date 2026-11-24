# Epic 3 Context: Every connection is secure (HTTPS)

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Serve the website and the API over HTTPS only, so that passwords, browser sessions and, later, Manage links never travel unencrypted. Plain HTTP is only ever redirected and never returns or changes data. The examiner can see the redirect, the HSTS header and the cookie attributes for themselves. The Core (Epics 1 and 2) already runs in compose behind Caddy on plain HTTP; this epic switches that stack to HTTPS in one pull request. Finishing it reaches the project's floor (Core plus HTTPS) before the 11 December feature cutoff. Epic 4 depends on it, because Manage links must be `https://` before they are emailed.

## Stories

- Story 3.1: Serve the website and the API over HTTPS only

## Requirements & Constraints

- **HT-1, redirect:** `http://localhost:<HTTP_PORT>/x?y` (a page or an `/api` path) gets Caddy's automatic redirect to `https://localhost:<HTTPS_PORT>/x?y`, with the same path and query. The redirect carries no `Strict-Transport-Security` and none of the site's headers. No request reaches the backend or the frontend, and nothing in the database changes.
- **HT-2, headers:** every HTTPS response carries `Strict-Transport-Security: max-age={$HSTS_MAX_AGE:3600}`, without `includeSubDomains` or `preload`. This covers Next.js pages, API envelopes, static assets and Caddy's own errors (502). The Core headers stay: `Referrer-Policy: no-referrer`, and `Cache-Control: no-store` on `@api`. The backend and the frontend set none of these headers.
- **HT-3, cookies:** every `Set-Cookie` (from `POST /api/session` and Administrator sign-in) has `Secure`, `HttpOnly`, `SameSite=Strict` and `Path=/`. A plain-HTTP request that carries the cookie gets only the redirect, and the session row (token hash and expiry) is unchanged afterwards.
- **HT-4, email links:** every link in every Outbox email is absolute and starts with the configured base URL `https://localhost:<HTTPS_PORT>`.
- **Config guard:** the backend refuses to start when `BP_HTTPS` is on and `BP_BASE_URL` is not `https://`. It prints one line that names both variables. A unit test covers the refusal and a valid `https://` base URL.
- **No regressions:** every Epic 1–2 e2e test passes over HTTPS, changed only to take `base_url` from the fixture. `test_fr21_privacy.py` still finds no third-party request. The log search still finds neither the test password nor any session token.
- **README:** the start section says `docker compose up --build --wait`, then `https://localhost:8443`. It uses `localhost`, not `127.0.0.1`, and says the browser warns once about the certificate. It shows how to copy the root (`docker compose cp proxy:/data/caddy/pki/authorities/local/root.crt .`), says that importing it is optional and should be undone after grading, and says that `down -v` makes a new root. It shows `curl -i http://localhost:8000/` for HT-1. It states the Known limits: browsers still send `Secure` cookies to `http://localhost`, where Caddy only redirects, and Chrome and Firefox ignore HSTS from `localhost`. The security section says HTTPS ends at Caddy, that the backend and the frontend are reachable only on the internal network, that no request goes to a third party, and that production would use a public certificate and one year of HSTS. Every Outbox link and base URL named in the README is `https://localhost:8443`. "Not delivered" no longer lists HTTPS.

## Technical Decisions

- **Caddy is the only public entry and terminates TLS.** Only the proxy publishes web ports, on `127.0.0.1`. `@api path /api /api/*` goes to the backend with the path unchanged, and everything else goes to the frontend. The backend never redirects and reads no `X-Forwarded-*` header.
- **The mode is three compose lines, changed together:** the proxy's `SITE_ADDRESS` becomes `localhost:${HTTPS_PORT:-8443}`, the backend's `BP_HTTPS` becomes `"on"`, and `BP_BASE_URL` becomes `https://localhost:${HTTPS_PORT:-8443}`. Use compose interpolation, never Caddy placeholders, in compose.
- **Ports:** publish `HTTPS_PORT` (8443) and `HTTP_PORT` (8000) each as the same host port, because the redirect and the base URL name the port. The proxy's `environment:` keeps passing `HTTP_PORT` (and `HSTS_MAX_AGE` when set) unchanged, because Caddy reads the container environment. The site answers only for `localhost`.
- **Caddyfile:** no `tls` line, no `https_port` and no `handle_errors`. The `localhost` certificate comes from Caddy's internal CA, and the global options keep `skip_install_trust`, the global `http_port {$HTTP_PORT}` and `servers { protocols h1 h2 }`. HSTS is added by one `header` directive without `defer`. The access log stays off. The named volume `caddy_data` keeps the root across `down`.
- **Healthchecks are unchanged.** The proxy check reads Caddy's admin endpoint on `:2019`, which does not depend on the mode, and `up --build --wait` still waits for all four services.
- **`config.py`** is the only reader of `BP_HTTPS`/`BP_BASE_URL`. The cookie's `Secure` flag follows `BP_HTTPS`. Links are built from the base URL using the constants in `config.links`.
- **E2E fixture (`tests/e2e/conftest.py`):** compose project `booking_e2e` with its own env file (`HTTP_PORT`, `HTTPS_PORT`, `DB_PORT`, `SWITCHES_DIR`). Every compose call goes through the one helper. The fixture copies `/data/caddy/pki/authorities/local/root.crt` out of the proxy, retrying until the file exists, and builds an `ssl.SSLContext` from it. The single `base_url` becomes `https://localhost:<HTTPS_PORT>`. Every HTTP call verifies TLS with that context, and Playwright uses `ignore_https_errors`. No test writes a literal URL. The fixture still seeds rows and moves the clock through `DB_PORT` and ends with `down -v`.
- **`tests/e2e/test_fr24_https.py`** holds HT-1 to HT-4. HT-1 uses a client with no HSTS state. HT-2's 502 case stops `frontend` and restarts it through `up --wait`, and it ignores `Alt-Svc`.
- Files touched: `Caddyfile`, `docker-compose.yml`, `config.py`, the e2e fixture, `test_fr24_https.py`, README.

## Cross-Story Dependencies

- **Depends on Epics 1–2:** the compose stack, the Caddy headers, the sessions and cookies (AD-8), the outbox service, the e2e fixture and helper, `test_fr21_privacy.py` and the README sections it updates.
- **Enables Epic 4:** Manage links (`<BP_BASE_URL>/manage#t=<token>`) must start with `https://`. Later emails also inherit the `https://` base URL.
- **Out of scope:** Railway/production TLS (a plain-HTTP mode that stays untested) and Content-Security-Policy (deferred).
