# EXPERIENCE.md: endringsteksten fra Story 4.1

## 2026-11-24 kl. 23:15 — Lisa Larsen

### Oppgave
Fjerne Core-teksten «A booking cannot be changed or refunded.» fra EXPERIENCE.md og bruke endringsteksten fra §4.8 i stedet. Den teksten er i produktet siden Story 4.1. Åpent punkt fra [story-4-1-manage-link](955-2026-11-24-11-43-33-story-4-1-manage-link.md).

### Plan
- Finne alle steder i EXPERIENCE.md der den gamle teksten står.
- Bruke ordlyden som er i `content/terms-seats.json` og Terms-siden: «Up to 12 hours before the session starts, you can move some or all seats to another session, or give them up for a voucher. Money is not refunded.»

### Resultat
Endret `.docs/planning-artifacts/ux-designs/ux-booking-platform-2026-11-05/EXPERIENCE.md`:
- Voice and Tone, Required statements: «What can be changed, in Core» heter nå «What can be changed» og har den nye teksten (FR-5, §4.8, Lisa, Story 4.1).
- Voice and Tone, Page and message wording: bookingvilkårene har den nye andre setningen. Raden nevner nå også bekreftelses-e-posten, `content/terms-seats` og Terms-seksjonen «Changes and refunds».
- Flow 1, steg 6: Review-vilkårene i reisen er oppdatert.
- Open Item 11 og avstemmingspunkt 5 (PRD) har en merknad om at teksten ble erstattet 2026-11-24. Den gamle teksten står igjen der bare som historikk.
- `updated` er satt til 2026-11-24.
Ikke committet. Dokumentendringen ligger i arbeidskopien på `main`.

### Åpne punkter
Ingen.
