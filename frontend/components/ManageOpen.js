'use client';

// Opening a Manage link (FR-25, AD-28, AD-19). The token travels only in the fragment `#t=<token>`, so it reaches no
// server log and no referrer. On arrival the fragment is read once (a ref set before the read, so React Strict Mode's
// second effect run does nothing), removed with `history.replaceState`, and sent in the body of
// `POST /api/manage/open`. The answer `{reference}` leads to `/manage/[reference]`, where FocusMover moves focus to the
// h1 once the Booking is shown. No fragment, and any 404 (an unknown, revoked or expired link), shows "This page is
// not available." (FR-20); any other failure shows the h1 and a Notice.
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import GuestShell from './GuestShell';
import NotAvailable from './NotAvailable';
import Notice from './Notice';
import Wordmark from './Wordmark';
import { ApiError, api } from '@/lib/api';
import { MANAGE } from '@/lib/copy';

const PREFIX = '#t=';

export default function ManageOpen() {
  const router = useRouter();
  const started = useRef(false);
  const [status, setStatus] = useState('opening');

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const hash = window.location.hash;
    const token = hash.startsWith(PREFIX) ? hash.slice(PREFIX.length) : '';
    window.history.replaceState(null, '', '/manage');
    if (!token) {
      setStatus('not_available');
      return;
    }
    api('/api/manage/open', { method: 'POST', body: { token } })
      .then(({ reference }) => router.replace(`/manage/${encodeURIComponent(reference)}`))
      .catch((err) => setStatus(err instanceof ApiError && err.status === 404 ? 'not_available' : 'failed'));
  }, [router]);

  if (status === 'not_available') return <NotAvailable />;
  return (
    <GuestShell rail={<Wordmark />}>
      <div className="col">
        {status === 'failed' && (
          <>
            <h1 className="heading-xl" tabIndex={-1}>
              {MANAGE.heading}
            </h1>
            <Notice>{MANAGE.loadFailed}</Notice>
          </>
        )}
      </div>
    </GuestShell>
  );
}
