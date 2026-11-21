// The Booking list (FR-16, UX-DR31). The guard shows nothing until `GET /api/admin/me` answers, and sends anyone not
// signed in to Sign-in (UX-DR30). The day's sessions come from the client component, which reads `?date` from the
// address (hence the Suspense boundary).
import { Suspense } from 'react';
import AdminBar from '@/components/AdminBar';
import AdminGuard from '@/components/AdminGuard';
import BookingList from '@/components/BookingList';
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
        <Suspense fallback={null}>
          <BookingList />
        </Suspense>
      </main>
    </AdminGuard>
  );
}
