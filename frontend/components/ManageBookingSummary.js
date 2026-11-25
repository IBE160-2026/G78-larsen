// Manage booking summary (FR-25; shared with Epic 5): the Reference display and the Booking summary of the Manage
// page, from the Manage read (`GET /api/manage/{reference}`): date, session, Seats and the total paid. No name, no
// email and, for a Seat booking, no Sauna (FR-4). A cancelled Booking (Story 4.3) shows the Seats given up and no
// total. A Whole-sauna booking (Story 5.2) shows its Sauna first, then date, session and total, never the Sauna's
// Capacity.
import BookingSummary from './BookingSummary';
import ReferenceDisplay from './ReferenceDisplay';
import { SUMMARY, VOUCHER, seatsWord } from '@/lib/copy';
import { clockTime, longDate } from '@/lib/dates';
import { nok } from '@/lib/venue-format';

export default function ManageBookingSummary({ booking }) {
  const w = booking.window;
  const cancelled = booking.status === 'cancelled';
  if (booking.kind === 'whole') {
    return (
      <>
        <ReferenceDisplay reference={booking.reference} />
        <BookingSummary
          rows={[
            { label: SUMMARY.sauna, value: booking.sauna?.name ?? '' },
            { label: SUMMARY.date, value: longDate(w.date) },
            { label: SUMMARY.session, value: `${clockTime(w.start)}–${clockTime(w.end)}` },
            { label: SUMMARY.total, value: `${nok(booking.total_ore)} incl. VAT` },
          ]}
        />
      </>
    );
  }
  return (
    <>
      <ReferenceDisplay reference={booking.reference} />
      <BookingSummary
        rows={[
          { label: SUMMARY.date, value: longDate(w.date) },
          { label: SUMMARY.session, value: `${clockTime(w.start)}–${clockTime(w.end)}` },
          ...(cancelled
            ? [{ label: VOUCHER.seatsGivenUp, value: seatsWord(booking.seats) }]
            : [
                { label: SUMMARY.seats, value: seatsWord(booking.seats) },
                { label: SUMMARY.total, value: `${nok(booking.total_ore)} incl. VAT` },
              ]),
        ]}
      />
    </>
  );
}
