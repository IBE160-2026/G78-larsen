'use client';

// The Administrator bar (UX-DR3, UX-DR30; DESIGN.md, Components): full width in --color-bar, the name on the left.
// On Sign-in it shows the name only (`links={false}`); on every other Administrator page it holds Booking list,
// Outbox and Sign out, with `current` marking the page shown (aria-current).
//
// Sign out (FR-15) calls `POST /api/admin/sign-out` and replaces the page with Sign-in, so neither the page nor the
// browser's Back reaches an Administrator page with the old sign-in. A 401 means it is already over, so it also goes
// to Sign-in; any other failure keeps the page and shows a Notice under the bar.
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';
import Notice from './Notice';
import { ApiError, api } from '@/lib/api';
import { ADMIN } from '@/lib/copy';

export const SIGN_IN_PATH = '/admin/sign-in';

const LINKS = [
  { key: 'bookings', href: '/admin/bookings', text: ADMIN.bookingList },
  { key: 'outbox', href: '/admin/outbox', text: ADMIN.outbox },
];

export default function AdminBar({ links = true, current }) {
  const router = useRouter();
  const busy = useRef(false);
  const [failed, setFailed] = useState(0);

  const signOut = async () => {
    if (busy.current) return;
    busy.current = true;
    try {
      await api('/api/admin/sign-out', { method: 'POST' });
      router.replace(SIGN_IN_PATH);
      return;
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.replace(SIGN_IN_PATH);
        return;
      }
      setFailed((n) => n + 1);
    }
    busy.current = false;
  };

  return (
    <>
      <header className="admin-bar">
        <span className="admin-bar-name">{ADMIN.name}</span>
        {links && (
          <nav aria-label={ADMIN.nav}>
            <ul className="admin-bar-links">
              {LINKS.map((l) => (
                <li key={l.key}>
                  <Link href={l.href} aria-current={current === l.key ? 'page' : undefined}>
                    {l.text}
                  </Link>
                </li>
              ))}
              <li>
                <button type="button" className="link-button" onClick={signOut}>
                  {ADMIN.signOut}
                </button>
              </li>
            </ul>
          </nav>
        )}
      </header>
      {failed > 0 && (
        <div className="admin-notice">
          <Notice focusKey={failed}>{ADMIN.signOutFailed}</Notice>
        </div>
      )}
    </>
  );
}
