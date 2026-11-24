'use client';

// Seat picker (FR-2, UX-DR18): a fieldset of ten radio cells, 1 to 10, one tab stop with arrow keys inside. No free
// number entry, so a number outside 1 to 10 cannot be sent. Nothing is pre-selected. The move step (Story 4.2) passes
// `max` (the Booking's Seats) and its own `legend`.
import FieldError from './FieldError';
import { BOOK } from '@/lib/copy';

export const SEAT_CHOICES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

export default function SeatPicker({ seats, onChange, error, max = 10, legend = BOOK.seatsQuestion }) {
  return (
    <fieldset className="question" id="seats" aria-describedby={error ? 'seats-error' : undefined}>
      <legend className="q">{legend}</legend>
      <FieldError id="seats-error">{error}</FieldError>
      <div className="seat-picker">
        {SEAT_CHOICES.filter((n) => n <= max).map((n) => (
          <label key={n} className="cell">
            <input
              type="radio"
              name="seats"
              id={`seats-${n}`}
              value={n}
              checked={seats === n}
              onChange={() => onChange(n)}
            />
            <span>{n}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
