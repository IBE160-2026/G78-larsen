// `/admin` is the Booking list's address family: it redirects there, and the Booking list's guard decides.
import { redirect } from 'next/navigation';

export default function AdminPage() {
  redirect('/admin/bookings');
}
