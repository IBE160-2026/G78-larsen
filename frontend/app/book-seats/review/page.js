// Review (FR-5, FR-6, UX-DR24): the Booking summary, the booking terms and Pay. Rendered per request (`connection()`):
// the Venue facts (identity, contact, price per Seat) come from `GET /api/venue` through server-api.js (AD-16); the
// draft, the session's times and the payment are the client component's.
import { connection } from 'next/server';
import Review from '@/components/Review';
import { getPublic } from '@/lib/server-api';
import { seatFlowVenue } from '@/lib/venue-format';

export const metadata = { title: 'Review' };

export default async function ReviewPage() {
  await connection();
  const result = await getPublic('/api/venue');
  return <Review venue={seatFlowVenue(result)} />;
}
