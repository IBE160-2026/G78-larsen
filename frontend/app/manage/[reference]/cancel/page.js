// Cancel private sauna (FR-33, AD-29, AD-31): `/manage/[reference]/cancel`. The confirming step and its result are read
// and sent in the browser, with its session cookie, by the client component: only a session with a grant for the
// Booking gets it.
import CancelPrivateSauna from '@/components/CancelPrivateSauna';

export const metadata = { title: 'Cancel booking' };

export default async function CancelPrivateSaunaPage({ params }) {
  const { reference } = await params;
  return <CancelPrivateSauna reference={reference} />;
}
