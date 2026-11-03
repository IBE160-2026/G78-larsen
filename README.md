# G78 — Saunalöyly Booking Platform

Gruppeprosjekt i **IBE160 Programmering med KI** ved Høgskolen i Molde, høsten 2026 (15 studiepoeng). Repoet inneholder applikasjonen og dokumentasjonen av hvordan den er planlagt, bygget og kvalitetssikret med KI (BMAD og Claude Code).

## Medlemmer

- Lisa Katarina Larsen

## Hva appen skal gjøre

Saunalöyly er et fiktivt, finsk-inspirert badstuanlegg med fire eller flere badstuer. Plattformen lar gjester velge dag og antall plasser, se hvilke tidsvinduer som har ledige plasser og hva det koster, og betale uten konto. Administrator logger inn og ser hvem som kommer til hvert vindu. Betaling, e-post og dørlåser er simulert.

Det vanskelige er kapasiteten: plasser og hele badstuer trekker på de samme rommene, og plattformen skal aldri selge samme plass to ganger, heller ikke når to gjester trykker «Pay» i samme sekund. Hele kravsettet står i [PRD-en](.docs/planning-artifacts/prds/prd-booking-platform-2026-10-29/prd.md).

## Status (2026-10-31)

| Del | Status |
|---|---|
| Product brief | Ferdig |
| Research (samtidighet, kapasitetsmodell, dørkoder) | Ferdig |
| PRD | Utkast, kjerne (Core) og «hvis tid» er beskrevet, `status: draft` |
| UX, arkitektur, epics og stories | Ikke startet |
| Applikasjon | **Ikke bygget.** `src/booking_platform/` inneholder bare et oppstartspunkt som skriver én linje |
| Automatiserte tester | Ingen ennå. De kommer sammen med hver story (PRD NFR-6) |

Byggeperioden er 27. oktober – 15. desember 2026. Denne README-en oppdateres når appen finnes: installasjon, testbrukere, miljøvariabler og skjermbilder legges til da.

## Forutsetninger

- [uv](https://docs.astral.sh/uv/) (installerer Python 3.12 etter behov, se `.python-version`)
- Git
- [Docker](https://www.docker.com/) (kjører databasen)

Databasen er PostgreSQL i en Docker-container (PRD §12 Q4, avgjort 2026-11-03; erstatter SQLite fra 2026-11-01). Kommandoen for å starte den skrives inn her når appen finnes. Frontend (Node.js) bestemmes i arkitekturfasen og skrives inn her når den er valgt.

## Kom i gang

```sh
git clone https://github.com/IBE160-2026/G78-larsen.git
cd G78-larsen
uv sync                  # installerer Python og avhengigheter i .venv
uv run booking-platform  # skriver «Hello from booking-platform!» (plassholder)
```

### Tester

Ingen tester finnes ennå. Når de kommer, kjøres de med `uv run pytest`, og kommandoen oppdateres her.

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
src/booking_platform/   Python-pakke (backend)
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
