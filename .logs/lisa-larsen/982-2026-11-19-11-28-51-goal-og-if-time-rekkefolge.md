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
