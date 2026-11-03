---
review: tech-currency
target: ARCHITECTURE-SPINE.md (Stack table + every named technology/API in AD-1..AD-19, Structural Seed)
reviewed: 2026-11-03
method: PyPI JSON API, npm registry, nodejs.org/dist/index.json, Docker Hub API + image docs, uv.lock, `uv pip compile` of the full Python stack, runtime probes (argon2 defaults, FastAPI API surface, pytest plugin load), a throwaway Vite 8 + React 19.3 + React Router 8 build and dev-proxy smoke test (scratchpad, not in repo)
---

# Review: technology currency of the architecture spine

## Verdict

The spine is in good shape for currency. Every Stack version matches the registries' latest today, and the memlog records the npm/PyPI/uv checks. Two things were asserted from habit rather than checked against the live library: how FastAPI 0.162 serves the SPA (it now has a native `app.frontend()` whose directory check fails at startup) and which React Router package and mode to use. A few rows are also loose (Node "26.7 LTS", the uv row, axe bundling an older axe-core). Nothing blocks the build. Fix the Medium items before the first frontend story.

## What was verified (no action needed)

| Item | Spine says | Live check (2026-11-03) | Result |
| --- | --- | --- | --- |
| fastapi / starlette / pydantic | 0.162.0 / 1.10.0 / 2.14.2 | PyPI latest = same; uv.lock = same | OK |
| psycopg / psycopg-pool | 3.3.7 / 3.3.3 | PyPI latest = same (psycopg 3.3.7 uploaded today 03:51 UTC); uv.lock = same | OK |
| uvicorn | 0.54.0 | PyPI latest; uv.lock | OK |
| pytest | 9.2.0 | PyPI latest; uv.lock | OK |
| argon2-cffi | 25.1.0 | Still PyPI latest (released 2025-06-03). Runtime defaults: Argon2id, m=65536 KiB (64 MiB), t=3, p=4, hash 32 B, salt 16 B | OK. Above the OWASP minimum (Argon2id, m=19 MiB, t=2, p=1). Not in pyproject/uv.lock yet |
| pytest-playwright / playwright | 0.10.0 / 1.64.1 | PyPI latest. Requires `pytest>=7,<10` and `playwright>=1.18`. The whole stack resolves together for py3.12/win (`uv pip compile`). Under pytest 9.2.0 the plugin loads and registers `--browser`, `--browser-channel` and the other options | OK |
| axe-playwright-python | 0.1.8 | PyPI latest (2026-07-24). Imports fine with playwright 1.64.1. Bundles **axe-core 4.12.1** | Usable, see F-5 |
| vite / @vitejs/plugin-react | 8.3.5 / 6.2.1 | npm latest. plugin-react peer `vite ^8.0.0`; its oxc, babel and react-compiler peers are all optional; it has no react peer. Engines `node ^20.19 \|\| >=22.12` | OK. A test build with React 19.3.1 and RR 8.5.1 succeeded |
| Vite dev proxy | `/api` → :8000 | Vite 8 docs: `server.proxy` keeps the `{ '/api': target }` shape on `http-proxy-3`. Smoke test: `GET :5199/api/ping` was forwarded to the target server (200) | OK, see F-4 |
| react / react-dom | 19.3.1 | npm latest; react-dom peer `react ^19.3.1` | OK |
| react-router | 8.5.1 | npm latest (8.0.0 was released 2026-06-17). Peers `react/react-dom >=19.2.7`, engines `node >=22.22.0` | OK, see F-2 |
| PostgreSQL image | `postgres:18`, spike on 18.6 | Docker Hub: newest 18.x tag is 18.6 | OK |
| Compose volume path | `dbdata:/var/lib/postgresql` | Docker Hub postgres docs: from 18 on, the image's `VOLUME` is `/var/lib/postgresql`, and PGDATA is version-specific (`/var/lib/postgresql/18/docker`). Mounting at `.../data` is the ≤17 rule | **Correct for 18**, see F-8 |
| Node.js | 26.7 "(any current LTS or newer)" | nodejs.org: **26.13.0 (2026-10-28) is the first LTS ("Lithium")**. 26.7.0 is a pre-LTS Current release. 24.22.x is "Krypton" LTS | See F-3 |
| Python | 3.12 | Supported (security-only phase). Meets every package's `requires_python` (starlette needs ≥3.11) | OK, see F-9 |

## Findings

### F-1 [Medium] SPA serving: FastAPI 0.162 has native `app.frontend()`, and its default directory check breaks dev/test when `dist/` is absent
The spine says only "SPA static" in `app.py`, and the memlog says "FastAPI serves built dist/. API under /api, everything else to SPA". FastAPI 0.162.0 has `FastAPI.frontend(path, *, directory, fallback="auto"|"index.html"|"404.html"|None, check_dir="auto")` (checked by introspecting the installed package). It registers low-priority routes, so API routes match first. The `index.html` fallback is returned with 200 **only for GET/HEAD navigation requests**. Other misses raise a plain 404. With `check_dir="auto"`, the app **raises at creation if the directory is missing**, unless `FASTAPI_ENV=development`. Only `fastapi dev` sets that variable; `uvicorn --reload` and `uv run booking-platform` do not. So a dev run before `npm run build`, and a pytest run of the API-only tests on a fresh clone, would crash at import. If an agent instead writes the older hand-rolled `StaticFiles` subclass or catch-all route from training data, it duplicates what is now built in. Also, an unknown `/api/...` path returns FastAPI's default `{"detail":"Not Found"}`, not the AD-16 envelope.
**Fix:** In the Structural Seed, name `app.frontend("/", directory=<frontend/dist>, fallback="index.html", check_dir=False)`, called after the routers are included, plus an `/api/{path:path}` catch-all that returns the AD-16 404 envelope.

### F-2 [Medium] React Router 8: the spine names no package entry point or mode
React Router 8.5.1 exists and is current. Its docs list three modes: Declarative (`<BrowserRouter>`), Data (`createBrowserRouter` + `<RouterProvider>`) and Framework (needs the React Router Vite plugin, with SPA/SSR/SSG strategies). All imports come from `"react-router"`. **`react-router-dom` is stuck at 7.18.5 on npm**, so an agent that installs it out of habit gets v7. Framework mode would also bring in the `@react-router/dev` plugin and its own build, which conflicts with the "Vite + React, FastAPI serves dist/" decision. A test build with `createBrowserRouter` from `react-router@8.5.1` on Vite 8.3.5 compiled cleanly.
**Fix:** Add to the Stack row or a convention: "`react-router` 8 only (no `react-router-dom`), Data mode (`createBrowserRouter`/`RouterProvider`), not Framework mode; no `@react-router/dev`."

### F-3 [Low] Node row: "26.7" is not an LTS release
Node 26 became LTS with 26.13.0 on 2026-10-28. The local 26.7.0 is an older pre-LTS build. "Any current LTS" also covers 24.x (Krypton), which satisfies Vite (`>=22.12`) and React Router (`>=22.22.0`). The row mixes "what Lisa has" with "what the examiner needs".
**Fix:** Change the row to "Node.js 24 or 26 LTS (26.13+ recommended; React Router 8 needs ≥22.22)", and add `engines` to `frontend/package.json`.

### F-4 [Low] Vite proxy target should be `127.0.0.1`, not `localhost`
The proxy works in Vite 8 (smoke-tested). The first attempt, which used `localhost` URLs, failed, while explicit `127.0.0.1` worked. Node ≥17 can resolve `localhost` to `::1`, and uvicorn here binds `127.0.0.1`, so `target: 'http://localhost:8000'` can give ECONNREFUSED on Windows.
**Fix:** Write the dev proxy as `server.proxy: { '/api': 'http://127.0.0.1:8000' }` in the Environments table.

### F-5 [Low] axe-playwright-python 0.1.8 bundles axe-core 4.12.1, not the 4.14.0 the memlog lists
It is maintained (releases 2025-10, 2025-12, 2026-07) but is a one-maintainer package with about 31 stars. The CHANGELOG on GitHub `main` already lists a 0.1.9 (axe-core 4.14.0, dated 2026-11-02) that **is not on PyPI**. Today's PyPI latest is 0.1.8 with axe-core 4.12.1. The memlog line "axe-core 4.14.0" therefore describes the npm package, not what the tests would run.
**Fix:** Either inject `frontend/node_modules/axe-core/axe.min.js` with `page.add_script_tag(path=...)` and `page.evaluate("axe.run()")` (version pinned by `package.json`, no extra Python dependency), or keep the package and correct the memlog to "bundles axe-core 4.12.1 (0.1.8)".

### F-6 [Low] Stack "uv" row refers to the README, which pins nothing; uv 0.13 is out
The README says only "uv" with no version. Locally uv is 0.12.6, while PyPI latest is uv / uv_build **0.13.7** (today). `pyproject.toml` pins `uv_build>=0.12.6,<0.13.0`. That still builds under uv 0.13, because the backend is fetched separately, but `uv init` or `uv` upgrade hints will propose 0.13. The row is self-referential, not verified.
**Fix:** State "uv ≥0.12.6 (tested 0.12.6; 0.13.x expected to work); `uv_build` pin stays <0.13 until bumped on purpose", or bump both to 0.13 and re-run the 42 tests.

### F-7 [Low] Packages in the Stack that are not in the lockfile yet
argon2-cffi, pytest-playwright, playwright and axe-playwright-python are named with exact versions but are absent from `pyproject.toml` and `uv.lock`. The frontend packages exist only on paper. They were checked against the registries, and the whole Python set resolves together (this review), but the Stack versions are a snapshot, not a lock. psycopg 3.3.7 and @vitejs/plugin-react 6.2.1 are each about one day old.
**Fix:** Add a note under Stack: "Versions are registry-latest on 2026-11-03; uv.lock / package-lock.json are authoritative once added."

### F-8 [Info] Postgres 18 volume path is right, but it is version-coupled
`/var/lib/postgresql` is correct only for images ≥18. Anyone who drops the image to 17 must move the mount to `/var/lib/postgresql/data`. An existing `dbdata` volume created by an older image layout will not be picked up.
**Fix:** Add a comment in `docker-compose.yml` / README: "mount path is for postgres ≥18; `docker compose down -v` if the major version changes."

### F-9 [Info] Python 3.12 is supported but not the current line
3.12 is in security-only support (until 2028-10). 3.13 and 3.14 are current. All packages support 3.12 and the slice is proven on it. Staying is fine for v1.
**Fix:** None needed. Optionally note "3.12 chosen; ≥3.11 required by Starlette 1.x".

### F-10 [Info] argon2-cffi defaults: verified, with a cost note
The defaults are the RFC 9106 low-memory profile (Argon2id, 64 MiB, t=3, p=4), which is above the OWASP minimum. AD-11 "defaults, rehash when params change" fits `PasswordHasher.check_needs_rehash`. Each sign-in allocates 64 MiB. That is harmless locally, but the AD-11 throttle tests should not run hundreds of hashes in parallel.
**Fix:** None. Optionally pin the parameters explicitly in `services/auth.py`, so that a future argon2-cffi default change triggers rehash deliberately rather than silently.

## Sources
- PyPI JSON API (`https://pypi.org/pypi/<pkg>/json`), npm registry (`npm view`), `https://nodejs.org/dist/index.json`, Docker Hub tags API
- https://hub.docker.com/_/postgres (PGDATA / VOLUME change in 18)
- https://reactrouter.com/start/modes (8.5.1 docs)
- https://vite.dev/config/server-options (`server.proxy`, `http-proxy-3`)
- https://github.com/pamelafox/axe-playwright-python and its CHANGELOG.md
- Installed-package introspection: `fastapi.FastAPI.frontend`, `fastapi.routing._FrontendStaticFiles`, `argon2.PasswordHasher()`
