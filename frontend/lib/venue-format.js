// How Landing writes the Venue facts from `GET /api/venue` (AD-16). The values come from the API; only the
// wording is here. Spaces inside a figure are no-break spaces, so "1 h 30 min" never wraps.
const NBSP = ' ';

/** "10:00–22:00" from two "HH:MM" strings. */
export function openingHours(opening, closing) {
  return `${opening}–${closing}`;
}

/** "1 h 30 min", "2 h" or "45 min" from a Session length in minutes. */
export function sessionLength(minutes) {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  const parts = [];
  if (h) parts.push(`${h}${NBSP}h`);
  if (m || !h) parts.push(`${m}${NBSP}min`);
  return parts.join(NBSP);
}

/** "NOK 250" from 25000 øre; "NOK 250,50" when there are øre left over. */
export function nok(ore) {
  const kroner = Math.floor(ore / 100);
  const rest = ore % 100;
  return `NOK${NBSP}${kroner}${rest ? `,${String(rest).padStart(2, '0')}` : ''}`;
}

/** A Sauna card's size line: "Holds 7". */
export function holds(capacity) {
  return `Holds ${capacity}`;
}

/**
 * The Venue facts a Seat-flow page needs (identity, contact, price per Seat), or null. Never the Saunas: no Seat-flow
 * page carries a Sauna, not even in the data handed to its client component (FR-4).
 */
export function seatFlowVenue(result) {
  if (!result.ok) return null;
  const { name, address_lines: addressLines, phone, email, price_per_seat_ore: price } = result.data;
  return { name, address_lines: addressLines, phone, email, price_per_seat_ore: price };
}
