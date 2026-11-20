// Details (FR-5, UX-DR23): the Guest's name and email. Everything depends on the Booking draft in the browser tab, so
// the page is the client component; it calls no API.
import Details from '@/components/Details';

export const metadata = { title: 'Your details' };

export default function DetailsPage() {
  return <Details />;
}
