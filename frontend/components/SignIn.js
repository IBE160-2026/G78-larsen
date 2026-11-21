'use client';

// Sign-in (FR-15, FR-19, UX-DR30, UX-DR33): the Administrator bar with the name only, then "Sign in", Email, Password
// and the "Sign in" button, in that order.
//
// - Opening the page calls `POST /api/session` once (AD-8): the sign-in needs a browser session to rotate. If that
//   session is already an Administrator's, the page goes to the Booking list.
// - Every refusal (wrong password, unknown email, too many attempts, an empty field) shows the one Error summary
//   "Wrong email or password" with no Field error (PW-5), so it never says which was wrong. The title then starts
//   with "Error: " (FocusMover).
// - `401 no_session` (the browser session expired or was never opened): open a new one and try once more.
// - No answer, a 5xx or 503: a Notice "Sign-in could not be completed, please try again."
// - Paste and password managers work: plain inputs with `autocomplete` username and current-password (WCAG 3.3.8).
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import AdminBar from './AdminBar';
import ErrorSummary from './ErrorSummary';
import Notice from './Notice';
import PrimaryButton from './PrimaryButton';
import { ApiError, api } from '@/lib/api';
import { SIGN_IN } from '@/lib/copy';

export const BOOKING_LIST_PATH = '/admin/bookings';

const openSession = () => api('/api/session', { method: 'POST', body: {} });

export default function SignIn() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [refused, setRefused] = useState(0); // a new value moves focus to the Error summary
  const [failed, setFailed] = useState(0); // a new value moves focus to the Notice
  const opened = useRef(false);
  const busy = useRef(false);

  useEffect(() => {
    if (opened.current) return;
    opened.current = true;
    openSession()
      .then((s) => {
        if (s && s.role === 'admin') router.replace(BOOKING_LIST_PATH);
      })
      .catch(() => {}); // the submit opens one again after `no_session`
  }, [router]);

  const send = () => api('/api/admin/sign-in', { method: 'POST', body: { email, password } });

  const onSubmit = async (event) => {
    event.preventDefault();
    if (busy.current) return;
    if (!email.trim() || !password) {
      setFailed(0);
      setRefused((n) => n + 1);
      return;
    }
    busy.current = true;
    try {
      try {
        await send();
      } catch (err) {
        if (!(err instanceof ApiError && err.code === 'no_session')) throw err;
        await openSession();
        await send();
      }
      router.push(BOOKING_LIST_PATH);
      return;
    } catch (err) {
      const code = err instanceof ApiError ? err.code : 'unavailable';
      if (code === 'sign_in_refused' || code === 'invalid_input') {
        setFailed(0);
        setRefused((n) => n + 1);
      } else {
        setRefused(0);
        setFailed((n) => n + 1);
      }
    }
    busy.current = false;
  };

  return (
    <>
      <AdminBar links={false} />
      <main id="main" className="admin-main">
        <div className="col">
          <h1 className="heading-xl" tabIndex={-1}>
            {SIGN_IN.heading}
          </h1>
          <form noValidate onSubmit={onSubmit} className="sign-in-form">
            {refused > 0 && <ErrorSummary errors={[{ key: 'refused', text: SIGN_IN.refused }]} focusKey={refused} />}
            {failed > 0 && <Notice focusKey={failed}>{SIGN_IN.failed}</Notice>}
            <div className="form-field">
              <label className="field-label" htmlFor="email">
                {SIGN_IN.email}
              </label>
              <input
                id="email"
                name="email"
                className="text-field"
                type="email"
                value={email}
                autoComplete="username"
                maxLength={254}
                spellCheck={false}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="form-field">
              <label className="field-label" htmlFor="password">
                {SIGN_IN.password}
              </label>
              <input
                id="password"
                name="password"
                className="text-field"
                type="password"
                value={password}
                autoComplete="current-password"
                maxLength={1024}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div className="form-actions">
              <PrimaryButton type="submit">{SIGN_IN.submit}</PrimaryButton>
            </div>
          </form>
        </div>
      </main>
    </>
  );
}
