---
title: 'Story 3.1: Serve the website and the API over HTTPS only'
type: 'feature'
created: '2026-11-24'
status: 'done'
baseline_commit: 'b6bd445fa0d5c2009b98836ef0a3190e74af5890'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/implementation-artifacts/epic-3-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The compose stack serves the website and the API over plain HTTP on `:8000`, so passwords, session cookies and emailed links travel unencrypted. HTTPS (FR-24) is the last part of the project floor (Core plus HTTPS) and Epic 4 depends on it.

**Approach:** Build Story 3.1 (`.docs/planning-artifacts/epics.md` L1032–1101) in one PR. Switch the three compose mode lines together, publish `HTTPS_PORT`, and let Caddy terminate TLS with its internal CA for `localhost` and add HSTS. Move the e2e fixture to `https://` with Caddy's root, add `test_fr24_https.py` (HT-1 to HT-4), and update the README. The backend already has the config guard, the `Secure` flag that follows `BP_HTTPS` and base-URL links, so it is only verified.

## Boundaries & Constraints

**Always:**
- `docker-compose.yml`: `SITE_ADDRESS: localhost:${HTTPS_PORT:-8443}`, `BP_HTTPS: "on"`, `BP_BASE_URL: https://localhost:${HTTPS_PORT:-8443}`. Publish `127.0.0.1:${HTTPS_PORT:-8443}:${HTTPS_PORT:-8443}` beside the HTTP port. Keep passing `HTTP_PORT`, and add `HSTS_MAX_AGE` only when it is set, by compose interpolation. Healthchecks stay unchanged.
- `Caddyfile`: one `header Strict-Transport-Security "max-age={$HSTS_MAX_AGE:3600}"`, with no `defer`, no `includeSubDomains` and no `preload`. Add no `tls`, `https_port` or `handle_errors`. Keep `skip_install_trust`, `http_port` and `protocols h1 h2`. Keep the Core headers.
- E2e: the fixture copies `/data/caddy/pki/authorities/local/root.crt` through `compose("cp", …)`, retrying until the file exists. It builds one `ssl.SSLContext` from that root and exposes it. `base_url` becomes `https://localhost:<HTTPS_PORT>`. Every e2e `httpx` call passes `verify=` with that context, and every Playwright context sets `ignore_https_errors=True`, including the explicit `browser.new_context` calls. No test writes a literal URL.
- `test_fr24_https.py` follows epics L1080–1086: HT-1 uses a fresh client with `follow_redirects=False` and checks a page path and an `/api` path. HT-2 checks a page, an API 404 envelope, a static file in `frontend/public/` and a 502 while `frontend` is stopped (then `up --wait`), and ignores `Alt-Svc`. HT-3 covers guest and Administrator `Set-Cookie` and checks the session row before and after an HTTP request. HT-4 checks the Outbox links. The AD-19 log search stays green.
- README (Norwegian) follows epics L1095–1101: `https://localhost:8443` everywhere the site is named, the one-time certificate warning, optional root copy and import (undo after grading, a new root after `down -v`) and `curl -i http://localhost:8000/`. It gets a new "Kjente begrensninger" section, an updated "Sikkerhet" section, and HTTPS is removed from "Ikke levert" and the Status line. The config table gains `HTTPS_PORT` and `HSTS_MAX_AGE`.

**Never:** Add Railway/production TLS, a plain-HTTP compose mode, or CSP. Set security headers in the backend or frontend. Read `X-Forwarded-*` in the backend. Change the API-layer test backend (`tests/conftest.py`, which stays `BP_HTTPS: "off"`). Weaken or remove an existing test, beyond the fixture, `verify=` and `ignore_https_errors` changes. Add a dependency.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| HTTP page | `GET http://localhost:<HTTP>/x?y=1` | 308 `Location: https://localhost:<HTTPS>/x?y=1`; no HSTS, Referrer-Policy or Cache-Control | Nothing reaches the backend; DB row counts are unchanged |
| HTTP API with cookie | `POST http://…/api/session` + `bp_session` | Same redirect only | The session row's token hash and expiry are unchanged |
| HTTPS page/API/asset | `GET https://…/`, `/api/nope`, `/favicon…` | HSTS `max-age=3600`; Core headers kept | — |
| Frontend down | `frontend` stopped, `GET https://…/` | Caddy 502 with HSTS | The test restarts it through `up --wait` in `finally` |
| Config guard | `BP_HTTPS=on`, `BP_BASE_URL=http://…` | One-line refusal naming both variables, exit 2 | Already covered by `tests/test_fr14_switches.py:47` |

</frozen-after-approval>

## Code Map

- `Caddyfile` -- 29 lines. Add HSTS after `Referrer-Policy` (L13) and update the comment on L2 ("HTTP now").
- `docker-compose.yml` -- the proxy ports at L11, env at L13–14, backend at L36–37 (marked `# mode`), and the header comments at L1 and L5.
- `src/booking_platform/config.py:73-79` -- guard exists (`ConfigError`, one line); no change.
- `src/booking_platform/api/deps.py:24-30` -- cookie `secure=config.settings().https`; no change.
- `src/booking_platform/services/outbox.py:20-22` -- `link()` = base_url + path; no change.
- `tests/e2e/conftest.py` -- `Stack.base_url` (L55) is the only literal; the env file already writes `HTTPS_PORT`; `compose()` helper.
- `tests/e2e/guest.py:14,16`, `test_fr01_landing.py:193,224`, `test_fr02_book_seats.py:36,45,292,300,341`, `test_fr05_book_and_pay.py:33`, `test_fr15_sign_in.py:59`, `test_fr16_booking_list.py:40,164`, `test_fr23_accessibility.py:41`, `test_stack_routing.py:16` -- bare `httpx` calls that need `verify=`.
- `tests/e2e/a11y.py:161`, `test_fr05:291`, `test_fr11:262`, `test_fr16:71`, `test_fr17:67`, `test_stack_routing.py:52` -- `browser.new_context(...)` calls that need `ignore_https_errors=True`.
- `tests/e2e/admin.py:19-21` -- the DB URL helper, reused for HT-1 and HT-3 row checks.
- `tests/e2e/test_fr21_privacy.py` -- origin compare by `base_url` (L43, 56, 111, 180); the log search is at L184 and after. It should pass unchanged.
- `README.md` -- Status L17, Ikke levert L19–27, Kom i gang L39–49, `localhost:8000` at L83, 97 and 112, config table L160–170, Sikkerhet L175–186.

## Tasks & Acceptance

**Execution:**
- [x] `docker-compose.yml` -- the three mode lines, the HTTPS port and `HSTS_MAX_AGE` pass-through, and the comments -- FR-24 in one place.
- [x] `Caddyfile` -- add the HSTS header and update the comments -- HT-2.
- [x] `tests/e2e/conftest.py` -- root copy with retry, a session-scoped `tls` fixture (`ssl.SSLContext`), `https` `base_url`, and `browser_context_args` with `ignore_https_errors` -- AD-27 Tests.
- [x] the e2e helpers and tests listed in the Code Map -- add `verify=` and `ignore_https_errors`, nothing else -- the no-regression rule.
- [x] `tests/e2e/test_fr02_book_seats.py:251` -- also assert `secure` on the cookie -- HT-3 in the browser.
- [x] `tests/e2e/test_fr24_https.py` -- HT-1 to HT-4 per the matrix -- FR-24.
- [x] `README.md` -- the sections listed in Boundaries -- DR-2.

**Acceptance Criteria:**
- Given a fresh `docker compose up --build --wait`, when the examiner opens `https://localhost:8443`, then the Landing loads after a one-time certificate warning, and `curl -i http://localhost:8000/` shows only the redirect.
- Given `uv run pytest`, when it runs the unit, API and e2e layers, then every test passes, including `test_fr24_https.py` and `test_fr21_privacy.py`.
- Given the diff, when grepped, then no backend or frontend file sets HSTS, and no e2e test contains `http://localhost` or `https://localhost`.

## Implementation Notes

- `HSTS_MAX_AGE` is passed as a bare compose key (`HSTS_MAX_AGE:`), not `${HSTS_MAX_AGE}`: an interpolated empty value reaches Caddy as `HSTS_MAX_AGE=` and yields `max-age=`, while a bare key is omitted from the container when unset (checked with `docker compose config`), so the Caddyfile default 3600 applies.
- New helper `tests/e2e/trust.py` holds the one `ssl.SSLContext`; helpers such as `guest.free_windows` and `today()` get only `base_url` and test modules do not import conftest. The `tls` fixture returns the same object.

## Spec Change Log

## Review Triage Log

| # | Layer | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|---|
| 1 | blind, edge, gap-other | e2e stack inherits a shell `HSTS_MAX_AGE`, so HT-2's fixed `max-age=3600` fails spuriously | low | `compose()` passes `os.environ`; shell values beat `--env-file` for the bare key | patch |
| 2 | gap | HSTS_MAX_AGE override / unset pass-through is untested | low | only the default is asserted; a dropped or `${}`-interpolated key passes every test | patch |
| 3 | blind, edge, gap-other | HT-1 log check claims the frontend; Next.js logs no requests | low | uvicorn's default access log carries the request line with the query, so the backend half is real; the frontend half is vacuous and the comment overstates it | patch |
| 4 | blind, gap-other | `tests/manual/core-accessibility.md:4` still says `http://localhost:8000` | low | file read; now only redirects | patch |
| 5 | blind | `docker-compose.yml:4` says "the only published web port" | low | two ports are published now | patch |
| 6 | blind | README root import/removal gives no commands | low | the copy is given, import and undo are not | patch |
| 7 | blind | README omits Safari HSTS-on-localhost behaviour | maybe-false | needs a current Safari check; if true, harm is ≤1 h (`max-age=3600`) → low | reject |
| 8 | blind | Caddy advertises HTTP/3 `Alt-Svc` on an unpublished UDP port | false | `Caddyfile:9` has `protocols h1 h2`; `curl -skI https://localhost:8443/` shows no `Alt-Svc` | reject |
| 9 | blind | No mixed-content check in the browser layer | low | frontend uses relative URLs; a new request-watching test is more than a direct fix | reject |
| 10 | blind | `verify=trust.context()` repeated instead of the `tls` fixture | false | the spec mandates `verify=` per call; no named harm | reject |
| 11 | blind | 502 test restarts with `up --wait` rather than `start` + `wait()` | false | the frozen intent prescribes `up --wait` | reject |
| 12 | blind | HT-4 regex skips scheme-less links | low | `outbox.link()` always prefixes `base_url`; unlikely, fix adds parsing | reject |
| 13 | blind, edge | `_static_asset()` may pick a dotfile or nothing | false | `frontend/public` holds only `fonts/` and `images/`; first file is a served font | reject |
| 14 | blind | Untested: `127.0.0.1` over HTTP, redirect body | low | `curl http://127.0.0.1:8000/` → 308 to `https://127.0.0.1/`, nothing reaches the app; README says use `localhost`; a fix needs `https_port`, which the spec forbids | reject |
| 15 | blind | Cookie check does not assert no `Domain` | low | backend sets no Domain (`deps.py:24-30`); unlikely, adds assertions beyond the spec | reject |
| 16 | blind | README mixes "kapsel" and "informasjonskapsel" | false | README already used "øktkapselen" (L178) and "kapselen" (L200) before this change | reject |
| 17 | edge | Empty or non-numeric `HSTS_MAX_AGE` gives a malformed header | low | only on deliberate misconfiguration; fix needs a validation guard | reject |
| 18 | edge | `_copy_root` does not catch `TimeoutExpired`, so the stack may stay up | low | `compose cp` would have to hang 900 s; fix adds exception handling | reject |
| 19 | edge | Root CA may exist before the leaf certificate | maybe-false | Caddy issues both at startup and `up --wait` precedes the copy; the full e2e run had no TLS handshake error; would be low | reject |
| 20 | edge | `HTTPS_PORT == HTTP_PORT` gives a bind conflict | low | user misconfiguration that fails loudly | reject |

## Verification

**Commands:**
- `uv run pytest tests --ignore=tests/e2e` -- expected: all pass
- `uv run pytest tests/e2e` -- expected: all pass (Docker running; the dev stack may keep 8000/8443)
- `docker compose up --build --wait; curl.exe -sI http://localhost:8000/; curl.exe -skI https://localhost:8443/` -- expected: 308 with an https `Location` and no HSTS; 200 with HSTS

**Manual checks:**
- Open `https://localhost:8443` in a browser: one certificate warning, then the Landing; sign in as Administrator and open the Outbox, where the links start with `https://localhost:8443`.
