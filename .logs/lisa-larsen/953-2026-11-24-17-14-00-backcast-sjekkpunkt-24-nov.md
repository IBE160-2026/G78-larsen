# Backcast-sjekkpunkt 24.11

## 2026-11-24 kl. 17:14 — Lisa Larsen

### Oppgave
Lisa ba om å kjøre backcasten på nytt ved sjekkpunktet 24.11 med den faktiske farten per story. Hun ville vite om Epic 5 rekker å bli ferdig før funksjonsstopp 11.12.

### Plan
- Les [backcasting-2026-11-01.md](../../.docs/planning-artifacts/backcasting-2026-11-01.md), `sprint-status.yaml` og PRD §10.1.
- Mål farten fra git-historikken: hvilken dag hver story ble ferdig, og diffstørrelsen per story.
- Sammenlign størrelsen på de gjenstående storyene i `epics.md` med de ferdige.
- Skriv resultatet som en ny seksjon i backcasting-dokumentet.

### Resultat
- Ny seksjon «Checkpoint Tue 24 November» nederst i `.docs/planning-artifacts/backcasting-2026-11-01.md` (committet i `c8e9790`).
- Farten: 12 stories på 3 arbeidsdager (20., 21. og 24.11). Core-en var 10 stories og ble ferdig 24.11, en uke før målet 1.12. HTTPS (3.1) er også ferdig.
- Sjekkpunktene: 8.11 bestått (Core-skiven `3bcd940` og `7d991d9` 3.11), 24.11 bestått, og 27.11 allerede bestått.
- Det gjenstår 7 stories (4.3, 4.4 og 5.1–5.5), omtrent like store som de ferdige. De tar ca. 2 arbeidsdager i målt fart, og 7 dager med 1 story per dag. Det er 10 kalenderdager fra 25.11 til 4.12. **Epic 5 er innen rekkevidde**, og planlagt v1 (Core + hvis-tid 1–3) kan leveres med SC2–SC4.
- Risikoer som farten ikke viser: Epic 5 endrer kapasitetsinvarianten (AD-6), 5.5 er den tyngste teststoryen (FR-31), timer per dag er ukjent, og det finnes ustabile tester i `issues.md`.
- Nye sjekkpunkter: 27.11 Epic 4 merget, 2.12 5.1–5.3 merget, og 4.12 Epic 5 ferdig. Hvis tiden ikke strekker til, droppes 5.4 først. 9.–11.12 er fortsatt buffer.

### Åpne punkter
- Hvis-tid 4–7 har ingen epics. Når Epic 5 er merget, avgjør PRD §12 Q6. Velg deretter mellom `bmad-correct-course` for «My booking»-resend (§4.10) og å bruke ekstradagene på gjeld og tidlig frysarbeid.
