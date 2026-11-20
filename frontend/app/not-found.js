// Every unknown page (UX-DR29). Next.js's default 404 page is never shown.
import NotAvailable from '@/components/NotAvailable';

export default function NotFound() {
  return <NotAvailable />;
}
