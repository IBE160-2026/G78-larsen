// Private sauna (FR-29, FR-30, UX-DR41): a date, then the Saunas that can be booked whole with their free sessions.
// Everything comes from the browser's own `/api` calls in the client component (the calendar facts from
// `GET /api/windows`, the pairs from `GET /api/private-saunas`); the page opens a session only when the Guest continues
// to book (AD-8, Story 5.2).
import PrivateSauna from '@/components/PrivateSauna';

export const metadata = { title: 'Private sauna' };

export default function PrivateSaunaPage() {
  return <PrivateSauna />;
}
