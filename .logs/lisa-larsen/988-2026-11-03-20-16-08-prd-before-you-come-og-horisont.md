# PRD: «Before you come» og Booking horizon-grense

## 2026-11-03 kl. 20:00 — Lisa Larsen

### Oppgave
Lisa ba om tre tekstendringer i «Before you come» og en grense på Booking horizon (først 1 år, deretter rettet til 1 måned).

### Plan
- Finne alle forekomster i PRD og addendum (`grep`), endre bare der teksten faktisk står.
- Tolke «booking horizon limit 1 year» som kolonnen Limit i FR-39-tabellen (var «—»); standardverdien 4 uker er uendret.

### Resultat
- `prd.md` (landingssiden, FR-1/«Before you come»): «alcohol is forbidden at the venue» → «alcohol is not allowed at the venue»; «be considerate to people who like it quiet in the sauna» fjernet; «children are supervised by an adult» → «children must be supervised by an adult».
- `prd.md` FR-39: Limit for Booking horizon «never more than 1 month» (Lisa bad først om 1 år og rettet det til 1 måned samme dag), og ny testbar linje: en endring som setter horisonten over 1 måned avvises.
- `addendum.md` F («For "Before you come"»): kildenotatet og «Wording on the page»-linjen oppdatert tilsvarende.
- Ikke endret: `review-*.md`, `reconcile-*.md`, `prd-v0.md` (historiske arbeidsfiler). **Endringene er ikke committet.**

### Åpne punkter
Ingen. (Punktet om ca. 2 900 vinduer gjaldt grensen på 1 år og er lukket etter rettelsen til 1 måned: ca. 250 vinduer, på størrelse med seedens ca. 230.)
