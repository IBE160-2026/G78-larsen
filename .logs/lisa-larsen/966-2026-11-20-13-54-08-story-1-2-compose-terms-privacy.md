# Story 1.2: compose-stakken, vilkår og personvern

## 2026-11-20 kl. 13:54 — Lisa Larsen

### Oppgave
Lisa ba om å starte `bmad-build` for Story 1.2: plattformen skal starte med én kommando (`docker compose up --build --wait`) og vise Booking terms og Privacy notice. Storyen bygger compose-stakken, Next.js-skjelettet med de delte hjemmene og e2e/a11y-laget som senere stories bruker.

### Plan
- Grenen `story/1-2-compose-terms-privacy` ble laget fra `main`.
- `bmad-build` med underagenter, som Lisa godkjente for hele kjøringen:
  - To research-agenter hentet ut spinens AD-10/14/17/22/27 og UX-kravene (tokens, shell, Terms/Privacy-mockupene).
  - Specen er [spec-1-2-compose-stack-terms-privacy.md](../../.docs/implementation-artifacts/spec-1-2-compose-stack-terms-privacy.md). Lisa valgte å beholde den samlet (ca. 2 400 tokens), og valgte en enkel forside-stub til Story 1.3 bygger Landing. Lisa godkjente specen.
  - Implementeringen ble gjort av en underagent.
  - Tre gjennomganger (Blind Hunter, Edge Case Hunter, Verification Gap), med vurdering av hvert funn i specens Review Triage Log.

### Resultat
- **Commit:** `75853c2` på `story/1-2-compose-terms-privacy`. Grenen er pushet til `origin`, og PR #2 er opprettet med `gh` (Lisa ba om begge): https://github.com/IBE160-2026/G78-larsen/pull/2. Lisa merger selv.
- **Stakken:** proxy (Caddy 2.11), backend, frontend og db i `docker-compose.yml`, med helsesjekkene fra AD-27 og `depends_on: service_healthy`.
  - Caddy er eneste publiserte webport (`127.0.0.1:8000`) og den eneste som setter `Referrer-Policy` og `Cache-Control`. Next.js' egen `Cache-Control` fjernes med `header_down`.
  - Images: rot-`Dockerfile` for backend (uv 0.12.24, uten `uv run`) og `frontend/Dockerfile` (with-docker-oppsett på `node:24-alpine`).
- **Frontend:**
  - Next 16.4.6 med App Router i JavaScript.
  - `app/styles.css` har alle tokens fra DESIGN.md.
  - Finlandica og Source Sans 3 er selvhostet som woff2 (OFL) og ført i `ASSETS.md`.
  - `lib/api.js` og `lib/server-api.js`.
  - Komponentene GuestShell, Rail, Wordmark, TextLink, Notice og FocusMover.
  - Feilsidene og `/terms` og `/privacy`, med teksten ordrett fra mockupene.
  - `/` er en midlertidig stub.
- **Tester:** 192 passerte (`uv run pytest`, ca. 2 min 20 s).
  - E2e-laget er `tests/e2e/` med compose-prosjektet `booking_e2e` på ledige porter og `down -v` til slutt.
  - `a11y.py` har `check_axe`, `no_horizontal_scroll`, `press`, `tab_to`, `tab_order` og `zoomed`.
  - Nye tester: ruting gjennom Caddy, FR-21-personvern, tilgjengelighet, `test_dr3_assets.py` og en speiltest for statuskodene.
  - Jeg sjekket at `Cache-Control`-testen feiler når Caddy-linjen fjernes.
- **Kjørt live:** helsesjekkene, `caddy adapt`, `curl -i http://localhost:8000/` og `next build`, med utskriften i specens Implementation Notes. Alle rutene er statiske, fordi ingen side bruker `server-api.js` ennå.
- **Gjennomgang:** 9 funn rettet, 5 utsatt til [deferred-work.md](../../.docs/implementation-artifacts/deferred-work.md), resten avvist med begrunnelse.
- **Status:** sprint-status for 1.2 er `review`. Dev-stakken kjører fortsatt på `localhost:8000` (`docker compose down` stopper den).
- **issues.md:**
  - Lukket: README-kommandoene fra Structural Seed.
  - Delvis løst: Caddy-/Next.js-påstandene (`caddy adapt` og `curl -i` er kjørt) og compose-detaljene (helsesjekker og `@api`). Den dynamiske `next build`-sjekken gjenstår til Story 1.3.

### Åpne punkter
- `next build` må vise sidene som bruker `server-api.js` som dynamiske. Sjekkes i Story 1.3, den første brukeren (står allerede i issues.md, 2026-11-19).
- E2e-test av feilsidene (`error.js`, `global-error.js`) når en side kan feile (Story 1.3).
- FocusMover reagerer ikke på navigasjon som bare endrer `#fragment` eller query på samme side. Det må på plass før Landing får «Before you come»-lenken (Story 1.3).
- Arkitekturbeslutning: skal Caddy også sende `X-Content-Type-Options`, en beskyttelse mot innramming og en CSP (`default-src 'self'`)? AD-27 har ingen av dem.
- Teste Landing-tittelen «Saunalöyly» (Story 1.3) og «Error: »-prefikset når det første skjemaet med Error summary kommer.
