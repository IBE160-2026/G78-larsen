# Story 1.1: backend-struktur

## 2026-11-20 kl. 10:37 — Lisa Larsen

### Oppgave
Lisa ba om å lage grenen for Story 1.1 og kjøre `bmad-build` på storyen i `.docs/planning-artifacts/epics.md`. Slicen skulle flyttes over på strukturen i spinen uten at noen regel ble løsnet.

### Plan
- Grenen `story/1-1-backend-structure` ble laget fra `main`.
- `bmad-build` med underagenter, som Lisa godkjente for hele kjøringen:
  - Epic-konteksten ble samlet i [epic-1-context.md](../../.docs/implementation-artifacts/epic-1-context.md).
  - Specen er [spec-1-1-capacity-slice-backend-structure.md](../../.docs/implementation-artifacts/spec-1-1-capacity-slice-backend-structure.md). Lisa valgte å beholde den samlet, selv om den er ca. 2 800 tokens, og godkjente den.
  - Implementeringen ble gjort av en underagent.
  - Tre gjennomganger (Blind Hunter, Edge Case Hunter, Verification Gap) fulgte, med vurdering og retting av funnene.

### Resultat
- **Commit:** `ae26bc9` på `story/1-1-backend-structure`. Grenen er pushet til `origin` (Lisa ba om det). Ingen PR er laget ennå.
- **Lag:** `api/` → `services/` → `db/`, med `config.py` som løvmodul. SQL ligger bare i `db/` og `migrations/`.
  - Det finnes én `Refused` og én kode → status-tabell (`api/errors.py`).
  - Databasefeil oversettes etter constraint-navn, også ved COMMIT. Ukjente feil gir `500 internal_error` uten databasetekst.
- **Migreringer:**
  - `0001_core.sql` er `schema.sql`, uendret og samme blob i git.
  - `0002_sessions.sql` lager `sessions`-tabellen. `holds.session_id` blir en fremmednøkkel, og gamle hold slettes.
  - `0003_named_store_refusals.sql` gir triggernes avvisninger navn.
  - Runneren bruker advisory lock, regner gamle databaser som at 0001 allerede er kjørt, og nekter to filer med samme nummer.
- **Sesjoner og tilgang:**
  - Cookien `bp_session` er HttpOnly og `SameSite=Strict`, og får `Secure` når `BP_HTTPS` er på.
  - En anonym sesjon varer 24 timer og en administrator-sesjon 8 timer, begge glidende.
  - CSRF sjekkes mot `Origin` og gir `403 cross_origin`.
  - `/api/admin/` svarer 401 `not_signed_in` og 403 `not_allowed`. Ukjente stier og 405 gir `404 not_found`.
  - `/docs` og `/openapi.json` er slått av.
- **Config og CLI:** alle `BP_*`-variabler har lokale standardverdier. Test-switchene leses fra TOML, og `config/test-switches.example.toml` er committet. Kommandoene er `uv run booking-platform dev` og `uv run booking-platform serve`, på 127.0.0.1:8001.
- **Tester:** 144 består på ca. 96 sekunder (før storyen: 42 på ca. 40 sekunder).
  - Slice-testene beholder sine assertions. Bare oppsettet er endret: `/api`-stier, ekte sesjoner, maks 10 plasser per booking eller rå rader, og admin via fixture.
  - Mutasjonene gjør fortsatt bypass-testene røde. Med `nocheck` feiler 9 av 10.
  - Nye testfiler: `test_fr18_csrf`, `test_fr20_access`, `test_fr21_sessions`, `test_fr2_input`, `test_dr4_migrations` og `test_fr14_switches`.
- **Gjennomgangen:**
  - 10 funn ble rettet: logging, grenser for heltall i input, `AwareDatetime` på Blocks, 400 → 422, logglinje når en forespørsel har brukt opp forsøkene, README-teksten, test av `Secure`-cookien, test av `rule_refused`-kodene og test av `_fkey` → 404.
  - 2 funn er utsatt til `.docs/implementation-artifacts/deferred-work.md`.
  - 16 er avvist med begrunnelse i specens Review Triage Log.
- **Annet:**
  - `sprint-status.yaml`: Story 1.1 står i `review` og Epic 1 i `in-progress`.
  - `docker-compose.yml` har fått helsesjekk og binder porten til `127.0.0.1`.
  - README er oppdatert.

### Åpne punkter
- AD-7 i spinen sier «migration `0002`» for `bookings.status`, men 0002 og 0003 er nå tatt av Story 1.1. Story 1.5 må ta neste ledige nummer (AD-15), og spinen bør eventuelt rettes.
- Utsatte tester (`deferred-work.md`): middlewarens 500-svar for uventede unntak, og migrering av en gammel database med data og samtidige `migrate()`-kjøringer.
