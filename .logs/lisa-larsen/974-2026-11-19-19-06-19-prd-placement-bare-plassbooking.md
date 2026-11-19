# PRD: «never told a Sauna» gjelder bare plassbooking

## 2026-11-19 kl. 19:06 — Lisa Larsen

### Oppgave
Lisa ba om å presisere at «Guests are never told a Sauna. The Administrator can see the Placement of each Window.» bare gjelder plassbooking. Ved booking av hel badstue velger gjesten badstuen selv.

### Plan
- Rette setningen (den står i FR-31, ikke FR-30) og den tilsvarende setningen i ordlisten (§3, Placement).

### Resultat
- `prd.md` FR-31: «A Guest with a Seat booking is never told a Sauna: Placement is not shown on any Guest page or in any Guest email (FR-4). Only the Administrator can see the Placement of each Window. A Whole-sauna booking is different: the Guest chooses the Sauna, and the confirmation names it (FR-30).»
- `prd.md` §3 Placement: «Guests with a Seat booking move freely … and are never told a Sauna.»
- Committet i `9f10890`.

### Åpne punkter
Ingen.

## 2026-11-19 kl. 19:22 — Lisa Larsen

### Oppgave
Pushe til origin.

### Plan
- `git push` på `main`.

### Resultat
9 commits pushet til `origin/main`: PRD-presiseringene av FR-29 (merket badstue), FR-31/FR-29 (B5) og FR-31/§3 (Placement bare for plassbooking), med sesjonsloggene. Denne loggoppføringen er pushet i samme omgang.

### Åpne punkter
Ingen.
