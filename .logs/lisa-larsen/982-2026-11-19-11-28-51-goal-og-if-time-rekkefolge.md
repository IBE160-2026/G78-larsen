# /goal-kjøring og If time-rekkefølgen

## 2026-11-19 kl. 11:28 — Lisa Larsen

### Oppgave
Ny forutsetning: senere skal en `/goal`-kommando la Claude bygge hele den planlagte nettsiden autonomt. Lisa spurte om det da blir tid til å ta med endring/avbestilling (§4.8) i If time, og om §4.9 bør komme foran HTTPS i If time-rekkefølgen, slik `tilbakemelding-prd.md` §4.1 foreslår.

### Plan
- Lese §4.7, §4.8, FR-33 i `appendix-fr-29-51.md`, `backcasting-2026-11-01.md` og tilbakemeldingen.
- Sjekke hvor langt koden er kommet (`src/`, `tests/`) og om det finnes epics.

### Resultat
Bare en vurdering. Ingen filer er endret.
- Fakta: «avbestilling» for plasser finnes ikke som egen funksjon i PRD-en. Gjesten kan flytte plasser (FR-26) eller gi dem fra seg mot et Voucher (FR-27), men får aldri penger tilbake. Avbestilling med refusjon finnes bare for hel badstue (FR-33). Det finnes ingen epics ennå. Koden har et backend-skjelett (`app.py`, `db.py`, `schema.sql`) og tester for FR-10 og FR-14.
- §4.8: `/goal` fjerner byggetid som flaskehals, men ikke Lisas tid til verifisering, frysen 12.–15. des. eller kravet om at noe må være planlagt for å bli bygget. Anbefaling: skriv epic og stories for §4.8 nå, og ta det med i `/goal`-kjøringen etter Core og HTTPS, med grønne tester som port. Det gir også SC3, som er innenfor lærerens foreslåtte minimum.
- §4.9 foran HTTPS: anbefales ikke. FR-33 trenger Manage-lenken (FR-25) og Voucher (FR-27) fra §4.8. HTTPS er lite, fullfører SC9 og bør være på plass før Manage-lenker sendes (`https://`-lenker, Secure-cookies). Alternativ for å møte tilbakemeldingen: dele §4.9 i FR-29–FR-32 (booke og Placement) og FR-33, og la FR-29–FR-32 være strekkmål etter §4.8.

### Åpne punkter
- Avgjør om §4.8 skal få epic og stories nå, slik at `/goal`-kjøringen bygger den (PRD §10.3, backcasting).

## 2026-11-19 kl. 11:52 — Lisa Larsen

### Oppgave
Lisa valgte alternativ A: rekkefølgen Core → HTTPS → §4.8 → §4.9 beholdes, §4.9 blir planlagt (epic og stories) slik at `/goal`-kjøringen bygger den, og en beslutningslinje om tilbakemeldingen legges inn i PRD-en.

### Plan
- Flytte §4.9 tilbake fra vedlegget til `prd.md`, og gi vedlegget nytt navn etter innholdet (FR-34–FR-51).
- Oppdatere §0, §10-tabellen, §10.1 (beslutningslinje), §10.3, §12 Q6 og §13.
- B (§4.8 og §4.9 foran HTTPS) og deling av §4.9 ble vurdert i samtalen og valgt bort.

### Resultat
- `appendix-fr-29-51.md` er omdøpt til `appendix-fr-34-51.md` (`git mv`) og har nå bare §4.10–§4.16. §4.9 står igjen i `prd.md` på samme sted som før. Begge deler er sjekket med `diff` mot forrige commit og er ordrett like.
- `prd.md`:
  - Erstatningsseksjonen heter nå «4.10 to 4.16 Specified, not planned», uten §4.9-raden.
  - §10-tabellen: «Built now: FR-1 to FR-24 (+ FR-25 to FR-33 if time), §4.1 to §4.9» og «Specified, not planned: FR-34 to FR-51, §4.10 to §4.16».
  - §10.1 har en ny beslutningslinje: `/goal`-kjøringen, flytting av §4.9 foran HTTPS er vurdert og valgt bort (FR-33 trenger Manage-lenke og Voucher fra §4.8, og HTTPS bør være på plass før Manage-lenker sendes), og §4.9 planlegges i stedet. Antagelsen om rekkefølgen gjelder nå punkt 4–6.
  - §10.3: HTTPS, §4.8 og §4.9 får hver sin epic, og storiene skrives før `/goal`-kjøringen. Arkitekturen avgjør Whole-sauna booking sammen med epicen for If-time 3. FR-34–FR-42 ligger utenfor denne runden.
  - §12 Q6 og §13 er oppdatert.
- Ikke committet.

### Åpne punkter
- §1 og §10.3 sier fortsatt at sannsynlig v1 er «Core plus HTTPS» (backcasting 2026-11-01). Avgjør om det skal endres nå som §4.8 og §4.9 er planlagt for `/goal`-kjøringen.
- Arkitekturen dekker bare Core. FR-29–FR-33 (Fill order, avledet Placement og FR-32 om at forespørsler ikke flettes) må avgjøres før storiene for §4.9 skrives.

## 2026-11-19 kl. 12:03 — Lisa Larsen

### Oppgave
1. Endre «likely v1 = Core plus HTTPS» i PRD-en nå som §4.8 og §4.9 er planlagt. 2. Begynne på arkitekturen for §4.9 (FR-29–FR-33).

### Plan
- PRD §1, §10.1 og §10.3: planlagt v1 = Core + If-time 1–3, med Core + HTTPS som gulv.
- Arkitektur: `bmad-architecture` som oppdatering av `ARCHITECTURE-SPINE.md` (coaching). Gå gjennom det som alt er avgjort, finne punktene der stories kan bygges ulikt, og la Lisa avgjøre dem.

### Resultat
- `prd.md`: I §1 står det nå at planlagt v1 er Core pluss HTTPS, Change Seats or take a Voucher og Whole-sauna booking. Core alene beviser at en plass aldri oversselges, Whole-sauna booking og Placement beviser resten, og Core + HTTPS er gulvet (DR-2). §10.1 (beslutningslinjen) og §10.3 sier det samme.
- Arkitektur (`architecture-booking-platform-2026-11-03/`): Lisa avgjorde:
  - AD-23: heldagsbookingen er en rad i `bookings` (`kind = 'whole'`, `sauna_id` satt, `seats` NULL) og hører sammen med en rad i `whole_bookings` (`booking_id` UNIQUE) som bare finnes mens bookingen er aktiv, kontrollert ved COMMIT. Avbestilling setter status og sletter kapasitetsraden. Flytting oppdaterer begge radene, beholder referansen og skriver en historikkrad. `saunas.whole_price_ore`; ulik pris gir `price_differs`. Fristen på 72 t ligger i `settings`.
  - AD-24: én SQL-funksjon, `whole_bookable(wid, sid)`, brukes av triggeren ved INSERT og UPDATE (lukker hullet der en flytting gikk forbi FR-29-sjekken i `0001`) og av Private sauna-lista. Avvisningskoden er `sauna_unavailable`.
  - AD-25: `placement(wid)` er eneste utregning av Placement.
  - AD-26: FR-31 testes med én Hypothesis-tilstandsmaskin (6.170.15, sjekket på PyPI) gjennom `services` mot ekte PostgreSQL. Senere If-time-punkter legger til sine handlinger der.
  - Refusjon eller Voucher ved avbestilling (FR-33) avgjøres sammen med §4.8 (Deferred).
- Spinen har `status: draft`. Lint-sjekken fant ett lavt, falskt treff (`{reference}` i AD-12). Kontrollrunden (reviewer gate) er ikke kjørt.
- Committet: PRD i `611854f`, arkitektur-spinen og memloggen i `dfb472b`.

### Åpne punkter
- Kjør kontrollrunden (reviewer gate) på spinen (rubrikk, versjonssjekk og en motstander som prøver å finne to stories som følger alle AD-ene men likevel ikke passer sammen), rett funnene og sett `status: final`.
- §4.8-tillegget til spinen må avgjøre refusjon og Voucher også for FR-33 før storiene for §4.9 skrives.

## 2026-11-19 kl. 12:29 — Lisa Larsen

### Oppgave
Kjøre kontrollrunden (reviewer gate) på arkitektur-spinen etter AD-23–AD-26, rette funnene og ferdigstille spinen.

### Plan
- Lint-sjekk med `lint_spine.py`, deretter fire uavhengige gjennomganger samtidig: sjekkliste, versjoner (Hypothesis), motstander (to stories som følger alle AD-ene men ikke passer sammen) og PRD §4.9 mot spinen.
- Rette det som følger av PRD-en og eksisterende AD-er, og bare spørre Lisa om reelle produktvalg.

### Resultat
- Rapportene ligger i `architecture-booking-platform-2026-11-03/reviews/*-2026-11-19.md`: sjekkliste (3 høy, 10 middels, 7 lav), motstander (1 kritisk, 4 høy, 7 middels, 2 lav), versjoner (Hypothesis 6.170.15 bekreftet ved å installere den; 3 middels, 4 lav) og PRD mot spine (1 høy, 8 middels, 9 lav). Funnene overlappet mye.
- Rettet i spinen:
  - Kritisk: `whole_bookable` telte sin egen rad i triggeren, så regelen for startede økter kunne forsvinne. Den har nå `ignore_booking` og bruker `mark_closed`.
  - Avvisningskoder: navngitte avvisninger fra databasen (`CONSTRAINT`). Rekkefølgen er `outside_horizon` → `deadline_passed` → `cutoff_passed` → `sauna_unavailable`.
  - Paringssjekken (`check_whole_pair`) står på begge tabellene med fast skriverekkefølge, og `kind` kan ikke endres.
  - Flytting kan bytte badstue. `price_differs` gjelder bare ved bytte til en annen badstue, og fristen sjekkes på målet.
  - Endepunktet for heldagsbooking fra den første kodeversjonen fjernes, og testhjelperen `raw_whole` erstatter det.
  - Én serializer for Booking-JSON.
  - Låserekkefølge for handlinger som starter fra en booking: les, lås, les på nytt (AD-3).
  - `window_started` og frist per booking med `change_allowed` (FR-39).
  - Engangsnøkler er bundet til type og mål.
  - E-post returneres i hvert endringssvar, og vilkårstekst finnes per type.
  - Seed-dataene fyller tomme referansekolonner.
  - `placement()` gir én rad per badstue med tilstand og vises bare for administratoren.
  - Innstillinger for Hypothesis: nullstilling per eksempel, ingen deadline, profiler, klokke-regel.
  - Testkonvensjoner for gruppe C og katalogeksempler.
  - `scope`/`binds` sier at FR-33 bare er dekket for kapasitetsdelen.
  - Deferred: §4.8-tillegget før `/goal`-kjøringen; badstuepriser velges av Lisa; F2 senere.
- Lint etter rettingene: bare det kjente falske treffet. Spinen har nå `status: final`, og memloggen har fått `spine finalized`.
- Spinen, memloggen og rapportene er committet i `dcb9cda`.

### Åpne punkter
- Lisa velger prisene for hel badstue og hvilke badstuer som kan bookes hele, i den første §4.9-storyen (seed-dataene).
- Fristen lagres nå per booking (AD-4, FR-39). Kolonnen kommer med epicen for If-time 2 og påvirker også bookinger av enkeltplasser.

## 2026-11-19 kl. 12:30 — Lisa Larsen

### Oppgave
Pushe dagens commits til origin.

### Plan
- `git push` på `main`.

### Resultat
16 commits pushet til `origin/main` (`6793ab8..b417d0b`): PRD-endringene, vedlegget, arkitektur-spinen med kontrollrunden og sesjonsloggene.

### Åpne punkter
Ingen nye.
