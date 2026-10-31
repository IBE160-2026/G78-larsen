# PRD: Release time-grense

## 2026-10-31 kl. 21:22 — Lisa Larsen

### Oppgave
Lisa ba om at grensen for Release time (06:00-regelen, FR-39) settes til Booking deadline.

### Plan
- Finne alle steder i PRD-en som beskriver Release time og Booking deadline (FR-39, FR-41, §13).
- Gjøre grensen til en regel som kan testes, uten å endre andre krav.

### Resultat
Endret `prd.md` (ikke committet sammen med noe annet):
- FR-39, tabellen: grensen for Release time er «never later than the Booking deadline of the Window it applies to».
- FR-39, konsekvenser: ny regel som sjekkes per vindu, fordi Release time er et klokkeslett og Booking deadline hører til et vindu. En endring av Release time som havner etter deadline for et vindu med en uløst Whole-booking-only-badstue avvises, og det samme gjelder en endring av Booking deadline til før Release time. Med regelen slått av gjelder ikke grensen. Merket som `[ASSUMPTION]`.
- FR-41: merking av en badstue avvises hvis Release time er senere enn vinduets Booking deadline. Den gamle regelen «ikke frigjort etter deadline» er erstattet med at frigjøring aldri hoppes over av den grunnen.
- §13: antakelsen under FR-41 byttet ut med antakelsen om per-vindu-sjekk. Front matter `updated: 2026-10-31`.
- Brief-addendum (`briefs/…/addendum.md`): regeltekst (L53) og innstillingsrad (L101) sier nå at Release time ikke kan være senere enn siste bookingtidspunkt. PRD-addendum H nevner beslutningen. Reconcile-filene er uendret (historiske).

### Åpne punkter
- Tolkningen «sjekkes per vindu» er min; Lisa bør bekrefte den (alternativet er én global grense, for eksempel mot første vindu på dagen).
- Ingen flere.
