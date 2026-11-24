'use client';

// Confirmation (FR-8, UX-DR14/27, AD-12): "Booking confirmed" in --color-success, the Reference display, the reception
// sentence directly under it with no heading, the Booking summary with the stored total, the booking terms, a link to
// "Before you come", and the stored email as sent.
//
// The Booking and the email come from `GET /api/bookings/{reference}/confirmation`, which answers only the paying
// browser session; any other browser, no browser session and an unknown reference get "This page is not available."
// (FR-20 RB-4). A reload in the paying session shows the page again. Straight after Pay, Review has read it already,
// so the h1 is on the page at once (lib/confirmation.js). The Manage link (Story 4.1) appears only in the email as sent.
import { useEffect, useRef, useState } from 'react';
import BookingSummary from './BookingSummary';
import EmailAsSent from './EmailAsSent';
import GuestShell from './GuestShell';
import NotAvailable from './NotAvailable';
import Notice from './Notice';
import ReferenceDisplay from './ReferenceDisplay';
import { venueRows } from './Review';
import TextLink from './TextLink';
import Wordmark from './Wordmark';
import reception from '@/content/reception.json';
import terms from '@/content/terms-seats.json';
import { ApiError, api } from '@/lib/api';
import { heldConfirmation } from '@/lib/confirmation';
import { CONFIRMATION, SUMMARY, seatsWord } from '@/lib/copy';
import { clockTime, longDate } from '@/lib/dates';
import { nok } from '@/lib/venue-format';

export default function Confirmation({ reference, venue }) {
  // Straight after Pay, Review has already read it (lib/confirmation.js): the h1 is there from the first render.
  const [state, setState] = useState(() => {
    const held = heldConfirmation(reference);
    return held ? { status: 'ok', ...held } : { status: 'loading' };
  });
  const heading = useRef(null);
  const ready = state.status === 'ok';

  useEffect(() => {
    if (ready) return undefined;
    const controller = new AbortController();
    api(`/api/bookings/${encodeURIComponent(reference)}/confirmation`, { signal: controller.signal })
      .then((body) => {
        if (!controller.signal.aborted) setState({ status: 'ok', ...body });
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setState({ status: err instanceof ApiError && err.status === 404 ? 'not_available' : 'failed' });
      });
    return () => controller.abort();
  }, [reference, ready]);

  // The heading appears only once the read has answered, so another browser never sees it before "This page is not
  // available."; focus that FocusMover could not give it on navigation (no h1 yet) goes to it then.
  useEffect(() => {
    const el = document.activeElement;
    if (state.status !== 'loading' && heading.current && (!el || el === document.body)) heading.current.focus();
  }, [state.status]);

  if (state.status === 'not_available') return <NotAvailable />;

  const b = state.booking;
  return (
    <GuestShell rail={<Wordmark />}>
      <div className="col">
        {state.status !== 'loading' && (
          <h1 className="heading-xl heading-success" tabIndex={-1} ref={heading}>
            {CONFIRMATION.heading}
          </h1>
        )}
        {state.status === 'failed' && <Notice>{CONFIRMATION.loadFailed}</Notice>}
        {b && (
          <>
            <ReferenceDisplay reference={b.reference} />
            {reception.paragraphs.map((p) => (
              <p className="reception" key={p}>
                {p}
              </p>
            ))}
            <BookingSummary
              rows={[
                { label: SUMMARY.date, value: longDate(b.date) },
                { label: SUMMARY.session, value: `${clockTime(b.start)}–${clockTime(b.end)}` },
                { label: SUMMARY.seats, value: seatsWord(b.seats) },
                { label: SUMMARY.total, value: `${nok(b.total_ore)} incl. VAT` },
                { label: SUMMARY.email, value: b.email },
                ...venueRows(venue),
              ]}
            />
            <section className="terms-section" aria-labelledby="terms-heading">
              <h2 className="heading-md" id="terms-heading">
                Booking terms
              </h2>
              {terms.paragraphs.map((p) => (
                <p key={p}>{p}</p>
              ))}
            </section>
            <p className="before-link">
              <TextLink href="/#before-you-come">{CONFIRMATION.beforeYouCome}</TextLink>
            </p>
            {state.emails.map((email, i) => (
              <EmailAsSent key={i} index={i} email={email} />
            ))}
          </>
        )}
      </div>
    </GuestShell>
  );
}
