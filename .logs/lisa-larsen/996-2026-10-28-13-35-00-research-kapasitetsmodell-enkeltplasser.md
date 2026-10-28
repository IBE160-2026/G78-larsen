# Research: kapasitetsmodell for enkeltplasser

## 2026-10-28 kl. 13:35 — Lisa Larsen

### Oppgave
Kjøre `bmad-deep-recon` som «technical», kort, om algoritmen «fyll én badstue om gangen, flytt plasser fra sist fylte ved avbestilling». Kartlegge kantcaser (flere vinduer, blokkering, hel-badstue-konflikt) som eksempler som senere blir akseptansekriterier og tester. Algoritmen er bare aktuell etter at hel badstubooking er på plass, og hvis tid.

### Plan
- Planporten godkjent av Lisa: `quick`-preset, to assistenter uten prosjektfiler (algoritme/sammenlignbare domener og implementasjon), validering `normal`, red team av.
- Kantcase-katalogen skrevet av meg fra addendumet (spesifikasjon, ikke bevis). Research brukt til å støtte og supplere.
- Lead sjekket to kilder selv: sqlite.org (transaksjonsregler) og RoomTetris-abstractet (tidlig romtildeling).

### Resultat
- Rapport: `.docs/planning-artifacts/research/technical-kapasitetsmodell-enkeltplasser-2026-10-28/research.md` (digests og `.memlog.md` i samme mappe). Ukommittert.
- Hovedfunn: algoritmen er uvanlig; hoteller tildeler rom sent og restauranter flytter ikke tildelte bord. Plasser er identiske og kan deles, så plassering kan utledes av tellinger. Da trengs ingen flyttekode ved avbestilling. Formelen er egen slutning, ikke kildebelagt.
- 39 eksempler i Gitt/Når/Så, gruppert A fyll og flytt, B hel badstue, C samtidighet, D blokkering, E flere vinduer, F adminendringer, G ikke-delbare grupper (bare trinn 2). Fem invarianter INV-1 til INV-5.
- Skarpeste funn: delvis overlappende vinduer gir for høy kapasitet (E1, E3). En blokkering kan tvinge ut bookinger (D3).
- Krav i ledgeren: 2 verifisert, 4 uverifisert. Sitatsjekk (mekanisk) OK.

### Åpne punkter
- Avgjør i PRD: hva som skjer ved opphevet blokkering (D7), hel-badstue-markering på badstue med plasser (D8), senket kapasitet (F1), endret fyllrekkefølge (F2) og flytting i vindu som har startet (F3). Katalogen har anbefalt svar på hver.
- Avgjør i PRD: tidsvinduer er felles for hele anlegget og overlapper ikke delvis (E1, E3). Uten dette holder ikke kapasitetsgarantien.
- Avgjør i arkitekturen: lagret eller utledet plassering. Bevis den utledede formelen med modellbasert test mot katalogen før den brukes.
- Semantisk sitatsjekk (egen assistent) og `bmad-review`-polering av research.md hoppet over for å holde kjøringen kort.
- Ingen kilde funnet på lagret vs utledet plassering i praksis, og ingen badstu/spa-sammenlignbare. Kan tas i en senere Deepen.

## 2026-10-28 kl. 14:47 — Lisa Larsen

### Oppgave
Sjekke om researchen dekket Success Criterion 6 (dørkoder sendt på e-post til nøyaktig de bookerne som får bruke hver dør, med administratorens verktøy for tidspunktet), og legge til gruppe H i `research.md`.

### Plan
- Søk i researchen og briefen: dørkoder var ikke nevnt, bare «én-badstue-tilgang (trinn 2)» indirekte.
- Bygge gruppe H fra addendumet (rad «Door codes», fast-i-v1-tabellen og blokkering), ikke fra nye kilder.

### Resultat
- `.docs/planning-artifacts/research/technical-kapasitetsmodell-enkeltplasser-2026-10-28/research.md`: ny gruppe H med 23 eksempler (H1–H23). Ukommittert.
  - H1–H7: hvem får hvilke koder i standardmodus (hel booking, blokkering, hel-booking-bare, badstue uten lås, to vinduer, avbestilling før utsendelse).
  - H8–H11: tidspunkt og adminverktøy (20 min standard, endret sendetid, booking etter sendetid, manglende kode, send på nytt).
  - H12–H15: endringer etter utsendelse (hel booking, blokk, opphevet blokk, overbooking).
  - H16–H18: gradvis åpning. H19–H23: én-badstue-tilgang.
- Hovedfunn: standardmodus trenger ikke lagret plassering, bare én-badstue-tilgang gjør det. Skarpeste hull: hel booking av en badstue etter at kodene er sendt lar plassbookere beholde en gyldig kode (H12).
- Endret også sammendrag (62 eksempler, ny punktliste om dørkoder), anbefaling 6 og ny 7, og ett nytt åpent spørsmål om låssystemer.
- Ikke kjørt: ny kildesøk eller sitatsjekk; H er spesifikasjon fra addendumet, ikke bevis.

### Åpne punkter
- Avgjør i PRD: H6 (kode gyldig 20 min før start mens forrige vindu pågår), H10 (endret sendetid etter utsendelse), H12 (hel booking etter utsendelse), H13 (blokk etter utsendelse), H21 (flytting i startet vindu med én-badstue-tilgang), H23 (slå på én-badstue-tilgang med delte bookinger). Katalogen har anbefalt svar.
- Kan en ekte låsløsning ha to koder på én dør eller bytte en sendt kode (H6, H12–H14)? Ikke undersøkt; låser er simulert.
