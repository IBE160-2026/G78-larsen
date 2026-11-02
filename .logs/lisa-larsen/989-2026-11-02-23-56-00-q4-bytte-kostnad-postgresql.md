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
