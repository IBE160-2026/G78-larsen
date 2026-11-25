# Seed-e-posten med Manage-lenke

## 2026-11-24 kl. 23:30 — Lisa Larsen

### Oppgave
Lisa skulle godkjenne ordlyden i seed-e-posten «Manage your booking: {ref}». Den sendes til eksempelbookinger som mangler Manage-lenke. Punktet var åpent fra [story-4-1-manage-link](955-2026-11-24-11-43-33-story-4-1-manage-link.md). Lisa godkjente teksten, men ba om tre tillegg:
- antall plasser
- hvordan bookingen ble betalt: med voucher, med kort eller begge deler
- utløpsdatoen til en eventuell voucher som ble brukt

### Plan
- Ny gren `story/4-1-seed-email-seats` fra `main`.
- Bruke samme linjeformat som bekreftelses-e-posten («Seats: N», «Paid with voucher», «Paid by card»).
- Hente utløpsdatoen fra `voucher.next_last_valid_date`. Det er den samme datoen som en ny voucher får når plassene gis fra seg.

### Resultat
- `src/booking_platform/services/seed.py` (`manage_email`, `issue_sample_links`): etter «Session» kommer nå «Seats: N». Deretter kommer «Paid with voucher: NOK {part}, valid until {long date}» og «Paid by card: NOK {card}». Hver linje vises bare når beløpet er over null, så en booking betalt på begge måter får begge linjene. Beløpene hentes med `bq.charges`.
- `tests/test_fr25_manage_link.py`: seed-testen sjekker nå plasser og kortlinje. En ny parametrisert test dekker de tre tilfellene: bare kort, bare voucher, og begge.
- EXPERIENCE.md, Voice and Tone: ny tabell «Sample Manage link email, accepted by Lisa».
- Testkjøring: `tests/test_fr25_manage_link.py` 30 bestått, og API-testene for seed/sample 25 bestått. Hele suiten er ikke kjørt.
- Commits på grenen: `b2a2cbb` (plasser) og `ee19f0d` (betaling og utløpsdato). Pushet, og PR #19 er åpnet mot `main`.
- Lisa skrev «kontanter». Appen har bare simulert kortbetaling, så teksten sier «card».

### Åpne punkter
- Eksempelbookingene i seeden er alltid betalt med kort. Voucherlinjen er derfor bare testet med en enhetstest, ikke i en ekte seed-kjøring.
