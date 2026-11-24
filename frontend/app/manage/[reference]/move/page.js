// Move seats (FR-26, AD-29): `/manage/[reference]/move`. The confirming step and its result are read and sent in the
// browser, with its session cookie, by the client component: only a session with a grant for the Booking gets it.
import MoveSeats from '@/components/MoveSeats';

export const metadata = { title: 'Move seats' };

export default async function MoveSeatsPage({ params }) {
  const { reference } = await params;
  return <MoveSeats reference={reference} />;
}
