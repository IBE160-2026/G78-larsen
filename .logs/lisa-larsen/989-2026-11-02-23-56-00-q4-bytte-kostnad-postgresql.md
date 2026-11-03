# Q4: kostnad ved å bytte fra SQLite til PostgreSQL

## 2026-11-02 kl. 23:56 — Lisa Larsen

### Oppgave
Lisa spurte om det er mulig å bytte fra SQLite til PostgreSQL etter at kjernen er bygget, og om PostgreSQL trengs for hel-badstue-bookinger og blokker (addendum A), V1 «hvis tid», trinn 2 og/eller visjon (spiken dekket bare Core). Deretter ba hun om at svaret føres inn som «switch cost»-notat i PRD §12 Q4.

### Plan
- Les PRD (§4.9, §4.13, §4.17, §12 Q4, NFR-1/6/11), addendum A og kapasitetsresearchen; ingen kode kjørt.
- Svare per fase i en tabell, og føre en kort kostnadsnotis inn under Q4.

### Resultat
- Svar i chat: bytte er mulig, og kostnaden ligger i låsingen, ikke SQL-syntaksen. PostgreSQL trengs ikke for hel badstue, blokker, hvis-tid 2–7 eller trinn 2 (den globale skrivelåsen serialiserer dem); først i visjon (ekte betaling, flere nettsteder, flere servere).
- Endret `.docs/planning-artifacts/prds/prd-booking-platform-2026-10-29/prd.md`: nytt underpunkt «Switch cost (noted 2026-11-02)» under §12 Q4. Ikke committet i denne økten (bare loggfilene committes her).
- Notatet hviler på PRD og research, ikke på test; spiken for hel badstue og blokker gjenstår (allerede åpent punkt fra 2026-11-01, ikke duplisert).

### Åpne punkter
- Arkitekturen må ta inn regelen fra notatet: hver skriveenhet låser vinduene den berører i starttidsrekkefølge, i én funksjon i datalaget, også på SQLite, så et senere bytte ikke skjuler racer.

## 2026-11-03 kl. 00:15 — Lisa Larsen

### Oppgave
Lisa ba om å bytte databasemotor til PostgreSQL. (Commit og push av notatet fra 2026-11-02 skjedde før dette: `8add5b5`, pushet.)

### Plan
- Finne alle levende dokumenter som sier SQLite/ingen Docker, og oppdatere dem konsistent; la historiske filer (reconcile-*, review-*, prd-v0, forskning) stå.
- Ingen kode finnes ennå, så byttet er en dokumentendring.

### Resultat
- `prd.md`: NFR-1 (Docker tilbake), §10.3 (låseenhet avgjøres i arkitekturen), §12 Q4 (omskrevet: PostgreSQL i Docker, avgjort 2026-11-03, grunn ikke oppgitt, konsekvenser; «switch cost»-notatet erstattet av én linje), Q14 (åpnet igjen, anbefaling vindusrader med `SELECT … FOR UPDATE`).
- `addendum.md`: A (PostgreSQL valgt, SQLite kun til referanse, spiken merket som SQLite-spesifikk, FR-10-trigger må bevises på PostgreSQL, versjonspåstander) og M (installasjonsrad byttet om).
- `.memlog.md`: beslutningsoppføring. `README.md`: Docker under forutsetninger, PostgreSQL i stedet for SQLite. `.docs/sensorveiledning-kravsporing.md`: beslutning 2 oppdatert.
- Ikke committet (bare loggfilene committes her); ikke pushet. Ingen kode eller docker-compose laget.
- Antakelse jeg la inn: Docker kjører PostgreSQL. Bekreftet av Lisa samme dag (PRD Q4 oppdatert). Igjen som `[ASSUMPTION]` i NFR-1: én kommando per start (database, backend, frontend) og én for alle tester.

### Åpne punkter
- Bevis FR-10 for hel badstue, blokker og hold; spiken (se under) dekket bare Core.
- Pin PostgreSQL-hovedversjon i README, legg inn startkommando, test ren klone med Docker.
- Q14 låseenhet er åpen igjen; arkitekturen avgjør.
- Grunnen til byttet er ikke oppgitt.

## 2026-11-03 kl. 00:50 — Lisa Larsen

### Oppgave
Lisa ba om å bevise FR-10 på PostgreSQL (SQLite-spiken gjaldt ikke lenger). Før dette: doc-endringene fra byttet er committet og pushet (`f3daa4c`).

### Plan
- Starte Docker Desktop (daemonen ssto av) og en `postgres:18`-container.
- Spike i scratchpad: schema med `windows(seat_capacity, booked)` + CHECK, `bookings` og en rad-trigger; råe skrivinger utenom appen, deretter parallelle skrivere på Read Committed uten eksplisitt lås.
- Mutasjonssjekk uten triggeren, så testene ikke er tomme.

### Resultat
- PostgreSQL 18.6: 17 av 17 sjekker bestått (råinsert over kapasitet, multi-rad, oppdatering, flytting, kapasitetsreduksjon avvist med SQLSTATE 23514 og ingenting skrevet; 100 runder × 8 parallelle for siste plass ga nøyaktig én vinner; 50 × 12 blandede størrelser aldri over kapasitet; naiv sjekk-så-insert solgte aldri for mye). Uten triggeren feilet 15 av 17.
- Skrevet inn i `addendum.md` A (FR-10-avsnittet), med begrensninger. Ikke committet.
- Begrensning funnet: `windows.booked` kan skrives ned direkte, og da aksepteres en senere insert over kapasitet.
- Skriptet ligger i scratchpad (`fr10_spike.py`), ikke i repoet. Containeren er fjernet; Docker Desktop startet jeg og lot stå.

### Åpne punkter
- Bevis FR-10 for hel badstue, blokker og hold; skriv bypass- og race-test mot ekte app-stack i Core-storyene; vurder vern mot nedskriving av `booked`.
