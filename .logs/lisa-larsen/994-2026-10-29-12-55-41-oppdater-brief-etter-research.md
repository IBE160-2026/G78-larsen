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

Ikke gjort: polering etter `doc_standards` (`bmad-review` med structure og prose) er hoppet over for å spare tokens. `brief.md` er nå ca. 2 600 ord, over målet på 1–2 sider; verdt en kortning ved neste runde. Brainstormens utsettelse av 10-minutters hold er ført inn i en oppfølging samme dag (se over).

### Åpne punkter
- Polering av `brief.md` og `addendum.md` (`bmad-review` structure, prose) er ikke kjørt; briefen er ca. 2 600 ord og bør kortes ned mot 1–2 sider.
