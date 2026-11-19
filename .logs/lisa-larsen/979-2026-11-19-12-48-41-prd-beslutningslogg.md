# PRD: beslutningslogg skilt fra krav

## 2026-11-19 kl. 12:48 — Lisa Larsen

### Oppgave
Tilbakemelding på PRD-en (lav): beslutningslogg og krav var blandet. Rundt halvparten av §12 var avgjort, navn og datoer sto midt i FR-teksten, og SC-tabellen manglet en FR-kolonne. Forslaget var å dele §12 i åpne og avgjorte spørsmål, samle beslutningsdatoene i addendum M og legge til FR-kolonnen.

### Plan
- §12: åpne spørsmål i full tekst (12.1), avgjorte som tabell med ett svar per spørsmål (12.2). Numrene beholdes, så «§12 Q3» osv. fortsatt virker. Full tekst flyttes ordrett til addendum M.2.
- Ta alle 22 dato-parenteser ut av FR-teksten (§4 i `prd.md` og vedlegget) med et skript, og føre hver av dem som en rad i addendum M.3 (hvor, krav, hvem, dato).
- Addendum M blir «Decision log», med det eksisterende innholdet som M.1.

### Resultat
- `prd.md` §11: SC-tabellen har kolonnen FR (SC1 FR-1–FR-17, SC2 FR-29–FR-32, SC3 FR-25–FR-28, SC4 FR-33, SC5 FR-43–44, SC6 FR-45–50, SC7 ingen, SC8 FR-39, SC9 som SM-2, SC10 FR-22/23 og FR-51).
- `prd.md` §12: 12.1 Open har Q1, Q6 (nå bare rekkefølgen på punkt 4–6), Q8, Q9, Q11, Q12, Q13, Q15 og Q16. 12.2 Decided er en tabell for Q2–Q7, Q10, Q14 og Q17, uten datoer.
- `prd.md` §4 og `appendix-fr-34-51.md`: 16 + 6 parenteser med navn og dato er fjernet. Der parentesen også hadde innhold, er det beholdt: «(addendum M)» i FR-35 og «(Vision)» i FR-38.
- `addendum.md` M: «Decision log» med M.1 (reviewer-runden, uendret), M.2 (de avgjorte spørsmålene ordrett) og M.3 (22 rader).
- Datoer utenfor FR-teksten, for eksempel i §10 og i de åpne spørsmålene, er ikke rørt.
- Committet i `38a0469`.

### Åpne punkter
Ingen.
