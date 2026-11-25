// Details of the Private sauna flow (FR-5, FR-29, UX-DR23, Story 5.2): the same page as the Seat flow's, with the draft
// `draft:whole`. Everything depends on the draft in the browser tab, so the page is the client component; it calls no
// API.
import Details from '@/components/Details';

export const metadata = { title: 'Your details' };

export default function PrivateSaunaDetailsPage() {
  return <Details flow="whole" />;
}
