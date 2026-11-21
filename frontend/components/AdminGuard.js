'use client';

// The guard of every Administrator page except Sign-in (UX-DR30, UJ-3). It asks `GET /api/admin/me` when the page
// mounts and again on `pageshow` (a page restored by the browser's Back from its cache), and renders nothing until
// that answers 200. A 401 (anonymous, signed out, or a sign-in that has expired) replaces the page with Sign-in, with
// no other copy. It never creates a session (AD-8): only Sign-in and Book seats do. Any other failure shows the
// "please try again" Notice. The server checks the role on every Administrator request anyway (AD-10).
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { SIGN_IN_PATH } from './AdminBar';
import Notice from './Notice';
import { ApiError, api } from '@/lib/api';

export default function AdminGuard({ children }) {
  const router = useRouter();
  const [state, setState] = useState('checking'); // 'checking' | 'ok' | 'failed'

  useEffect(() => {
    let live = true;
    const check = async () => {
      try {
        await api('/api/admin/me');
        if (live) setState('ok');
      } catch (err) {
        if (!live) return;
        if (err instanceof ApiError && err.status === 401) {
          setState('checking');
          router.replace(SIGN_IN_PATH);
        } else {
          setState('failed');
        }
      }
    };
    const onPageShow = (event) => {
      if (event.persisted) {
        setState('checking');
        check();
      }
    };
    check();
    window.addEventListener('pageshow', onPageShow);
    return () => {
      live = false;
      window.removeEventListener('pageshow', onPageShow);
    };
  }, [router]);

  if (state === 'ok') return children;
  if (state === 'failed') {
    return (
      <main id="main" className="admin-main">
        <Notice />
      </main>
    );
  }
  return null;
}
