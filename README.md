# G78 — Saunalöyly Booking Platform

Gruppeprosjekt i **IBE160 Programmering med KI** ved Høgskolen i Molde, høsten 2026 (15 studiepoeng). Repoet inneholder applikasjonen og dokumentasjonen av hvordan den er planlagt, bygget og kvalitetssikret med KI (BMAD og Claude Code).

## Medlemmer

- Lisa Katarina Larsen

## Hva appen skal gjøre

Saunalöyly er et fiktivt, finsk-inspirert badstuanlegg med fire eller flere badstuer. Plattformen lar gjester velge dag og antall plasser, se hvilke tidsvinduer som har ledige plasser og hva det koster, og betale uten konto. Administrator logger inn og ser hvem som kommer til hvert vindu. Betaling, e-post og dørlåser er simulert.

Det vanskelige er kapasiteten: plasser og hele badstuer trekker på de samme rommene, og plattformen skal aldri selge samme plass to ganger, heller ikke når to gjester trykker «Pay» i samme sekund. Hele kravsettet står i [PRD-en](.docs/planning-artifacts/prds/prd-booking-platform-2026-10-29/prd.md).

## Status (2026-11-20)

| Del | Status |
|---|---|
| Product brief | Ferdig |
| Research (samtidighet, kapasitetsmodell, dørkoder) | Ferdig |
| PRD | Ferdig. Planlagt v1 er Core + If-time 1–3 (HTTPS, endringer og Vouchere, hel badstue) |
| UX | Ferdig ([EXPERIENCE.md](.docs/planning-artifacts/ux-designs/ux-booking-platform-2026-11-05/EXPERIENCE.md), [DESIGN.md](.docs/planning-artifacts/ux-designs/ux-booking-platform-2026-11-05/DESIGN.md)) |
| Arkitektur | Ferdig ([arkitekturspine](.docs/planning-artifacts/architecture/architecture-booking-platform-2026-11-03/ARCHITECTURE-SPINE.md)): FastAPI + PostgreSQL, Next.js som frontend og Caddy som eneste inngang, alt i Docker Compose |
| Epics og stories | Ferdig ([epics](.docs/planning-artifacts/epics.md)). Implementering pågår: Story 1.1 (backendstruktur) og Story 1.2 (compose-stakken, vilkår og personvern) er ferdige, Story 1.3 (landingssiden) |
| Applikasjon | **Core-skiva på spinens backendstruktur (Story 1.1).** `src/booking_platform/` er delt i `api/` → `services/` → `db/` med `config.py` som løv. Skjemaet endres bare gjennom nummererte migrasjoner i `migrations/`. Alle stier ligger under `/api`, Administrator-endepunktene under `/api/admin/`, og økter er rader på serveren med hashet token i en informasjonskapsel. Story 1.2 la til compose-stakken (Caddy, FastAPI, Next.js og PostgreSQL), Next.js-frontenden med ett stilark og selvhostede fonter, og sidene for bookingvilkår (`/terms`) og personvern (`/privacy`). Story 1.3 la til landingssiden (`/`) med anlegget, «Before you come», badstuene og «Find us», `GET /api/venue` og seed-data i `seeds/`. **Book seats** går til `/book-seats`, som bygges i Story 1.4 og til da viser «This page is not available.». Ingen innlogging, betaling eller e-post ennå |
| Automatiserte tester | Skivas tester for FR-10/11/12/14/35/36/41 med påstandene beholdt, mens oppsettet er omformet (stier under `/api`, økter fra serveren, Administrator-økt fra en fixture, høyst 10 plasser per forespørsel eller rå innsettinger). Én endring i oppførsel: en avvisning fra databasen uten navngitt constraint gir nå 500 (`internal_error`), så retry-testen for en definitiv avvisning tvinger fram en navngitt constraint. I tillegg kommer tester for anlegget og seed-dataene (FR-1, `tests/test_fr01_venue.py`), CSRF (FR-18), tilgang (FR-20), økter (FR-21), inndata (FR-2), migrasjoner (DR-4), testbrytere og asset-registeret (DR-3) (`tests/`), og e2e-tester i nettleser mot hele stakken: ruting gjennom Caddy, feilsider, `<noscript>`, personvern (FR-21), tilgjengelighet med axe-core og tastatur (FR-22, FR-23) og landingssiden (FR-1, `tests/e2e/test_fr01_landing.py`) (`tests/e2e/`). Resten kommer sammen med hver story (PRD NFR-6) |

Byggeperioden er 27. oktober – 15. desember 2026. Denne README-en oppdateres når appen finnes: installasjon, testbrukere, miljøvariabler og skjermbilder legges til da.

## Forutsetninger

- [uv](https://docs.astral.sh/uv/) (installerer Python 3.12 etter behov, se `.python-version`)
- Git
- [Node.js](https://nodejs.org/) 24 LTS eller nyere (tester og utvikling av frontend)
- [Docker](https://www.docker.com/) med Docker Compose (kjører hele plattformen)

Databasen er PostgreSQL i en Docker-container (PRD §12 Q4, avgjort 2026-11-03; erstatter SQLite fra 2026-11-01). Hele plattformen kjører i Docker Compose: Caddy er eneste inngang, sender `/api` og `/api/*` til FastAPI og resten til Next.js. Plattformen kjører over HTTP til HTTPS-storyen (FR-24) er bygget.

## Kom i gang

Én kommando starter hele plattformen:

```sh
git clone https://github.com/IBE160-2026/G78-larsen.git
cd G78-larsen
docker compose up --build --wait   # bygger og starter proxy, backend, frontend og db; venter til alle er friske
```

Åpne så `http://localhost:8000` (bruk `localhost`, ikke `127.0.0.1`: Caddy svarer bare for `localhost`). Bare Caddy har en publisert webport (`127.0.0.1:8000`); backend og frontend nås bare på det interne compose-nettverket. Databasen er i tillegg publisert på `127.0.0.1:55432` for utvikling og API-testene.

### Drift lokalt

```sh
docker compose ps                    # status og helsesjekker for de fire tjenestene
docker compose logs backend proxy    # logger fra backend og Caddy
docker compose restart backend       # leser testbryterne på nytt (se under)
docker compose down                  # stopper og fjerner containerne; data blir liggende
docker compose down -v               # fjerner også volumene: databasen og Caddys data
```

Testbrytere: kopier `config/test-switches.example.toml` til `config/test-switches.toml`, endre den og kjør `docker compose restart backend`. Mappen `config/` er montert skrivebeskyttet i backend, og uten filen er alle brytere av.

### Utvikling uten Docker for backend og frontend

```sh
uv sync                              # installerer Python og avhengigheter i .venv
docker compose up -d --wait db       # starter bare PostgreSQL 18 (port 55432)
uv run booking-platform dev          # API-et på http://127.0.0.1:8001 med automatisk omstart
npm --prefix frontend ci             # én gang: frontendens avhengigheter
npm --prefix frontend run dev        # Next.js på http://127.0.0.1:3000; /api/* sendes videre til 127.0.0.1:8001
```

`uv run booking-platform dev` oppretter databasen `booking_dev` første gang, kjører migrasjonene i `migrations/` og svarer på `http://127.0.0.1:8001/api/health`. Ved hver oppstart legges badstuene fra `seeds/venue.json` inn der de mangler. Pris, åpningstider, øktlengde, adresse og kontakt kommer fra standardverdiene i migrasjon `0004`, som er de samme som i seed-fila (en test sjekker det), og seeden fyller bare en slik kolonne hvis den er NULL; en verdi som allerede står i databasen, overskrives aldri, og en ugyldig seed-fil stopper oppstarten med én linje som nevner filen og feltet. `uv run booking-platform serve` gjør det samme uten automatisk omstart.

Konfigurasjonen leses bare fra `BP_*`-miljøvariabler, og alle har en standardverdi som virker lokalt:

| Variabel | Standard | Betydning |
|---|---|---|
| `BP_DATABASE_URL` | `postgresql://postgres:booking@127.0.0.1:55432/booking_dev` | Databasen (`booking_dev` opprettes bare når standard-URL-en brukes) |
| `BP_BASE_URL` | `http://127.0.0.1:3000` | Opprinnelsen nettleseren bruker; skrivende forespørsler må komme derfra (CSRF) |
| `BP_HTTPS` | `off` | Gjør øktkapselen `Secure`; krever at `BP_BASE_URL` begynner med `https://` |
| `BP_HOST`, `BP_PORT` | `127.0.0.1`, `8001` | Hvor backend lytter |
| `BP_ROOT` | repoets rot | Rot for `migrations/`, `seeds/` og `config/` (imaget setter `/app`) |
| `BP_TEST_SWITCHES` | `config/test-switches.toml` | Testbrytere. Kopier `config/test-switches.example.toml` dit for å bruke dem; mangler filen, er alle av |

Docker Compose og frontenden leser i tillegg disse (de er ikke `BP_*`, og backend leser dem ikke):

| Variabel | Standard | Betydning |
|---|---|---|
| `HTTP_PORT` | `8000` | Porten Caddy lytter på og publiserer på `127.0.0.1`; også i `BP_BASE_URL` i compose |
| `DB_PORT` | `55432` | Databaseporten på `127.0.0.1` (en annen verdi krever en tilsvarende `BP_DATABASE_URL`) |
| `SWITCHES_DIR` | `./config` | Mappen som monteres skrivebeskyttet som `/app/config` i backend (testbryterne) |
| `API_INTERNAL_URL` | compose: `http://backend:8000`, ellers `http://127.0.0.1:8001` | Hvor frontendens server kaller backend (`frontend/lib/server-api.js`) |

### Tester

To forberedelser, én gang:

```sh
npm --prefix frontend ci             # frontendens avhengigheter, også axe-core som e2e-testene bruker
uv run playwright install chromium   # nettleseren til e2e-testene
```

Deretter:

```sh
uv run pytest            # API-testene og e2e-testene
```

`uv run pytest` kjører to lag, så Docker må kjøre. API-laget (`tests/`) kjører først `docker compose up -d --wait db`, oppretter `booking_test` på nytt og starter backend som en egen prosess. E2e-laget (`tests/e2e/`) starter hele stakken som et eget compose-prosjekt, `booking_e2e`, på ledige porter (så det aldri kolliderer med stakken på 8000), kjører Playwright og axe-core mot den og fjerner den med `down -v` til slutt. Testene sender ekte HTTP-forespørsler til en ekte backend-prosess (`uv run booking-platform serve`) mot ekte PostgreSQL, og skriver også rett til databasen for å omgå API-et (FR-10). Hele settet tar ca. to–tre minutter, mer første gang imagene bygges. `BP_TEST_MUTATE=<navn>` slår av én beskyttelse i databasen (se `MUTATIONS` i `tests/conftest.py`) for å vise at testene da feiler.

### Hverdagskommandoer

```sh
uv add <pakke>           # legg til avhengighet
uv add --dev <pakke>     # legg til utviklingsavhengighet (tester, linter)
uv remove <pakke>        # fjern avhengighet
uv lock --upgrade        # oppgrader låste versjoner
```

`pyproject.toml` er eneste kilde for avhengigheter, og `uv.lock` låser versjonene. Begge committes. Ikke bruk pip, venv, poetry eller `requirements.txt`, og ikke commit `.venv/`.

## Mappestruktur

```
src/booking_platform/   Python-pakke (backend): api/ → services/ → db/, config.py
migrations/             Nummererte SQL-migrasjoner (0001_core.sql er skivas opprinnelige skjema)
seeds/                  Seed-data som legges inn ved hver oppstart uten å overskrive (venue.json)
config/                 Eksempel på testbryterfil (den ekte filen committes ikke)
frontend/               Next.js (App Router, JavaScript): app/ (sider og styles.css), components/, lib/, public/ (fonts/, images/)
tests/                  API-tester mot ekte backend og PostgreSQL; tests/e2e/ kjører nettleser og axe mot hele stakken
Caddyfile               Proxyen: eneste inngang, ruting og svarhoder
docker-compose.yml      De fire tjenestene (proxy, backend, frontend, db) med helsesjekker
Dockerfile              Backend-imaget (frontend/Dockerfile er frontend-imaget)
ASSETS.md               Register over fonter og bilder med kilde og lisens (DR-3)
.docs/                  Planlegging og research (se under)
.logs/<bruker>/         Sesjonslogger: oppgave, plan, resultat og åpne punkter per økt
_bmad/                  BMad Method-konfigurasjon
.claude/skills/         BMad-skills og prosjektets egne skills for Claude Code
pyproject.toml          Prosjektmetadata og avhengigheter
uv.lock                 Låste versjoner
```

## Plan- og prosessdokumentasjon

| Dokument | Innhold |
|---|---|
| [Product brief](.docs/planning-artifacts/briefs/brief-booking-platform-2026-09-20/brief.md) og [tilbakemelding](.docs/planning-artifacts/briefs/brief-booking-platform-2026-09-20/tilbakemelding-product-brief.md) | Hva som skal bygges, og lærerens vurdering av briefen |
| [PRD](.docs/planning-artifacts/prds/prd-booking-platform-2026-10-29/prd.md) og [addendum](.docs/planning-artifacts/prds/prd-booking-platform-2026-10-29/addendum.md) | Krav (FR-1 …), testbare konsekvenser, leveringskrav (DR-1 …) og åpne spørsmål |
| [Research](.docs/planning-artifacts/research/) | Samtidighet og plassreservasjon, kapasitetsmodell med 85 eksempler, dørkoder |
| [Brainstorm: minste v1](.docs/brainstorming/brainstorm-minste-v1-mvp-2026-10-27/brainstorm-intent.md) | Hva som er kjerne og hva som er «hvis tid» |
| [Sesjonslogger](.logs/lisa-larsen/) | Hva som ble spurt om, planlagt og besluttet i hver KI-økt |
| [Åpne punkter](.logs/lisa-larsen/issues.md) | Avklaringer som gjenstår, med lenke til økta de oppstod i |
| [Sensorveiledning: kravsporing](.docs/sensorveiledning-kravsporing.md) | Status per vurderingskriterium og hva som gjenstår |

## Prosess

Planleggingen er gjort med BMAD-skills i Claude Code. Hver økt logges i `.logs/` med oppgave, plan og resultat, og beslutninger føres inn i PRD-en med dato. Under implementeringen arbeides det på én gren per story, med pull request som viser hvilke krav (FR-nummer) som er dekket, hvordan KI ble brukt, og hvilke tester og funn kvalitetssikringen ga. Se [PR-malen](.github/pull_request_template.md).
