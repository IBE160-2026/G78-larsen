# Research: låsløsninger og dørkoder

## 2026-10-28 kl. 14:58 — Lisa Larsen

### Oppgave
Kjøre en liten teknisk research på om ekte smartlåser kan ha to gyldige koder på samme dør samtidig og om en kode som allerede er sendt kan byttes eller trekkes tilbake. Det skal avgjøre hvordan PRD formulerer H6 og H12–H14 (gruppe H, SC6). Lisa la til: krever dette at plasser flyttes likevel?

### Plan
- Planporten godkjent av Lisa: `quick`, to assistenter uten prosjektfiler (A: Nuki, TTLock, igloohome, August/Yale; B: Seam, RemoteLock, Schlage), validering `normal`, red team av.
- Flyttespørsmålet besvart av meg i syntesen som egen slutning (ikke sendt til assistentene, på grunn av brannmuren).
- Stikkprøve: jeg hentet Seam-guiden, Allegion-guiden og Seam-siden om igloohome på nytt.

### Resultat
- Rapport: `.docs/planning-artifacts/research/technical-smart-lock-door-code-overlap-and-revoke-2026-10-28/research.md` (digests og `.memlog.md` i samme mappe). Ukommittert.
- Flere koder per dør er vanlig (Schlage 100, igloohome 199). Ingen kilde har en regel mot overlappende gyldighet med ulike PIN-er, men ingen bekrefter det heller. Kollisjonsregler gjelder lik PIN.
- Tilbakekalling avhenger av kodetype: nettkoder kan endres eller slettes (Seam, Nuki), offline-koder (igloohome, TTLock offline) kan ikke trekkes tilbake. Låser med timeoppløsning gjør H6-overlappet lengre.
- Anbefaling: skriv reglene slik at de ikke krever tilbakekalling (H12: ingen heltbooking av S etter sendetid mens plassbookere har K(S)); bytte av kode er et ekstra for låser som støtter det.
- Flytting: i standardmodus krever dørkoder ingen flytting. Med én-badstue-tilgang bør plassering fryses ved sendetid (strengere enn H21, i strid med addendumets «flytting når som helst»). Slutning, ikke kildebelagt.
- Krav i ledgeren: 3 verifisert, 7 uverifisert. Mekanisk sitatsjekk OK.

### Åpne punkter
- Avgjør i PRD: frys plassering ved sendetid under én-badstue-tilgang (utvider H21); H6 aksepter overlapp eller start gyldighet ved vinduets start; H12 baseline uten tilbakekalling.
- Ikke svart på av noen kilde: kan to koder med ulike PIN-er overlappe på én lås, og virker endring/sletting etter at gyldigheten har startet? Krever test på ekte eller Seam-sandbox-lås.
- TTLock, Nuki og Yale/August er dekket bare via integratorer og forumposter (delvis 2018–2019); RemoteLock-dokumentet er bare lest til tegn 100 000 av 317 000; Schlages API-referanse er ikke lest.
- Semantisk sitatsjekk og `bmad-review`-polering hoppet over.
- Funnene er ikke ført tilbake i gruppe H i kapasitetsmodell-rapporten ennå.

## 2026-10-28 kl. 15:03 — Lisa Larsen

### Oppgave
Føre funnene fra låsresearchen tilbake i gruppe H i kapasitetsmodell-rapporten.

### Plan
- Oppdatere de berørte radene i H og legge til kilde [11] (låsresearchen) i kildetabellen.

### Resultat
- `.docs/planning-artifacts/research/technical-kapasitetsmodell-enkeltplasser-2026-10-28/research.md`: H6 (ulike PIN-er, lengre overlapp på timelåser), H11 (kode bekreftet på låsen før utsendelse), H12 (baseline uten tilbakekalling, bytte av kode bare for nettkoder), H13 (bytt eller slett der låsen støtter det), H15 (best effort), H20 og H21 (frys plassering ved sendetid) er oppdatert. Sammendrag, anbefaling 7 og det åpne spørsmålet om låser er justert. Ny kilde [11]. Ukommittert.

### Åpne punkter
- Ingen nye. Punktet om å føre funnene tilbake i gruppe H er lukket.
