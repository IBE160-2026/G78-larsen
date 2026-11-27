// Move private sauna (FR-33, AD-24, AD-29): `/manage/[reference]/move-sauna`. The confirming step and its result are
// read and sent in the browser, with its session cookie, by the client component: only a session with a grant for the
// Booking gets it.
import MovePrivateSauna from '@/components/MovePrivateSauna';

export const metadata = { title: 'Move private sauna' };

export default async function MovePrivateSaunaPage({ params }) {
  const { reference } = await params;
  return <MovePrivateSauna reference={reference} />;
}
