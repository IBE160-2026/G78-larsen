// Confirmation (FR-8, UX-DR27): `/confirmation/[reference]`. Rendered per request (`connection()`); the Venue facts
// come from `GET /api/venue` through server-api.js (AD-16). The Booking and the email as sent are read in the browser,
// with its session cookie, by the client component: only the paying browser session gets them (AD-12).
import { connection } from 'next/server';
import Confirmation from '@/components/Confirmation';
import { getPublic } from '@/lib/server-api';
import { seatFlowVenue } from '@/lib/venue-format';

export const metadata = { title: 'Booking confirmed' };

export default async function ConfirmationPage({ params }) {
  await connection();
  const { reference } = await params;
  const result = await getPublic('/api/venue');
  return <Confirmation reference={reference} venue={seatFlowVenue(result)} />;
}
