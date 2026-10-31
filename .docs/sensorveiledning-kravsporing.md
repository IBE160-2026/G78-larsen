# Kravsporing mot sensorveiledning, del 1

Kilde: *Sensorveiledning – Del 1, IBE160 høst 2026*. Del 1 teller 70 % av karakteren. PRD §8.1 kobler allerede hvert kriterium til krav (DR-1 til DR-5, NFR-1, NFR-6). Denne tabellen viser status per 2026-10-31 og hva som må på plass, ut fra det sensor faktisk ser etter.

Status per 2026-10-31: planlegging er sterk, men det finnes ingen app, ingen tester, ingen grener, issues eller pull requests. Mesteparten av arbeidet gjenstår.

| # | Kriterium (vekt) | Status nå | Gjenstår | Når |
|---|---|---|---|---|
| 1 | Prosess og KI-styring (30 %) | **Sterk planlegging:** brief, PRD, tre research-rapporter og sju sesjonslogger. 111 commits fra 7. sept., jevnt fordelt i oktober. **Mangler:** arkitektur, epics og stories, grener, PR-er, issues, og commits som viser kode | Arkitektur og stories med FR-referanser. Én gren og én PR per story (PR-mal finnes). Commit-meldinger med story/FR-nummer. Issues for store punkter fra `issues.md`. Logg avvist og rettet KI-output (DR-1) | Fortløpende |
| 2 | Funksjonalitet og omfang (20 %) | Ingen app. `src/` er en «Hello»-plassholder | Bygg Core (PRD §4.1–4.6) først, deretter «hvis tid» i rekkefølgen i §10.1. Dokumenter det som ikke leveres (DR-2) | 27.10–8.12 |
| 3 | Kvalitetssikring og testing (15 %) | Ingen tester. Testtilfeller finnes i brief-addendumet (IV, PW, RB, HT, CT) og PRD (FR-konsekvenser) | `pytest` med test per story (NFR-6), parallell kapasitetstest mot ekte database (FR-11), valideringstester (IV), tilgangstester (RB). Manuell testplan for flyten. Før funn fra kodegjennomgang inn i PR-ene | Sammen med hver story |
| 4 | Design og brukeropplevelse (10 %) | Retning er beskrevet (PRD §6, §7, FR-22, FR-23), men ingen UX-dokumenter | Kjør `bmad-ux` (DESIGN.md og EXPERIENCE.md) før frontend. Tilgjengelighetssjekk og tastaturtest. Mobil er satt til sist i trinn 2, men sensor «prøver gjerne ulike skjermstørrelser» | Før frontend |
| 5 | Kodekvalitet og arkitektur (10 %) | Ingen kode å vurdere. Arkitektur ikke skrevet | `bmad-architecture` (databasemotor, lås per vindu, utledet plassering, Q4/Q5/Q14). Legg til linter/formatter (for eksempel ruff) og kjør i CI eller før commit | Før første story |
| 6 | README og kjørbarhet (10 %) | README er omskrevet 2026-10-31: ærlig status, mappestruktur, lenker til planer. Installasjon gjelder foreløpig bare plassholderen | Når appen finnes: eksakte kommandoer for backend, frontend og database, `.env.example`, testbruker (admin), seed, testkjøring, skjermbilder. Sjekk på en ren maskin eller ny klone | Løpende, endelig i frysen 9.–15.12 |
| 7 | Ryddighet i repoet (5 %) | Bra: `.gitignore` dekker `.venv`, `.env`, `__pycache__`; ingen `__pycache__` eller `.venv` er sporet; ingen hemmeligheter funnet. `.docs/`, `.logs/`, `_bmad/` er tydelig skilt fra `src/` | Skill seed, tester og kode i egne mapper (DR-5). Hold rotmappa uten løse filer. Sjekk historikken for hemmeligheter før innlevering | Løpende |

## Varseltegn i veiledningen (kapittel 5) som gjelder her

- **«Hele koden i få commits rett før fristen».** Unngås bare ved å committe små, jevne endringer fra første story. Frysen 9.–15.12 (PRD §8.2) må ikke bli et sted å legge inn kode.
- **«Planleggingsdokumenter beskriver en annen app enn den som er levert».** PRD-en er svært ambisiøs (Step 2, dørkoder, gavekort). Hold PRD, README og leveranse i samsvar: det som ikke bygges, skal stå som ikke levert (DR-2, SM-4).
- **«Dokumentasjon av KI-bruk er generell».** Hver PR og hver sesjonslogg skal peke på konkrete endringer.
- **README-kommandoer som ikke virker.** Hver kommando i README skal kjøres på en ren klone før innlevering.

## Beslutninger som venter på deg

1. Q17 i PRD: frys 9.–15.12, tokenbudsjett per story og planleggingsdybde er ikke bekreftet.
2. Q4: databasemotor (PostgreSQL i Docker eller SQLite). Påvirker kjørbarhet (kriterium 6) og hvordan FR-10 bygges.
3. Rekkefølgen på «hvis tid» punkt 3–6 er ikke backcastet fra 15.12.

## Medlemmer og samarbeid

Lisa er eneste student og byggeren (README, PRD). De fem commitene fra Bård Pettersen (7. sept.–27. okt.) er sensorens: oppsett av repoet, tilbakemelding på briefen og sesjonslogg-skillen. Veiledningen trekker ikke for ujevn fordeling alene.
