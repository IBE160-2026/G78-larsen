'use client';

// The Outbox (FR-17, FR-21, UX-DR32): every simulated email, newest first, one entry per email and always open.
//
// - Each entry is Email as sent with the subject as its heading and "Sent dd.mm.yyyy HH:MM" (Venue time, as the API
//   writes it) and "To {recipient}" in `label` above the body.
// - A recipient or body masked for retention arrives as '' and shows as "To Anonymised" and "Removed after 12
//   months.", never as the original.
// - Stored text is rendered as React text, never as HTML (IV-5).
// - A 401 goes to Sign-in; any other failure shows the "please try again" Notice. No emails: "No emails".
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { SIGN_IN_PATH } from './AdminBar';
import EmailAsSent from './EmailAsSent';
import Notice from './Notice';
import { ApiError, api } from '@/lib/api';
import { OUTBOX } from '@/lib/copy';
import { dottedTime } from '@/lib/dates';

export const OUTBOX_PATH = '/admin/outbox';

export default function Outbox() {
  const router = useRouter();
  const [result, setResult] = useState({ status: 'loading', emails: null });

  useEffect(() => {
    let live = true;
    api('/api/admin/outbox')
      .then((data) => {
        if (live) setResult({ status: 'ok', emails: data.emails });
      })
      .catch((err) => {
        if (!live) return;
        if (err instanceof ApiError && err.status === 401) {
          router.replace(SIGN_IN_PATH);
          return;
        }
        setResult({ status: 'failed', emails: null });
      });
    return () => {
      live = false;
    };
  }, [router]);

  if (result.status === 'failed') return <Notice>{OUTBOX.failed}</Notice>;
  if (!result.emails) return null;
  if (result.emails.length === 0) return <p className="outbox-none">{OUTBOX.noEmails}</p>;
  return result.emails.map((e) => (
    <EmailAsSent
      key={e.id}
      id={`outbox-email-${e.id}`}
      className="outbox-entry"
      heading={e.subject}
      lines={[OUTBOX.sent(dottedTime(e.created_at)), OUTBOX.to(e.recipient || OUTBOX.anonymised)]}
      email={{ body: e.body || OUTBOX.removed }}
    />
  ));
}
