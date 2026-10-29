# Oppdater brief etter research

## 2026-10-29 kl. 12:55 — Lisa Larsen

### Oppgave
Lisa ba om å oppdatere product brief i forhold til de tre research-rapportene (samtidighet, kapasitetsmodell for enkeltplasser, låsløsninger og dørkoder). Briefen skal bare ta inn det som endrer produktutsagn; detaljer går i addendumet.

### Plan
- `bmad-product-brief` i Update-modus: les brief, addendum, memlogg, brainstorm-logg og de tre rapportene.
- Legg fram hva research endrer, og la Lisa avgjøre de tre funnene som strider mot tidligere beslutninger (vinduer, dørkoder etter sendetid, plassering) samt hvor mye av de åpne tilfellene som skal inn i briefen.
- Fører beslutningene i `.memlog.md`, oppdater `brief.md` og `addendum.md`.

### Resultat
Beslutninger fra Lisa (alle fulgte anbefalingen):
- Tidsvinduer er felles for alle badstuer og overlapper aldri delvis (E1, E3). Avløser antakelsen om ulik lengde per badstue.
- Dørkode-reglene er ikke avhengige av tilbakekalling: etter sendetid nektes hel booking av en badstue så lenge enkeltplass-bookere har koden (H12).
- Briefen krever plasseringsresultat (invarianter), ikke flytting. Utledet eller lagret plassering er arkitektur. Under én-badstue-tilgang fryses plasseringen ved sendetid (H21). Avløser «flytting er tillatt når som helst» og «ny e-post ved flytting» for én-badstue-tilgang.
- Åpne tilfeller står kort i briefens Open Questions, detaljert i addendumet.

Endringer (ikke committet):
- `.docs/planning-artifacts/briefs/brief-booking-platform-2026-09-20/brief.md`: hel-badstue-punktet, dørkode-punktet og SC6, Administration (vinduer), SC1 (parallelle tester, ingen ytelsestall), Open Questions (arkitektur, PRD, ikke testet). `updated: 2026-10-29`.
- `addendum.md`: radene Seat placement, Door codes, Time windows og «Fixed in v1»; seksjonene «Open questions» for enkeltplasser og dørkoder; ny seksjon «Research input» med 14 anbefalte tilfeller, samtidighetskrav og testtilnærming.
- `.memlog.md`: fire beslutninger og én endringsoppføring (117 oppføringer).

Oppfølging samme dag: 10-minutters seat hold er «hvis tid» i v1 (beslutning fra brainstorm-minste-v1, 2026-10-27). `brief.md`: ny Scope-linje (v1 reserverer kapasitet atomisk ved bekreftelse; holdet bygges bare hvis tid). `addendum.md`: faseraden for v1, notat under fasetabellen, raden Seat hold, notat under Concurrency tests, og Research input. SC1 er uendret. Beslutningen er ført i `.memlog.md` (118 oppføringer).

Oppfølging 2: resten av «hvis tid»-listen og kjernen fra brainstormen er ført inn. `brief.md`: Scope v1 delt i «Core: must finish» og «If time allows, in this order» (1 avbestilling av enkeltplasser, 2 hel badstue, 3 «min booking», 4 hold, 5 gjestekontoer, 6 trinn 2, 7 resten av v1); SC2–4 og 8 merket «if time», HTTPS åpen, SC10 enkel i kjernen; nye linjer i sammendrag og Open Questions. `addendum.md`: faseraden for v1 delt i kjerne og hvis-tid, ny seksjon «Schedule and build order», frist 15.12.2026. Lisa valgte å plassere v1-punktene brainstormen ikke nevner (admin-skjermer, de fem innstillingene, blokkeringskalender, 06:00-regel, «bare hel badstue»-vinduer, overbooking-fallback) sist, etter trinn 2. Bare «avbestilling før hel badstue» er avgjort av Lisa; resten av rekkefølgen er merket [ASSUMPTION]. Flagget i addendumet: «min booking» med referanse + e-post strider mot token-lenken i Accounts. Lisa avgjorde samme dag at avbestilte enkeltplasser kun gir voucher eller endring (ingen refusjon, heller ikke midlertidig); hvis-tid-punkt 1 er endret til endring først, voucher sist [ASSUMPTION].

Oppfølging 3: «Min booking» (hvis-tid-punkt 3) sender bare token-lenken på nytt til e-posten på bookingen; siden viser ingen data, gir likt svar ved treff og ikke-treff, og har forsøksgrense. Kun lenken gir tilgang. Oppdatert i `brief.md` (punkt 3, Open Questions) og `addendum.md` (faserad, Accounts, Schedule). Token-levetid og hashet lagring er `[ASSUMPTION]` til PRD.

Oppfølging 4: polering kjørt med `bmad-review` (structure, prose). `brief.md`: alle rader godtatt (journey kortet, SC9-underpunkter kortet, Scope flyttet foran Success Criteria, mindre kutt, språkrettinger); 2 593 → 2 355 ord. `addendum.md`: alt unntatt sammenslåingen av «Open questions»-seksjonene (Lisa vil beholde dem): Door codes, Heater, Membership, Period cards og Renewal flyttet fra tabellen til egne underseksjoner, Concurrency tests flyttet til de andre testseksjonene, Research input og Schedule kondensert, if-time-rekkefølgen slått sammen med faseraden, tre språkrettinger; 8 954 → 8 892 ord. Én brief-rad var et spørsmål (innlogging i reiseløpet): løst ved å si at alle gjester i kjernen fortsetter uten konto.

Ikke gjort (opprinnelig): polering etter `doc_standards` (`bmad-review` med structure og prose) er hoppet over for å spare tokens. `brief.md` er nå ca. 2 600 ord, over målet på 1–2 sider; verdt en kortning ved neste runde. Brainstormens utsettelse av 10-minutters hold er ført inn i en oppfølging samme dag (se over).

### Åpne punkter
- `brief.md` er fortsatt ca. 2 350 ord, over målet på 1–2 sider; videre kortning krever at innhold flyttes eller fjernes.

## 2026-10-29 kl. 13:39 — Lisa Larsen

### Oppgave
Endre responsiv-rekkefølgen i brief og addendum: lag webside (desktop) først, og mobil etterpå, i stedet for «mobile first».

### Plan
- Finne alle steder som sier «mobile first» / responsivt i `brief.md` og `addendum.md`.
- Endre bare rekkefølgen, ikke kravet: SC10 (responsivt på mobil, nettbrett og desktop) står fast.

### Resultat
Tre små tekstendringer, ikke committet (arbeidsendring i brief-mappen):
- `brief.md`, Scope-kjernen: «A simple responsive design» → desktop først, mobil-layout følger når desktop-siden fungerer.
- `brief.md`, SC10: «one stylesheet, mobile first» → «one stylesheet, desktop first; the mobile layout is added afterwards, once the desktop website works».
- `addendum.md`, Risk handling: «mobile first» → «desktop first with the mobile layout added afterwards».
`.memlog.md` er ikke oppdatert med denne endringen. Native mobilapper er fortsatt utenfor omfanget (uendret).


### Oppfølging (samme økt): laptop først
Lisa endret rekkefølgen igjen: laptop-versjon først, deretter mobil og desktop hvis tid. Avløser «desktop først, mobil etterpå» over.
- `brief.md`: Scope-kjernen sier «a simple layout for a laptop screen; mobile and desktop layouts are if time allows»; nytt hvis-tid-punkt 8 (mobil- og desktop-layout, etter at laptop-layoutet fungerer); SC10 delt i laptop (kjerne) og mobil/desktop (hvis tid); «core is done when» og setningen om hvis-tid-kriterier justert tilsvarende.
- `addendum.md`, Risk handling: «laptop layout first, with mobile and desktop layouts if time allows».
- Plasseringen sist i hvis-tid-listen er en antakelse; ikke committet; `.memlog.md` ikke oppdatert.

### Åpne punkter
- Plasseringen av mobil/desktop (punkt 8) sist i hvis-tid-listen er en antakelse; bekreft i PRD.

## 2026-10-29 kl. 13:54 — Lisa Larsen

### Oppgave
Lisa ba om at v1 og «hvis tid» i v1 kommer før trinn 2, at hvis-tid-punkt 6 endres tilsvarende, og at mobil- og desktop-layout kommer sist i trinn 2.

### Plan
- Flytte «resten av v1» (administratorskjermer, blokkeringskalender, 06:00-regel m.m.) foran trinn 2 i hvis-tid-listen.
- Flytte mobil/desktop fra eget punkt 8 til siste punkt i trinn 2.
- Rette alle steder som viser til rekkefølgen: Scope, Success Criteria (innledning, SC8, SC10), faseraden og Risk handling i addendumet.

### Resultat
Ikke committet (arbeidsendring i brief-mappen):
- `brief.md`: hvis-tid-listen har nå 7 punkter (6 = resten av v1, 7 = trinn 2); overskriften er «Step 2 (item 7 above), in this order» med mobil/desktop som siste punkt; setningen om rekkefølge sier at v1 og dets hvis-tid-punkter kommer før trinn 2 og at mobil/desktop kommer sist i trinn 2; kjernens layoutsetning, SC8 («if time, before step 2»), SC10 og innledningen til Success Criteria er rettet tilsvarende.
- `addendum.md`: faseradene «v1 if time» (6 = resten av v1, 7 = trinn 2) og «Step 2» (mobil/desktop sist), og Risk handling.
Rekkefølgen er nå Lisas beslutning, ikke en antakelse. `.memlog.md` er ikke oppdatert.

### Åpne punkter
Ingen.

## 2026-10-29 kl. 14:03 — Lisa Larsen

### Oppgave
Lisa ba om å ta desktop ut av briefen og addendumet, slik at bare laptop (kjerne) og mobil (sist i trinn 2, hvis tid) står igjen.

### Plan
- Finne alle forekomster av «desktop» i `brief.md` og `addendum.md` (5 + 2).
- Endre «mobile and desktop» til «mobile» i Scope, trinn 2, Success Criteria (innledning og SC10) og Risk handling/faseraden i addendumet.
- La `.memlog.md` og eldre loggfiler stå urørt (historikk).

### Resultat
- `brief.md`: Scope-kjernen («the mobile layout comes last in step 2, if time allows»), rekkefølgesetningen, trinn 2-punktet («Mobile layout, last, …»), Success Criteria-innledningen («the mobile part of 10») og SC10 («on mobile and at any window size») er rettet.
- `addendum.md`: faseraden for trinn 2 («mobile layout last», «Mobile layout, after the laptop layout works») og Risk handling («the mobile layout last in step 2 if time allows»).
- Verifisert at alle 5 + 2 forekomster er byttet. `.memlog.md` nevner fortsatt desktop som historikk og er ikke endret.

### Åpne punkter
Ingen.

## 2026-10-29 kl. 14:15 — Lisa Larsen

### Oppgave
Lisa spurte om `sauna_id` bør følge hver plass fra dag én, slik at hel-badstue-booking blir en utvidelse og ikke en omskriving, og ba om at svaret føres inn i `issues.md`.

### Plan
- Støtte svaret på addendumets Seat placement-rad (forskningen anbefaler utledet plassering).
- Føre anbefalingen inn som eget åpent punkt, uten å lukke det opprinnelige punktet fra brainstorm-minste-v1.

### Resultat
- Anbefaling: ikke `sauna_id` per plass; plassering utledes fra antall per vindu. `sauna_id` på blokkeringer og hel-badstue-bookinger, én kapasitetsfunksjon over ledige badstuer fra v1, nullable «plassert i badstue»-kolonne for én-badstue-tilgang i trinn 2.
- Ført inn i `issues.md`. Ingen endringer i brief eller addendum. Forskningsfila selv er ikke lest på nytt.

### Åpne punkter
- Arkitekturbeslutningen om plassering og `sauna_id` er ikke tatt (ført i `issues.md`).
