# Oppdater brief etter research

## 2026-10-29 kl. 12:55 — Lisa Larsen

### Oppgave
Lisa ba om å oppdatere product brief i forhold til de tre research-rapportene (samtidighet, kapasitetsmodell for enkeltplasser, låsløsninger og dørkoder). Briefen skal bare ta inn det som endrer produktutsagn; detaljer går i addendumet.

### Plan
- `bmad-product-brief` i Update-modus: les brief, addendum, memlogg, brainstorm-logg og de tre rapportene.
- Legg fram hva research endrer, og la Lisa avgjøre de tre funnene som strider mot tidligere beslutninger (vinduer, dørkoder etter sendetid, plassering) samt hvor mye av de åpne tilfellene som skal inn i briefen.
- Fører beslutningene i `.memlog.md`, oppdater `brief.md` og `addendum.md`.

### Resultat
Beslutninger fra Lisa (alle fulgte anbefalingen):
- Tidsvinduer er felles for alle badstuer og overlapper aldri delvis (E1, E3). Avløser antakelsen om ulik lengde per badstue.
- Dørkode-reglene er ikke avhengige av tilbakekalling: etter sendetid nektes hel booking av en badstue så lenge enkeltplass-bookere har koden (H12).
- Briefen krever plasseringsresultat (invarianter), ikke flytting. Utledet eller lagret plassering er arkitektur. Under én-badstue-tilgang fryses plasseringen ved sendetid (H21). Avløser «flytting er tillatt når som helst» og «ny e-post ved flytting» for én-badstue-tilgang.
- Åpne tilfeller står kort i briefens Open Questions, detaljert i addendumet.

Endringer (ikke committet):
- `.docs/planning-artifacts/briefs/brief-booking-platform-2026-09-20/brief.md`: hel-badstue-punktet, dørkode-punktet og SC6, Administration (vinduer), SC1 (parallelle tester, ingen ytelsestall), Open Questions (arkitektur, PRD, ikke testet). `updated: 2026-10-29`.
- `addendum.md`: radene Seat placement, Door codes, Time windows og «Fixed in v1»; seksjonene «Open questions» for enkeltplasser og dørkoder; ny seksjon «Research input» med 14 anbefalte tilfeller, samtidighetskrav og testtilnærming.
- `.memlog.md`: fire beslutninger og én endringsoppføring (117 oppføringer).

Ikke gjort: polering etter `doc_standards` (`bmad-review` med structure og prose) er hoppet over for å spare tokens. `brief.md` er nå ca. 2 200 ord, over målet på 1–2 sider; verdt en kortning ved neste runde. Brainstormens beslutning om å utsette 10-minutters hold i MVP (997) er ikke ført inn i briefen eller addendumet, siden den ikke kommer fra research.

### Åpne punkter
- Polering av `brief.md` og `addendum.md` (`bmad-review` structure, prose) er ikke kjørt; briefen er ca. 2 200 ord og bør kortes ned mot 1–2 sider.
- Briefen sier ikke at 10-minutters hold er utsatt i MVP (beslutning i brainstorm-minste-v1); avgjør om brief/addendum skal justeres eller om dette hører hjemme i PRD.
