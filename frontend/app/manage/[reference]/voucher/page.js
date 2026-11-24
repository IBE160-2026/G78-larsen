// Give up seats for a voucher (FR-27, AD-29): `/manage/[reference]/voucher`. The confirming step and its result are
// read and sent in the browser, with its session cookie, by the client component: only a session with a grant for the
// Booking gets it.
import GiveUpSeats from '@/components/GiveUpSeats';

export const metadata = { title: 'Give up seats' };

export default async function GiveUpSeatsPage({ params }) {
  const { reference } = await params;
  return <GiveUpSeats reference={reference} />;
}
