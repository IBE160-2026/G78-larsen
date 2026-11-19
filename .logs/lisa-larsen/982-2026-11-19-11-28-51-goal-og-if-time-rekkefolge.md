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
