# Kravsporing mot sensorveiledning, del 1

Kilde: *Sensorveiledning – Del 1, IBE160 høst 2026*. Del 1 teller 70 % av karakteren. PRD §8.1 kobler allerede hvert kriterium til krav (DR-1 til DR-5, NFR-1, NFR-6). Denne tabellen viser status per 2026-10-31 og hva som må på plass, ut fra det sensor faktisk ser etter.

Status per 2026-10-31: planlegging er sterk, men det finnes ingen app, ingen tester, ingen grener, issues eller pull requests. Mesteparten av arbeidet gjenstår.

| # | Kriterium (vekt) | Status nå | Gjenstår | Når |
|---|---|---|---|---|
| 1 | Prosess og KI-styring (30 %) | **Sterk planlegging:** brief, PRD, tre research-rapporter og sju sesjonslogger. 111 commits fra 7. sept., jevnt fordelt i oktober. **Mangler:** arkitektur, epics og stories, grener, PR-er, issues, og commits som viser kode | Arkitektur og stories med FR-referanser. Én gren og én PR per story (PR-mal finnes). Commit-meldinger med story/FR-nummer. Issues for store punkter fra `issues.md`. Logg avvist og rettet KI-output (DR-1) | Fortløpende |
| 2 | Funksjonalitet og omfang (20 %) | **2026-11-24:** Core er bygget (Epic 1 og 2) og går over HTTPS (Epic 3, FR-24). Epic 4: **FR-25** (Story 4.1): Manage-lenken i bekreftelses-e-posten åpner bookingen uten konto, `test_fr25_manage_link.py` og e2e `test_fr25_manage.py`. **FR-26** (Story 4.2): gjesten flytter alle eller noen plasser til en annen økt før Cutoff; en deling gir en ny booking med egen referanse og Manage-lenke, og bookinglisten viser status og endringshistorikk. Testet i `test_fr26_move.py` (alle avvisninger, gjentak, fire kappløp × 100) og e2e `test_fr26_move.py`. FR-27 og videre er ikke levert (README «Ikke levert») | Bygg Core (PRD §4.1–4.6) først, deretter «hvis tid» i rekkefølgen i §10.1. Dokumenter det som ikke leveres (DR-2) | 27.10–4.12 |
| 3 | Kvalitetssikring og testing (15 %) | **2026-11-21:** 536 tester (`uv run pytest`): API-tester mot ekte backend og PostgreSQL, og e2e-tester med Playwright og axe-core mot hele stakken. Testtilfellene kommer fra brief-addendumet (IV, PW, RB, HT, CT) og PRD-en (FR-konsekvenser) | `pytest` med test per story (NFR-6), parallell kapasitetstest mot ekte database (FR-11), valideringstester (IV), tilgangstester (RB). Manuell testplan for flyten: de manuelle tilgjengelighetstestene for Core står i [`tests/manual/core-accessibility.md`](../tests/manual/core-accessibility.md) (Story 2.4). Før funn fra kodegjennomgang inn i PR-ene | Sammen med hver story |
| 4 | Design og brukeropplevelse (10 %) | Retning er beskrevet (PRD §6, §7, FR-22, FR-23), men ingen UX-dokumenter | Kjør `bmad-ux` (DESIGN.md og EXPERIENCE.md) før frontend. Tilgjengelighetssjekk og tastaturtest. Mobil er satt til sist i trinn 2, men sensor «prøver gjerne ulike skjermstørrelser» | Før frontend |
| 5 | Kodekvalitet og arkitektur (10 %) | Ingen kode å vurdere. Arkitektur ikke skrevet | `bmad-architecture` (databasemotor, lås per vindu, utledet plassering, Q4/Q5/Q14). Legg til linter/formatter (for eksempel ruff) og kjør i CI eller før commit | Før første story |
| 6 | README og kjørbarhet (10 %) | **2026-11-21 (Story 2.4):** README er skrevet om til sensors kjøreguide: tre verktøy, `docker compose up --build --wait`, utviklingskommandoer, forberedelser og `uv run pytest`, testinnlogging for Administrator, eksempelbookingene, bookinglisten og Outbox, drift (`create-admin`, testbrytere, logger, `down`, `down -v`), sikkerhet og «Ikke levert». Alle innstillinger har standardverdier, så ingen `.env`-fil trengs. En fersk klone av `main` i en ny mappe er kjørt etter README-en (se sesjonsloggen for Story 2.4 del B) | Skjermbilder. Oppdater «Ikke levert» for hver epic. Ny klone-sjekk i frysen | Løpende, endelig i frysen 12.–15.12 |
| 7 | Ryddighet i repoet (5 %) | Bra: `.gitignore` dekker `.venv`, `.env`, `__pycache__`; ingen `__pycache__` eller `.venv` er sporet; ingen hemmeligheter funnet. `.docs/`, `.logs/`, `_bmad/` er tydelig skilt fra `src/` | Skill seed, tester og kode i egne mapper (DR-5). Hold rotmappa uten løse filer. Sjekk historikken for hemmeligheter før innlevering | Løpende |

## Varseltegn i veiledningen (kapittel 5) som gjelder her

- **«Hele koden i få commits rett før fristen».** Unngås bare ved å committe små, jevne endringer fra første story. Frysen 12.–15.12 (PRD §8.2) må ikke bli et sted å legge inn kode.
- **«Planleggingsdokumenter beskriver en annen app enn den som er levert».** PRD-en er svært ambisiøs (Step 2, dørkoder, gavekort). Hold PRD, README og leveranse i samsvar: det som ikke bygges, skal stå som ikke levert (DR-2, SM-4).
- **«Dokumentasjon av KI-bruk er generell».** Hver PR og hver sesjonslogg skal peke på konkrete endringer.
- **README-kommandoer som ikke virker.** Hver kommando i README skal kjøres på en ren klone før innlevering.

## Beslutninger som venter på deg

1. ~~Q17 i PRD~~ Avgjort 2026-11-06: tokenbudsjett per story er droppet. Bekreftet 2026-11-01: frys (funksjonsstopp 11.12, frys 12.–15.12) og planleggingsdybde (slank: Core i full arkitektur, Core-stories i to puljer, epics bare for HTTPS og «hvis tid» 2).
2. ~~Q4: databasemotor~~ Avgjort 2026-11-03: PostgreSQL i Docker (erstatter SQLite fra 2026-11-01). FR-10 bygges med CHECK og trigger og må bevises på PostgreSQL; SQLite-spiken gjelder ikke lenger.
3. ~~Backcasting fra 15.12~~ Kjørt og avgjort 2026-11-01 (`backcasting-2026-11-01.md`): trolig v1 er Core + HTTPS, og rekkefølgen på «hvis tid» 3–6 avgjøres når «hvis tid» 2 er sammenslått. Det som ikke nås, står som ikke levert (DR-2).

## Medlemmer og samarbeid

Lisa er eneste student og byggeren (README, PRD). De fem commitene fra Bård Pettersen (7. sept.–27. okt.) er sensorens: oppsett av repoet, tilbakemelding på briefen og sesjonslogg-skillen. Veiledningen trekker ikke for ujevn fordeling alene.
