# Arkitektur: HTTPS (§4.7) og endringer (§4.8)

## 2026-11-19 kl. 20:24 — Lisa Larsen

### Oppgave
Oppdatere arkitekturspinen med tillegget for HTTPS (§4.7, FR-24) og endringer og Vouchere (§4.8, FR-25 til FR-28), og avgjøre valget mellom refusjon og Voucher når en hel badstue avbestilles (FR-33). Tillegget blokkerte resten: det måtte på plass før If-time 1–3-storyene skrives til `/goal`-kjøringen. Fremgangsmåten var den samme som for §4.9, bare mindre.

### Plan
- `bmad-architecture`, oppdatering, coaching-sti, bare spinen som leveranse. Gjenopptatt fra `.memlog.md` i [spine-mappa](../../.docs/planning-artifacts/architecture/architecture-booking-platform-2026-11-03/).
- Lest PRD §4.7, §4.8, FR-16, FR-17, FR-20, FR-21 og FR-33, token-tabellen i addendum A og UX-flytene for Manage og Voucher. Versjonene er sjekket på PyPI: cryptography 50.0.2, og uvicorn 0.54.0 har TLS-parametrene.
- Seks valg lagt fram med alternativer. Lisa valgte alle anbefalingene.
- Reviewer-gate med fire parallelle reviewere: sjekkliste, motpart, teknologi og avstemming mot PRD-en. Fire produktvalg fra gaten gikk tilbake til Lisa, og resten ble rettet direkte.

### Resultat
- **Spinen:** `ARCHITECTURE-SPINE.md` har `status: final`, scope «Core + If-time 1–3» og binds FR-1..FR-33.
  - **AD-27 HTTPS:** sertifikatet lages ved første start med `cryptography`. Det gir en lokal CA med NameConstraints for localhost og et blad på 365 dager, i `certs/`. Én prosess har HTTPS på :8443 og en lytter på :8000 som bare sender 308 videre. Plattformen har én origin, base-URL-en. HSTS er `max-age=3600`, og headerne legges på i en ytre ASGI-wrapper. HTTPS er på i test og hos sensor og av i dev (`booking-platform dev`, 127.0.0.1:5173). Testene for HT-1 til HT-4 er beskrevet, og det samme er grensene på localhost.
  - **AD-28 Manage-lenke:**
    - Tokenet står i fragmentet `#t=` og byttes mot en tilgang på sesjonen, med 30 min glidende levetid og aldri forbi slutten på Vinduet.
    - `access_tokens` (hash, `purpose`) og `manage_grants` lagrer token og tilgang.
    - Bare de som oppretter en booking, utsteder token. Endringer rører det aldri.
    - Rutene er delt per type booking, og svaret er 404 med eller uten sesjon.
    - GET-svaret gir ingen hemmeligheter.
  - **AD-29 Endringer:**
    - `bookings.version` gir `booking_changed`, og `change_invalid` dekker resten av ugyldige endringer.
    - En historikkrad per endring, med CHECK per handling.
    - En delt-ut booking får egne felt.
    - Kolonnene `cancelled_at`, `cancel_cause` og `cancel_remedy` har CHECK-er.
    - Svarene har én felles form, og det står i en tabell hvilke e-poster hver endring sender.
  - **AD-30 Voucher:** saldoen trekkes med én betinget UPDATE etter `lock_windows`. Koden har 80 bit og lagres bare som hash; at hashen er uten nøkkel, er akseptert. Det er én Voucher per booking. Utløpet er en dato i Venue-tid. Et quote-endepunkt gir tallene til Review, og bookingen sender med `voucher_part_ore`. `retention_due()` avgjør når persondata slettes.
  - **AD-31 Refusjon:** hver retur blir en `payments`-rad, og en ledger-regel sjekkes i modelltesten. `refund()` returnerer også Voucher-koden. En returnert Voucher får minst 30 dager. Voucher-valget i FR-33 gir ett år på hele beløpet.
  - **Endret:** AD-3 (READ COMMITTED), AD-4 (Cutoff-migrering, to unntak fra «reads never write»), AD-8, AD-9 (fingeravtrykk av forespørselen, nøkler per handling), AD-12 (`change_id` på e-post), AD-13, AD-16 (nye koder), AD-18, AD-22 (byggerekkefølge), AD-24, AD-25 og AD-26. I tillegg er seed, ER-diagram, kapabilitetskart, konvensjoner og Deferred oppdatert.
- **Lisas valg** (logget i memlog):
  - Sertifikatet lages ved første start. HSTS er kort og kan endres. HTTPS er på i test og hos sensor og av i dev.
  - Token i fragment med tilgang på sesjonen. Saldo med betinget UPDATE. Kode på 80 bit lagret som hash. Én Voucher per booking. Refusjonen går samme vei som betalingen. Kanselleringskolonner.
  - Etter gaten: ingen Manage-lenke i e-posten etter en endring, én e-post per endring, minst 30 dager på en returnert Voucher, og ett år på hele beløpet ved Voucher-valget i FR-33.
- **Reviews:** `reviews/review-{rubric,adversarial,tech-currency,reconcile-prd}-4-7-4-8-2026-11-19.md`. Til sammen 6 høye funn, alle samme tre saker. Rettet eller avgjort.
- Lint viser bare falske treff på plassholdere (`{reference}` og `{token}` i API-stier).
- Spinen, memlog og reviewene er committet i `5ca5ded`.
- PRD og addendum følger spinen (commit `PRD §7, FR-21, FR-24, FR-27, FR-28, FR-33 …`). §7: endrings-e-posten har ingen Manage-lenke, og en Voucher står i endringens ene e-post. FR-21: cookien settes også når en Manage-lenke åpnes. FR-24: avviket for HT-3 på localhost er notert. FR-27: én e-post per endring. FR-28: 30-dagersgrensen; antagelsen er fjernet fra teksten og fra §13. FR-33: ett år på hele beløpet. Alle sju står i addendum M.3, datert 2026-11-19.
- **Lukket i issues.md:** endre spinen for Manage-lenke og vouchersaldo (2026-11-03) og refusjon/Voucher for FR-33 i §4.8-tillegget (2026-11-19).

- **Rydding i issues.md:** 4 utdaterte punkter er lukket: databasemotor, HTTPS som kjerne eller hvis-tid, `sauna_id` og §12 Q5/Q14. 5 punkter har fått en merknad om hva som nå er dekket: DS-29/DS-33, arkitektur/UX/epics, FR-34–FR-51 i epics, base-URL og README-sikkerhet.

### Åpne punkter
- README (FR-24-storyen) skal forklare:
  - advarselen fra nettleseren, og at import av CA-en er valgfri og gjelder bare localhost;
  - at `ca-key.pem` aldri skal deles;
  - `curl -i http://localhost:8000/` for HT-1;
  - avviket for Secure-cookies på localhost.
- Hvordan en delt Seat-booking fordeler betalingen ved refusjon, avgjøres i If-time 7. Til da gir `refund()` 500 for bookinger som er delt.
