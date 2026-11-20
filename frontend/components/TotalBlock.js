// Total block (FR-3, UX-DR20): in the rail, once and never per Session. The per-seat line shows from the first
// arrival; "Total NOK 500 incl. VAT" appears once a number of Seats is chosen, in a polite live region, so a change
// is announced without moving focus. The price comes from `GET /api/venue`. Without it, the rail shows the
// "please try again" Notice instead of the price lines.
import Notice from './Notice';
import { BOOK, VENUE_UNAVAILABLE } from '@/lib/copy';
import { nok } from '@/lib/venue-format';

export default function TotalBlock({ pricePerSeatOre, seats }) {
  if (pricePerSeatOre == null) {
    return (
      <div className="total-block">
        <Notice>{VENUE_UNAVAILABLE}</Notice>
      </div>
    );
  }
  return (
    <div className="total-block">
      <p className="total" aria-live="polite">
        {seats ? (
          <>
            <span className="total-amount">{BOOK.total(nok(seats * pricePerSeatOre))}</span> {BOOK.inclVat}
          </>
        ) : null}
      </p>
      <p className="total-note">{BOOK.perSeat(nok(pricePerSeatOre))}</p>
    </div>
  );
}
