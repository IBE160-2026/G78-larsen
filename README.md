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
| Epics og stories | Ferdig ([epics](.docs/planning-artifacts/epics.md)). Implementering pågår: Story 1.1 (backendstruktur) |
| Applikasjon | **Core-skiva på spinens backendstruktur (Story 1.1).** `src/booking_platform/` er delt i `api/` → `services/` → `db/` med `config.py` som løv. Skjemaet endres bare gjennom nummererte migrasjoner i `migrations/`. Alle stier ligger under `/api`, Administrator-endepunktene under `/api/admin/`, og økter er rader på serveren med hashet token i en informasjonskapsel. Ingen innlogging, betaling, e-post eller frontend ennå |
| Automatiserte tester | Skivas tester for FR-10/11/12/14/35/36/41 med påstandene beholdt, mens oppsettet er omformet (stier under `/api`, økter fra serveren, Administrator-økt fra en fixture, høyst 10 plasser per forespørsel eller rå innsettinger). Én endring i oppførsel: en avvisning fra databasen uten navngitt constraint gir nå 500 (`internal_error`), så retry-testen for en definitiv avvisning tvinger fram en navngitt constraint. I tillegg kommer tester for CSRF (FR-18), tilgang (FR-20), økter (FR-21), inndata (FR-2), migrasjoner (DR-4) og testbrytere (`tests/`). Resten kommer sammen med hver story (PRD NFR-6) |

Byggeperioden er 27. oktober – 15. desember 2026. Denne README-en oppdateres når appen finnes: installasjon, testbrukere, miljøvariabler og skjermbilder legges til da.

## Forutsetninger

- [uv](https://docs.astral.sh/uv/) (installerer Python 3.12 etter behov, se `.python-version`)
- Git
- [Node.js](https://nodejs.org/) 24 LTS eller nyere (tester og utvikling av frontend)
- [Docker](https://www.docker.com/) (kjører databasen nå, og hele plattformen når skjelettet er bygget)

Databasen er PostgreSQL i en Docker-container (PRD §12 Q4, avgjort 2026-11-03; erstatter SQLite fra 2026-11-01). Start den med `docker compose up -d --wait db` (port 55432 på `127.0.0.1`; sett `DB_PORT` for en annen, og da også `BP_DATABASE_URL`). Når skjelett-storyen er bygget, starter `docker compose up --build --wait` hele plattformen (Caddy, FastAPI, Next.js og PostgreSQL) på `http://localhost:8000`, og på `https://localhost:8443` når HTTPS-storyen (FR-24) er bygget. Se spinens Structural Seed. Til da gjelder kommandoene under, som starter backend alene.

## Kom i gang

```sh
git clone https://github.com/IBE160-2026/G78-larsen.git
cd G78-larsen
uv sync                         # installerer Python og avhengigheter i .venv
docker compose up -d --wait db  # starter PostgreSQL 18 i en container (port 55432)
uv run booking-platform dev     # starter API-et på http://127.0.0.1:8001 med automatisk omstart
```

`uv run booking-platform dev` oppretter databasen `booking_dev` første gang, kjører migrasjonene i `migrations/` og svarer på `http://127.0.0.1:8001/api/health`. `uv run booking-platform serve` gjør det samme uten automatisk omstart.

Konfigurasjonen leses bare fra `BP_*`-miljøvariabler, og alle har en standardverdi som virker lokalt:

| Variabel | Standard | Betydning |
|---|---|---|
| `BP_DATABASE_URL` | `postgresql://postgres:booking@127.0.0.1:55432/booking_dev` | Databasen (`booking_dev` opprettes bare når standard-URL-en brukes) |
| `BP_BASE_URL` | `http://127.0.0.1:3000` | Opprinnelsen nettleseren bruker; skrivende forespørsler må komme derfra (CSRF) |
| `BP_HTTPS` | `off` | Gjør øktkapselen `Secure`; krever at `BP_BASE_URL` begynner med `https://` |
| `BP_HOST`, `BP_PORT` | `127.0.0.1`, `8001` | Hvor backend lytter |
| `BP_ROOT` | repoets rot | Rot for `migrations/` og `config/` |
| `BP_TEST_SWITCHES` | `config/test-switches.toml` | Testbrytere. Kopier `config/test-switches.example.toml` dit for å bruke dem; mangler filen, er alle av |

### Tester

```sh
uv run pytest            # starter databasen, oppretter booking_test på nytt og starter backend som en egen prosess
```

`uv run pytest` kjører først `docker compose up -d --wait db`, så Docker må kjøre. Testene sender ekte HTTP-forespørsler til en ekte backend-prosess (`uv run booking-platform serve`) mot ekte PostgreSQL, og skriver også rett til databasen for å omgå API-et (FR-10). Hele settet tar ca. to minutter. `BP_TEST_MUTATE=<navn>` slår av én beskyttelse i databasen (se `MUTATIONS` i `tests/conftest.py`) for å vise at testene da feiler.

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
config/                 Eksempel på testbryterfil (den ekte filen committes ikke)
tests/                  API-tester mot ekte backend og PostgreSQL
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
