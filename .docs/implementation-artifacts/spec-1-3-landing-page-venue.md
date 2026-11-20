---
title: 'Story 1.3: The Landing page presents the Venue'
type: 'feature'
created: '2026-11-20'
status: 'done'
baseline_commit: 'b5e0e9bd3bc732a1a199996efa3c4611e99df492'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/planning-artifacts/epics.md'
  - '{project-root}/.docs/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `/` is a stub, there is no seed, and no endpoint serves the Venue facts. A first-time Guest cannot see what Saunalöyly is, how to prepare, where it is or what it costs, and cannot start booking (FR-1).

**Approach:** Build Story 1.3 in `.docs/planning-artifacts/epics.md` (L503–558) exactly as its ACs list:
- a `seeds/` step at startup (AD-18) with migration `0004_venue_facts.sql`
- `GET /api/venue`
- the Landing page from `mockups/directions-3.html` L137–147, with DESIGN.md and EXPERIENCE.md winning where they differ
- the images moved to `frontend/public/`
- the API and e2e tests the ACs name

## Boundaries & Constraints

**Always:**
- No Venue fact is hard-coded in the frontend: name, address, contact, hours, Session length, price and Saunas come from `GET /api/venue`. Copy is frontend text: the description, Rule lists, Seat statement, Sauna lines and alt texts.
- The seed only inserts absent rows or fills NULL seed-owned columns. It never overwrites, and invalid seed data stops startup with one line naming the file and the field.
- `GET /api/venue` needs no session, writes nothing and sets no cookie. Landing loads create no session.
- Every keyboard step in e2e goes through `a11y.press` / `a11y.tab_to`. Every page still uses only `styles.css`.

**Never:**
- Build Window generation, `ensure_generated`, the Booking horizon, the Book seats page, the Administrator account or sample Bookings (Stories 1.4, 1.5 and 2.1).
- Edit migrations `0001`–`0003`.
- Show a Window schedule on Landing (EXPERIENCE.md L91).

**Decisions (made in planning):**
- **Seed format:** one file, `seeds/venue.json`, applied by `services/seed.py` after migrations and before the app serves. It is validated by Pydantic models in `services/venue.py`, which the future Administrator endpoints will reuse (IV-6).
- **Store:** `0004_venue_facts.sql` adds NOT NULL columns to `settings` with the seed values as defaults (AD-18). The columns are `venue_name`, `address_lines text[]`, `phone`, `email`, `opening_time`, `closing_time`, `session_minutes` (CHECK > 0) and `price_per_seat_ore` (CHECK ≥ 0).
- **Response:** `GET /api/venue` returns `{name, address_lines, phone, email, opening_time "HH:MM", closing_time, session_minutes, price_per_seat_ore, saunas: [{id, name, capacity}]}` with the Saunas in Fill order. `today`, `horizon_end` and `horizon_days` (AD-16) arrive with the horizon in Story 1.4.
- **Sauna copy:** each card's image, alt text and line come from a frontend map keyed by Sauna id. An id with no entry shows its name and size line only.
- **Rail order:** Wordmark, facts, then **Book seats** (DESIGN.md L408 and the AC order; the mockup differs).
- **Venue read fails:** the rail shows the Wordmark, a Notice "The venue details could not be loaded, please try again." and Book seats. The main column keeps the hero, description, "Before you come" and the band. "The saunas" shows its intro only, and "Find us" shows its heading and the Terms and Privacy links only.
- **`lang="fi"`:** only on "Löyly" opening the description, the Finnish word being explained. Sauna names are names.
- **Book seats target (human, 2026-11-20):** `/book-seats`. Story 1.4 builds the page there; until then the link reaches the not-available page.
- **Scope (human, 2026-11-20):** the story stays whole even though the spec is about 2200 tokens.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected |
|---|---|---|
| Fresh start | empty db, backend starts | four Saunas and every Venue fact seeded |
| Restart | backend starts again | same rows, none duplicated or changed |
| Store owns value | price changed in db, restart | changed price kept |
| Invalid seed | `capacity: -1` or `price_per_seat_ore: -1` in seed | startup stops, one line naming file and field |
| Venue facts | `GET /api/venue` without cookie | 200 with the shape above; no `Set-Cookie`; no row written |
| Backend down | Landing with backend stopped | Notice, Book seats present and working, no fact shown |
| Fragment | open `/#before-you-come` | section visible and focused |
| No session | load `/`, `/#before-you-come` | no cookie; every request to `base_url` |

</frozen-after-approval>

## Code Map

- `migrations/0001_core.sql` -- `settings` is one row (`only_row`); `saunas(id, name, capacity CHECK > 0, fill_order UNIQUE, bookable_whole)`. The trigger `t_saunas` recomputes Windows on insert.
- `src/booking_platform/app.py` lifespan -- add `seed.apply()` after `db.open_pool`, beside `sessions.purge_expired()`. A seed `ConfigError`-style failure must stop startup with one line, as AD-14 does for the switch file.
- `src/booking_platform/config.py` `paths` -- add `SEEDS = ROOT / "seeds"`. The docstring already names it.
- `src/booking_platform/api/public.py`, `api/schemas.py`, `db/` -- add `GET /api/venue` with its SQL in a new `db/venue.py`. Keep `api` → `services` → `db`.
- `tests/conftest.py` -- `world` truncates `saunas`, so seeded rows vanish in the API tests. `test_fr01_venue.py` uses its own fresh database plus `start_backend(...)` twice for the restart check, and must not use `world`. `start_backend` and `free_port` can be reused.
- `frontend/app/page.js` -- the stub to replace. `lib/server-api.js` `getPublic('/api/venue')` returns `{ok, data}`. The page awaits `connection()` from `next/server` first. Reuse GuestShell, Rail, Wordmark (`heading`), TextLink and Notice.
- `frontend/app/styles.css` -- the tokens exist. Add the primary button, Rule list, Sauna card, hero, band and Find us styles per DESIGN.md L368–433, and the `.before` columns stacking at `max-width: 1199px`.
- `mockups/directions-3.html` L64–96 and L137–147 -- the layout values and copy. Its `h3`/`h4` headings, `href="#book"` and `<span class="lnk">` are placeholders.
- `EXPERIENCE.md` L156–158 (Rule list items) and L564 (Sauna lines) -- copy to take verbatim.
- `mockups/images/*.jpg` (7 files) -- `git mv` to `frontend/public/images/`. Update the `ASSETS.md` rows and the note about where the images live. Each row names `images/<file>`.
- `tests/e2e/test_fr21_privacy.py` `PAGES` already has `/`. Add `/#before-you-come`.
- Deferred from Story 1.2, done here:
  - `next build` lists `/` as dynamic (the open issues.md item).
  - The Landing title "Saunalöyly" is tested.

## Tasks & Acceptance

**Execution:**
- [x] `migrations/0004_venue_facts.sql` -- settings columns as decided -- AD-15, AD-18
- [x] `seeds/venue.json`, `src/booking_platform/services/{seed,venue}.py`, `db/venue.py`, `config.py`, `app.py` -- seed (insert Saunas `ON CONFLICT (id) DO NOTHING`, `COALESCE` fill of settings), validation and startup hook -- AD-18, IV-6
- [x] `src/booking_platform/api/{public,schemas}.py` -- `GET /api/venue` -- AD-16
- [x] `tests/test_fr01_venue.py` -- matrix rows 1–5 against a fresh database
- [x] `frontend/public/images/*`, `ASSETS.md` -- images moved; rows updated -- DR-3
- [x] `frontend/app/page.js`, `frontend/components/{PrimaryButton,RuleList,SaunaCard}.js`, `frontend/lib/{venue-format,sauna-copy}.js`, `frontend/app/styles.css` -- Landing as the ACs list, with the failure state as decided -- FR-1, UX-DR4/5/15/16
- [x] `tests/e2e/test_fr01_landing.py`, `tests/e2e/test_fr21_privacy.py` -- the sections and copy, title, axe, keyboard reach of every link and the button, no horizontal scroll, `/#before-you-come` focus, Book seats navigation, backend-stopped Notice -- FR-22, FR-23
- [x] `README.md` -- status and the seed sentence

**Acceptance Criteria:**
- Given the stack, when `npm --prefix frontend run build` runs, then `/` is listed as dynamic (ƒ) and the record shows it.
- Given `uv run pytest`, then every test passes, those of Stories 1.1 and 1.2 included.
- Given 1366×768, when Landing loads, then Book seats is fully inside the first view.

## Implementation Notes

- `npm --prefix frontend run build` (2026-11-20) lists `ƒ /`, with `/privacy`, `/terms` and `/_not-found` static (○). Closes the issues.md item deferred from Story 1.2.
- The seed file is validated twice: once in `booking_platform.main` before uvicorn starts (so an invalid seed prints one line and exits 2, as the switch file does), and again by `seed.apply()` after the migrations in the lifespan. A missing `seeds/venue.json` also stops startup; `test_dr4_migrations.py`'s duplicate-number test now copies `seeds/` into its temporary root.
- `GuestShell` gained `mainClass`, so Landing's main has no padding and the hero runs full width.
- `/book-seats` is an unknown route until Story 1.4, and Next.js loads it as a new document, so focus there stays at the start of the page (not on the h1). The e2e test checks the not-available heading only.
- The Terms → "Before you come" case in `test_fr22_terms_privacy_a11y.py` now expects focus on the section, not the Wordmark.
- `mockups/directions-3.html` still points at `images/…`, which moved; the mockup now shows broken images.

## Spec Change Log

## Review Triage Log

Pass 1 (blind-hunter BH, edge-case-hunter EC, verification-gap VG, plus the step-3 audit AU):

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| VG1/BH3/BH4/EC-o3 | `seed_settings` never writes: 0001 always inserts the row and 0004 gives every column a NOT NULL default, so the facts come from the migration and nothing checks that they equal `seeds/venue.json` | medium | follows AD-18 (a new column gets the seed value as its default), but the two copies can drift silently and the docstrings and README claim the seed fills them | patch (drift test + docstrings) |
| BH1/EC1/VG-o1/AU | `seed_sauna` conflicts only on `id`; a store Sauna holding a seeded `fill_order` stops startup with a store traceback | low | `saunas.fill_order` is UNIQUE (0001); `ON CONFLICT DO NOTHING` without a target is a direct fix | patch |
| EC5 | A seed file saved with a UTF-8 BOM is refused | low | `read_text(encoding="utf-8")` keeps the BOM and `json.loads` fails; `utf-8-sig` is a direct fix on a Windows-developed project | patch |
| BH14 | README "Automatiserte tester" row does not mention FR-1 or the seed tests | low | the row lists earlier FRs only | patch |
| BH2/EC2/VG-o2 | A deleted seeded Sauna is inserted again at every restart | medium | literal AD-18 ("writes where the row is absent"), and no Sauna delete exists yet; must be decided before Sauna administration | defer |
| VG2/BH8 | `venue-format.js` branches (øre rest, whole hours, minutes only) tested only with 25000 and 90 | medium | no JS unit runner; values change only through the store until an Administrator edits them | defer |
| EC3/BH5 | `facts()` raises TypeError if the settings row is missing | false | the row is inserted by 0001 under `only_row` and nothing deletes it | reject |
| EC4 | Seed file changed between the `main()` check and the lifespan prints a traceback | low | needs an edit during startup | reject |
| EC6/BH9 | Sauna grid and Find us keep their columns on narrow screens | false | the narrow layout is FR-51 and 1.4.10 is the accepted gap; no horizontal scroll at 1024 passes | reject |
| EC7 | Empty `saunas` list renders an empty `ul` | low | the seed always provides four Saunas | reject |
| BH6 | `session_minutes` may exceed the opening hours | low | an added cross-field rule; no Administrator input yet | reject |
| BH7/AU | Invalid-seed tests cover two fields and only the `main()` path | low | the rest are Pydantic's own branches | reject |
| BH10 | Below-the-fold images not `loading="lazy"` | low | local platform; lazy loading would change what the e2e request checks see | reject |
| BH11 | Phone and email not `tel:`/`mailto:` links | false | FR-1.8: the contacts must not reach anyone | reject |
| BH12 | Sauna copy keyed by id; alt texts in three places | false | the spec's Decision keys copy by id; ASSETS.md is the register | reject |
| BH13 | "The saunas" has no cards when the read fails | false | the spec's Decision for the failure state | reject |
| AU1 | `venue.name` unused; Wordmark and title hard-code "Saunalöyly" | false | the Wordmark is the typeset brand on every page (UX-DR7), including the static Terms and Privacy, and the title is fixed copy (EXPERIENCE.md L407) | reject |
| AU2 | "Open every day" is fixed copy | low | addendum J: the same hours every day; no per-day hours exist in the store | reject |

## Verification

**Commands:**
- `docker compose up --build --wait` then `curl -s http://localhost:8000/api/venue` -- expected: the seeded facts
- `npm --prefix frontend run build` -- expected: `ƒ /`
- `uv run pytest -q` -- expected: all pass
