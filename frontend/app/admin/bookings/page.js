// The Booking list (FR-16). Story 2.1 gives it the Administrator bar and the heading only; Story 2.2 adds the
// sessions of a chosen day. The guard shows nothing until `GET /api/admin/me` answers, and sends anyone not signed in
// to Sign-in (UX-DR30).
import AdminBar from '@/components/AdminBar';
import AdminGuard from '@/components/AdminGuard';
import { ADMIN } from '@/lib/copy';

export const metadata = { title: 'Booking list' };

export default function BookingListPage() {
  return (
    <AdminGuard>
      <AdminBar current="bookings" />
      <main id="main" className="admin-main">
        <h1 className="heading-xl" tabIndex={-1}>
          {ADMIN.bookingList}
        </h1>
      </main>
    </AdminGuard>
  );
}
