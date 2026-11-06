# Tilgjengelighetsreview: DESIGN.md og EXPERIENCE.md

Dato: 2026-11-06. Grunnlag: `DESIGN.md`, `EXPERIENCE.md`, `mockups/`, PRD, addendum og `ARCHITECTURE-SPINE.md`. Målestokk: WCAG 2.2 nivå AA. Dokumentene er fasit, mockups er illustrasjoner. `.working/` er ikke vurdert.

## Samlet vurdering

Nei: bygger en utvikler nøyaktig det som står, blir resultatet ikke WCAG 2.2 AA, selv om fargene, tastatur uten mus, målstørrelser, tid og autentisering er riktig løst. Kontrakten svikter der siden endrer seg under brukeren: fokus forsvinner og en radio laster siden på nytt ved avvisning. I tillegg er zoom under 1366 px ikke lovet, og sidetitler, gruppenavn, landemerker og feltkoblinger må gjettes.

Jeg fant ingen critical-funn, det vil si ingen steder der dokumentene alene gjør booking umulig for en hel gruppe. A-03 må testes før den vurderingen er endelig.

| Alvorlighetsgrad | Kontrakt | Bare mockup | Sum |
|---|---|---|---|
| Critical | 0 | 0 | 0 |
| High | 5 | 0 | 5 |
| Medium | 13 | 2 | 15 |
| Low | 9 | 4 | 13 |

## Beregnede kontrastforhold

Beregnet med skript etter WCAG-formelen fra de 15 fargetokenene i `DESIGN.md` linje 6–21, ikke fra påstandene i dokumentet. Alle tallene i dokumentets egen tabell (`DESIGN.md` linje 310–322) stemmer. Eneste avvik er `on-primary` på `primary`, som er 8,955 og står som 8,9. Det har ingen betydning.

**Tekst (krav 4,5:1, 1.4.3)**

| Forgrunn | Bakgrunn | Brukes til | Forhold | Resultat |
|---|---|---|---|---|
| `text` | `page` | Brødtekst, overskrifter, ledetekster | 11,39 | Består |
| `text` | `surface` | Felttekst, Notice, valgt Session | 12,32 | Består |
| `text` | `unavailable` | Utilgjengelig Session-rad, full Session-gruppe | 10,48 | Består |
| `muted` | `page` | Rail note, hint, Total note, meta, "No bookings" | 6,17 | Består |
| `muted` | `surface` | Total note hvis den flyttes til Fixed action bar | 6,67 | Består |
| `muted` | `unavailable` | Ikke-bookbar kalenderdag | 5,67 | Består |
| `on-primary` | `primary` | Primary button, valgt dag og plass | 8,95 | Består |
| `on-bar` | `bar` | Administrator bar | 8,95 | Består |
| `link` | `page` | Text link | 6,70 | Består |
| `link` | `surface` | Text link i Notice og Fixed action bar | 7,24 | Består |
| `link` | `unavailable` | Reserve, ikke brukt i spesifikasjonen | 6,16 | Består |
| `link` | `bar` | Bare hvis en utvikler bruker Text link-tokenet i baren | 4,70 | Består |
| `error` | `page` | Field error | 7,30 | Består |
| `error` | `surface` | Error summary og lenkene der | 7,90 | Består |
| `success` | `page` | "Booking confirmed" | 6,56 | Består |
| `success` | `surface` | Reserve, ikke brukt i spesifikasjonen | 7,10 | Består |

**Ikke-tekst (krav 3:1, 1.4.11)**

| Element | Mot | Forhold | Resultat |
|---|---|---|---|
| `border` (feltkant, dagcelle, setecelle) | `page` / `surface` / `unavailable` | 3,43 / 3,71 / 3,16 | Består |
| `button-edge` (Primary button, valgt celle) | `primary` / `page` / `surface` | 8,00 / 11,39 / 12,32 | Består |
| `focus` (ring) | `page` / `surface` | 6,70 / 7,24 | Består |
| `focus` (ring) | `primary` / `bar` / `unavailable` | 4,70 / 4,70 / 6,16 | Består |
| `button-edge` (3 px strek, valgt Session) | `surface` | 12,32 | Består |
| `link` som `accent-color` (avkrysset radio og Terms checkbox) | `surface` / `page` | 7,24 / 6,70 | Består |
| `error` (ramme på Error summary) | `surface` / `page` | 7,90 / 7,30 | Består |

**Tilstander**

| Tilstand | Par | Forhold | Vurdering |
|---|---|---|---|
| Valgt mot ikke valgt celle, fyll | `primary` mot `surface` | 1,54 | For lite alene, men ikke eneste signal |
| Valgt mot ikke valgt celle, kant | `button-edge` mot `border` | 3,32 | Består. Sammen med vekt 700 er valget synlig uten farge |
| Valgt Session, fyll | `surface` mot `page` | 1,08 | Ikke bærende. Strek, vekt 600 og radio bærer valget |
| Ikke-bookbar dag eller utilgjengelig rad, fyll | `unavailable` mot `page` | 1,09 | Ikke bærende. Manglende kant eller tekst bærer tilstanden. Inaktive kontroller er unntatt 1.4.3 og 1.4.11 |
| Primary button, fyll | `primary` mot `page` | 1,42 | Ikke bærende. Kanten er påkrevd, som dokumentet sier |
| Fokusring mot knappekant | `focus` mot `button-edge` | 1,70 | Ikke et brudd, fordi 2 px offset legger `page` mellom ringen og kanten |
| Disabled radio | Nettleserens egen stil | Ikke beregnet | Inaktiv, unntatt. Teksten i raden beholder 10,48 |
| Ikke avkrysset radio og Terms checkbox | Nettleserens egen stil | Omtrent 4,09 på `page` | Antar Chromiums standard `#767676`. Ikke et token, se testlisten |
| Hover og active | Ikke definert | Kan ikke beregnes | Se A-24. Ingen mockup har `:hover` eller `:active` |

Konklusjon: ingen kontrastbrudd i tokenene eller komponenttabellene.

## Funn

`A` er funn i kontrakten. `M` er funn bare i mockups. Linjer viser til filen som er nevnt.

### Critical

Ingen.

### High

#### A-01 Avvisning fjerner knappen som har fokus (2.4.3, 4.1.3)

- **Plassering:** `EXPERIENCE.md` linje 322 (After a refusal), 210 (Keeps focus while processing), 248 og 380 (Notices announced without moving focus). `DESIGN.md` linje 383.
- **Konsekvens:** Når plassene blir tatt mens brukeren betaler, fjernes Pay, som har fokus. Dokumentene sier ikke hvor fokus skal, og linje 380 forbyr å flytte det. Notice står foran i DOM, under Back. En skjermleserbruker kan bli stående uten fokus, høre meldingen delvis eller ikke i det hele tatt, og lete forover fra et sted der løsningen ligger bak. Det rammer akkurat det øyeblikket UJ-2 handler om. Linje 321 ("please try again") sier heller ikke om Pay blir værende, selv om linje 322 kaller alle avvisninger like.
- **Forslag:** Legg til en generell regel: når elementet med fokus forsvinner, flyttes fokus til nærmeste meningsbærende etterfølger. På Review er det Notice (`tabindex="-1"`). Gjør dette til et uttrykkelig unntak fra linje 380. Si også at Pay blir værende ved "please try again". Samme regel gjelder når Notice forsvinner på Book seats etter valg av Nearest sessions.

#### A-02 Nearest sessions laster siden på nytt når brukeren flytter med piltast (3.2.2)

- **Plassering:** `EXPERIENCE.md` linje 249, 322, 365, 475–476 (Flow 2), `DESIGN.md` linje 434. Mock: `key-review.html` linje 101.
- **Konsekvens:** Radioer velges allerede når piltasten trykkes, og å velge en rad laster Review på nytt. En tastaturbruker som trykker pil ned fra rad 1 for å høre på rad 2, blir sendt videre med rad 2 uten å ha bestemt seg. Rad 3 nås bare med Shift+Tab bakfra. Dette er en kontekstendring ved inndata uten varsel. Lasting på nytt til samme adresse er kanskje ikke en route change, så heller ikke fokusregelen på linje 366 slår inn.
- **Forslag:** Vis radene som en liste med ett Text link-lignende valg per rad, hver med egen tabulatorstopp og navn som "Choose Friday 13 November, 19:00 to 20:30, 6 seats left". Alternativt: behold radioene og legg til en Primary button, "Use this session", som bare vises mens Pay er borte, slik at én per side fortsatt holder. Si at fokus etter valget går til overskriften på Review.

#### A-03 Zoom på målmaskinen faller utenfor det som er lovet (1.4.4, 1.4.10)

- **Plassering:** `EXPERIENCE.md` linje 18, 392, 397–399. `DESIGN.md` linje 124, 360, 387. PRD FR-23 linje 435.
- **Konsekvens:** FR-23 unntar bare 1.4.10, men linje 392 sier at alt under 1366 px ikke er lovet for v1. Da faller også 1.4.4 bort, og det er et krav i WCAG 2.0. PRD-ens påstand om at Core "meets it in full" holder altså ikke uten videre. En 1366 px-skjerm på 200 % gir 683 CSS px. Da blir hovedspalten 251 px (683 − 320 − 112) mens datospalten er 348 px, så Book seats får rulling i to retninger og Rail ruller ut til siden. Det trengs ikke engang høy zoom: 1920 × 1080 med 150 % skalering i Windows gir 1280 CSS px, altså under grensen. Svaksynte kommer trolig gjennom med mye rulling, så dette er high og ikke critical, men Rail og Continue må testes.
- **Forslag:** Flytt 1024–1365-laget og en enkel enspalteløsning under 1024 px inn i Core, uten Fixed action bar. Addendum linje 393 nevner allerede dette alternativet. Løft "200 % uten tap" inn i FR-23 som eget krav. Beholdes unntaket, må README og Accessibility Floor si at også 1.4.4 er åpent.
- **Usikkerhet:** 1.4.4 forbyr ikke horisontal rulling i seg selv. Om noe faktisk går tapt, må avgjøres i nettleser.

#### A-04 Sidetitler er ikke spesifisert (2.4.2)

- **Plassering:** Ordet finnes ikke som krav i `DESIGN.md`, `EXPERIENCE.md` eller Conventions i `ARCHITECTURE-SPINE.md` linje 293. Innholdstabellene på `EXPERIENCE.md` linje 112–120 har ingen rad for det.
- **Konsekvens:** Dette er en React SPA, så uten en regel får alle sider samme statiske `<title>`. Brukere med skjermleser eller mange faner kan ikke skille Review fra Confirmation, og en feiltilstand synes ikke i tittelen.
- **Forslag:** Legg en tabell i Content Homes med tittel per side, for eksempel "Book seats – Saunalöyly", "Review – Saunalöyly", "Booking confirmed – Saunalöyly". Legg til prefikset "Error: " når Error summary vises. Tittelen settes før fokus flyttes (linje 366). Husk Terms, Privacy notice, "This page is not available." og Administrator-sidene.

#### A-05 Radiogruppene har ikke noe gruppenavn (1.3.1, 3.3.2, 4.1.2)

- **Plassering:** `EXPERIENCE.md` linje 365 (radio groups), `DESIGN.md` linje 335 (spørsmålene er "Small heading") og 417. Mock: `directions-3.html` linje 145–146.
- **Konsekvens:** Dokumentet sier at valgene er radiogrupper, men ikke at gruppen skal ha navn. `DESIGN.md` kaller spørsmålene overskrifter, så den naturlige koden er en overskrift pluss løse radioer. Da hører en skjermleserbruker "3, radio button, 3 of 10" uten å få vite hva tallet gjelder. Mocken gjør nøyaktig dette, uten `fieldset` eller `radiogroup`.
- **Forslag:** Krev `fieldset` med `legend` for Seat picker og Session list, med spørsmålsteksten i `legend` (`{typography.heading-md}` kan beholdes). Gi kalenderens radiogruppe navn med måned og år, for eksempel "Pick a day, November 2026". Oppgi også om nummereringen "1.", "2." og "3." skal leses opp.

### Medium

#### A-06 Feilmodellen på Book seats motsier seg selv (3.3.1, 2.4.3)

- **Plassering:** `EXPERIENCE.md` linje 232 og 300–301 mot linje 250–251 og 381. PRD FR-23 linje 443.
- **Konsekvens:** Linje 232 sier at Continue viser en Field error og flytter fokus dit. Linje 251 sier at en Field error alltid kommer med Error summary, og linje 250 sier at summary tar fokus. Fokusmålet er derfor uklart. Dokumentene sier heller ikke hva som skjer når alle tre svarene mangler, eller hvilket element i en radiogruppe som får fokus. Plassbudsjettet på `DESIGN.md` linje 379 kan ha ført til dette, men FR-23 krever summary.
- **Forslag:** Velg én modell. Anbefalt: Error summary øverst i main med fokus og lenker til hvert spørsmål, siden siden kan ha tre feil. Sjekk at det får plass i budsjettet. Knytt Field error til `fieldset` med `aria-describedby`, og la lenken flytte fokus til valgt eller første radio.

#### A-07 Hvert trykk på piltast leser Sessions, endrer total og kan tømme valget (2.1.1 som støtte, 4.1.3)

- **Plassering:** `EXPERIENCE.md` linje 224, 226, 227, 234, 365, 367.
- **Konsekvens:** Pil velger straks. Mus går direkte fra 2 til 6, mens tastatur går innom 3, 4 og 5, med en ny lesing av Sessions og en ny kunngjøring av totalen for hvert steg. Pil opp fra 1 går rundt til 10 og kan tømme en valgt Session. I kalenderen er pil én dag om gangen (linje 379), så 5. til 28. november gir 23 lesinger. Hvert steg tømmer valgt Session (linje 234). Det brutte kravet er ikke klart, men brukeren får mer støy og mister valg musebrukere beholder. Skrevet dato gjør kalenderen mulig å unngå, så dette blokkerer ikke.
- **Forslag:** Spesifiser en kort forsinkelse før lesing og kunngjøring, at bare siste svar teller, og at valgt Session først tømmes når verdien har ligget stille. Vurder dag som knapp-rutenett med pil i to retninger og egen bekreftelse hvis manuell test viser at listen er for tung.

#### A-08 Statusmeldinger er ufullstendige og mangler mekanisme (4.1.3)

- **Plassering:** `EXPERIENCE.md` linje 248, 291, 367, 380.
- **Konsekvens:** Linje 380 lister Total block, Notices og "Processing". "Loading sessions" er ikke med, heller ikke at listen er oppdatert eller hvilke rader som ble utilgjengelige da antallet endret seg. Regelen sier ikke at live-regionen må finnes i DOM før innholdet kommer. Total block "appears once a number is chosen" (linje 227), og en region som settes inn sammen med teksten, blir ofte ikke lest opp. Skjermleserbrukeren kan derfor endre antall og aldri få vite at valgene har endret seg.
- **Forslag:** Bruk én fast `role="status"`-region per side, tilstede fra første visning. Kunngjør en samlet setning etter at lesingen er ferdig, for eksempel "Total NOK 750. 6 of 8 sessions have room for 3 seats." Legg "Loading sessions" til listen, men bare hvis lesingen tar merkbar tid.

#### A-09 Hint, feil og påkrevd er ikke koblet til feltene i kontrakten (1.3.1, 3.3.1, 3.3.2)

- **Plassering:** `EXPERIENCE.md` linje 215, 251, 381. `DESIGN.md` linje 410, 436. Mock: `directions-3.html` linje 144 (hintet er ikke koblet), `key-details.html` linje 90 (feilen er koblet).
- **Konsekvens:** Kontrakten sier "next to the field", altså plassering, ikke kobling. Bare mocken for Details har `aria-invalid` og `aria-describedby`. Datoformatet er ikke knyttet til datofeltet i mocken, så en blind bruker hører ikke "dd.mm.yyyy" i feltet. Påkrevde felter er ikke merket noe sted. Terms-feil og datofeil finnes ikke som mock.
- **Forslag:** Legg til i Text field-regelen: `aria-describedby` til hint og feil, `aria-invalid="true"` ved feil, `required` på alle felter, og `novalidate` slik at Error summary og ikke nettleserens bobler viser feilen. Oppgi rekkefølgen når både hint og feil vises på datofeltet.

#### A-10 Autocomplete er ikke krevd (1.3.5)

- **Plassering:** `EXPERIENCE.md` linje 215, 385. Mock: `key-details.html` linje 82–83 har attributtene, men det er ikke kontrakt.
- **Konsekvens:** "Paste and password managers work" dekker ikke autofyll av navn og e-post. Brukere med motoriske eller kognitive vansker må skrive alt selv, og det er bare mocken som viser løsningen. Sign-in er ikke rendert i det hele tatt.
- **Forslag:** Skriv det inn: `autocomplete="name"` og `email` på Details, `username` og `current-password` på Sign-in, `autocomplete="off"` på datofeltet.

#### A-11 Review viser ikke navnet og e-posten brukeren skrev (3.3.4)

- **Plassering:** `EXPERIENCE.md` linje 45 ("Check everything"), 170, 252, 463. Mock: `key-review.html` linje 92.
- **Konsekvens:** En booking kan ikke endres eller refunderes, men en skrivefeil i e-posten vises først på Confirmation (linje 252), etter at betalingen er gjort. Mennesker med dysleksi eller som bruker tale til tekst, er særlig utsatt. Back gjør det mulig å sjekke, så kriteriet er trolig formelt oppfylt, men Review-siden er ikke en full gjennomgang slik linje 45 lover.
- **Forslag:** Legg radene "Name" og "Email" til Booking summary på Review. Sjekk mot plassbudsjettet på `DESIGN.md` linje 383 og mot no-repetition-regelen. Dette er ikke en gjentakelse, for Review viser dem ikke andre steder.

#### A-12 Kalenderens månedsnavigasjon og datoinntasting er ikke avklart (2.4.3, 4.1.2, 4.1.3)

- **Plassering:** `EXPERIENCE.md` linje 223, 298, 300–301. `DESIGN.md` linje 416.
- **Konsekvens:** "Next month" er en handling, men er spesifisert som Text link. Horisonten er fire uker, så kontrollen forsvinner eller byttes med "Previous month" etter ett trykk, og fokus kan gå tapt. Månedsbyttet er ikke på listen over statusmeldinger. Det står ikke når en skrevet dato gjelder (hvert tastetrykk, blur eller Enter). Ikke-bookbare dager finnes som tall uten forklaring for skjermleser, selv om `DESIGN.md` linje 397 sier at tilstand alltid sies i ord.
- **Forslag:** Bruk `<button>` med lenkeutseende for begge månedsvalg. Hold kontrollen på plass og la fokus stå, eller flytt det til den andre knappen. Kunngjør "December 2026". La skrevet dato gjelde ved blur og Enter, og la feil vises først da. Gi ikke-bookbare dager skjult tekst, for eksempel "3 November, not bookable", eller skjul dem for skjermleser.

#### A-13 Landemerker, overskriftsnivåer og Rail er ikke definert semantisk (1.3.1, 2.4.1, 2.4.6)

- **Plassering:** `EXPERIENCE.md` linje 213, 366. `DESIGN.md` linje 333–335, 408. Mock: `aside` for Rail, ingen `main` på gjestesider.
- **Konsekvens:** Bare én regel om nivå finnes: Wordmark er toppnivå på Landing. `<h1>` på andre sider er ikke fastsatt, og heller ikke om "Before you come" er `h2`. Typografirollene sier størrelse, ikke nivå. Rail følger mocken som `aside`, og da havner den ene handlingen, og på Landing hovedoverskriften, i et komplementært landemerke som skjermleserbrukere ofte hopper over. Ingen hopplenke er vurdert.
- **Forslag:** Legg en tabell over nivåer per side. Definer `header`, `main` og `footer` eller `nav`. Rail skal ikke være `aside` når den holder handlingen. Fokusregelen på linje 366 gjør hopplenke unødvendig ved rutebytte, men ikke ved direkte innlasting, så avgjør det eksplisitt.

#### A-14 Tabulatorrekkefølgen på Book seats (åpent punkt 14) (2.4.3, 1.3.2, 3.2.3)

- **Plassering:** `EXPERIENCE.md` linje 377, 550. `DESIGN.md` linje 408. Mock: `directions-3.html` linje 67, 147–149.
- **Konsekvens:** Rekkefølgen dato, plasser, Session, Continue gir mening, så selve hovedvalget består trolig 2.4.3. Det svake punktet er Wordmark, som står øverst visuelt, men kommer etter Continue i DOM. Fokus hopper oppover forbi totalen for en bruker med forstørrelse, og Wordmark står et annet sted i rekkefølgen enn på alle andre sider. Mockens `order:-1` er CSS-omstokking av den typen 1.3.2 advarer mot.
- **Forslag:** Del Rail i to rutenett-områder: Wordmark som `header` først i DOM (kolonne 1, rad 1), `main` deretter (kolonne 2), og total, Continue og notater sist (kolonne 1, rad 2). Ingenting gjentas, og Wordmark står først på alle sider. Klebrig plassering må testes med denne delingen.

#### A-15 Utilgjengelige rader forsvinner fra tastatur- og fokusmodus (1.3.1, 4.1.2)

- **Plassering:** `EXPERIENCE.md` linje 225, 226, 294, 378. `DESIGN.md` linje 419.
- **Konsekvens:** Disabled radioer hoppes over av Tab og piltaster. En skjermleserbruker i fokusmodus hører bare valgbare rader, og kan ikke vite at 17:30 finnes og er utsolgt, selv om linje 225 sier at listen skal vise hele timeplanen. Dokumentet tar dette som noe som skal sjekkes, men har ingen løsning hvis sjekken feiler.
- **Forslag:** Bestem løsningen nå: Vis utilgjengelige rader uten radio, som tekst i samme liste, og legg en setning i statusregionen, for eksempel "2 of 8 sessions are not available for 2 seats". Alternativet er `aria-disabled` med stopp i JavaScript, men det gjør radiogruppen mer sårbar.
- **Usikkerhet:** Virkemåten varierer mellom skjermlesere og krever test.

#### A-16 Faste høyder, ingen bryting og smale kolonner hindrer tekstforstørrelse og tekstavstand (1.4.4, 1.4.12)

- **Plassering:** `DESIGN.md` linje 164, 173, 188 (`height`, ikke `min-height`), 405 ("no wrapping"), 419 (150 px tidskolonne), 99–108 (`lineHeight: '1'`). Accessibility Floor nevner ikke 1.4.12.
- **Konsekvens:** Med bare tekstforstørrelse på 200 % blir klokkeslettet 42 px høyt og omtrent 230 px bredt, i en kolonne på 150 px. "Continue booking" i 34 px vil trolig ikke få plass i Railens 240 px uten bryting. Tekst kan overlappe naboen eller gå utenfor kontrollen.
- **Forslag:** Bytt til `min-height`, og tillat bryting på Primary button på smale og forstørrede flater. Bruk `minmax()` i radene i stedet for fast 150 px. Legg 1.4.4 og 1.4.12 til i Accessibility Floor.
- **Usikkerhet:** Breddene er anslag fra tekststørrelse. Faktisk resultat avhenger av de ekte fontene.

#### A-17 Fixed action bar kan dekke det meste av en lav skjerm (1.4.10, 2.4.11)

- **Plassering:** `EXPERIENCE.md` linje 228, 382, 403, 405. `DESIGN.md` linje 421. Gjelder med FR-51.
- **Konsekvens:** Total, tillegg, knapp og padding gir omtrent 124 px i en bar som alltid står. En 1366 × 768-skjerm på 400 % har omtrent 155 CSS px sidehøyde igjen, så baren dekker rundt 80 %. Innholdet og fokus forsvinner bak den. Reglene sier "must leave room", men ikke hvordan.
- **Forslag:** Sett `scroll-padding-bottom` lik barens høyde. Gjør baren statisk på lave vinduer (`@media (max-height: ...)`). Vis total og knapp på én linje, og flytt per-sete-linjen ut av baren.

#### A-18 Administrator-sidene motsier FR-51 (1.4.10, 1.4.4)

- **Plassering:** `EXPERIENCE.md` linje 52, 409. `DESIGN.md` linje 385. PRD FR-51 linje 810–814.
- **Konsekvens:** FR-51 sier "Guests and Administrators" og "every page" fra 320 px, mens spinen sier laptop-only uten smal layout. Bygger man spinen, lukkes Reflow-unntaket aldri for Sign-in, Booking list og Outbox. Ansatte med svakt syn får ingen zoom-støtte.
- **Forslag:** Velg ett. Enten smal layout for Sign-in, Administrator bar og Outbox, med Booking table som egen rullbar region (tabeller er unntatt 1.4.10), eller endre FR-51 og oppgi gapet i README.

#### M-01 Lenker og månedsvalg er `span` i mocken (2.1.1, 4.1.2)

- **Plassering:** `directions-3.html` linje 142 og 149 (Terms, Privacy notice), linje 144 ("Next month").
- **Konsekvens:** Elementene kan ikke nås med tastatur og har ingen rolle. Kopieres dette, kommer tastaturbrukere aldri til neste måned med kalenderen.
- **Forslag:** Kontrakten er riktig (Text link). Rett mocken, eller merk den som ikke-interaktiv.

#### M-02 Session-radioene i mocken skjuler tilgjengelighet (4.1.2, 1.3.1)

- **Plassering:** `directions-3.html` linje 146.
- **Konsekvens:** `aria-label="14:30 to 16:00"` overstyrer etiketten. Skjermleserbrukeren hører tiden, men ikke "6 seats left" eller "Sold out". `EXPERIENCE.md` linje 378 vet om dette og vinner, men mocken er det utviklere kopierer.
- **Forslag:** Fjern `aria-label` og la etiketten gi navnet. Da får raden både tid og plasser, og A-22 forsvinner samtidig. `key-review.html` linje 101 har allerede rett innhold.

### Low

#### A-19 "Processing" kan bli implementert med `disabled` (2.4.3, 4.1.2)

- **Plassering:** `EXPERIENCE.md` linje 210, 315.
- **Konsekvens:** "Takes no second press" leder lett til `disabled`, som i noen nettlesere gjør at fokus går tapt. Det er i strid med "Keeps focus".
- **Forslag:** Skriv `aria-disabled="true"` med blokkering i kode, ikke `disabled`.

#### A-20 Error summary og feiltekster har hull (3.3.1, 3.3.3)

- **Plassering:** `EXPERIENCE.md` linje 179–193, 250, 300–301, 314, 317. `DESIGN.md` linje 435.
- **Konsekvens:** Summary skal lenke til felt, men en mislykket betaling har ikke noe felt. Teksten mangler for manglende dato, manglende antall, ikke-godtatte vilkår, feil datoformat og ikke-bookbar dato. Uten tittel (`DESIGN.md` linje 435) har fokusmålet ikke noe navn, og den første setningen må stå alene.
- **Forslag:** Legg til: summary uten lenke ved betalingsfeil, med fokus på teksten. Skriv de fem manglende tekstene, gjerne med hvorfor og hva brukeren kan gjøre. Gi summary tilgjengelig navn med `aria-label="Errors"` selv om det ikke vises en tittel.

#### A-21 Dyplenken til "Before you come" krasjer med fokusregelen (2.4.3)

- **Plassering:** `EXPERIENCE.md` linje 240, 366. Mock: `key-confirmation.html` linje 88 og 106.
- **Konsekvens:** Fokus flyttes til Wordmark i Rail på hvert rutebytte, så fokus og synlig seksjon havner på forskjellige steder. Neste Tab går til Book seats og ikke inn i seksjonen.
- **Forslag:** Unntak: med ankeradresse går fokus til seksjonens overskrift.

#### A-22 Tilgjengelig navn inneholder ikke den synlige teksten ordrett (2.5.3)

- **Plassering:** `EXPERIENCE.md` linje 378 ("13:00 to 14:30, 12 seats left") mot synlig "13:00–14:30".
- **Konsekvens:** Talestyringsbrukere som sier det de ser, kan bomme. Praktisk virkning er liten og varierer med programmet.
- **Forslag:** La etiketten gi navnet (se M-02), eller bruk samme tegnsetting som den synlige teksten.

#### A-23 Alt-tekster finnes ikke ennå, og finske ord kan ikke merkes i `alt` (1.1.1, 3.1.2)

- **Plassering:** `EXPERIENCE.md` linje 217, 386, 387, 540, 542.
- **Konsekvens:** Linje 542 sier at alt-tekstene ikke er skrevet, så 1.1.1 kan ikke vurderes. Bildene er oppført med ordene lauteet, kiuas, kiulu, kauha og vihta. `alt` kan ikke ha `lang`, så kravet på linje 386 kan ikke oppfylles der, og skjermlesere vil uttale ordene feil.
- **Forslag:** Skriv alt-tekst på engelsk, for eksempel "wooden sauna benches". Spar finske ord med gloser til synlig tekst med `lang="fi"`. Avgjør om bildestripen og håndkleet er pynt (`alt=""`). Sauna-navn er egennavn og unntatt. Jeg fant ingen svenske ord.

#### A-24 Hover, active og tvungne farger er ikke definert (1.4.11, 1.4.1)

- **Plassering:** Fravær i `DESIGN.md` Components. Ingen mockup har `:hover` eller `:active`.
- **Konsekvens:** Utviklere finner på egne farger som ikke er kontrastsjekket. I Windows' høykontrastmodus forsvinner fyll, så valgt dag og plass skilles bare av fontvekt, siden radioene er skjulte. Ikke et AA-brudd i seg selv.
- **Forslag:** Definer hover og active fra eksisterende tokens, gjerne kun med understreking eller kanttykkelse. Legg til en `forced-colors`-regel for valgt celle, for eksempel `Highlight` som bakgrunn.

#### A-25 Datofeltet på Booking list er uspesifisert (3.3.2, 4.1.3)

- **Plassering:** `EXPERIENCE.md` linje 262, 265. Mock: `key-booking-list.html` linje 81.
- **Konsekvens:** Ingen formatinstruks, ingen måte å sende inn på, og det er ikke sagt om "Previous day" og "Next day" er rutebytte. Er de det, flyttes fokus til overskriften etter hvert trykk, og Katja må tabbe tilbake. Er de det ikke, endres innholdet uten kunngjøring.
- **Forslag:** Bruk samme hint som gjesten ser. La Enter og blur gjelde. Ikke flytt fokus fra dagsknappene, og kunngjør ny dato i en statusregion.

#### A-26 Administratorøkten på 8 timer varsles ikke (2.2.1)

- **Plassering:** `ARCHITECTURE-SPINE.md` linje 125 (AD-8, Lifetimes), `EXPERIENCE.md` linje 353.
- **Konsekvens:** 8 timer er under unntaket på 20 timer, og det finnes ingen varsling eller forlengelse. Listen er skrivebeskyttet, så det eneste tapet er en ny innlogging. Gjesteøkten på 24 timer er innenfor.
- **Forslag:** Sett grensen til 20 timer eller mer, eller noter dette som et bevisst, lite avvik. Ingen nedtelling trengs.

#### A-27 Oppførsel uten JavaScript er ikke besluttet (ikke et WCAG-krav)

- **Plassering:** `EXPERIENCE.md` linje 551. `ARCHITECTURE-SPINE.md` (`POST /api/session` ved innlasting). Addendum linje 248.
- **Konsekvens:** WCAG krever ikke at siden virker uten JavaScript, men blokkert eller feilet skript gir en tom side uten kontaktinformasjon. Skrevet dato hjelper ikke da.
- **Forslag:** Legg `<noscript>` med navn, adresse og kontakt i `index.html`, og lukk punkt 15 med det.

#### M-03 Hint, total og Continue i `directions-3.html` (1.3.1, 4.1.3)

- **Plassering:** Linje 144, 147, 148.
- **Konsekvens:** Hintet er ikke koblet til feltet, totalen har ingen live-semantikk, og Continue er `<a href>` der kontrakten sier knapp. Kalenderens `th` mangler `scope`, og tabellen har ingen måned i navnet.
- **Forslag:** Rett i mocken, eller la A-05, A-08 og A-09 styre.

#### M-04 `<caption hidden>` på Booking table (1.3.1)

- **Plassering:** `key-booking-list.html` linje 82.
- **Konsekvens:** `hidden` tar teksten ut av tilgjengelighetstreet, så tabellene mangler trolig navn. `<h3 aria-label>` over tabellen gir navn til overskriften, ikke tabellen.
- **Forslag:** Bruk `aria-labelledby` til Session-overskriften, eller en visuelt skjult `caption` uten `hidden`.

#### M-05 Skjemamarkup i Details og Review (4.1.3, 4.1.2)

- **Plassering:** `key-details.html` linje 83, 88, 90. `key-review.html` linje 100–101.
- **Konsekvens:** `role="alert"` kombinert med fokus kan gi dobbel opplesing. E-postfeltet er `type="email"` i én tilstand og `type="text"` i feiltilstanden. `role="status"` rundt radioer kan få hele innholdet opplest, og fungerer dårlig om regionen settes inn samtidig med teksten.
- **Forslag:** Bruk fokus uten `role="alert"` for Error summary. Bruk `type="email"` i begge tilstander, med `novalidate`. Hold statusregionen til meldingen, og legg valgene utenfor.

#### M-06 Mockene motsier "no change beyond one column" (1.4.10)

- **Plassering:** `EXPERIENCE.md` linje 407. `key-review.html` linje 83, `key-confirmation.html` linje 76.
- **Konsekvens:** Nearest sessions-raden krever minst 372 px pluss padding, og er bredere enn 320 px. `.email` mangler `overflow-wrap`, så en lang lenke kan gi horisontal rulling. Gjelder ved FR-51.
- **Forslag:** Stable raden på smale bredder, og legg `overflow-wrap: anywhere` på Email as sent.

## Vurdert uten funn

- **Tastatur (2.1.1, 2.1.2, 2.5.7):** Alle handlinger har tastaturvei, det finnes ingen dialoger eller feller, og dra-bevegelser er utelukket (`EXPERIENCE.md` linje 363, 370).
- **Fokusring (2.4.7, 2.4.11):** 3 px med 2 px offset er tydelig, og `surface`, `page`, `primary` og `bar` gir minst 4,70:1. Ringen ville også klart AAA-kriteriet 2.4.13. Sticky Rail i egen kolonne dekker ikke fokus ved 100 %.
- **Målstørrelse (2.5.8):** 34 px dager og 40 px rader består. Setecellene blir 25,2 px brede på 320 px, som holder så vidt.
- **Tid (2.2.1):** Core har ingen Hold og ingen nedtelling. Gjesteøkten er 24 timer. Hold (If time) forkaster aldri inntastet data (FR-35, FR-36), og lesningen i addendum linje 72 er forsvarlig.
- **Farge alene (1.4.1):** Lenker er alltid understreket, utilgjengelighet sies i ord og feil er tekst.
- **Økonomisk transaksjon (3.3.4):** Review, Terms checkbox og Back oppfyller kravet, med forbehold om A-11.
- **Autentisering og gjentatt inntasting (3.3.8, 3.3.7):** Ingen kognitiv test, lim inn er tillatt, navn og e-post beholdes ved avvisning.
- **Språk (3.1.1):** Sidespråket er spesifisert.
- **Bevegelse (2.3.3):** Ingen bevegelse trengs, og redusert bevegelse respekteres.
- **Session-listens form:** Radiogruppe er et godt valg. En tabell ville ikke gitt mer, så lenge navnet inneholder tid og tilgjengelighet.
- **Betaling og leveranser:** Simulert betaling skjer i eget nettsted uten tredjepart. Core har ingen PDF-er. E-poster er ren tekst, som er tilgjengelig i seg selv.
- **Logo:** Wordmark er tekst, så 1.1.1 berøres ikke.

## Må avgjøres ved testing

Akseptkriteriene i FR-23 er axe og tastatur. Ingen av dem fanger de viktigste funnene over. Legg derfor til skjermleser og zoom i den manuelle gjennomgangen.

**Skjermleser (NVDA med Chrome, JAWS, VoiceOver med Safari)**

- Hvordan disabled radioer leses i bla- og fokusmodus, og om telling som "3 of 8" stemmer (A-15).
- Om `role="status"` leses opp når innholdet settes inn etter rutebytte eller avvisning (A-01, A-08).
- Om navnebytte til "Processing" på en fokusert knapp leses opp (A-19).
- Hvordan radioer i en tabell leses, og om radiogruppe i tabell er forståelig (A-05, A-12).
- Hvordan Booking reference `7K3MQ9XD` uttales, og om den bør leses tegn for tegn.

**Tastatur**

- Hvilken radio Tab og Shift+Tab lander på i en gruppe uten valg, i Chromium, Firefox og Safari (A-02).
- Hvor neste Tab havner etter at fokusert element er fjernet (A-01, A-12).
- Om lenker i Error summary faktisk flytter fokus, også til radiogrupper (A-06).
- Om en fokusring vises på overskrift og summary når fokus settes med skript. Kontrakten krever ring bare på interaktive elementer (`EXPERIENCE.md` linje 364).
- Om tabulatorrekkefølgen på Book seats oppleves som logisk (A-14).

**Zoom og visning**

- 110 %, 150 %, 200 % og 400 % på 1366 × 768, og 1920 × 1080 med 150 % skalering (A-03).
- Om Rail blir høyere enn vinduet, slik at klebrig plassering skjuler notater og lenker, og om fokus da når dem. Regnet til omtrent 516 px, så det skjer allerede rundt 125 % zoom.
- Tekststørrelse 200 % og tekstavstand med ekte fonter (A-16).
- Om ringen på 5 px dekkes av nabocellen, siden gapet bare er 4 px, og mocken bruker `position:relative`.
- Wordmark på 52 px ved 320 px med ekte font (`DESIGN.md` linje 387).
- Windows høykontrast med skjulte radioer (A-24).

**Annet**

- Kontrast på ikke avkryssede radioer og Terms checkbox i hver nettleser, siden de bruker nettleserens egen kant.
- Talestyring på Session-rader (A-22).
- Endelig kontroll av 1.1.1 når alt-tekst og bilder finnes (A-23).
