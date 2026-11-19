# PRD: forventet utfall fra katalogen skrevet inn

## 2026-11-19 kl. 12:35 — Lisa Larsen

### Oppgave
Etter tilbakemelding på PRD-en: mange konsekvenser viste bare til katalog-ID-er (A6, D3, H12 osv.), så den som skriver story eller test måtte åpne katalogen med 85 eksempler. Forventet utfall skulle skrives inn i FR-ene som kommer med i bygget.

### Plan
- Avgrense til FR-ene som bygges (FR-1–FR-33, §4.1–§4.9, jf. §10-tabellen). FR-40 og andre FR-er i `appendix-fr-34-51.md` er ikke med.
- Hente tallene fra katalogen (`research/technical-kapasitetsmodell-enkeltplasser-2026-10-28/research.md`) og regne hvert eksempel om igjen med seed-badstuene 7/10/12/15. ID-ene blir stående som sporingsmerker.

### Resultat
`prd.md`:
- §4.9 har fått en forklaring på notasjonen: Saunas 1–4 = 7, 10, 12, 15 plasser (addendum J), `[7,10,5,0]` og `—`. ID-ene er bare sporingsmerker.
- FR-13: eksempel for E2/E4/E6 (avbestilling kl. 14:30 endrer ikke 16:00; hel Sauna 3 kl. 14:30 påvirker ikke 16:00).
- FR-26: E5 (flytte 3 plasser til en økt med 2 ledige avvises; ingenting endres).
- FR-29: B2 med begrunnelse (20 > 17), B3, B7 (44 → 29), B5 (`[7,—,2,0]`) og H12 som nytt eksempel (startet økt, 29 plasser, Sauna 4 kan ikke bookes hel).
- FR-31: «Catalogue groups A and B hold» er erstattet med utfallet for A1–A5, A8, B4 (omskrevet under 10-plassgrensen: 10+10+10+7 = 37), B5 og B6, med henvisning til FR-12 og FR-29 for resten.
- FR-32: C2, C3 og C4 med tall. C6 viser til FR-40 i stedet for D2/D3.
- F1 i FR-32 er ikke skrevet ut (kapasitetsendring hører til FR-38, If-time 7).
- Committet i `19acd6e`.

### Åpne punkter
Ingen.
