'use client';

// A page that fails to render shows the "please try again" Notice (UX-DR29). Next.js's default error page is
// never shown.
import TryAgain from '@/components/TryAgain';

export default function ErrorPage() {
  return <TryAgain />;
}
