---
review: tech-currency
target: ARCHITECTURE-SPINE.md, 2026-11-19 amendment for §4.7 and §4.8 (AD-27 HTTPS, and the technical claims in AD-8, AD-12, AD-22, AD-28 and AD-30, plus the Stack row `cryptography`)
reviewed: 2026-11-19
method: PyPI JSON API; RFC 6797 (HSTS), RFC 9110 (308); chromestatus API; blink-dev and WebKit Bugzilla; Crockford's spec; PostgreSQL 18 docs; NIST SP 800-63B-4; Apple TLS requirements. Probes ran in a throwaway venv in the session scratchpad, never in the repo: cryptography 50.0.2, uvicorn 0.54.0, FastAPI 0.162.0, Starlette 1.10.0, httpx 0.28.1, requests 2.34.2 and Playwright 1.64.1 with its own Chromium 156.0.8078.4 and Firefox 157.0, on Python 3.12.14 with OpenSSL 3.5.8 under Windows 11. `uv pip compile` was run for the full stack. No PostgreSQL probe was possible because Docker was not running; the PG items rest on the PG 18 docs.
---

# Review: technology currency of the §4.7/§4.8 amendment

## Verdict

**Sound.** The amendment can stand with small additions to AD-27, and nothing is High. Every library claim held up. cryptography 50.0.2 is current and builds the CA and leaf on Windows/3.12. Two `uvicorn.Server`s share one loop and stop together on Ctrl+C. Playwright's `ignore_https_errors` works. The 308, token, Crockford and PostgreSQL claims are correct.

The weak points are things AD-27 leaves unsaid, and real Windows behaviour exposes them. The worst ones:

- a ~2 s penalty on every new Python connection to `https://localhost` when the server listens on IPv4 only;
- untidy startup failure when a port is taken;
- no certificate profile, so Python 3.13+ (`VERIFY_X509_STRICT`) and Safari/macOS reject a minimal cert;
- a CA key that can mint certificates for any site once the examiner imports the CA.

The HSTS rationale is out of date. Chrome since M132 and Firefox ignore HSTS from `localhost` altogether. This harms nothing, but the text should say so.

| Severity | Count |
| --- | --- |
| High | 0 |
| Medium | 4 |
| Low | 8 |
| Info | 1 |

## What was verified (no action needed)

| Claim (spine) | Evidence | Result |
| --- | --- | --- |
| cryptography 50.0.2 is latest on 2026-11-19 (Stack) | PyPI: 50.0.2 uploaded 2026-09-30. Earlier releases were 50.0.1 (08-25) and 50.0.0 (07-31). Windows wheels include `cp311-abi3-win_amd64`, which covers 3.12. Its only dependency is `cffi>=2.0.0`, which argon2-cffi already brings in | OK |
| It resolves with the rest of the Stack | `uv pip compile` for py3.12/windows of the whole Stack plus cryptography 50.0.2 resolves. It adds only `cffi 2.1.1` and `pycparser 3.12` | OK |
| `tls.py` can build a local CA and a leaf for `localhost`, `127.0.0.1`, `::1`, valid 365 days | Probe `mkcerts.py`, with ECDSA P-256 and with RSA-2048. It runs with `-W error`, so no deprecation warnings. The leaf's `not_valid_after_utc` is 2027-11-19 and its SAN holds all three names | OK |
| HTTP clients verify against the run's `ca.pem` | On Python 3.12, `httpx` (ssl context), `requests` (`verify=path`) and `urllib` (`create_default_context(cafile=)`) all return 200 against a CA-signed leaf. Without the CA they fail with `CERTIFICATE_VERIFY_FAILED` | OK (see F-3, F-7) |
| Two `uvicorn.Server`s in one event loop, one with `ssl_certfile`/`ssl_keyfile` and one plain | Probe `serve2.py`, `asyncio.gather(s_https.serve(), s_http.serve())`, works. Each `serve()` installs its handler with `signal.signal`, restores the previous one on exit, and re-raises captured signals (uvicorn 0.54.0 `server.py` `capture_signals`). A simulated Ctrl+C reached the second server, cascaded to the first, and both stopped (`gather ended after 2.3s; https.should_exit=True http.should_exit=True`) | OK (see F-2) |
| The redirect listener answers `308` to base URL + path + query | Probe: `POST http://127.0.0.1:18000/api/x?a=1` → `308 https://localhost:18443/api/x?a=1`, empty body. httpx and requests follow it as **POST** with the body (RFC 9110 §15.4.9 and RFC 7538: the method is not changed) | OK |
| HSTS is ignored over HTTP, so it belongs only on the TLS app | RFC 6797 §8.1: "If an HTTP response is received over insecure transport, the UA MUST ignore any present STS header field(s)". §7.2: a host "MUST NOT include the STS header field in HTTP responses conveyed over non-secure transport". AD-27 puts the middleware on the app only, which is right | OK |
| HSTS is ignored when there are certificate errors | RFC 6797 §8.1 notes a host only if "there are no underlying secure transport errors or warnings". Probe: with `ignore_https_errors=True`, Chromium 156 and Firefox 157 did **not** upgrade `http://hsts.test:18050` after a `max-age=3600` response from `https://hsts.test:18450` | OK |
| HSTS is per host, not per port | RFC 6797 §8.3: a non-80 port "MUST be preserved". Probe (control): Chromium trusting the leaf via `--ignore-certificate-errors-spki-list` went from `http://hsts.test:18050/probe` to `https://hsts.test:18050/probe` (`ERR_SSL_PROTOCOL_ERROR`; uvicorn logged "Invalid HTTP request received") | OK (see F-5) |
| Browsers ignore HSTS for IP literals | RFC 6797 §8.1.1: the UA "MUST NOT note this host as a Known HSTS Host". Probe: trusted Chromium did not upgrade `http://127.0.0.1:18050` | OK |
| Browsers still send `Secure` cookies to `http://localhost` (README) | Probe (server log of the redirect listener): Chromium 156 and Firefox 157 sent `Cookie: sid=x` to `http://localhost:18050` and to `http://127.0.0.1:18050`, but not to `http://hsts.test:18050`. This matches Firefox bug 1618113 (FF 75) and httpwg/http-extensions#2605 (Chrome and Firefox allow it; Safari does not) | OK (see F-6) |
| Playwright `ignore_https_errors` | Present on `Browser.new_context` and `APIRequest.new_context` in 1.64.1. pytest-playwright 0.10.0 exposes the `browser_context_args` fixture to set it. With it, both browsers load the page and store the `Secure` cookie | OK |
| `secrets.token_urlsafe(32)` is a 256-bit token, safe in `#t=` | 43 characters from `[A-Za-z0-9_-]`, decoding to 256 bits. A fragment is never sent in a request, so it cannot reach access logs (AD-19) | OK |
| SHA-256 is adequate for hashing 256-bit link and session tokens | NIST SP 800-63B-4 §3.1.2.2 (look-up secrets): a one-way hash is enough at ≥ 112 bits. Only shorter secrets need salting and a password hash | OK (Voucher codes: see F-11) |
| Crockford base32: 16 characters is 80 bits; I/L → 1 and O → 0; hyphens ignored | crockford.com/base32.html: alphabet `0123456789ABCDEFGHJKMNPQRSTVWXYZ` (32 symbols, no I L O U). "i and l will be treated as 1 and o will be treated as 0" in either case, and "Hyphens are ignored during decoding". Probe: `norm('abcd-efgh-ijkl-mnop')` → `ABCDEFGH1JK1MN0P` | OK |
| PG 18 Read Committed: `UPDATE … WHERE code_hash = :h AND balance_ore >= :part …` cannot overspend | PG 18 docs §13.2.1: the second updater waits, then "the search condition of the command (the WHERE clause) is re-evaluated to see if the updated version of the row still matches". A raced spend therefore finds no row, and AD-30 maps that to `voucher_invalid`. One predetermined row is the "safe" case in the docs | OK (docs only; no live PG) |
| Partial unique index syntax | PG 18 `CREATE [UNIQUE] INDEX … [WHERE predicate]`: "use WHERE with UNIQUE to enforce uniqueness over a subset of a table" | OK (see F-12) |
| `--reload` for a `dev` subcommand | `uvicorn.run("booking_platform.app:app", reload=True)` from a uv console script works. Scratch project `relprobe`: StatReload started, and the worker process saw `BP_HTTPS=0` set by the parent. Reload needs an import string, or uvicorn stops with "You must pass the application as an import string" | OK (see F-9) |

## Findings

### F-1 [Medium] `https://localhost` costs ~2 s per new connection on Windows when the listener is IPv4 only

- **Claim:** the base URL defaults to `https://localhost:8443` (AD-22). The redirect target and every email link use it (AD-27, AD-12). The leaf covers `::1`. The listener's host is "the host" from config, and today `uvicorn.run(..., host="127.0.0.1")`.
- **Evidence (probe `clients.py`, server bound to `127.0.0.1`):** every Python client took about 2 s per new connection to `localhost`, against 0.01 s to `127.0.0.1`. The output: `httpx … localhost: 200 (2.04s)`, `requests … localhost: 200 (2.08s)`, `urllib … localhost: 200 (2.02s)`, `httpx … 127.0.0.1: 200 (0.01s)`. Python tries `::1` first, and Windows takes about 2 s to give up on a refused loopback port (`[::1]` → `WinError 10061` after 2.05 s). With `host="localhost"`, uvicorn binds both loopbacks: `localhost` dropped to 0.01 to 0.11 s and `[::1]` answered. The `::1` SAN is useless unless something listens on `::1`. Browsers hide most of this with Happy Eyeballs, but the test suite (HT-1 following the 308, HT-4 opening email links, a fresh `httpx` client per test) would pay it every time. The Dev proxy convention already avoids `localhost` for the same reason (Node).
- **Fix (AD-27 Listeners and AD-22):** both listeners bind to `localhost`, which uvicorn/asyncio resolve to `127.0.0.1` and `::1`, so both stay loopback-only. Alternatively, the test server sets `BP_BASE_URL=https://127.0.0.1:<port>`, which the SAN already covers. State one of them so the first HTTPS story does not discover it.

### F-2 [Medium] The two-listener `main()` needs a defined startup failure and Ctrl+C exit

- **Claim:** "`main()` runs two `uvicorn.Server`s in one event loop" (AD-27). Nothing more is said.
- **Evidence (probe `serve2.py`):**
  - **Ctrl+C:** both servers stop (see the verified table). The last re-raised SIGINT then reaches Python's default handler, and `KeyboardInterrupt escaped asyncio.run`. `uvicorn.run()` swallows it (`main.py` L633, `except KeyboardInterrupt: pass`), but a hand-written `main()` does not. The result is a traceback on every normal stop.
  - **HTTPS port busy:** uvicorn calls `sys.exit(3)` from inside the task. `SystemExit` escapes `asyncio.run` with an `ERROR … 10048` line and a "Task exception was never retrieved" traceback.
  - **HTTP port busy (8000 is a common dev port):** the same exit, but the app's lifespan has **already started**. In the real app that means migrations, seed and catch-up. It is then cancelled mid-lifespan (`CancelledError` in `starlette/routing.py lifespan`), so the pool is never closed cleanly.
- **Fix (AD-27 Listeners, one sentence each):**
  1. `main()` binds both sockets itself (`socket.bind` on `BP_HTTPS_PORT` and `BP_HTTP_PORT`) **before** any server or lifespan starts. It passes them as `serve(sockets=[…])`, and on `OSError` it exits with one line naming the busy port and its `BP_*` variable.
  2. The redirect server uses `lifespan="off"`.
  3. `asyncio.run(...)` is wrapped in `except KeyboardInterrupt: pass`, as `uvicorn.run` does.

### F-3 [Medium] AD-27 names no certificate profile; Python 3.13+ and Apple reject a minimal one

- **Claim:** "a local CA, and a leaf for `localhost`, `127.0.0.1` and `::1`, valid 365 days and signed by that CA". No extensions are named.
- **Evidence:**
  - Probe `strict.py`: a leaf with only a SAN (no KU/EKU/SKI/AKI) verifies under Python 3.12 defaults (`3.12 default 200`). It fails with the flags that Python 3.13+ `create_default_context()` sets by default (`VERIFY_X509_STRICT | VERIFY_X509_PARTIAL_CHAIN`): `certificate verify failed: Missing Authority Key Identifier`. `pyproject.toml` says `requires-python = ">=3.12"`, so a later bump of `.python-version` would break every HTTPS test.
  - Apple's TLS requirements (support.apple.com/en-us/103769) for certificates issued after 2019-07-01: the leaf needs **EKU id-kp-serverAuth**, the name in the **SAN**, validity **≤ 825 days**, SHA-2, and RSA ≥ 2048. Without EKU, a Mac examiner who imports the CA still gets an error in Safari.
  - The probe's "full" profile below passed both the strict flags and the default ones, for ECDSA and RSA.
- **Fix (AD-27 Certificate):** name the profile.
  - **CA:** `BasicConstraints(ca=True, path_length=0)` critical, `KeyUsage(key_cert_sign, crl_sign)` critical, SKI, and a fixed validity (for example 10 years).
  - **Leaf:** SAN (the three names), `BasicConstraints(ca=False)` critical, `KeyUsage(digital_signature)` critical, `EKU serverAuth`, SKI, AKI (from the CA key), 365 days, SHA-256.
  - **Key type:** ECDSA P-256. It is fast to generate for a fresh test cert dir, and all target browsers accept it.

### F-4 [Medium] An imported local CA whose key sits in `certs/` can impersonate any site

- **Claim:** the README says "how to import `certs/ca.pem` if wanted". `ca-key.pem` sits beside it, unencrypted, and is reused across starts.
- **Evidence:** mkcert's README warns that the CA key "gives complete power to intercept secure requests from your machine" (github.com/FiloSottile/mkcert). AD-27's CA has no name constraints, so once it is imported, a leaf for any domain would be trusted. Probe `nc.py`: a CA with a critical `NameConstraints` extension (permitted `DNS:localhost`, `IP:127.0.0.0/8`, `IP:::1/128`) still verifies the localhost leaf under both the default and the strict flags. It refuses a leaf for `bank.example` with `permitted subtree violation`. Browser enforcement of name constraints on a user-imported root was **not** probed (the Chromium SPKI bypass skips path checks).
- **Fix:** add the `NameConstraints` extension above to the CA in `tls.py`. The README should say three things: importing is optional; `ca-key.pem` must never be copied or shared; and the CA should be removed from the trust store after grading.

### F-5 [Low] HSTS on `localhost` is inert in Chrome (since M132) and Firefox; the "locks localhost for a year" rationale is outdated

- **Claim:** AD-27 Prevents "an HSTS value that locks the examiner's `localhost` for a year", and `BP_HSTS_MAX_AGE` defaults to 3600 for that reason.
- **Evidence:**
  - chromestatus feature 5134293196865536, "Ignore Strict-Transport-Security for localhost": status "Enabled by default", desktop 132 and Android 132.
  - The blink-dev intent lists Gecko as "Shipped/Shipping". WebKit bug 282054 (same change for Safari) is still NEW; a comment there says the Fetch standard now requires skipping localhost.
  - Probe with trusted Chromium 156: `http://localhost:18050` was **not** upgraded (the 308 was served), while the control host `hsts.test` was upgraded with its port kept.
  - In Chrome and Firefox the header therefore protects nothing on `localhost`, and HT-2 can only check that the header is present.
  - The opposite risk is real for any non-localhost name. If `BP_BASE_URL` is ever pointed at a `hosts`-file name and the CA is trusted, `http://name:8000` is upgraded to `https://name:8000` and fails. The redirect listener only works on the first visit.
- **Fix:** reword the AD-27 Prevents clause to "an HSTS value that locks a local host name (Safari still honours it on localhost) for a year". Keep 3600. Add a line to the README: in Chrome and Firefox, HSTS has no effect on localhost, and HT-2 checks the header only.

### F-6 [Low] `Secure` cookies also reach `http://127.0.0.1`; HT-3's "never sent over HTTP" cannot hold on loopback

- **Claim:** the README says "browsers still send `Secure` cookies to `http://localhost` (the redirect listener ignores them)". PRD FR-24 and HT-3 say session cookies "are never sent over HTTP".
- **Evidence:** the server log of the redirect listener in the browser probe shows `localhost:18050 … cookie: b'sid=x'` and `127.0.0.1:18050 … cookie: b'sid=x'` for both Chromium 156 and Firefox 157. Safari does not send them (httpwg/http-extensions#2605).
- **Fix:**
  - The README names `localhost` and `127.0.0.1`.
  - The `test_fr24_https.py` HT-3 test asserts the `Set-Cookie` attributes (`Secure; HttpOnly; SameSite=Strict`), plus a check that the redirect listener's response is the same with or without a cookie. It must not assert in a browser that the cookie is never sent.
  - Optionally, flag to the PRD owner that "never sent over HTTP" is a browser policy the server cannot enforce on loopback.

### F-7 [Low] httpx 0.28 deprecates `verify=<path>`

- **Claim:** "HTTP clients verify against that `ca.pem`."
- **Evidence:** probe warning: "`verify=<str>` is deprecated. Use `verify=ssl.create_default_context(cafile=...)`". httpx 0.28.1 is in `uv.lock`.
- **Fix:** add to the Tests convention, or to the conftest story, that clients use `verify=ssl.create_default_context(cafile=<run>/ca.pem)`. `requests` still accepts a path.

### F-8 [Low] The regeneration rule in `tls.py` contradicts itself at the edges

- **Claim:** "If any is missing, or `cert.pem` expires within 30 days, it creates them … An existing CA is reused."
- **Evidence:** "creates them" (all four files) conflicts with "an existing CA is reused". Three cases are not covered:
  - `ca.pem` exists but `ca-key.pem` is missing, so the leaf cannot be signed;
  - `ca.pem` was replaced while `cert.pem` is still valid, so the server sends a leaf the new CA does not verify;
  - the CA itself expires, since its validity is unstated.
- **Fix:** split the rule in two.
  - **CA:** reuse the CA when both CA files are present and the CA is valid for more than 30 days; otherwise make a new CA, and with it a new leaf.
  - **Leaf:** make a new leaf when it is missing, expires within 30 days, or does not verify against the current `ca.pem`.

### F-9 [Low] `dev` must export `BP_HTTPS=0` before uvicorn, because `--reload` runs the app in a spawned worker

- **Claim:** "`uv run booking-platform dev` runs one HTTP listener with `--reload`". `BP_HTTPS` defaults to on, and `config.py` reads it.
- **Evidence:**
  - With `reload=True`, uvicorn runs the app in a `multiprocessing` spawn child. That child imports `config` afresh, so a flag held only in the parent's memory is lost. Probe `relprobe`: the worker saw `BP_HTTPS=0` only because the parent had put it in `os.environ`.
  - Restarts on Windows use `os.kill(pid, CTRL_C_EVENT)` (`basereload.py` L87–90). This works in a terminal, but the restart hung in a headless background run. That is harmless for dev, but `dev` must not be used from the test harness.
- **Fix (AD-27 Environments):** `dev` sets `os.environ["BP_HTTPS"] = "0"` (and the HTTP base URL default) and then calls `uvicorn.run("booking_platform.app:app", reload=True, reload_dirs=["src"])`. It never runs `tls.py`.

### F-10 [Low] Browsers may cache the 308

- **Claim:** the redirect listener "sets nothing".
- **Evidence:** RFC 9110 §15.4.9: "A 308 response is heuristically cacheable". Suppose a developer opens `http://localhost:8000/...` in examiner mode and later runs `dev` (plain app on :8000). The browser can replay the cached 308 to `:8443`. Vite proxies to `127.0.0.1:8000` server-side, so only typed URLs are affected.
- **Fix:** the redirect response carries `Cache-Control: no-store`, which is not a cookie and not app state. Alternatively, the README tells developers to clear the browser cache for localhost when switching between modes.

### F-11 [Low] An 80-bit Voucher code with an unkeyed SHA-256 hash and `code_last4` stored leaves 60 bits against an offline attacker

- **Claim (AD-30):** "Only the SHA-256 hash and the last four characters are stored", and typed codes are exempt from the 128-bit rule.
- **Evidence:**
  - NIST SP 800-63B-4 §3.1.2.2: look-up secrets below 112 bits "SHALL be stored in a salted and hashed form using a suitable password hashing scheme". A per-row salt would break the `code_hash UNIQUE` lookup.
  - Storing the last four characters removes 20 of the 80 bits. With a stolen table, each code is a 2^60 SHA-256 search: years on one GPU, but not out of reach. Gift cards reuse the pattern later.
  - Online guessing is not a concern at 2^80.
- **Fix:**
  - Hash with HMAC-SHA-256 under a server key: `BP_CODE_KEY`, defaulting to a random key generated once into a git-ignored file, as `certs/` is. Lookups stay deterministic, and a leaked table alone gives nothing.
  - Or accept the risk in one sentence in AD-30.
  - Either way, drop `code_last4` or keep it out of anything an attacker could combine with the hash.

### F-12 [Low] The partial unique index on `access_tokens` cannot be deferred, so `issue()` must revoke first

- **Claim (AD-28):** `issue()` "makes a 256-bit token …, stores its hash, revokes any earlier `manage` token". A partial unique index allows one unrevoked `manage` token per Booking.
- **Evidence:** `CREATE UNIQUE INDEX … WHERE …` has no `DEFERRABLE` (PG 18 synopsis). Its uniqueness is checked "each time data is added", and a partial unique constraint does not exist. Insert-then-revoke as worded raises `23505` on a re-issue (FR-34 later).
- **Fix:** reorder the sentence: "revokes any earlier `manage` token of the Booking, then stores the new hash". Name the index, for example `CREATE UNIQUE INDEX access_tokens_one_manage ON access_tokens (booking_id) WHERE purpose = 'manage' AND revoked_at IS NULL`.

### F-13 [Info] Playwright has a newer release than the Stack row

- **Evidence:** PyPI playwright 1.65.2 was uploaded 2026-11-14. The Stack row says 1.64.1, and it is not marked "latest". pytest-playwright 0.10.0 is still the latest. 1.64.1 worked for every probe here (Chromium 156.0.8078.4, Firefox 157.0).
- **Fix:** none needed. Pin whichever version the story that adds it resolves, and update the row then.

## Probe files (scratchpad, not in the repo)

`C:\Users\lisak\AppData\Local\Temp\claude\0ef73fbd82df1f2d\bfee85e0-af51-4a0b-819e-63defa6a375e\scratchpad\tc\`: `mkcerts.py`, `serve2.py`, `clients.py`, `strict.py`, `nc.py`, `browser.py`; reload probe in `…\scratchpad\relprobe\`.

## Sources

- https://pypi.org/pypi/cryptography/json, https://pypi.org/pypi/playwright/json
- https://www.rfc-editor.org/rfc/rfc6797 (§7.2, §8.1, §8.1.1, §8.3)
- https://www.rfc-editor.org/rfc/rfc9110 (§15.4.9), https://www.rfc-editor.org/rfc/rfc7538
- https://chromestatus.com/feature/5134293196865536 (API: status "Enabled by default", desktop 132)
- https://groups.google.com/a/chromium.org/g/blink-dev/c/WJnjKYY2iSs
- https://bugs.webkit.org/show_bug.cgi?id=282054
- https://bugzilla.mozilla.org/show_bug.cgi?id=1618113, https://github.com/httpwg/http-extensions/issues/2605
- https://www.crockford.com/base32.html
- https://www.postgresql.org/docs/18/transaction-iso.html, https://www.postgresql.org/docs/18/sql-createindex.html
- https://pages.nist.gov/800-63-4/sp800-63b.html (§3.1.2.2)
- https://support.apple.com/en-us/103769
- https://github.com/FiloSottile/mkcert (CA key warning)
