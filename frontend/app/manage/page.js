// Manage link (FR-25, AD-28): `/manage#t=<token>`. The client component reads the token from the fragment once,
// removes it from the address bar, exchanges it for a grant on this browser's session and goes to the Booking.
import ManageOpen from '@/components/ManageOpen';

export const metadata = { title: 'Manage booking' };

export default function ManagePage() {
  return <ManageOpen />;
}
