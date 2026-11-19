# PRD: §10-tabellen viser planlagt v1 og gulvet

## 2026-11-19 kl. 13:00 — Lisa Larsen

### Oppgave
Lisa spurte om spørsmålene i `tilbakemelding-prd.md` var avklart: «Hva er kjernen i tesen i den versjonen som faktisk leveres (4.1)?» og «Hvilke FR-er bygges, og hvilke er bare spesifisert (4.2)?». 4.1 var avklart i §1. Første rad i §10-tabellen («Built now: FR-1 to FR-24 (+ FR-25 to FR-33 if time)») stemte ikke med beslutningen om `/goal`, og Lisa ba om at den ble rettet.

### Plan
- Dele raden i «Planned, built with `/goal`» (FR-1–FR-33) og «Floor if the build falls short» (FR-1–FR-24).

### Resultat
- `prd.md` §10: tabellen har nå tre rader. «Planned, built with `/goal`» er FR-1–FR-33 (Core FR-1–FR-23 og If-time 1–3 FR-24–FR-33, §4.1–§4.9). «Floor if the build falls short» er FR-1–FR-24 (Core pluss HTTPS, §4.1–§4.7). «Specified, not planned» er FR-34–FR-51.
- Uhell: før redigeringen ble `prd.md` ved en feil publisert som en privat artifact på claude.ai (https://claude.ai/artifact/5SXJPbSyKjuV4ZZbUN7VXs, versjon 1, uten tabellendringen). Den er privat og ikke delt med noen. Lisa avgjør om den skal slettes.
- Ikke committet.

### Åpne punkter
- Avgjør om den feilpubliserte artifacten av `prd.md` skal slettes.
