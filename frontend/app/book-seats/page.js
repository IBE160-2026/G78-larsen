// Book seats (FR-2, FR-3, FR-4): a date, a number of seats and a session, with the total. Rendered per request
// (`connection()`), so it is dynamic. The price per Seat comes from `GET /api/venue` through server-api.js; if the
// read fails, the rail shows the "please try again" Notice instead of the price lines and Continue still works.
// Everything that depends on the Guest's choices (Windows, Seats left, the session cookie, the draft) happens in
// the client component.
import { connection } from 'next/server';
import BookSeats from '@/components/BookSeats';
import { getPublic } from '@/lib/server-api';

export const metadata = { title: 'Book seats' };

export default async function BookSeatsPage() {
  await connection();
  const result = await getPublic('/api/venue');
  const price = result.ok && Number.isInteger(result.data.price_per_seat_ore) ? result.data.price_per_seat_ore : null;
  return <BookSeats pricePerSeatOre={price} />;
}
