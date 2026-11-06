# Validation Report — Saunalöyly Booking Platform

- **DESIGN.md:** `C:/Booking platform/G78-larsen/.docs/planning-artifacts/ux-designs/ux-booking-platform-2026-11-05/DESIGN.md`
- **EXPERIENCE.md:** `C:/Booking platform/G78-larsen/.docs/planning-artifacts/ux-designs/ux-booking-platform-2026-11-05/EXPERIENCE.md`
- **Run at:** 2026-11-06 10:47

## Overall verdict

Spine-paret holder som kontrakt for det meste av Core: alle 58 unike token-referanser resolver, alle 32 komponenter finnes i begge spines, og UJ-navnene er ordrette. Svakheten ligger i feil- og gjenopprettingsstiene for Book seats og Review, der fire high-funn tvinger story-dev til å ta beslutninger selv: motstridende feilmønster, tapt fokus etter refusal, radioer som bytter kontekst, og manglende cold-load. Ingen funn er critical, men disse fire bør lukkes før stories for Book seats og Review skrives.

Tilgjengelighet og innhold endrer bildet: dokumentene er solide på tokens, komponenter og samsvar med kildene, men ikke ferdige der gjesten står i en feil eller et kjøp. Kontrastene består, men en bygging etter kontrakten gir ikke WCAG 2.2 AA, og PRD-ens påstand om at Core oppfyller WCAG 2.0 AA fullt ut må testes. Gjesten mangler dessuten vilkår og personvernerklæring, adresse og kontakt i bekreftelsen, og en sjekk av e-posten før et kjøp som ikke kan endres.

Alle linsene sier 0 critical. Rapportene har 100 funn, og 14 high blir 12 unike. Disse 12 bør lukkes før stories for Book seats, Review og Confirmation skrives. Dokumentene har allerede status final fra 5. november, så endringene er en oppdatering av ferdigstilte dokumenter.

## Category verdicts

- Flow coverage — adequate
- Token completeness — strong
- Component coverage — adequate
- State coverage — adequate
- Visual reference coverage — adequate
- Bloat & overspecification — adequate
- Inheritance discipline — adequate
- Shape fit — strong

## Funn per linse

| Linse | Critical | High | Medium | Low | Sum |
|---|---|---|---|---|---|
| Rubrikk | 0 | 4 | 14 | 19 | 37 |
| Tilgjengelighet | 0 | 5 | 15 | 13 | 33 |
| Innhold | 0 | 5 | 13 | 12 | 30 |
| **Sum** | 0 | 14 | 42 | 44 | 100 |

## De 12 unike high-funnene

| # | Funn | Funnet av |
|---|---|---|
| 1 | Feilmønsteret på Book seats motsier seg selv | Rubrikk high; Tilgjengelighet A-06 medium |
| 2 | Fokus forsvinner når Pay fjernes etter avvisning | Rubrikk high; Tilgjengelighet A-01 high |
| 3 | Nearest sessions laster Review på nytt ved piltast | Rubrikk high; Tilgjengelighet A-02 high |
| 4 | Details og Review mangler direkte lasting, og Back etter betaling er ubeskrevet | Rubrikk high; Innhold M-11 medium |
| 5 | Zoom under 1366 px er ikke lovet, og det rammer 1.4.4 | Tilgjengelighet A-03 high |
| 6 | Sidetitler er ikke spesifisert | Tilgjengelighet A-04 high |
| 7 | Radiogruppene har ikke noe gruppenavn | Tilgjengelighet A-05 high |
| 8 | Setningen om ingen refusjon har ikke noe unntak når stedet avlyser | Innhold H-1 high |
| 9 | Bekreftelsen sier ikke hvem eller hvor | Innhold H-2 high |
| 10 | Navn og e-post vises ikke på Review | Innhold H-3 high; Tilgjengelighet A-11 medium |
| 11 | Ny nøkkel etter tapt økt kan gi dobbel Booking og betaling | Innhold H-4 high |
| 12 | Terms og Privacy notice er ikke skrevet | Innhold H-5 high |

## Beslutninger for Lisa

| Tema | Spørsmål |
|---|---|
| Refusjonssetningen (H-1) | Går imot en lukket beslutning: Open Item 11 og FR-5 mot PRD §9. Må setningen få et unntak når Saunalöyly avlyser? |
| "never alone" (Innhold M-8) | Går imot en lukket beslutning: Open Item 12. Skal regelen stå, eller byttes til noe gjesten faktisk kan følge? |
| Zoom (A-03) | Skal laget 1024–1365 px og en enkel enspalteløsning flyttes inn i Core, eller skal unntaket i FR-23 utvides og sies åpent? |
| Administrator og FR-51 (A-18) | Skal Administrator-sidene få smal layout, eller skal FR-51 endres? |
| Tapt økt og nøkkel (H-4, cold-load) | Hvor lever valg, navn, e-post og nøkkel, og skal nøkkelraden overleve økten? Dette kan endre AD-8 og AD-9. |
| Bekreftelsen (H-2, H-3) | Skal Venue og kontakt inn i FR-8 og §7, og Name og Email inn på Review, innenfor plassbudsjettet? |
| Terms og Privacy notice (H-5) | Når skal de skrives? Flere andre funn må løses i disse tekstene. |

## Findings by severity

### Critical (0)

### High (14)

**[State coverage]** — Feilmønsteret på Book seats er selvmotsigende.
Field error er "Always with an Error summary" (E 251), og Error summary "Takes focus" (E 250). FR-23 krever begge (PRD linje 443). E 232 sier derimot Field error alene med fokus på spørsmålet, og E 300–301 sier Field error alene ved datofeil. En Error summary er heller ikke regnet inn i budsjettet på 570 px (D 379).
Fix: bestem ett mønster for Book seats, inkludert fokusmål, og sjekk det mot første visning ved 1366 × 768.

**[State coverage]** — Fokus etter refusal er udefinert.
Pay "Keeps focus while processing" (E 210), og etter en refusal fjernes Pay, payment note og Terms checkbox (E 322). Notice annonseres "without moving focus" (E 380). Tastaturbrukeren står da på et element som ikke lenger finnes, midt i climax for taperen i Flow 2. Regelen om fokus ved route change (E 366) dekker ikke dette, for Guest "stays on Review". Manuell tastaturpass kreves av FR-23.
Fix: flytt fokus til Notice ved refusal, og lag et unntak i E 380. Si også hvor fokus lander når Review lastes på nytt med valgt Session.

**[State coverage]** — Nearest sessions på Review bytter kontekst ved input.
Valg er radioer med piltaster (E 365, `key-review.html` linje 101), og å velge "reloads Review" (E 322, se også E 249). Ingen knapp bekrefter valget, så piltast til neste rad laster siden på nytt. Da kan tastaturbrukere ikke nå rad to og tre, og det bryter WCAG 3.2.2 On Input (FR-23).
Fix: legg til en egen handling for valgt rad. Pay er borte i denne tilstanden, så sidens ene Primary button er ledig. Alternativt kan radene være Text links.

**[State coverage]** — Details og Review mangler cold-load.
Ingen state dekker direkte adresse eller reload uten valgt Session, og IA gir bare rute for Confirmation (E 46). E 316 lover at reload returnerer første utfall, men AD-9 lar SPA-en lage nøkkelen når Guest når Review, og ingen spine sier hvor valg, navn, e-post og nøkkel overlever en reload. Browser Back fra Confirmation til Review er heller ikke dekket (E 368).
Fix: legg til states for "Details/Review uten valg" og "Back etter betalt Booking", og si hva som er lagret hvor.

**[Tilgjengelighet]** — A-01 Avvisning fjerner knappen som har fokus (2.4.3, 4.1.3) (§ `EXPERIENCE.md` linje 322 (After a refusal), 210 (Keeps focus while processing), 248 og 380 (Notices announced without moving focus). `DESIGN.md` linje 383.)
Når plassene blir tatt mens brukeren betaler, fjernes Pay, som har fokus. Dokumentene sier ikke hvor fokus skal, og linje 380 forbyr å flytte det. Notice står foran i DOM, under Back. En skjermleserbruker kan bli stående uten fokus, høre meldingen delvis eller ikke i det hele tatt, og lete forover fra et sted der løsningen ligger bak. Det rammer akkurat det øyeblikket UJ-2 handler om. Linje 321 ("please try again") sier heller ikke om Pay blir værende, selv om linje 322 kaller alle avvisninger like.
Fix: Legg til en generell regel: når elementet med fokus forsvinner, flyttes fokus til nærmeste meningsbærende etterfølger. På Review er det Notice (`tabindex="-1"`). Gjør dette til et uttrykkelig unntak fra linje 380. Si også at Pay blir værende ved "please try again". Samme regel gjelder når Notice forsvinner på Book seats etter valg av Nearest sessions.

**[Tilgjengelighet]** — A-02 Nearest sessions laster siden på nytt når brukeren flytter med piltast (3.2.2) (§ `EXPERIENCE.md` linje 249, 322, 365, 475–476 (Flow 2), `DESIGN.md` linje 434. Mock: `key-review.html` linje 101.)
Radioer velges allerede når piltasten trykkes, og å velge en rad laster Review på nytt. En tastaturbruker som trykker pil ned fra rad 1 for å høre på rad 2, blir sendt videre med rad 2 uten å ha bestemt seg. Rad 3 nås bare med Shift+Tab bakfra. Dette er en kontekstendring ved inndata uten varsel. Lasting på nytt til samme adresse er kanskje ikke en route change, så heller ikke fokusregelen på linje 366 slår inn.
Fix: Vis radene som en liste med ett Text link-lignende valg per rad, hver med egen tabulatorstopp og navn som "Choose Friday 13 November, 19:00 to 20:30, 6 seats left". Alternativt: behold radioene og legg til en Primary button, "Use this session", som bare vises mens Pay er borte, slik at én per side fortsatt holder. Si at fokus etter valget går til overskriften på Review.

**[Tilgjengelighet]** — A-03 Zoom på målmaskinen faller utenfor det som er lovet (1.4.4, 1.4.10) (§ `EXPERIENCE.md` linje 18, 392, 397–399. `DESIGN.md` linje 124, 360, 387. PRD FR-23 linje 435.)
FR-23 unntar bare 1.4.10, men linje 392 sier at alt under 1366 px ikke er lovet for v1. Da faller også 1.4.4 bort, og det er et krav i WCAG 2.0. PRD-ens påstand om at Core "meets it in full" holder altså ikke uten videre. En 1366 px-skjerm på 200 % gir 683 CSS px. Da blir hovedspalten 251 px (683 − 320 − 112) mens datospalten er 348 px, så Book seats får rulling i to retninger og Rail ruller ut til siden. Det trengs ikke engang høy zoom: 1920 × 1080 med 150 % skalering i Windows gir 1280 CSS px, altså under grensen. Svaksynte kommer trolig gjennom med mye rulling, så dette er high og ikke critical, men Rail og Continue må testes. Usikkerhet: 1.4.4 forbyr ikke horisontal rulling i seg selv. Om noe faktisk går tapt, må avgjøres i nettleser.
Fix: Flytt 1024–1365-laget og en enkel enspalteløsning under 1024 px inn i Core, uten Fixed action bar. Addendum linje 393 nevner allerede dette alternativet. Løft "200 % uten tap" inn i FR-23 som eget krav. Beholdes unntaket, må README og Accessibility Floor si at også 1.4.4 er åpent.

**[Tilgjengelighet]** — A-04 Sidetitler er ikke spesifisert (2.4.2) (§ Ordet finnes ikke som krav i `DESIGN.md`, `EXPERIENCE.md` eller Conventions i `ARCHITECTURE-SPINE.md` linje 293. Innholdstabellene på `EXPERIENCE.md` linje 112–120 har ingen rad for det.)
Dette er en React SPA, så uten en regel får alle sider samme statiske `<title>`. Brukere med skjermleser eller mange faner kan ikke skille Review fra Confirmation, og en feiltilstand synes ikke i tittelen.
Fix: Legg en tabell i Content Homes med tittel per side, for eksempel "Book seats – Saunalöyly", "Review – Saunalöyly", "Booking confirmed – Saunalöyly". Legg til prefikset "Error: " når Error summary vises. Tittelen settes før fokus flyttes (linje 366). Husk Terms, Privacy notice, "This page is not available." og Administrator-sidene.

**[Tilgjengelighet]** — A-05 Radiogruppene har ikke noe gruppenavn (1.3.1, 3.3.2, 4.1.2) (§ `EXPERIENCE.md` linje 365 (radio groups), `DESIGN.md` linje 335 (spørsmålene er "Small heading") og 417. Mock: `directions-3.html` linje 145–146.)
Dokumentet sier at valgene er radiogrupper, men ikke at gruppen skal ha navn. `DESIGN.md` kaller spørsmålene overskrifter, så den naturlige koden er en overskrift pluss løse radioer. Da hører en skjermleserbruker "3, radio button, 3 of 10" uten å få vite hva tallet gjelder. Mocken gjør nøyaktig dette, uten `fieldset` eller `radiogroup`.
Fix: Krev `fieldset` med `legend` for Seat picker og Session list, med spørsmålsteksten i `legend` (`{typography.heading-md}` kan beholdes). Gi kalenderens radiogruppe navn med måned og år, for eksempel "Pick a day, November 2026". Oppgi også om nummereringen "1.", "2." og "3." skal leses opp.

**[Innhold]** — H-1. Setningen om ingen refusjon har ikke noe unntak når Saunalöyly selv avlyser (§ EXP L158, Required statements; `key-review.html` L95; `key-confirmation.html` L87 og L103.)
Sitat: "A booking cannot be changed or refunded." Setningen er absolutt, men PRD-en sier noe annet for det tilfellet at stedet ikke kan levere. Gjesten blir fortalt at pengene er tapt uansett årsak, også ved stengt anlegg. Det stemmer ikke med produktets egen posisjon og kan villede om gjestens rettigheter. Core har heller ingen vei for dette: Booking list er skrivebeskyttet (EXP L552, PRD Q7) og ingen annen rute tilbys (PRD L233). Kilde: PRD §9 L933: "When Saunalöyly cancels, the Guest chooses between a refund and a Voucher." ADD D L176: "Keeping the money when the trader cancels may be unfair". FR-5 L233 pålegger setningen, så PRD-en er selvmotsigende her.
Fix: Endre til det som faktisk menes: "You cannot change or cancel a booking, and there is no refund if you do not come." Legg til i Terms: "If Saunalöyly has to cancel, you get your money back." Oppdater FR-5 L233, og gjenåpne Open Items 11 (EXP L547). Si også i Terms hvordan gjesten da hører fra stedet.

**[Innhold]** — H-2. Bekreftelsen sier ikke hvem eller hvor (§ `key-confirmation.html` L90–109 (e-post), L85 (side); EXP L116, L252, L426.)
Sitat: "Keep your booking reference and give it at reception when you arrive." E-posten nevner ikke Saunalöyly i det hele tatt: ordet forekommer ikke i brødteksten, og den har heller ikke adresse eller kontakt. Bekreftelsessiden har Wordmark, men ingen adresse eller kontakt, fordi Booking summary bare har Venue-radene på Review (EXP L252). Gjesten får beskjed om å gå til en resepsjon, uten å få vite hvor den er i det eneste varige dokumentet. Har gjesten et spørsmål, står det ingen kontaktvei der. Kilde: PRD §7 L879 og FR-8 L259–266 ramser ikke opp Venue-opplysninger, så mangelen starter i PRD-en. ADD D L168 krever bekreftelse på varig medium, og FR-5 L231 krever Venue-identitet før betaling. Malen følger mocken gjennom antakelsen i EXP L426.
Fix: Legg til rader for Venue og Contact på Confirmation, som på Review, og en blokk øverst i e-posten: "Saunalöyly", adresse, kontakt. Oppdater FR-8 og tabellen i §7.

**[Innhold]** — H-3. Gjesten får ikke sjekket navn og e-post før betaling (§ EXP L45, L170, L252; `key-review.html` L93; Flow 1 EXP L463.)
Sitat: "Check everything, accept the terms, pay" (L45). Booking summary: "On Review it also holds Venue identity and contact details" (L252). Review viser verken navn eller e-post, selv om siden lover "Check everything". E-posten er den eneste kanalen for bekreftelsen, og en skrivefeil oppdages først på Confirmation, etter et kjøp som ikke kan endres. Da har bekreftelsen med personopplysninger gått til en fremmed, og resepsjonens reserveløsning (navn og e-post) treffer dårligere. Kilde: ADD E L249: "use a check-answers page". ADD D L173: forklare "how to correct mistakes" før bestilling. FR-5 L229–232 krever ikke feltene, men forbyr dem heller ikke.
Fix: Legg til radene Name og Email i Booking summary på Review, med Back som rettevei. Kontroller at Pay fortsatt er i første visning ved 1366 × 768 (Lisa, EXP L396). Legg til en linje på Details om at bekreftelsen sendes til denne adressen.

**[Innhold]** — H-4. Antakelsen for tapt nettleserøkt kan gi dobbel Booking og dobbel betaling (§ EXP L342.)
Sitat: "The SPA makes a new browser session and a new key without comment, entered values stay, and the Guest sees \"please try again\"." Etter AD-9 lagres bare suksess, så `409 invalid_key` betyr at nøkkelen allerede har gitt en Booking i en annen økt. Da er det feil svar å lage ny nøkkel og be gjesten prøve igjen: neste trykk på Pay gir en ny Booking og en ny betaling. Gjesten ser ikke den første, og kjøpet kan ikke endres eller refunderes. Tilfellet krever at svaret gikk tapt og at økten utløp, så det er smalt, men følgen er alvorlig. `401 no_session` har samme risiko hvis økten er slettet, for da forsvinner også nøkkelraden (AD-8: `CASCADE`). Kilde: ARCH AD-9 L134–138: "It reuses the same key for every retry of that review", "only a success is stored". FR-6 L246. ARCH AD-8 L123, L126.
Fix: Skill de to kodene. Ved `invalid_key`: ingen ny nøkkel og ingen Pay, men en Notice som ber gjesten kontrollere bekreftelsen før nytt forsøk. Ved `no_session`: la arkitekturen avgjøre om nøkkelraden skal overleve økten til Window er slutt. Dette er en antakelse som må bekreftes før Review bygges.

**[Innhold]** — H-5. Gjesten godtar en tekst som ikke finnes (§ `key-review.html` L95; `key-confirmation.html` L87, L104; EXP L538–539.)
Sitat: "[Rest of the booking terms]" Terms og Privacy notice er ikke skrevet. Dermed er det uavklart hva "I accept the booking terms" binder gjesten til. Det er ført i Open Items, men ingen av punktene har eier eller frist, og flere funn i denne rapporten må løses i disse tekstene. Tekstene trengs i `content/` for både side og e-post (AD-12). §10.1 krever endelig tekst før Core er ferdig. Kilde: PRD §10.1 L955, FR-5, FR-21, ADD D. EXP L532.
Fix: Skriv Terms og Privacy notice før Review og Confirmation regnes som ferdige. Bruk listen under "Manglende innhold" som innholdsliste.

### Medium (42)

**[Flow coverage]** — §4.12 Guest accounts har ingen Key Flow, selv om PRD §7 setter flows for §4.8–§4.12 i scope.
Sign-up, sign-in og My bookings finnes bare i plug-in-tabellen (E 439, 444), og passordreset (FR-37, PRD linje 630) er ikke nevnt noe sted. Se også Open Item 29 (E 571).
Fix: legg til en kort flow for §4.12, eller skriv eksplisitt at den er utsatt, med begrunnelse.

**[Flow coverage]** — FR-33 (cancel eller move av Whole-sauna booking) har ingen steg, bare én setning etter Flow 5 (E 518).
Valget mellom refund og Voucher og det bekreftende steget er ikke beskrevet.
Fix: legg til en Flow 5b, eller en failure-/variantsti med steg.

**[Component coverage]** — Fem rendrede Core-elementer har ingen rad i noen av spinene.
Dette gjelder payment note (E 115, 322; kravet står i FR-6), booking terms-blokken (E 115–116), resepsjonssetningen (E 116), Back (E 114–115, 180, 368) og "Booking confirmed"-overskriften (E 116, 181). Søk i `DESIGN.md` gir null treff på "payment note", "reception" og "Booking confirmed", og booking terms og Back nevnes bare som plassering (D 383). Typografien finnes bare i mockene (`key-review.html`, `key-confirmation.html`).
Fix: gi hvert element en navngitt rad i begge spines, eller si eksplisitt hvilken eksisterende komponent det er.

**[State coverage]** — Error summary-regelen passer ikke overalt.
Hver oppføring er "a link to its field" (E 250, D 435), men Payment failed (E 317) og Wrong email or password (E 349) har ingen felt å lenke til.
Fix: spesifiser oppføring uten lenke, eller et bestemt mål.

**[State coverage]** — Core-feiltekst mangler.
Voice har ingen tekst for Terms not accepted (E 314), manglende dato eller antall Seats (bare "Choose a session", E 190), Date not bookable, typed (E 300), eller Notice når valgt Session nullstilles (E 226). Lesefeil finnes bare som fragmentet "please try again" (E 284, 292, 357), som bryter egen regel om å si hva som skjedde (E 130).
Fix: legg rader i Voice-tabellen.

**[State coverage]** — "No room anywhere in the horizon" gir ingen neste handling (E 299, 189).
Det bryter E 130 og FR-22 ("what the Guest can do next", PRD linje 432).
Fix: legg til ett neste steg, for eksempel færre Seats eller kontaktvei.

**[State coverage]** — Booking list mangler to tilstander: dato uten Sessions og ugyldig typet dato (E 265, 345–357).
Windows genereres fra seed-kjøringsdagen (FR-13), så "Previous day" og "Next day" kan havne der.
Fix: legg til begge rader med tekst.

**[State coverage]** — Lasting og lesefeil er ujevnt dekket.
Bare Book seats har lastetekst (E 291). Confirmation, Booking list og Outbox har ingen lastestate, og Confirmation og Outbox har ingen lesefeil (E 324–329, 345–357).
Fix: legg til én felles regel for lasting og lesefeil.

**[Visual reference coverage]** — Mockene som viser tilstander er ikke lenket der tilstandene spesifiseres.
`key-review.html` viser refused Review (E 318–322), `key-details.html` viser skjemafeil (E 307), og `key-booking-list.html` viser dato uten Bookings (E 354). `EXPERIENCE.md` lenker bare samlet i E 16 og generelt i E 110, og D 431 sier bare "the key-screen mocks in `mockups/`".
Fix: legg en kort referanse per state og per komponent.

**[Bloat & overspecification]** — PRD impact (E 574–592) er historikk.
E 576 sier at alt er overført, og jeg bekreftet det mot PRD og arkitektur (FR-5, §3, §12 Q2 og Q7, AD-12, AD-16). Likevel står punktene som imperativer ("Close §12 Q2", "reword FR-5"), og en AI-konsument kan ta dem som åpne oppgaver.
Fix: flytt seksjonen til `.memlog.md`.

**[Inheritance discipline]** — Spine omtaler PRD slik den var før 2026-11-05.
E 50 sier at PRD §7 lister Details og Review som én, men FR-5 og §7 har to sider (PRD linje 229, 860). E 342 sier at tilstanden mangler i §7-listen, men den står der (PRD linje 873). E 446 og 585 forklarer en "Book action", men PRD sier **Continue booking** (PRD linje 598) og har ingen "Book action".
Fix: rett de tre stedene mot gjeldende PRD.

**[Inheritance discipline]** — Administrator-sider er låst til laptop (E 52, 409; D 385), men FR-51 gjelder "Guests and Administrators" og "Every page" (PRD linje 811, 814).
Avviket er verken i Open Items eller PRD impact.
Fix: be Lisa om en beslutning, og endre enten FR-51 eller spine.

**[Inheritance discipline]** — `extract §14` (E 452, 539, 551, 586) peker til `.working/source-extract.md`, som er forkastet, ikke står i `sources` og ikke forklares i spine.
C13 og C15 bærer reell begrunnelse.
Fix: erstatt med direkte kilder: addendum E og AD-8 for E 551 og E 539. E 452 kan kuttes, siden UJ-ene nå bruker seed-tider.

**[Shape fit]** — En tom linje (E 173) deler den aksepterte teksttabellen.
De 23 radene i E 174–196 mangler header og rendres ikke som tabell, så markdown-parsere mister den største delen av tabellen.
Fix: fjern linje 173.

**[Tilgjengelighet]** — A-06 Feilmodellen på Book seats motsier seg selv (3.3.1, 2.4.3) (§ `EXPERIENCE.md` linje 232 og 300–301 mot linje 250–251 og 381. PRD FR-23 linje 443.)
Linje 232 sier at Continue viser en Field error og flytter fokus dit. Linje 251 sier at en Field error alltid kommer med Error summary, og linje 250 sier at summary tar fokus. Fokusmålet er derfor uklart. Dokumentene sier heller ikke hva som skjer når alle tre svarene mangler, eller hvilket element i en radiogruppe som får fokus. Plassbudsjettet på `DESIGN.md` linje 379 kan ha ført til dette, men FR-23 krever summary.
Fix: Velg én modell. Anbefalt: Error summary øverst i main med fokus og lenker til hvert spørsmål, siden siden kan ha tre feil. Sjekk at det får plass i budsjettet. Knytt Field error til `fieldset` med `aria-describedby`, og la lenken flytte fokus til valgt eller første radio.

**[Tilgjengelighet]** — A-07 Hvert trykk på piltast leser Sessions, endrer total og kan tømme valget (2.1.1 som støtte, 4.1.3) (§ `EXPERIENCE.md` linje 224, 226, 227, 234, 365, 367.)
Pil velger straks. Mus går direkte fra 2 til 6, mens tastatur går innom 3, 4 og 5, med en ny lesing av Sessions og en ny kunngjøring av totalen for hvert steg. Pil opp fra 1 går rundt til 10 og kan tømme en valgt Session. I kalenderen er pil én dag om gangen (linje 379), så 5. til 28. november gir 23 lesinger. Hvert steg tømmer valgt Session (linje 234). Det brutte kravet er ikke klart, men brukeren får mer støy og mister valg musebrukere beholder. Skrevet dato gjør kalenderen mulig å unngå, så dette blokkerer ikke.
Fix: Spesifiser en kort forsinkelse før lesing og kunngjøring, at bare siste svar teller, og at valgt Session først tømmes når verdien har ligget stille. Vurder dag som knapp-rutenett med pil i to retninger og egen bekreftelse hvis manuell test viser at listen er for tung.

**[Tilgjengelighet]** — A-08 Statusmeldinger er ufullstendige og mangler mekanisme (4.1.3) (§ `EXPERIENCE.md` linje 248, 291, 367, 380.)
Linje 380 lister Total block, Notices og "Processing". "Loading sessions" er ikke med, heller ikke at listen er oppdatert eller hvilke rader som ble utilgjengelige da antallet endret seg. Regelen sier ikke at live-regionen må finnes i DOM før innholdet kommer. Total block "appears once a number is chosen" (linje 227), og en region som settes inn sammen med teksten, blir ofte ikke lest opp. Skjermleserbrukeren kan derfor endre antall og aldri få vite at valgene har endret seg.
Fix: Bruk én fast `role="status"`-region per side, tilstede fra første visning. Kunngjør en samlet setning etter at lesingen er ferdig, for eksempel "Total NOK 750. 6 of 8 sessions have room for 3 seats." Legg "Loading sessions" til listen, men bare hvis lesingen tar merkbar tid.

**[Tilgjengelighet]** — A-09 Hint, feil og påkrevd er ikke koblet til feltene i kontrakten (1.3.1, 3.3.1, 3.3.2) (§ `EXPERIENCE.md` linje 215, 251, 381. `DESIGN.md` linje 410, 436. Mock: `directions-3.html` linje 144 (hintet er ikke koblet), `key-details.html` linje 90 (feilen er koblet).)
Kontrakten sier "next to the field", altså plassering, ikke kobling. Bare mocken for Details har `aria-invalid` og `aria-describedby`. Datoformatet er ikke knyttet til datofeltet i mocken, så en blind bruker hører ikke "dd.mm.yyyy" i feltet. Påkrevde felter er ikke merket noe sted. Terms-feil og datofeil finnes ikke som mock.
Fix: Legg til i Text field-regelen: `aria-describedby` til hint og feil, `aria-invalid="true"` ved feil, `required` på alle felter, og `novalidate` slik at Error summary og ikke nettleserens bobler viser feilen. Oppgi rekkefølgen når både hint og feil vises på datofeltet.

**[Tilgjengelighet]** — A-10 Autocomplete er ikke krevd (1.3.5) (§ `EXPERIENCE.md` linje 215, 385. Mock: `key-details.html` linje 82–83 har attributtene, men det er ikke kontrakt.)
"Paste and password managers work" dekker ikke autofyll av navn og e-post. Brukere med motoriske eller kognitive vansker må skrive alt selv, og det er bare mocken som viser løsningen. Sign-in er ikke rendert i det hele tatt.
Fix: Skriv det inn: `autocomplete="name"` og `email` på Details, `username` og `current-password` på Sign-in, `autocomplete="off"` på datofeltet.

**[Tilgjengelighet]** — A-11 Review viser ikke navnet og e-posten brukeren skrev (3.3.4) (§ `EXPERIENCE.md` linje 45 ("Check everything"), 170, 252, 463. Mock: `key-review.html` linje 92.)
En booking kan ikke endres eller refunderes, men en skrivefeil i e-posten vises først på Confirmation (linje 252), etter at betalingen er gjort. Mennesker med dysleksi eller som bruker tale til tekst, er særlig utsatt. Back gjør det mulig å sjekke, så kriteriet er trolig formelt oppfylt, men Review-siden er ikke en full gjennomgang slik linje 45 lover.
Fix: Legg radene "Name" og "Email" til Booking summary på Review. Sjekk mot plassbudsjettet på `DESIGN.md` linje 383 og mot no-repetition-regelen. Dette er ikke en gjentakelse, for Review viser dem ikke andre steder.

**[Tilgjengelighet]** — A-12 Kalenderens månedsnavigasjon og datoinntasting er ikke avklart (2.4.3, 4.1.2, 4.1.3) (§ `EXPERIENCE.md` linje 223, 298, 300–301. `DESIGN.md` linje 416.)
"Next month" er en handling, men er spesifisert som Text link. Horisonten er fire uker, så kontrollen forsvinner eller byttes med "Previous month" etter ett trykk, og fokus kan gå tapt. Månedsbyttet er ikke på listen over statusmeldinger. Det står ikke når en skrevet dato gjelder (hvert tastetrykk, blur eller Enter). Ikke-bookbare dager finnes som tall uten forklaring for skjermleser, selv om `DESIGN.md` linje 397 sier at tilstand alltid sies i ord.
Fix: Bruk `<button>` med lenkeutseende for begge månedsvalg. Hold kontrollen på plass og la fokus stå, eller flytt det til den andre knappen. Kunngjør "December 2026". La skrevet dato gjelde ved blur og Enter, og la feil vises først da. Gi ikke-bookbare dager skjult tekst, for eksempel "3 November, not bookable", eller skjul dem for skjermleser.

**[Tilgjengelighet]** — A-13 Landemerker, overskriftsnivåer og Rail er ikke definert semantisk (1.3.1, 2.4.1, 2.4.6) (§ `EXPERIENCE.md` linje 213, 366. `DESIGN.md` linje 333–335, 408. Mock: `aside` for Rail, ingen `main` på gjestesider.)
Bare én regel om nivå finnes: Wordmark er toppnivå på Landing. `<h1>` på andre sider er ikke fastsatt, og heller ikke om "Before you come" er `h2`. Typografirollene sier størrelse, ikke nivå. Rail følger mocken som `aside`, og da havner den ene handlingen, og på Landing hovedoverskriften, i et komplementært landemerke som skjermleserbrukere ofte hopper over. Ingen hopplenke er vurdert.
Fix: Legg en tabell over nivåer per side. Definer `header`, `main` og `footer` eller `nav`. Rail skal ikke være `aside` når den holder handlingen. Fokusregelen på linje 366 gjør hopplenke unødvendig ved rutebytte, men ikke ved direkte innlasting, så avgjør det eksplisitt.

**[Tilgjengelighet]** — A-14 Tabulatorrekkefølgen på Book seats (åpent punkt 14) (2.4.3, 1.3.2, 3.2.3) (§ `EXPERIENCE.md` linje 377, 550. `DESIGN.md` linje 408. Mock: `directions-3.html` linje 67, 147–149.)
Rekkefølgen dato, plasser, Session, Continue gir mening, så selve hovedvalget består trolig 2.4.3. Det svake punktet er Wordmark, som står øverst visuelt, men kommer etter Continue i DOM. Fokus hopper oppover forbi totalen for en bruker med forstørrelse, og Wordmark står et annet sted i rekkefølgen enn på alle andre sider. Mockens `order:-1` er CSS-omstokking av den typen 1.3.2 advarer mot.
Fix: Del Rail i to rutenett-områder: Wordmark som `header` først i DOM (kolonne 1, rad 1), `main` deretter (kolonne 2), og total, Continue og notater sist (kolonne 1, rad 2). Ingenting gjentas, og Wordmark står først på alle sider. Klebrig plassering må testes med denne delingen.

**[Tilgjengelighet]** — A-15 Utilgjengelige rader forsvinner fra tastatur- og fokusmodus (1.3.1, 4.1.2) (§ `EXPERIENCE.md` linje 225, 226, 294, 378. `DESIGN.md` linje 419.)
Disabled radioer hoppes over av Tab og piltaster. En skjermleserbruker i fokusmodus hører bare valgbare rader, og kan ikke vite at 17:30 finnes og er utsolgt, selv om linje 225 sier at listen skal vise hele timeplanen. Dokumentet tar dette som noe som skal sjekkes, men har ingen løsning hvis sjekken feiler. Usikkerhet: Virkemåten varierer mellom skjermlesere og krever test.
Fix: Bestem løsningen nå: Vis utilgjengelige rader uten radio, som tekst i samme liste, og legg en setning i statusregionen, for eksempel "2 of 8 sessions are not available for 2 seats". Alternativet er `aria-disabled` med stopp i JavaScript, men det gjør radiogruppen mer sårbar.

**[Tilgjengelighet]** — A-16 Faste høyder, ingen bryting og smale kolonner hindrer tekstforstørrelse og tekstavstand (1.4.4, 1.4.12) (§ `DESIGN.md` linje 164, 173, 188 (`height`, ikke `min-height`), 405 ("no wrapping"), 419 (150 px tidskolonne), 99–108 (`lineHeight: '1'`). Accessibility Floor nevner ikke 1.4.12.)
Med bare tekstforstørrelse på 200 % blir klokkeslettet 42 px høyt og omtrent 230 px bredt, i en kolonne på 150 px. "Continue booking" i 34 px vil trolig ikke få plass i Railens 240 px uten bryting. Tekst kan overlappe naboen eller gå utenfor kontrollen. Usikkerhet: Breddene er anslag fra tekststørrelse. Faktisk resultat avhenger av de ekte fontene.
Fix: Bytt til `min-height`, og tillat bryting på Primary button på smale og forstørrede flater. Bruk `minmax()` i radene i stedet for fast 150 px. Legg 1.4.4 og 1.4.12 til i Accessibility Floor.

**[Tilgjengelighet]** — A-17 Fixed action bar kan dekke det meste av en lav skjerm (1.4.10, 2.4.11) (§ `EXPERIENCE.md` linje 228, 382, 403, 405. `DESIGN.md` linje 421. Gjelder med FR-51.)
Total, tillegg, knapp og padding gir omtrent 124 px i en bar som alltid står. En 1366 × 768-skjerm på 400 % har omtrent 155 CSS px sidehøyde igjen, så baren dekker rundt 80 %. Innholdet og fokus forsvinner bak den. Reglene sier "must leave room", men ikke hvordan.
Fix: Sett `scroll-padding-bottom` lik barens høyde. Gjør baren statisk på lave vinduer (`@media (max-height: ...)`). Vis total og knapp på én linje, og flytt per-sete-linjen ut av baren.

**[Tilgjengelighet]** — A-18 Administrator-sidene motsier FR-51 (1.4.10, 1.4.4) (§ `EXPERIENCE.md` linje 52, 409. `DESIGN.md` linje 385. PRD FR-51 linje 810–814.)
FR-51 sier "Guests and Administrators" og "every page" fra 320 px, mens spinen sier laptop-only uten smal layout. Bygger man spinen, lukkes Reflow-unntaket aldri for Sign-in, Booking list og Outbox. Ansatte med svakt syn får ingen zoom-støtte.
Fix: Velg ett. Enten smal layout for Sign-in, Administrator bar og Outbox, med Booking table som egen rullbar region (tabeller er unntatt 1.4.10), eller endre FR-51 og oppgi gapet i README.

**[Tilgjengelighet]** — M-01 Lenker og månedsvalg er `span` i mocken (2.1.1, 4.1.2) (§ `directions-3.html` linje 142 og 149 (Terms, Privacy notice), linje 144 ("Next month").)
Elementene kan ikke nås med tastatur og har ingen rolle. Kopieres dette, kommer tastaturbrukere aldri til neste måned med kalenderen.
Fix: Kontrakten er riktig (Text link). Rett mocken, eller merk den som ikke-interaktiv.

**[Tilgjengelighet]** — M-02 Session-radioene i mocken skjuler tilgjengelighet (4.1.2, 1.3.1) (§ `directions-3.html` linje 146.)
`aria-label="14:30 to 16:00"` overstyrer etiketten. Skjermleserbrukeren hører tiden, men ikke "6 seats left" eller "Sold out". `EXPERIENCE.md` linje 378 vet om dette og vinner, men mocken er det utviklere kopierer.
Fix: Fjern `aria-label` og la etiketten gi navnet. Da får raden både tid og plasser, og A-22 forsvinner samtidig. `key-review.html` linje 101 har allerede rett innhold.

**[Innhold]** — M-1. Uklart hvilke vilkår gjesten godtar og får med seg (§ EXP L169, L181, L538, L425; `key-review.html` L94–97; `key-confirmation.html` L86–88, L101–104.)
Sitat: "I accept the booking terms". "The part shown on Review must stay short, about six lines at most ... The rest belongs on the Terms page." Heading sier "Booking terms", lenken sier "Terms", og avkrysningen sier ikke om den gjelder de seks linjene eller hele siden. Confirmation og e-post har bare kortdelen og ingen lenke til Terms, så gjesten har ikke vilkårene hun godtok i det varige dokumentet. Kilde: FR-5 L232–234, FR-8 L265, ADD D L168, ARCH AD-12 L169.
Fix: Bruk "I accept the booking terms" sammen med lenketeksten "Full booking terms", og vis samme lenke på Confirmation og i e-posten. Avklar om e-posten skal ha hele teksten (se Vilkår, kjøp og personvern).

**[Innhold]** — M-2. "cannot be withdrawn" sier ikke det loven krever at gjesten får vite (§ EXP L157; `key-review.html` L95; `key-confirmation.html` L87, L102.)
Sitat: "A booking for a fixed date cannot be withdrawn." Ordet "withdrawn" er en juridisk term uten kontekst, og setningen nevner ikke retten som faller bort. Rett etter følger "cannot be changed", så den leses lett som en gjentakelse og ikke som opplysning om angrerett. Kilde: FR-5 L232: "has no right of withdrawal". ADD D L164–165.
Fix: "This booking is for a fixed date and time, so there is no right of withdrawal." Endelig ordlyd må sjekkes av jurist ved ekte drift.

**[Innhold]** — M-3. Egen bekreftelse møter gjesten som "not available", uten forklaring (§ EXP L194, L329, L341.)
Sitat: "This page is not available." Økten varer i 24 timer (AD-8). Åpner gjesten bekreftelsen dagen etter, eller på en annen enhet, står det bare at siden ikke er tilgjengelig, og det kan leses som at bookingen er borte. Reglen om at svaret skal være likt er riktig, men teksten kan likevel forklare. Kilde: FR-8 L269, FR-20 L401, ARCH AD-8 L125, FR-22 L432.
Fix: På `/confirmation/:reference`, likt for alle referanser: "This page is not available. A confirmation can only be opened in the browser you booked in. Your booking is not affected: find the confirmation in your email." Avklar sammen med M-7.

**[Innhold]** — M-4. Reserveløsningen ved tapt referanse når aldri gjesten (§ EXP L490, L549; PRD §3 L134.)
Sitat: "A Guest who has lost the reference gives their name and email instead, and Katja finds the Booking the same way (Lisa)." Reglen finnes bare i Flow 3 og i PRD-en. Ingen gjestetekst nevner den, så en gjest uten referanse har ingen grunn til å tro at hun slipper inn. Kilde: PRD §3 L134, FR-22 L432.
Fix: Legg setningen i Terms og i "Before you come", Practical: "Lost your booking reference? Give your name and email at reception."

**[Innhold]** — M-5. "please try again" er et fragment, og Pay kan være borte (§ EXP L144, L284, L292, L321–322, L342–343.)
Sitat: "Notice with \"please try again\", different from \"No seat free\"." "Pay, the payment note and the Terms checkbox are removed for the refused Session". Alle andre meldinger på Review sier "You have not been charged.", men denne, som kommer rett etter et trykk på Pay, gjør det ikke. Fire tilstander deler fragmentet, og ingen full setning er skrevet. Raden "After a refusal" skiller heller ikke `try_again` fra de andre, så leser man den bokstavelig fjernes Pay, og gjesten blir bedt om å prøve igjen uten en knapp å prøve med. Kilde: FR-14 L319–320, FR-22 L432, ARCH Conventions L290 (503 `try_again`), AD-9 L138.
Fix: Review: "Something went wrong on our side. You have not been charged. Please try again." Skriv i L322 at Pay, merknaden og avkrysningen står igjen ved `try_again`.

**[Innhold]** — M-6. Ingen plass i hele horisonten gir ingen neste steg (§ EXP L189, L299; motsier L130.)
Sitat: "There is no room for 2 seats in the next 4 weeks." og "Say so plainly, with no alternatives". Gjesten står uten neste steg, som Voice-tabellen selv avviser ("A message with no next step"). Hun kan faktisk gjøre noe: velge færre seter, eller komme tilbake senere. Kilde: FR-22 L432.
Fix: "There is no room for 2 seats in the next 4 weeks. You can try fewer seats, or come back later: booking opens 4 weeks ahead."

**[Innhold]** — M-7. Teksten sier ikke at e-posten er simulert og stedet fiktivt (§ EXP L172, L254, L422; `key-confirmation.html` L90; `directions-3.html` L143.)
Sitat: "Sent by email:" Ingen e-post sendes. Merknaden "Simulated payment: no money moves" gjelder bare betalingen, og ingen gjestetekst sier at Saunalöyly er fiktivt. En ekte bruker venter på en e-post som aldri kommer, og hvis fanen lukkes, er referansen tapt. M-3 og M-4 lener seg på den samme e-posten. Kilde: PRD §1 L35: "it does not pretend to be one". PRD §3 L119. FR-6 L243.
Fix: Bruk "Sent by email (simulated):" over e-posten, og legg til i Find us og Terms: "Saunalöyly is a fictional venue in a student project." Da må "Keep your booking reference" stå som den viktigste handlingen.

**[Innhold]** — M-8. "never alone" er ikke sant for alle gjester, og begrunnelsen holder ikke (§ `directions-3.html` L140; EXP L548; FR-1 L179.)
Sitat: "Bathe with caution, and never alone." og "The saunas are shared, so a Guest with 1 seat is not alone." En sikkerhetsregel må kunne følges. Alle kan bestille 1 sete, også i en økt uten andre gjester (`key-booking-list.html` L83 viser "Seats booked 0"), og systemet håndhever ingenting (PRD §9 L938). Med fire badstuer og fri bevegelse kan gjesten også være alene i et rom selv om økten er delt. Begrunnelsen for å lukke punktet stemmer derfor ikke. Kilde: FR-2, FR-1 L179, PRD §9 L938, EXP L131.
Fix: Gjenåpne Open Items 12 og erstatt regelen med noe gjesten kan gjøre, for eksempel: "Bathe with caution and look out for each other. If you are on your own, tell reception." Det siste krever en beslutning om hva resepsjonen gjør. Oppdater FR-1 hvis teksten endres.

**[Innhold]** — M-9. Sikkerhetsteksten dekker ikke den største risikoen kildene nevner, og sier ikke hva gjesten gjør ved ubehag (§ `directions-3.html` L140, Safety.)
Sitat: "Alcohol is not allowed at the venue." og "leave the sauna if you feel unwell." Alkoholregelen gjelder bare på stedet. Kilden begrunner den med påvirkning, og det gjelder også den som har drukket før ankomst. "Leave the sauna" stopper der: ingenting sier hvem gjesten skal si fra til, verken om seg selv eller om andre. Hjerteproblemer, graviditet og lignende nevnes ikke, men det har heller ingen av kildene. Hele innholdet er merket som antakelse i PRD-en. Kilde: ADD F L285: "about 80 % of Finland's 30–40 yearly sauna heat deaths involved intoxication". ADD F L289. FR-1 L177.
Fix: "Do not use the sauna after drinking alcohol." og "Leave the sauna if you feel unwell, and tell reception." Legg til en linje som ber gjester med helseplager spørre lege først. Ordlyden i ADD F L289 er valgt av Lisa, så endringen må bekreftes.

**[Innhold]** — M-10. Gjesten får ikke vite at barn trenger sete og koster det samme (§ `directions-3.html` L136, L140; EXP L84, L224.)
Sitat: "Children must be supervised by an adult." Regelen sier at barn kan komme, men ikke at hvert barn trenger et sete og koster fullt. PRD-en har bestemt dette, men det står ikke i noen gjestetekst. En familie kan bestille feil og oppdage det i resepsjonen, uten rett til å endre. Ingen tekst sier heller om det finnes en aldersgrense for å bestille. Kilde: PRD §9 L937: "every Seat costs the same". PRD §3 L124.
Fix: Legg til i "Before you come", Practical: "Everyone needs a seat. Adults and children pay the same." Avklar aldersgrense for å bestille (se juridisk del).

**[Innhold]** — M-11. Tilbake fra Confirmation er ikke beskrevet og kan gi ny Booking (§ EXP L316, L368.)
Sitat: "Back in the browser and the Back link do the same thing, and neither loses input (FR-5)." Regelen dekker ikke Confirmation. Etter AD-9 lages nøkkelen "when the Guest reaches the review page", så en bokstavelig bygging gir Review med ny nøkkel etter nettleserens tilbake-knapp, og Pay kan da gi en andre Booking. L316 gjelder bare dobbeltklikk, reload og retry. Kilde: FR-6 L246, ARCH AD-9 L134.
Fix: Legg til en tilstand: "After payment, Back to Review shows Confirmation." Da kan ikke samme gjennomgang betales to ganger.

**[Innhold]** — M-12. Samtykkebanner er forbudt mens spørsmålet fortsatt er åpent (§ EXP L371 mot L539.)
Sitat: "consent banner (FR-21)" under **Banned**, og "Check the \"no consent banner\" claim against the session cookie". Spinen sier at banner er forbudt og at påstanden må sjekkes. AD-8 setter cookie for hver besøkende når SPA-en lastes, også for dem som bare leser Landing. Om det er strengt nødvendig for en tjeneste brukeren har bedt om, er ikke opplagt. Punktet har ingen eier, og Privacy notice kan ikke skrives ferdig uten svaret. Kilde: FR-21 L416, ARCH AD-8 L124, ADD D L194.
Fix: Opprett økten først når gjesten går inn på Book seats, så forsvinner spørsmålet for Landing. Dette krever endring i AD-8. Ved ekte drift må jurist sjekke vurderingen.

**[Innhold]** — M-13. FR-21 gir ikke grunnlag for en fullstendig personvernerklæring (§ EXP L539; FR-21 L409–414; PRD §3 L134.)
Sitat: "Privacy notice text. Required contents are in FR-21." Tre hull: (1) FR-21 nevner ikke hvem behandlingsansvarlig er og hvordan hen kontaktes, og det er påkrevd etter GDPR art. 13. Her trengs et ærlig svar, siden stedet er fiktivt. (2) Sletting etter 12 måneder er en antakelse og står mot ADD D L192 om 5 års oppbevaring av regnskapsmateriale. (3) "Who sees it" må dekke resepsjonen, som etter antakelsen bruker Administrator-listen med alle gjesters navn og e-post. Kilde: FR-21 L414, ADD D L190–192, ARCH AD-4 L88, AD-12 L173.
Fix: Utvid FR-21 med behandlingsansvarlig, og bekreft oppbevaringstiden før teksten skrives. I studentprosjektet kan erklæringen si at data bare ligger lokalt.

### Low (44)

**[Flow coverage]** — Move Seats (FR-26) står som én setning i failure-avsnittet til Flow 4 (E 506), selv om delvis flytting gir ny Booking med egen referanse.
Fix: skill det ut som egen variant med steg.

**[Token completeness]** — Lenker i Administrator bar har ingen farge i spine.
D 443 sier bare "links on the right", Text link sier `{colors.link}` (D 406), mens mocken arver `on-bar` (`key-booking-list.html` linje 55). `{colors.link}` på `{colors.bar}` er 4,7:1 og passerer, men paret står ikke i kontrasttabellen.
Fix: velg farge, og legg den til i `administrator-bar` og i tabellen.

**[Token completeness]** — Visuelle verdier uten token: `terms-checkbox.size: 20px` (D 167), radio 32 px, tid 150 px og radio 20 px i Session row (D 419).
Focus ring-målene (3 px, 2 px offset) finnes bare i E 364, selv om dette er visuell spec.
Fix: legg inn tokens, eller flytt focus ring til `DESIGN.md`.

**[Token completeness]** — Prosaen har mer enn `components`-frontmatter, så kode generert fra YAML alene blir ufullstendig: `notice` mangler type og foreground (D 433), `total-block` mangler "incl.
VAT"-typen (D 420), `administrator-bar` mangler vekt 600 (D 443), `rule-list` og `sauna-card` mangler tekst-typer (D 425–426), `session-group` mangler full-header (D 444).
Fix: speil disse i frontmatter.

**[Component coverage]** — Fixed action bar er ulikt spesifisert.
D 421 sier at den holder "one full-width Primary button", mens E 405 legger både Total block og Continue i den på Book seats.
Fix: legg til Total block i den visuelle spesifikasjonen. Betydningen er begrenset så lenge FR-51 kommer sist i Step 2.

**[Component coverage]** — Session group med full Session: D 444 sier "its figures in weight 600", mens E 355 og `key-booking-list.html` gir vekt 600 bare til "Sold out" og "Seats left 0".
Fix: bruk formuleringen fra E 355 i D.

**[Component coverage]** — Nearest sessions kaller radene Session rows med dato (D 434), men Session row er definert med tre kolonner (D 419), og mocken har fire med 190 px datokolonne (`key-review.html`).
Fix: beskriv varianten med kolonner.

**[State coverage]** — Landing slår sammen lasting og feil i én rad (E 284).
Det står ikke hva railen viser under lasting, eller hvor Notice står.
Fix: del raden og navngi plasseringen.

**[State coverage]** — Sign-in mangler tomt felt og allerede innlogget Administrator (E 349–353).
Fix: legg til to rader.

**[State coverage]** — "This page is not available." har ikke shell eller rekkefølge (E 341; ikke i E 112–120 eller D 381).
Fix: legg siden til i Content Homes og Layout.

**[State coverage]** — To tilgjengelighetssjekker er uavklarte, men ikke sporet: om deaktiverte Session rows kan nås ved lesing (E 378), og radio-mønsteret for kalenderen (E 379).
Open Items har bare tastaturrekkefølgen (E 550).
Fix: før dem i Open Items, eller beslutt.

**[Visual reference coverage]** — Noe tekst finnes bare i mockene: "1.
Choose a date", "2. How many seats?", "NOK 250 per seat in every session", rail-faktaene på Landing og etiketten "Booking reference" (`directions-3.html`, `key-confirmation.html`). Søk i `EXPERIENCE.md` gir null treff på de tre første.
Fix: legg dem i Voice and Tone, så spine faktisk vinner.

**[Visual reference coverage]** — Lenken "colours" (E 16) sier ikke at bare variant A gjelder, selv om filen også viser variant B.
Fix: skriv "colours, variant A", som D 291 gjør.

**[Bloat & overspecification]** — If-time-tabellen og E 448 gjentar FR-25 til FR-37 i stedet for bare å plassere dem.
Fix: behold plassering og det spine legger til, og vis til FR for resten.

**[Bloat & overspecification]** — Sju punkter merket "Closed by Lisa" står i Open Items (E 546–554), selv om beslutningene allerede står i kroppen.
Fix: fjern dem.

**[Bloat & overspecification]** — Mock-historikk uten nedstrøms verdi: listen over folding av spacing (D 358) og radiene i mockens rammer (D 395).
Fix: behold regelen og flytt historikken til memlog.

**[Inheritance discipline]** — Paletten avviker fra PRD §6, som lister blant annet forest green og granite grey, og FR-22 tester "the look described in §6".
D 291 forklarer valget, men det står ikke i PRD impact, og arkitekturens Styling viser fortsatt til "the PRD §6 palette".
Fix: registrer lesningen i PRD §6.

**[Inheritance discipline]** — Kildekolonnen i E 146 oppgir FR-1 for "Private sauna" og "My booking", men de står i §4.1/FR-4 og §4.10.
Fix: rett kilden.

**[Shape fit]** — Open Items blander innhold, lukkede beslutninger og PRD-logg, og PRD impact starter nummereringen på 1 igjen (E 578), så "item 14" kan bety to ting.
Fix: unik nummerering, eller flytt loggen ut som foreslått under kategori 6.

**[Tilgjengelighet]** — A-19 "Processing" kan bli implementert med `disabled` (2.4.3, 4.1.2) (§ `EXPERIENCE.md` linje 210, 315.)
"Takes no second press" leder lett til `disabled`, som i noen nettlesere gjør at fokus går tapt. Det er i strid med "Keeps focus".
Fix: Skriv `aria-disabled="true"` med blokkering i kode, ikke `disabled`.

**[Tilgjengelighet]** — A-20 Error summary og feiltekster har hull (3.3.1, 3.3.3) (§ `EXPERIENCE.md` linje 179–193, 250, 300–301, 314, 317. `DESIGN.md` linje 435.)
Summary skal lenke til felt, men en mislykket betaling har ikke noe felt. Teksten mangler for manglende dato, manglende antall, ikke-godtatte vilkår, feil datoformat og ikke-bookbar dato. Uten tittel (`DESIGN.md` linje 435) har fokusmålet ikke noe navn, og den første setningen må stå alene.
Fix: Legg til: summary uten lenke ved betalingsfeil, med fokus på teksten. Skriv de fem manglende tekstene, gjerne med hvorfor og hva brukeren kan gjøre. Gi summary tilgjengelig navn med `aria-label="Errors"` selv om det ikke vises en tittel.

**[Tilgjengelighet]** — A-21 Dyplenken til "Before you come" krasjer med fokusregelen (2.4.3) (§ `EXPERIENCE.md` linje 240, 366. Mock: `key-confirmation.html` linje 88 og 106.)
Fokus flyttes til Wordmark i Rail på hvert rutebytte, så fokus og synlig seksjon havner på forskjellige steder. Neste Tab går til Book seats og ikke inn i seksjonen.
Fix: Unntak: med ankeradresse går fokus til seksjonens overskrift.

**[Tilgjengelighet]** — A-22 Tilgjengelig navn inneholder ikke den synlige teksten ordrett (2.5.3) (§ `EXPERIENCE.md` linje 378 ("13:00 to 14:30, 12 seats left") mot synlig "13:00–14:30".)
Talestyringsbrukere som sier det de ser, kan bomme. Praktisk virkning er liten og varierer med programmet.
Fix: La etiketten gi navnet (se M-02), eller bruk samme tegnsetting som den synlige teksten.

**[Tilgjengelighet]** — A-23 Alt-tekster finnes ikke ennå, og finske ord kan ikke merkes i `alt` (1.1.1, 3.1.2) (§ `EXPERIENCE.md` linje 217, 386, 387, 540, 542.)
Linje 542 sier at alt-tekstene ikke er skrevet, så 1.1.1 kan ikke vurderes. Bildene er oppført med ordene lauteet, kiuas, kiulu, kauha og vihta. `alt` kan ikke ha `lang`, så kravet på linje 386 kan ikke oppfylles der, og skjermlesere vil uttale ordene feil.
Fix: Skriv alt-tekst på engelsk, for eksempel "wooden sauna benches". Spar finske ord med gloser til synlig tekst med `lang="fi"`. Avgjør om bildestripen og håndkleet er pynt (`alt=""`). Sauna-navn er egennavn og unntatt. Jeg fant ingen svenske ord.

**[Tilgjengelighet]** — A-24 Hover, active og tvungne farger er ikke definert (1.4.11, 1.4.1) (§ Fravær i `DESIGN.md` Components. Ingen mockup har `:hover` eller `:active`.)
Utviklere finner på egne farger som ikke er kontrastsjekket. I Windows' høykontrastmodus forsvinner fyll, så valgt dag og plass skilles bare av fontvekt, siden radioene er skjulte. Ikke et AA-brudd i seg selv.
Fix: Definer hover og active fra eksisterende tokens, gjerne kun med understreking eller kanttykkelse. Legg til en `forced-colors`-regel for valgt celle, for eksempel `Highlight` som bakgrunn.

**[Tilgjengelighet]** — A-25 Datofeltet på Booking list er uspesifisert (3.3.2, 4.1.3) (§ `EXPERIENCE.md` linje 262, 265. Mock: `key-booking-list.html` linje 81.)
Ingen formatinstruks, ingen måte å sende inn på, og det er ikke sagt om "Previous day" og "Next day" er rutebytte. Er de det, flyttes fokus til overskriften etter hvert trykk, og Katja må tabbe tilbake. Er de det ikke, endres innholdet uten kunngjøring.
Fix: Bruk samme hint som gjesten ser. La Enter og blur gjelde. Ikke flytt fokus fra dagsknappene, og kunngjør ny dato i en statusregion.

**[Tilgjengelighet]** — A-26 Administratorøkten på 8 timer varsles ikke (2.2.1) (§ `ARCHITECTURE-SPINE.md` linje 125 (AD-8, Lifetimes), `EXPERIENCE.md` linje 353.)
8 timer er under unntaket på 20 timer, og det finnes ingen varsling eller forlengelse. Listen er skrivebeskyttet, så det eneste tapet er en ny innlogging. Gjesteøkten på 24 timer er innenfor.
Fix: Sett grensen til 20 timer eller mer, eller noter dette som et bevisst, lite avvik. Ingen nedtelling trengs.

**[Tilgjengelighet]** — A-27 Oppførsel uten JavaScript er ikke besluttet (ikke et WCAG-krav) (§ `EXPERIENCE.md` linje 551. `ARCHITECTURE-SPINE.md` (`POST /api/session` ved innlasting). Addendum linje 248.)
WCAG krever ikke at siden virker uten JavaScript, men blokkert eller feilet skript gir en tom side uten kontaktinformasjon. Skrevet dato hjelper ikke da.
Fix: Legg `<noscript>` med navn, adresse og kontakt i `index.html`, og lukk punkt 15 med det.

**[Tilgjengelighet]** — M-03 Hint, total og Continue i `directions-3.html` (1.3.1, 4.1.3) (§ Linje 144, 147, 148.)
Hintet er ikke koblet til feltet, totalen har ingen live-semantikk, og Continue er `<a href>` der kontrakten sier knapp. Kalenderens `th` mangler `scope`, og tabellen har ingen måned i navnet.
Fix: Rett i mocken, eller la A-05, A-08 og A-09 styre.

**[Tilgjengelighet]** — M-04 `<caption hidden>` på Booking table (1.3.1) (§ `key-booking-list.html` linje 82.)
`hidden` tar teksten ut av tilgjengelighetstreet, så tabellene mangler trolig navn. `<h3 aria-label>` over tabellen gir navn til overskriften, ikke tabellen.
Fix: Bruk `aria-labelledby` til Session-overskriften, eller en visuelt skjult `caption` uten `hidden`.

**[Tilgjengelighet]** — M-05 Skjemamarkup i Details og Review (4.1.3, 4.1.2) (§ `key-details.html` linje 83, 88, 90. `key-review.html` linje 100–101.)
`role="alert"` kombinert med fokus kan gi dobbel opplesing. E-postfeltet er `type="email"` i én tilstand og `type="text"` i feiltilstanden. `role="status"` rundt radioer kan få hele innholdet opplest, og fungerer dårlig om regionen settes inn samtidig med teksten.
Fix: Bruk fokus uten `role="alert"` for Error summary. Bruk `type="email"` i begge tilstander, med `novalidate`. Hold statusregionen til meldingen, og legg valgene utenfor.

**[Tilgjengelighet]** — M-06 Mockene motsier "no change beyond one column" (1.4.10) (§ `EXPERIENCE.md` linje 407. `key-review.html` linje 83, `key-confirmation.html` linje 76.)
Nearest sessions-raden krever minst 372 px pluss padding, og er bredere enn 320 px. `.email` mangler `overflow-wrap`, så en lang lenke kan gi horisontal rulling. Gjelder ved FR-51.
Fix: Stable raden på smale bredder, og legg `overflow-wrap: anywhere` på Email as sent.

**[Innhold]** — L-1. Tre setninger i EXPERIENCE.md er utdatert etter PRD-oppdateringen (§ EXP L50, L342, L446.)
Sitat: "PRD §7 lists them as one, and FR-5 allows either." "Not in the PRD's §7 list." "The Book action in FR-35 and FR-37 is the Continue action on Book seats." PRD-en sier nå det motsatte eller noe mer presist: FR-5 L229 og §7 L860 har to sider, §7 L873 har tilstanden, og FR-35 L598 og FR-37 L631 sier "Continue booking".
Fix: Stryk de tre setningene, og marker i L580–592 at punktene er gjennomført.

**[Innhold]** — L-2. Henvisninger til forkastet materiale (§ EXP L452, L539, L551, L586.)
Sitat: "Times are seed times (extract §14, C1)." "extract" er `.working/source-extract.md`. Den er forkastet og står ikke blant kildene i front matter, så sporene brytes.
Fix: Vis direkte til PRD §12 Q3, FR-21 og AD-8, og ADD E L248.

**[Innhold]** — L-3. Knappen heter to ting (§ EXP L44–45, L102, L114, L190, L232, L439–440 mot L166.)
Sitat: "Continue" og "Continue booking". Etiketten er "Continue booking", og PRD-en bruker den. Spinen sier "Continue" i flere rader, også der den beskriver når en Hold starter.
Fix: Bruk "Continue booking" i rader som beskriver knappen.

**[Innhold]** — L-4. "Only" ligger nær det Voice-tabellen avviser (§ EXP L183 mot L128.)
Sitat: "Only 1 seat left in this session. You have not been charged." Tallet er sant, men "Only" er ordet i eksempelet på det som ikke skal brukes, og setningen sier ikke hvorfor gjesten ble avvist. Kilde: FR-3 L205, NFR-9.
Fix: "1 seat left in this session, too few for this booking. You have not been charged."

**[Innhold]** — L-5. Siste dag i horisonten kan ha økter som mangler uten forklaring (§ EXP L225, L298.)
Sitat: "All Sessions for the date in time order, including unavailable ones". Horisonten telles "from the moment of booking" (PRD §3 L145), så den siste dagen kan ha økter utenfor. Spinen beskriver ikke dem, og `horizon_end` er bare en dato (AD-16 L215).
Fix: Bestem at slike økter ikke vises, og la linjen "Booking opens 4 weeks ahead." forklare dem.

**[Innhold]** — L-6. Avvisning på Review uten noen ledige økter (§ EXP L171, L322.)
Sitat: "The nearest sessions with room:" Finnes det ingen økter å foreslå, står etiketten over en tom liste, og Pay er borte.
Fix: Bruk teksten fra M-6 i stedet for etiketten, og la Back være neste steg.

**[Innhold]** — L-7. Grensen på 10 seter forklares ikke (§ EXP L224; `directions-3.html` L146.)
Sitat: "Ten choices, 1 to 10 (FR-2)." En gruppe på 12 ser at valgene stopper, uten å få vite at de kan lage to bookinger (FR-9). Private sauna finnes ikke i Core.
Fix: Hint under spørsmål 2: "Up to 10 seats per booking. For more, make another booking." Sjekk mot plassbudsjettet på siden (DES L379).

**[Innhold]** — L-8. "Already started" følger ikke med til Review (§ EXP L176, L295; `key-review.html` L93.)
Sitat: "Already started" Gjesten betaler full pris for en økt som er i gang, og Review, der kjøpet skjer, sier det ikke. Ingen kilde sier hva som gjelder ved sen ankomst eller om gjesten ikke møter. Kilde: PRD §3 L146; FR-5.
Fix: Vis "Already started" ved Session-raden på Review, og ta sen ankomst og uteblivelse inn i Terms.

**[Innhold]** — L-9. Begrunnelsen for feil på Landing holder ikke (§ EXP L284.)
Sitat: "the Notice says \"please try again\", because Book seats still works without them" Book seats henter øktene fra det samme API-et, så feilen vil trolig ramme begge. Prisen, åpningstidene og adressen mangler da også. Kilde: ARCH AD-16 L220.
Fix: Fjern begrunnelsen og si hva gjesten ser i tomme felt.

**[Innhold]** — L-10. Format for beløp over 1000 er ikke bestemt (§ `key-booking-list.html` L83; EXP L141.)
Sitat: "NOK 1000" Mocken bruker "NOK 1000" og addendumet "NOK 1,360". Pay for 10 seter viser "Pay NOK 2500". Kilde: ARCH Conventions L289.
Fix: Velg én form, gjerne "NOK 2,500" på engelsk, og før den inn i Conventions.

**[Innhold]** — L-11. Sign-in mangler lenke til Privacy notice (§ EXP L48, L118.)
Sitat: "Text link wherever data is collected" Sign-in samler inn e-post og passord, men sideoppskriften har ingen lenke. Det får betydning når gjestekonto kommer, fordi EXP L444 gjenbruker skjemaet. Kilde: FR-21 L409.
Fix: Legg lenken til i L118.

**[Innhold]** — L-12. Følgesvenner vet ikke om referansen (§ EXP L159; `key-confirmation.html` L84.)
Sitat: "Keep your booking reference and give it at reception when you arrive." Bare den som bestiller har referansen, og navnet er bestillerens. En venn som kommer først, har ingenting å oppgi.
Fix: Legg til i "Before you come", Practical: "Coming separately? Share the booking reference with your group."

## Reviewer files

- `review-rubric.md`
- `review-accessibility.md`
- `review-content.md`
