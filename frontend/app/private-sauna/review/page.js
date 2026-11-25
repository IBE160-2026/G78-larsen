// Review of the Private sauna flow (FR-5, FR-6, FR-29, UX-DR24, Story 5.2): the same page as the Seat flow's, with the
// draft `draft:whole`. Rendered per request (`connection()`): the Venue facts (identity, contact) come from
// `GET /api/venue` through server-api.js (AD-16); the Sauna, its price and the session are read by the client
// component from `GET /api/private-saunas`, and the payment is the client component's.
import { connection } from 'next/server';
import Review from '@/components/Review';
import { getPublic } from '@/lib/server-api';
import { seatFlowVenue } from '@/lib/venue-format';

export const metadata = { title: 'Review' };

export default async function PrivateSaunaReviewPage() {
  await connection();
  const result = await getPublic('/api/venue');
  return <Review venue={seatFlowVenue(result)} flow="whole" />;
}
