# Spine Pair Review — Saunalöyly Booking Platform

## Overall verdict
Spine-paret holder som kontrakt for det meste av Core: alle 58 unike token-referanser resolver, alle 32 komponenter finnes i begge spines, og UJ-navnene er ordrette. Svakheten ligger i feil- og gjenopprettingsstiene for Book seats og Review, der fire high-funn tvinger story-dev til å ta beslutninger selv: motstridende feilmønster, tapt fokus etter refusal, radioer som bytter kontekst, og manglende cold-load. Ingen funn er critical, men disse fire bør lukkes før stories for Book seats og Review skrives.

Alle linjenumre under gjelder filene slik de lå ved review. E = `EXPERIENCE.md`, D = `DESIGN.md`.

## 1. Flow coverage — adequate
Sjekket: alle seks UJ-er fra `prd.md` §2.3 mot Key Flows, pluss omfanget i PRD §7 (linje 872: "the flows of §4.8 to §4.12"). `brief.md` har ingen nummererte journeys. UJ-1 til UJ-5 har navngitt protagonist, nummererte steg, **Climax** og failure-sti (E 454–520). UJ-6 har ingen flow, men det er forsvarlig: PRD §7 legger §4.13 utenfor runden, og E 524 sier det.

### Findings
- **medium** §4.12 Guest accounts har ingen Key Flow, selv om PRD §7 setter flows for §4.8–§4.12 i scope. Sign-up, sign-in og My bookings finnes bare i plug-in-tabellen (E 439, 444), og passordreset (FR-37, PRD linje 630) er ikke nevnt noe sted. Se også Open Item 29 (E 571). *Fix:* legg til en kort flow for §4.12, eller skriv eksplisitt at den er utsatt, med begrunnelse.
- **medium** FR-33 (cancel eller move av Whole-sauna booking) har ingen steg, bare én setning etter Flow 5 (E 518). Valget mellom refund og Voucher og det bekreftende steget er ikke beskrevet. *Fix:* legg til en Flow 5b, eller en failure-/variantsti med steg.
- **low** Move Seats (FR-26) står som én setning i failure-avsnittet til Flow 4 (E 506), selv om delvis flytting gir ny Booking med egen referanse. *Fix:* skill det ut som egen variant med steg.

## 2. Token completeness — strong
Sjekket med skript (PyYAML): D-frontmatter parser, med 15 colors, 17 typography, 1 rounded, 25 spacing og 31 components. 294 referanser (58 unike) resolver, og ingen token er ubrukt. Alle 15 fargeverdier er gyldig hex og stemmer med prosaen. Alle 17 rader i typografitabellen stemmer med YAML. Kun lys modus er uttalt (D 287), så mørke par gjelder ikke. Kontrasttabellen (D 310–322) er regnet om og stemmer, se Mechanical notes for én avrunding.

### Findings
- **low** Lenker i Administrator bar har ingen farge i spine. D 443 sier bare "links on the right", Text link sier `{colors.link}` (D 406), mens mocken arver `on-bar` (`key-booking-list.html` linje 55). `{colors.link}` på `{colors.bar}` er 4,7:1 og passerer, men paret står ikke i kontrasttabellen. *Fix:* velg farge, og legg den til i `administrator-bar` og i tabellen.
- **low** Visuelle verdier uten token: `terms-checkbox.size: 20px` (D 167), radio 32 px, tid 150 px og radio 20 px i Session row (D 419). Focus ring-målene (3 px, 2 px offset) finnes bare i E 364, selv om dette er visuell spec. *Fix:* legg inn tokens, eller flytt focus ring til `DESIGN.md`.
- **low** Prosaen har mer enn `components`-frontmatter, så kode generert fra YAML alene blir ufullstendig: `notice` mangler type og foreground (D 433), `total-block` mangler "incl. VAT"-typen (D 420), `administrator-bar` mangler vekt 600 (D 443), `rule-list` og `sauna-card` mangler tekst-typer (D 425–426), `session-group` mangler full-header (D 444). *Fix:* speil disse i frontmatter.

## 3. Component coverage — adequate
Sjekket med skript: 32 navn i D Components og 32 i E Component Patterns, med full overlapp og reelle regler i hver rad. Rader som peker til If-time Plug-in Points resolver (E 271–273, 436–439). `Session list`, `Nearest sessions` og de fire If-time-komponentene har ingen frontmatter-oppføring.

### Findings
- **medium** Fem rendrede Core-elementer har ingen rad i noen av spinene. Dette gjelder payment note (E 115, 322; kravet står i FR-6), booking terms-blokken (E 115–116), resepsjonssetningen (E 116), Back (E 114–115, 180, 368) og "Booking confirmed"-overskriften (E 116, 181). Søk i `DESIGN.md` gir null treff på "payment note", "reception" og "Booking confirmed", og booking terms og Back nevnes bare som plassering (D 383). Typografien finnes bare i mockene (`key-review.html`, `key-confirmation.html`). *Fix:* gi hvert element en navngitt rad i begge spines, eller si eksplisitt hvilken eksisterende komponent det er.
- **low** Fixed action bar er ulikt spesifisert. D 421 sier at den holder "one full-width Primary button", mens E 405 legger både Total block og Continue i den på Book seats. *Fix:* legg til Total block i den visuelle spesifikasjonen. Betydningen er begrenset så lenge FR-51 kommer sist i Step 2.
- **low** Session group med full Session: D 444 sier "its figures in weight 600", mens E 355 og `key-booking-list.html` gir vekt 600 bare til "Sold out" og "Seats left 0". *Fix:* bruk formuleringen fra E 355 i D.
- **low** Nearest sessions kaller radene Session rows med dato (D 434), men Session row er definert med tre kolonner (D 419), og mocken har fire med 190 px datokolonne (`key-review.html`). *Fix:* beskriv varianten med kolonner.

## 4. State coverage — adequate
Sjekket: alle Core-surfaces fra IA (E 38–59) mot State Patterns (E 276–359) og Interaction Primitives, for empty, cold-load, focus, error, offline og permission-denied. Book seats, Review-refusals, Administrator og Not available er rikt dekket. Offline er bevisst valgt bort (E 292). Permission-denied er dekket (E 329, 341, 351). Hullene samler seg rundt feilmønsteret, fokus og direkte lasting.

### Findings
- **high** Feilmønsteret på Book seats er selvmotsigende. Field error er "Always with an Error summary" (E 251), og Error summary "Takes focus" (E 250). FR-23 krever begge (PRD linje 443). E 232 sier derimot Field error alene med fokus på spørsmålet, og E 300–301 sier Field error alene ved datofeil. En Error summary er heller ikke regnet inn i budsjettet på 570 px (D 379). *Fix:* bestem ett mønster for Book seats, inkludert fokusmål, og sjekk det mot første visning ved 1366 × 768.
- **high** Fokus etter refusal er udefinert. Pay "Keeps focus while processing" (E 210), og etter en refusal fjernes Pay, payment note og Terms checkbox (E 322). Notice annonseres "without moving focus" (E 380). Tastaturbrukeren står da på et element som ikke lenger finnes, midt i climax for taperen i Flow 2. Regelen om fokus ved route change (E 366) dekker ikke dette, for Guest "stays on Review". Manuell tastaturpass kreves av FR-23. *Fix:* flytt fokus til Notice ved refusal, og lag et unntak i E 380. Si også hvor fokus lander når Review lastes på nytt med valgt Session.
- **high** Nearest sessions på Review bytter kontekst ved input. Valg er radioer med piltaster (E 365, `key-review.html` linje 101), og å velge "reloads Review" (E 322, se også E 249). Ingen knapp bekrefter valget, så piltast til neste rad laster siden på nytt. Da kan tastaturbrukere ikke nå rad to og tre, og det bryter WCAG 3.2.2 On Input (FR-23). *Fix:* legg til en egen handling for valgt rad. Pay er borte i denne tilstanden, så sidens ene Primary button er ledig. Alternativt kan radene være Text links.
- **high** Details og Review mangler cold-load. Ingen state dekker direkte adresse eller reload uten valgt Session, og IA gir bare rute for Confirmation (E 46). E 316 lover at reload returnerer første utfall, men AD-9 lar SPA-en lage nøkkelen når Guest når Review, og ingen spine sier hvor valg, navn, e-post og nøkkel overlever en reload. Browser Back fra Confirmation til Review er heller ikke dekket (E 368). *Fix:* legg til states for "Details/Review uten valg" og "Back etter betalt Booking", og si hva som er lagret hvor.
- **medium** Error summary-regelen passer ikke overalt. Hver oppføring er "a link to its field" (E 250, D 435), men Payment failed (E 317) og Wrong email or password (E 349) har ingen felt å lenke til. *Fix:* spesifiser oppføring uten lenke, eller et bestemt mål.
- **medium** Core-feiltekst mangler. Voice har ingen tekst for Terms not accepted (E 314), manglende dato eller antall Seats (bare "Choose a session", E 190), Date not bookable, typed (E 300), eller Notice når valgt Session nullstilles (E 226). Lesefeil finnes bare som fragmentet "please try again" (E 284, 292, 357), som bryter egen regel om å si hva som skjedde (E 130). *Fix:* legg rader i Voice-tabellen.
- **medium** "No room anywhere in the horizon" gir ingen neste handling (E 299, 189). Det bryter E 130 og FR-22 ("what the Guest can do next", PRD linje 432). *Fix:* legg til ett neste steg, for eksempel færre Seats eller kontaktvei.
- **medium** Booking list mangler to tilstander: dato uten Sessions og ugyldig typet dato (E 265, 345–357). Windows genereres fra seed-kjøringsdagen (FR-13), så "Previous day" og "Next day" kan havne der. *Fix:* legg til begge rader med tekst.
- **medium** Lasting og lesefeil er ujevnt dekket. Bare Book seats har lastetekst (E 291). Confirmation, Booking list og Outbox har ingen lastestate, og Confirmation og Outbox har ingen lesefeil (E 324–329, 345–357). *Fix:* legg til én felles regel for lasting og lesefeil.
- **low** Landing slår sammen lasting og feil i én rad (E 284). Det står ikke hva railen viser under lasting, eller hvor Notice står. *Fix:* del raden og navngi plasseringen.
- **low** Sign-in mangler tomt felt og allerede innlogget Administrator (E 349–353). *Fix:* legg til to rader.
- **low** "This page is not available." har ikke shell eller rekkefølge (E 341; ikke i E 112–120 eller D 381). *Fix:* legg siden til i Content Homes og Layout.
- **low** To tilgjengelighetssjekker er uavklarte, men ikke sporet: om deaktiverte Session rows kan nås ved lesing (E 378), og radio-mønsteret for kalenderen (E 379). Open Items har bare tastaturrekkefølgen (E 550). *Fix:* før dem i Open Items, eller beslutt.

## 5. Visual reference coverage — adequate
Sjekket: seks filer i `mockups/`, `imports/` er tom, og `wireframes/` finnes ikke. Alle seks er lenket og navngitt (E 16, D 291, 381, 401, 411, 441, 443). Ingen foreldreløse filer. Spines-win-on-conflict står én gang (E 16). Fargeverdiene i mockene (variant A i `color-themes-3.html`) stemmer med DESIGN-tokens.

### Findings
- **medium** Mockene som viser tilstander er ikke lenket der tilstandene spesifiseres. `key-review.html` viser refused Review (E 318–322), `key-details.html` viser skjemafeil (E 307), og `key-booking-list.html` viser dato uten Bookings (E 354). `EXPERIENCE.md` lenker bare samlet i E 16 og generelt i E 110, og D 431 sier bare "the key-screen mocks in `mockups/`". *Fix:* legg en kort referanse per state og per komponent.
- **low** Noe tekst finnes bare i mockene: "1. Choose a date", "2. How many seats?", "NOK 250 per seat in every session", rail-faktaene på Landing og etiketten "Booking reference" (`directions-3.html`, `key-confirmation.html`). Søk i `EXPERIENCE.md` gir null treff på de tre første. *Fix:* legg dem i Voice and Tone, så spine faktisk vinner.
- **low** Lenken "colours" (E 16) sier ikke at bare variant A gjelder, selv om filen også viser variant B. *Fix:* skriv "colours, variant A", som D 291 gjør.

## 6. Bloat & overspecification — adequate
Vurdert: restatement, pikselmål, seksjoner uten leser og pyntefortelling. `EXPERIENCE.md` er 47 kB mot 5–9 kB i eksemplene. Mye er forsvarlig, fordi produktet har to roller og fastsatt tekst. DESIGN-prosaen holder seg innenfor redaksjonell stemme, og E har ingen pyntefortelling.

### Findings
- **medium** PRD impact (E 574–592) er historikk. E 576 sier at alt er overført, og jeg bekreftet det mot PRD og arkitektur (FR-5, §3, §12 Q2 og Q7, AD-12, AD-16). Likevel står punktene som imperativer ("Close §12 Q2", "reword FR-5"), og en AI-konsument kan ta dem som åpne oppgaver. *Fix:* flytt seksjonen til `.memlog.md`.
- **low** If-time-tabellen og E 448 gjentar FR-25 til FR-37 i stedet for bare å plassere dem. *Fix:* behold plassering og det spine legger til, og vis til FR for resten.
- **low** Sju punkter merket "Closed by Lisa" står i Open Items (E 546–554), selv om beslutningene allerede står i kroppen. *Fix:* fjern dem.
- **low** Mock-historikk uten nedstrøms verdi: listen over folding av spacing (D 358) og radiene i mockens rammer (D 395). *Fix:* behold regelen og flytt historikken til memlog.

## 7. Inheritance discipline — adequate
Sjekket: fire `sources` resolver til eksisterende filer. Alle seks UJ-navn er ordrette mot PRD. Alle FR-, NFR-, DR-, UJ- og AD-numre i spinene finnes i kildene. Session/Window-mappingen er identisk i `EXPERIENCE.md`, PRD §3 og AD-12, og `DESIGN.md` bruker aldri Window. Komponentnavn er like i begge filer. Fem token-referanser i `EXPERIENCE.md` resolver mot `DESIGN.md`.

### Findings
- **medium** Spine omtaler PRD slik den var før 2026-11-05. E 50 sier at PRD §7 lister Details og Review som én, men FR-5 og §7 har to sider (PRD linje 229, 860). E 342 sier at tilstanden mangler i §7-listen, men den står der (PRD linje 873). E 446 og 585 forklarer en "Book action", men PRD sier **Continue booking** (PRD linje 598) og har ingen "Book action". *Fix:* rett de tre stedene mot gjeldende PRD.
- **medium** Administrator-sider er låst til laptop (E 52, 409; D 385), men FR-51 gjelder "Guests and Administrators" og "Every page" (PRD linje 811, 814). Avviket er verken i Open Items eller PRD impact. *Fix:* be Lisa om en beslutning, og endre enten FR-51 eller spine.
- **medium** `extract §14` (E 452, 539, 551, 586) peker til `.working/source-extract.md`, som er forkastet, ikke står i `sources` og ikke forklares i spine. C13 og C15 bærer reell begrunnelse. *Fix:* erstatt med direkte kilder: addendum E og AD-8 for E 551 og E 539. E 452 kan kuttes, siden UJ-ene nå bruker seed-tider.
- **low** Paletten avviker fra PRD §6, som lister blant annet forest green og granite grey, og FR-22 tester "the look described in §6". D 291 forklarer valget, men det står ikke i PRD impact, og arkitekturens Styling viser fortsatt til "the PRD §6 palette". *Fix:* registrer lesningen i PRD §6.
- **low** Kildekolonnen i E 146 oppgir FR-1 for "Private sauna" og "My booking", men de står i §4.1/FR-4 og §4.10. *Fix:* rett kilden.

## 8. Shape fit — strong
Sjekket: `DESIGN.md` har alle åtte seksjoner i kanonisk rekkefølge (D 279–455). `EXPERIENCE.md` har alle åtte påkrevde standardseksjoner. Inspiration er med (kilder og memlog viser referanser og avvisninger), og Responsive er med (breakpoints). De fire oppfunne seksjonene gjør nytte: Content Homes bærer no-repetition-regelen, Emails bærer kopi-eierskap, If-time Plug-in Points svarer på PRD §7, og Open Items samler åpne valg.

### Findings
- **medium** En tom linje (E 173) deler den aksepterte teksttabellen. De 23 radene i E 174–196 mangler header og rendres ikke som tabell, så markdown-parsere mister den største delen av tabellen. *Fix:* fjern linje 173.
- **low** Open Items blander innhold, lukkede beslutninger og PRD-logg, og PRD impact starter nummereringen på 1 igjen (E 578), så "item 14" kan bety to ting. *Fix:* unik nummerering, eller flytt loggen ut som foreslått under kategori 6.

## Mechanical notes
- **Frontmatter:** `DESIGN.md` parser rent. `status` og `updated` står ikke i tabellen i `design-md-spec.md`, men er ufarlige. `EXPERIENCE.md` feiler i streng YAML (PyYAML) fordi `- {planning_artifacts}/...` er uquotet. Eksempelfilene bruker samme form, så dette er et malvalg, men en maskinell konsument må quote eller erstatte plassholderen først.
- **Tokens:** `{path.to.token}` i E 20 er en bevisst plassholder, ikke en brutt referanse. Ingen andre brace-mønstre er ugyldige.
- **Avrunding:** `on-primary` på `primary` er 8,95:1, oppgitt som 8.9 (D 314). Alle andre kontrastverdier stemmer på én desimal.
- **Navn:** "Continue" og "Continue booking" brukes om samme handling (E 44–45, 102, 114, 190, 232, 405, 439–440), mens fastsatt tekst er "Continue booking" (E 166). Glossary har **Reception** med stor forbokstav (PRD §3), mens E skriver "reception" i løpende tekst; PRD gjør det samme i FR-8.
- **Kryssreferanser:** alle interne lenker til `mockups/` resolver. E 191 og D 411 viser til mockfiler som kode, ikke lenke. Brutte referanser er bare `extract §14` (kategori 7).
- **Mermaid:** ingen diagrammer eller kodeblokker i noen av filene.
- **Tagger:** 41 `[ASSUMPTION]` i `EXPERIENCE.md` og 10 i `DESIGN.md`. E 528 definerer dem som arbeidsstandarder frem til Lisa bekrefter dem.
