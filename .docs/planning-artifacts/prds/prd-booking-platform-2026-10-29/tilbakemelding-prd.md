# Tilbakemelding på PRD

| | |
|---|---|
| **Gruppe** | G78 – G78-larsen |
| **PRD vurdert** | `.docs/planning-artifacts/prds/prd-booking-platform-2026-10-29/prd.md` (status `final`, sist endret 2026-11-09, commit a7a7b54), lest sammen med `addendum.md` |
| **Dato** | 2026-11-12 |
| **Type** | Formativ tilbakemelding, ikke karakter |

## 1. Samlet inntrykk

Dette er en uvanlig sterk PRD: tydelig tese, 51 nummererte FR-er med testbare konsekvenser, et konsekvent glossar og åpenhet om hva som sannsynligvis ikke blir levert. Risikoen ligger i størrelsen (ca. 18 700 ord) og i at den spesifiserer mye mer enn dere planlegger å bygge. Det gjør det vanskeligere å se hva epics og stories faktisk skal hente fra.

## 2. Dette fungerer godt

- **Tesen er eksplisitt og testbar.** §1: «if the capacity rules are precise enough to test, one person can deliver a booking core that never oversells». FR-10 og FR-11 følger opp: dataene avviser overbooking selv når applikasjonen omgås, og kappløpstesten kjøres «against the same kind of data store the platform uses, not a mock».
- **Ærlig scope.** §10.1 deler i Core, If time (rangert), Step 2 og Vision, og sier rett ut at sannsynlig v1 er «the Core plus HTTPS». Avviket fra lærerens minimumsforslag er flagget med `[NOTE FOR PM]`, og §10.3 sier hva som får epics nå.
- **Gode motmål og avgrensninger.** SM-C1 til SM-C4 (f.eks. «Booking speed … must never be gained by weakening the atomic check») og §9 (Non-Goals, bl.a. «No AI features in the app») gjør at valg kan forsvares senere.

## 3. Oversikt per dimensjon

| Dimensjon | Vurdering | Kort begrunnelse |
|---|---|---|
| Beslutningsklarhet | sterk | Valg står som datofestede beslutninger, med avveininger i `[NOTE FOR PM]` (f.eks. §4.9 om streng Fill order). |
| Substans | god | Lite pynt og ingen NFR-boilerplate. Noe er likevel detaljer som hører til UX/innhold (kopitekster, juridiske henvisninger). |
| Strategisk sammenheng | god | Klar tese, men sannsynlig v1 inneholder ikke det som gjør tesen spesiell (se 4.1). |
| Testbarhet | sterk | Nesten alle FR-er har konkrete konsekvenser med tall og tester. Noen krever oppslag i andre filer (4.3). |
| Scope og avgrensning | god | Utelatelser er eksplisitte, men spesifikasjonen er langt større enn planlagt bygg (4.2). |
| Brukbarhet for neste fase | god | Glossar og ID-er er ryddige, men PRD-en er lang og lener seg på eksterne tabeller. |
| Formtilpasning | god | UJ-1 til UJ-6 med navngitte hovedpersoner passer et publikumsrettet bookingprodukt. Totalt noe overformalisert for ett semester. |

## 4. Viktigste forbedringer

### 4.1 Tesen og sannsynlig v1 peker ulike veier
- **Alvorlighet:** høy
- **Hvor:** §1 «seats and private saunas in one system»; §10.1 «Lisa accepted the Core plus HTTPS as the likely v1»
- **Problem og hvorfor det betyr noe:** Tesen og forskjellen fra andre tilbydere er at enkeltplasser og hele badstuer deler rom, med Fill order, Placement og blokkering. Core har ingen hel-badstue-booking (FR-29 ff.) og bare ett tall per vindu (summen av Capacity). Det vanskeligste og mest særegne er altså plassert i det som sannsynligvis ikke bygges. Arkitektur og stories får da et uklart signal om hva som er kjernen.
- **Forslag:** Legg til to setninger i §1: «For den versjonen vi sannsynligvis leverer (Core + HTTPS) er satsingen: aldri oversolgt plass under samtidig booking. Hel badstue og Placement er første utvidelse og testes først når §4.9 er bygget.» Vurder også om §4.9 bør komme foran HTTPS i If time-rekkefølgen, siden det er der domenelogikken ligger.

### 4.2 Spesifikasjon utover det dere planlegger å bygge
- **Alvorlighet:** høy
- **Hvor:** §10.3 «If-time 3 to 7 get neither epics nor stories in this round»; FR-29 til FR-51
- **Problem og hvorfor det betyr noe:** Rundt 23 av 51 FR-er (FR-29 til FR-51) er detaljert, men ikke planlagt. Det er lett å miste oversikten, og et epics-arbeid kan ved et uhell dra inn FR-er som ikke skal bygges.
- **Forslag:** Legg en tabell øverst i §10: «Bygges nå: FR-1–FR-24 (+FR-25–FR-28 hvis tid). Spesifisert, ikke planlagt: FR-29–FR-51.» Vurder å flytte FR-29–FR-51 til en egen vedleggsfil, slik at PRD-en blir ca. 40 % kortere og lettere å bruke som kilde.

### 4.3 Testbarhet som krever oppslag i andre filer
- **Alvorlighet:** medium
- **Hvor:** FR-40 «the latest Seat bookings lose (D3)»; FR-32 «(C2)», «(C6)»; FR-31 «catalogue groups A and B hold»
- **Problem og hvorfor det betyr noe:** Mange konsekvenser peker til katalog-ID-er (A6, D3, H12) i en annen rapport. Den som skriver story eller test må åpne et 85-eksempel-katalog for å vite forventet resultat. Der dere skriver tallene inline (FR-12: «42 of 44 Seats booked, a request for 3 is rejected») er det mye tydeligere.
- **Forslag:** Skriv forventet utfall inn for de FR-ene som kommer med i bygget. Eksempel for FR-40: «40 av 44 plasser er booket og Sauna 3 (12 plasser) blokkeres. Kapasiteten blir 32. Bookingene med senest Entry time kanselleres, nyeste først (5 plasser, så 4), til 31 ≤ 32 gjenstår. Begge gjester får valget refusjon eller Voucher.»

### 4.4 Enkelte FR-er er for store til én story eller ett testtilfelle
- **Alvorlighet:** medium
- **Hvor:** FR-1 (landingsside med kopitekst), FR-39 (tabell + ti konsekvenser), FR-40 (ca. tolv konsekvenser)
- **Problem og hvorfor det betyr noe:** FR-1 blander krav med ferdig tekst («Löyly is the steam that rises …»), og FR-40 dekker blokkering, omflytting, kansellering og oppheving. Da blir én story for stor, og det er uklart når FR-en er «ferdig».
- **Forslag:** Gi konsekvensene egne ID-er (FR-40.1, FR-40.2 …) eller del opp i FR-40a/b/c. Flytt ferdig kopitekst til UX-dokumentet og la FR-1 kreve hva siden skal inneholde.

### 4.5 Beslutningslogg og krav blandes
- **Alvorlighet:** lav
- **Hvor:** parenteser som «(… , 2026-11-05)» i mange FR-er; §12 «Open Questions»; §11 SC-tabellen
- **Problem og hvorfor det betyr noe:** Rundt halvparten av §12 er allerede avgjort (Q2–Q7, Q10, Q14, Q17), så listen svarer dårlig på «hva er fortsatt åpent». Navn og datoer midt i FR-tekst gjør utdrag støyende. SC-tabellen mangler kolonne for hvilke FR-er hvert kriterium dekker.
- **Forslag:** Del §12 i «Åpne» og «Avgjort» (flytt de siste til addendum). Samle beslutningsdatoer i addendum M. Legg til kolonnen «FR» i SC-tabellen.

## 5. Mekaniske funn

- ID-er er sammenhengende og unike: FR-1–51, UJ-1–6, SM-1–6, SM-C1–4, NFR-1–11, DR-1–5. Krysshenvisninger jeg sjekket løser seg.
- Glossaret brukes konsekvent. «Whole-booking-only» og «Whole-sauna booking» ligner mye på hverandre, så vær nøye i stories.
- Én `[ASSUMPTION: half-open intervals]` i FR-40 er ikke egen linje i §13 (den er slått sammen med en annen). Elles stemmer indeksen godt.
- Ingen sensitive opplysninger funnet.

## 6. Før dere går videre

**Må avklares før UX/arkitektur/epics:**
- Hva er kjernen i tesen i den versjonen som faktisk leveres (4.1)?
- Hvilke FR-er bygges, og hvilke er bare spesifisert (4.2)?

**Kan vente:** Q1 (to koder på én dør), Q8, Q11, Q12, Q15 og Q16 gjelder Step 2 eller Vision. DR-1 dekker dokumentasjon av KI-bruk i utviklingen. Appen har ingen KI-funksjon, så testing av KI-svar og kostnad gjelder ikke.

**Oppfølging av tilbakemelding på briefen: ja.** Scope er delt i Core/If time/Step 2/Vision, medlemskap, periodekort, fjernstyring og oppvarming ligger i Vision, SC9 er blitt konkrete tester (IV, PW, RB, HT), samtidighetstester er med (FR-11, FR-32), og README med testbruker er krav (DR-2).

## 7. Refleksjonsspørsmål

1. Mange regler i §4.9 og §4.13 er veldig detaljerte. Hvor mye av det kom fra KI-forslag dere godtok, og hvordan sjekket dere at reglene er riktige og ønskede?
2. Core har ingen avbestilling eller endring. Hva vil en bruker eller sensor oppleve som mangler i en app som bare booker og viser en liste, og hvordan veier det mot tidspresset dere beskriver i §8.2?

_Vurdert mot kvalitetsrubrikken i bmad-prd. Dette er veiledning, ikke sensur._
