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

## 2026-11-03 kl. 02:10 — Lisa Larsen

### Oppgave
Lisa ba om å bevise FR-10 for hel-badstue-bookinger og blokker på PostgreSQL (kapasiteten endrer seg; Core-spiken dekket bare fast kapasitet). Før dette er Core-beviset committet og pushet (`b562695`).

### Plan
- Ny spike i scratchpad (`fr10_whole_blocks.py`) på `postgres:18`: `saunas`, `windows(seat_capacity, booked)` + CHECK, `bookings`, `whole_bookings`, `blocks(tstzrange)`; triggere som utleder tallene per vindu fra kilderadene, vindusrad låst først, og en utsatt kontrolltrigger ved COMMIT.
- Deterministiske råskrivinger utenom appen, løp (C2, C6), firerløp, stresstest mot en uavhengig Python-referanse, og mutasjonskjøringer som slår av ett lag om gangen.

### Resultat
- 52 av 52 sjekker bestått (hel badstue, blokker over flere vinduer alt-eller-ingenting, F1, D1/D5/D7, dobbelt utelukking, `booked`/`seat_capacity` kan ikke skrives for hånd, 100 runder C2 og C6 med ekte konkurranse, firerløp, stress 6×150 mot brute-force-referanse, ingen inkonsistent snapshot).
- Funn: første kjøring ga 773 vranglåser fordi fremmednøkkelsjekken tar delt lås på vindusraden før AFTER-triggeren; BEFORE-triggere som låser i id-rekkefølge ga 0. Flersetnings-enheter må låse alle vinduer i id-rekkefølge før første skriving (20 av 20 vranglåste uten, 0 av 20 med).
- Mutasjon: uten vindulås men med utsatt kontroll ingen overselling, men falsk «full» i 100 av 100 runder der begge forespørsler passet; uten begge lag solgte løpene over i 100 av 100; uten bare den utsatte kontrollen ble løpene trygge, men tamper-testene feilet.
- Skrevet inn i `addendum.md` A (FR-10, linje 26 ff.) og `prd.md` Q14. Ikke committet. Containeren er fjernet; skriptene ligger i scratchpad, ikke i repoet.
- Ikke dekket: hold, markering/frigjøring og Release time, startede vinduer, FR-29 «Room ahead» (applikasjonsregel), ekte app-stack.

### Åpne punkter
- FR-10 for hold, markering/frigjøring, Release time og startede vinduer; bypass- og race-test mot ekte app-stack i Core-storyene.
- Arkitektur: `lock_windows`-regelen og retry på 40P01/40001.

## 2026-11-03 kl. 03:40 — Lisa Larsen

### Oppgave
Lisa ba om å bevise FR-10 for hold på PostgreSQL. Før dette er beviset for hel badstue og blokker committet og pushet (`c2efac7`).

### Plan
- Bygge videre på spike 2 (`fr10_holds.py` i scratchpad): `held`-teller og `CHECK (booked + held <= seat_capacity)`, `holds`-tabell med 10-minutters-CHECK, testklokke (`app_now()`), og gjenberegning av `held` fra ikke-utløpte rader under vindulåsen i hver skriving.
- 52 gamle sjekker som regresjon, nye H-tester (rå skrivinger, utløp uten opprydding, forbruk av eget hold, endre størrelse, blokk, kapasitetsendring, tamper), hold-løp og stress med tikkende klokke.
- Mutasjoner: `nohold`, `nofresh`, `nolock`, `noverify`, `nolock+noverify`.

### Resultat
- 108 av 108 sjekker bestått; stress ga 0 vranglåsretter og ingen inkonsistent snapshot.
- Mutasjoner: uten `held` i CHECK feilet 25; hvis utløpte hold telles feilet 4 (ingen får siste plass i sen-betaling-løpet, 100 av 100); uten vindulås feilet 2 (falsk «full», ikke overselling); uten utsatt kontroll feilet 4 (bare tamper); uten begge solgte løpene over.
- Regler funnet: vis ledige plasser fra radene, ikke telleren (kan være for høy etter utløp, trygt); frigjør hold før booking (samme transaksjon eller én CTE-setning), ellers avvises bookingen; hold + blokk i samme transaksjon.
- Skrevet inn i `addendum.md` A og «Holds are data». Ikke committet. Containeren er fjernet; skriptene ligger i scratchpad, ikke i repoet.
- Ikke dekket: bookingfrist i hold-levetid, én hold per økt, grense per kilde-adresse, markering/frigjøring og Release time, startede vinduer, FR-29 «Room ahead», ekte app-stack.

### Åpne punkter
- FR-10 for markering/frigjøring, Release time og startede vinduer; bypass- og race-test mot ekte app-stack i Core-storyene.
- Hold-reglene til arkitekturen (se issues.md).

## 2026-11-03 kl. 06:10 — Lisa Larsen

### Oppgave
Lisa ba om å bevise FR-10 for markering («kun hel booking») og frigjøring (Release time) på PostgreSQL. Før dette er hold-beviset committet og pushet (`4ef2b4a`).

### Plan
- Ny spike (`fr10_marks.py` i scratchpad) oppå hold-spiken: `marks`, `settings` (Release time på/av, Europa/Oslo), `releases` (adskilt fra `marks`), kapasitet utledet av klokka, Room ahead-sjekker for hel booking og markering (D8, B1–B3), regelen for startede vinduer (FR-29), og catch-up av forfalte frigjøringer når Release time endres.
- 108 gamle sjekker som regresjon, nye MK-/RL-tester, løp (MR1–MR3), stress med klokke som passerer Release time, mutasjoner.

### Resultat
- 168 av 168 sjekker bestått i flere hele kjøringer; stress med 8 gjenværende markeringer og 8 registrerte frigjøringer, 0 vranglåsretter, ingen inkonsistent snapshot.
- Egen feil funnet og rettet underveis: `seats_left()` leste lagret kapasitet og skjulte en forfalt frigjøring (RL2, RL5d); nå utledet fra radene. Stressen nådde først ikke Release time (klokka endte 04:43Z) og hadde ingen markeringer igjen; rettet med større klokkesteg, utsådde markeringer og færre unmark.
- Mutasjoner fullført: `noroom` (5 feil), `norelease` (10 feil). `nosettrig` avbrutt (RL4b feilet som forventet). Resten ikke kjørt: systemet stoppet bakgrunnsjobben pga. lite minne, og jeg startet den ikke på nytt.
- Uforklart: HR6 feilet i 1 av 100 runder i `nosettrig`-kjøringen; ikke gjenskapt (400 av 400 alene; åtte andre hele kjøringer rene). Ført åpent i addendum A og issues.md.
- Skrevet inn i `addendum.md` A. Ikke committet. Containeren er fjernet; Docker Desktop står fortsatt åpen (bruker ca. 2 GB). Skriptene ligger i scratchpad, ikke i repoet.

### Åpne punkter
- HR6-avviket; fullføre mutasjonskjøringene hvis Lisa vil; bypass- og race-test mot ekte app-stack; applikasjonsreglene og marks-reglene til arkitekturen (se issues.md).
