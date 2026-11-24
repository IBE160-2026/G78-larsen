// Manage booking (FR-25, AD-28): `/manage/[reference]`. The Booking is read in the browser, with its session cookie,
// by the client component: only a session that opened the Manage link has a grant for it.
import ManageBooking from '@/components/ManageBooking';

export const metadata = { title: 'Manage booking' };

export default async function ManageBookingPage({ params }) {
  const { reference } = await params;
  return <ManageBooking reference={reference} />;
}
