---
review: tech-currency
target: ARCHITECTURE-SPINE.md (2026-11-19 amendment: AD-23 to AD-26, Stack row `hypothesis`, Tests convention), with a spot-check of the rest of the Stack against uv.lock
reviewed: 2026-11-19
method: PyPI JSON API (hypothesis and every Python Stack row), Hypothesis docs (API reference, changelog), `uv pip compile` of the full Python stack for py3.12/Windows, runtime probes of hypothesis 6.170.15 under pytest 9.2.0 / Python 3.12.14 in a throwaway venv (scratchpad, not in repo), reading `hypothesis/stateful.py` and `core.py` of the installed version, uv.lock, pyproject.toml, tests/conftest.py, .gitignore
---

# Review: technology currency of the 2026-11-19 amendment

## Verdict

The new dependency was checked against reality: hypothesis 6.170.15 is today's latest release, supports Python 3.12, works with pytest 9.2.0, and all four named APIs are current. The rest of the Stack matches uv.lock. The gaps are in AD-26's run settings. The spine names the tool but not how a real-database state machine must be configured, and the library's live defaults bite in three places: the deadline, state reset between examples, and the store clock. Fix the three Medium items in AD-26 before the first §4.9 story is written.

## What was verified (no action needed)

| Item | Spine / memlog says | Live check (2026-11-19) | Result |
| --- | --- | --- | --- |
| hypothesis version | 6.170.x (6.170.15 on 2026-11-19) | PyPI latest = 6.170.15, uploaded 2026-11-06 09:53 UTC. 6.170.0 was 2026-10-15, so the series is current | OK |
| Python support | Python 3.12 | `requires_python >=3.11`. Python 3.10 was dropped in 6.169.0 (2026-10-11), which does not affect us | OK |
| pytest compatibility | pytest 9.2.0 | The `pytest` extra only asks for `pytest>=4.6`. Installed with pytest 9.2.0 on Python 3.12.14: the plugin loads and stateful tests collect and run | OK |
| Resolution with the stack | — | `uv pip compile` (py3.12, windows) of fastapi 0.162.0, starlette 1.10.0, pydantic 2.14.2, psycopg[binary,pool] 3.3.7, psycopg-pool 3.3.3, uvicorn 0.54.0, argon2-cffi 25.1.0, pytest 9.2.0, hypothesis 6.170.15, pytest-playwright 0.10.0, playwright 1.64.1 and httpx 0.28.1 resolves. The only new transitive dependency is `sortedcontainers 2.4.0` | OK |
| `RuleBasedStateMachine`, `@rule`, `@invariant`, `@initialize` | AD-26 | All exist in `hypothesis.stateful` 6.170.15, as do `precondition`, `Bundle`, `consumes`, `multiple` and `run_state_machine_as_test`. `@invariant` runs after every rule. By default (`check_during_init=False`) it does not run until all `@initialize` rules have run. 6.170.0 and 6.170.7 changed only output and typing for stateful tests, with no deprecations | OK |
| Settings defaults | — | Probed: `max_examples=100`, `stateful_step_count=50`, `deadline=200ms`, example database `DirectoryBasedExampleDatabase(./.hypothesis/examples)`. Health checks: `data_too_large`, `filter_too_much`, `too_slow`, `large_base_example`, `function_scoped_fixture`, `differing_executors`, `nested_given`. A built-in `ci` profile is loaded automatically when a CI environment is detected (`deadline=None`, `derandomize=True`, `database=None`, `too_slow` suppressed) | Facts behind F-1 to F-4 |
| Stack rows vs uv.lock | fastapi 0.162.0, starlette 1.10.0, pydantic 2.14.2, psycopg 3.3.7, psycopg-pool 3.3.3, uvicorn 0.54.0, pytest 9.2.0 | uv.lock has exactly these versions (pydantic-core 2.50.2, httpx 0.28.1). `requires-python >=3.12` and `.python-version` 3.12 match. Local uv is 0.12.6, which matches `uv_build>=0.12.6,<0.13` | No mismatch |
| Rows not yet in uv.lock | argon2-cffi 25.1.0, hypothesis, pytest-playwright 0.10.0, playwright 1.64.1 | Absent from pyproject.toml and uv.lock. This is expected, because no story has added them yet | See F-6 |
| docker-compose | `postgres:18`, volume `/var/lib/postgresql` | Same in docker-compose.yml | OK |

## Findings (ranked)

### F-1 [Medium] The deadline will fail a per-example database reset, and the two ways to run a machine use different defaults

**Evidence (probed on 6.170.15):**

- In `run_state_machine`, the time spent inside each `@rule` and `@invariant` is recorded in `_stateful_run_times`. `core.py` subtracts that time before it compares the example's runtime with `deadline`. Slow database *steps* therefore never trip the deadline. A probe with 350 ms rules passed under `deadline=200`.
- The machine's `__init__` and `teardown()` are **not** subtracted. A probe whose `__init__` slept 350 ms (a stand-in for TRUNCATE + reseed) failed with `DeadlineExceeded: Test took 350.80ms, which exceeds the deadline of 200.00ms`.
- `Machine.TestCase` and `run_state_machine_as_test(M)` with no settings use `Settings(deadline=None, suppress_health_check=list(HealthCheck))`. As soon as you pass your own `settings(max_examples=…, stateful_step_count=…)`, which you will do to bound runtime (F-4), it inherits the profile default `deadline=200ms` and the normal health checks. The same machine then behaves differently depending on how it is wired.
- `Machine.TestCase` is a `unittest.TestCase`, so it cannot receive the value of the pytest `database` fixture. The test-database URL would then have to come from somewhere else.

**Sources:** https://hypothesis.readthedocs.io/en/latest/reference/api.html (settings.deadline: "The maximum allowed duration of an individual test case"; the `ci` profile), https://github.com/HypothesisWorks/hypothesis/blob/master/hypothesis-python/src/hypothesis/stateful.py (`get_state_machine_test`, `_to_test_case`)

**Fix (AD-26, add to the Rule):**
> The machine runs through `run_state_machine_as_test(PlacementMachine, settings=FR31_SETTINGS)` inside one pytest function that takes the session `database` fixture. It is never run through `PlacementMachine.TestCase`. `FR31_SETTINGS` sets `deadline=None` explicitly. The per-example reset happens in an `@initialize` rule, not in `__init__`.

### F-2 [Medium] AD-26 does not say how the database is reset between examples, and the existing fixture resets per test, not per example

**Evidence:** Hypothesis constructs a fresh machine for each example (probe: 5 `__init__` calls and 5 `teardown` calls for 5 examples). Pytest fixtures still run once per *test function*. The existing `world` fixture (tests/conftest.py, `TRUNCATE … RESTART IDENTITY CASCADE` plus the seed) is function-scoped. If the model test leans on it, all 100 examples share one database, so each example starts from the previous one's leftovers. That breaks the comparison with a reference model that starts empty. It also breaks shrinking and replay: Hypothesis re-runs a failing example and reports `FlakyFailure` when the result differs. Services commit through `db.run()` on the pool, so wrapping the example in a rolled-back outer transaction is not available. The reset has to be an explicit TRUNCATE and reseed. `RESTART IDENTITY` is required so that Window and Sauna ids are the same on every replay. (The `function_scoped_fixture` health check does not catch this, because it applies to `@given` with fixtures, not to a machine run from inside a test.)

**Sources:** https://hypothesis.readthedocs.io/en/latest/reference/api.html (HealthCheck.function_scoped_fixture: fixtures run "once for the whole function, not once per test case"), tests/conftest.py `world`

**Fix (AD-26, add):**
> Each example starts from the same store. An `@initialize` rule truncates every table the machine writes (`… RESTART IDENTITY CASCADE`), re-applies the fixed Saunas, Windows and Settings, and pins the clock. The brute-force reference is rebuilt from the same values. The test never relies on a function-scoped fixture for per-example state.

### F-3 [Medium] The store clock keeps moving, so replays of time-rule steps are not deterministic

**Evidence:** AD-4: `app_now()` is `clock_timestamp()` plus `clock.off`. Wall time advances during a 50-step example, and more between generation and the shrink or replay of that example, which can be seconds or minutes later. Any rule whose outcome depends on the Booking deadline, the 72 h Whole-sauna Cutoff, Hold expiry or the started-Window rule can flip between runs. Hypothesis then reports `FlakyFailure` instead of a minimal counterexample. This is a known requirement of property-based testing (the test must be deterministic given its inputs), and nothing in AD-26 addresses it.

**Fix (AD-26, add):**
> The reset sets `clock.off` so that `app_now()` is at a fixed instant far from every edge (at least a day before the first Window's Booking deadline). Time moves only through an explicit `@rule advance_clock(to=…)` that sets the clock to an absolute instant drawn from a strategy of edge-adjacent instants. No rule depends on the wall clock in between.

### F-4 [Low] No run budget: the defaults mean 5,000 service calls on every `uv run pytest`

**Evidence:** The docs say `stateful_step_count` (default 50) is "effectively multiplicative with max_examples" (default 100). Against a real PostgreSQL, each step is a `db.run` round trip, and each invariant runs `placement(wid)` and Seats-left queries per Window plus the Python brute force. That is about 5,000 actions and 5,000 invariant checks per run, plus 100 resets. NFR-1 says the examiner runs everything with `uv run pytest`. Because the built-in `ci` profile is loaded automatically on CI, a CI run would also differ silently from the examiner's laptop.

**Source:** https://hypothesis.readthedocs.io/en/latest/reference/api.html (settings.stateful_step_count, settings profiles)

**Fix (Conventions → Tests, add):**
> The FR-31 model test uses explicit settings in the test file, `max_examples=50, stateful_step_count=30, deadline=None` (tune once it is measured). A `fr31-thorough` profile registered in `tests/conftest.py` raises both values and is chosen with `--hypothesis-profile`. The default `uv run pytest` must finish the model test in under 2 minutes on the examiner laptop.

### F-5 [Low] `.hypothesis/` example database is not git-ignored

**Evidence:** The probe confirms that the default example database is `DirectoryBasedExampleDatabase(./.hypothesis/examples)`, created in the working directory, which is the repo root under `uv run pytest`. `.gitignore` lists `.pytest_cache/` but not `.hypothesis/`. Committed example files would make one developer's failures replay on another machine, and they add noise to DR-1 and DR-4 traceability.

**Fix:** In the story that adds Hypothesis, add `.hypothesis/` to `.gitignore`. Optionally, add a sentence to the spine's Tests convention: "Hypothesis's example database (`.hypothesis/`) is git-ignored."

### F-6 [Low] The Stack row floats on `.x`, and rows not yet locked will move when added

**Evidence:** Hypothesis releases patch versions every few days (6.170.0 to 6.170.15 in three weeks). Since the 2026-11-03 check, PyPI has published newer versions of locked or planned rows: fastapi 0.165.0 (2026-11-18), pydantic 2.14.3 (2026-11-05), psycopg 3.3.9 (2026-11-12) and playwright 1.65.2 (2026-11-14). None contradicts uv.lock, which is authoritative. The four rows that are not yet locked (argon2-cffi, hypothesis, pytest-playwright, playwright) will resolve to whatever is latest when a story runs `uv add`. playwright would then be 1.65.x, not the 1.64.1 the spine states. FastAPI's release notes show no "Breaking Changes" section for 0.163 to 0.165, but the spine relies on `app.frontend(..., check_dir=False)`, so a lock refresh should re-run the SPA smoke test.

**Sources:** https://pypi.org/project/hypothesis/6.170.15/, https://pypi.org/pypi/playwright/json, https://fastapi.tiangolo.com/release-notes/

**Fix (Stack row):**
> `hypothesis | 6.170.15 (PyPI 2026-11-19; requires Python ≥3.11); added with `uv add --dev "hypothesis>=6.170.15"`, then uv.lock is authoritative`

Add a line under the table: "Rows not yet in uv.lock (argon2-cffi, hypothesis, pytest-playwright, playwright) are minimums. The version the adding story locks replaces the row."

### F-7 [Low, outside the strict lens] In-process services calls inherit the developer's local test-switch file

**Evidence:** AD-14 reads `config/test-switches.toml` once at import into a frozen object. AD-26 calls `services` in-process, so the model test runs with whatever switches the developer has set locally. A leftover `payment = "fail"` would make every booking rule refuse, and the machine would then explore nothing while staying green.

**Fix (AD-26, add):**
> The model test asserts that every test switch is off before it runs, and it fails fast otherwise.

## Sources

- PyPI: https://pypi.org/project/hypothesis/6.170.15/ and https://pypi.org/pypi/hypothesis/json (version, upload time, requires_python, requires_dist)
- Hypothesis API reference: https://hypothesis.readthedocs.io/en/latest/reference/api.html
- Hypothesis changelog: https://hypothesis.readthedocs.io/en/latest/changelog.html (6.169.0 drops Python 3.10; 6.170.0 and 6.170.7 stateful output and typing only)
- Hypothesis source, stateful runner: https://github.com/HypothesisWorks/hypothesis/blob/master/hypothesis-python/src/hypothesis/stateful.py
- FastAPI release notes: https://fastapi.tiangolo.com/release-notes/
- Local evidence: uv.lock, pyproject.toml, .python-version, docker-compose.yml, .gitignore, tests/conftest.py (`world` fixture)
