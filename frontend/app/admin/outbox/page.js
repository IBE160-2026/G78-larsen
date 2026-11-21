// The Outbox (FR-17, UX-DR32). The guard shows nothing until `GET /api/admin/me` answers, and sends anyone not
// signed in to Sign-in (UX-DR30). The emails come from the client component.
import AdminBar from '@/components/AdminBar';
import AdminGuard from '@/components/AdminGuard';
import Outbox from '@/components/Outbox';
import { OUTBOX } from '@/lib/copy';

export const metadata = { title: 'Outbox' };

export default function OutboxPage() {
  return (
    <AdminGuard>
      <AdminBar current="outbox" />
      <main id="main" className="admin-main">
        <h1 className="heading-xl" tabIndex={-1}>
          {OUTBOX.heading}
        </h1>
        <Outbox />
      </main>
    </AdminGuard>
  );
}
