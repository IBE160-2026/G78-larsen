'use client';

// Review (FR-5, FR-6, UX-DR5/10/14/24/26/33): "Review" and Back, then two columns down to 1200 px: the Booking summary
// (Date, Session, Seats, Total, Name, Email, Venue, Contact) on the left; on the right "Booking terms" with the shared
// statements (`content/terms-seats.json`), the Terms and Privacy notice links, the unticked Terms checkbox and
// "Pay NOK 500" with the payment note beside it.
//
// - The draft is read only in effects. After a payment (a `{reference}`-only draft) the page replaces itself with
//   Confirmation; without a session it goes to Book seats, without a name or email to Details (no error).
// - The idempotency key is made when the Guest first reaches Review and kept in the draft for every retry (AD-9).
// - The session's start and end are read from the Window listing of the draft's date; the total before payment is
//   the number of Seats times the price per Seat, as on Book seats. Confirmation shows the stored total.
// - Pay without the checkbox gives an Error summary and a Field error and charges nothing. While paying, Pay says
//   "Processing", keeps focus and takes no second press. On success the draft becomes `{reference}` and the page
//   replaces itself with Confirmation. Until Story 1.6, every refusal shows the "please try again" Notice with Pay
//   kept; after `401 no_session` a new session is opened first, and the draft and its key are kept.
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import BookingSummary from './BookingSummary';
import ErrorSummary from './ErrorSummary';
import GuestShell from './GuestShell';
import Notice from './Notice';
import PrimaryButton from './PrimaryButton';
import TermsCheckbox from './TermsCheckbox';
import TextLink from './TextLink';
import Wordmark from './Wordmark';
import terms from '@/content/terms-seats.json';
import { ApiError, api } from '@/lib/api';
import { REVIEW, SIMULATED_PAYMENT, SUMMARY, seatsWord } from '@/lib/copy';
import { clockTime, longDate } from '@/lib/dates';
import { newKey, paidReference, readDraft, replaceDraft, writeDraft } from '@/lib/draft';
import { nok } from '@/lib/venue-format';

/** The Venue and Contact rows of a Booking summary, from the Venue facts (AD-16); none when they are not known. */
export function venueRows(venue) {
  if (!venue) return [];
  return [
    { label: SUMMARY.venue, value: [venue.name, venue.address_lines.join(', ')] },
    { label: SUMMARY.contact, value: [venue.phone, venue.email] },
  ];
}

export default function Review({ venue }) {
  const router = useRouter();
  const [draft, setDraft] = useState(null);
  const [session, setSession] = useState(null); // the Window: {start, end}
  const [loadFailed, setLoadFailed] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [showErrors, setShowErrors] = useState(false);
  const [focusKey, setFocusKey] = useState(0);
  const [paying, setPaying] = useState(false);
  const [refused, setRefused] = useState(false);
  const busy = useRef(false);

  useEffect(() => {
    const stored = readDraft();
    const paid = paidReference(stored);
    if (paid) {
      router.replace(`/confirmation/${paid}`);
      return;
    }
    if (!Number.isInteger(stored.window_id) || !stored.date || !stored.seats) {
      router.replace('/book-seats');
      return;
    }
    if (!stored.name || !stored.email) {
      router.replace('/book-seats/details');
      return;
    }
    const key = typeof stored.key === 'string' && stored.key ? stored.key : newKey();
    if (key !== stored.key) writeDraft({ key });
    setDraft({ ...stored, key });
  }, [router]);

  useEffect(() => {
    if (!draft) return undefined;
    const controller = new AbortController();
    api(`/api/windows?date=${encodeURIComponent(draft.date)}`, { signal: controller.signal })
      .then((body) => {
        if (controller.signal.aborted) return;
        const w = (body.windows || []).find((x) => x.id === draft.window_id);
        if (!w) {
          router.replace('/book-seats'); // the session is no longer offered: choose again
          return;
        }
        setSession({ start: w.start, end: w.end });
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && err.code === 'outside_horizon') router.replace('/book-seats');
        else setLoadFailed(true);
      });
    return () => controller.abort();
  }, [draft, router]);

  const pay = async () => {
    if (busy.current) return; // no second press while paying
    if (!accepted) {
      setShowErrors(true);
      setFocusKey((k) => k + 1);
      return;
    }
    busy.current = true;
    setPaying(true);
    setRefused(false);
    try {
      const body = await api('/api/bookings', {
        method: 'POST',
        body: { window_id: draft.window_id, seats: draft.seats, name: draft.name, email: draft.email },
        idempotencyKey: draft.key,
      });
      const reference = body.booking.reference;
      replaceDraft({ reference }); // Back can never reach a page that pays again
      router.replace(`/confirmation/${reference}`);
      return;
    } catch (err) {
      if (err instanceof ApiError && err.code === 'no_session') {
        // a new browser session; the draft and its key stay for the retry (UX-DR26)
        await api('/api/session', { method: 'POST', body: {} }).catch(() => {});
      }
      setRefused(true);
    }
    busy.current = false;
    setPaying(false);
  };

  const errors = showErrors && !accepted ? [{ key: 'terms', text: REVIEW.acceptTerms, href: '#terms' }] : [];
  const price = venue?.price_per_seat_ore;
  const amount = draft && Number.isInteger(price) ? nok(draft.seats * price) : null;

  const rows = draft
    ? [
        { label: SUMMARY.date, value: longDate(draft.date) },
        { label: SUMMARY.session, value: session ? `${clockTime(session.start)}–${clockTime(session.end)}` : '' },
        { label: SUMMARY.seats, value: seatsWord(draft.seats) },
        ...(amount ? [{ label: SUMMARY.total, value: `${amount} incl. VAT` }] : []),
        { label: SUMMARY.name, value: draft.name },
        { label: SUMMARY.email, value: draft.email },
        ...venueRows(venue),
      ]
    : [];

  return (
    <GuestShell rail={<Wordmark />}>
      <div className="review">
        <h1 className="heading-xl" tabIndex={-1}>
          {REVIEW.heading}
        </h1>
        <p className="back">
          <TextLink href="/book-seats/details">{REVIEW.back}</TextLink>
        </p>
        {errors.length > 0 && (
          <ErrorSummary errors={errors} focusKey={focusKey} onChoose={() => document.getElementById('terms')?.focus()} />
        )}
        {refused && <Notice>{REVIEW.tryAgain}</Notice>}
        {loadFailed && <Notice>{REVIEW.loadFailed}</Notice>}
        {draft && session && (
          <div className="review-cols">
            <BookingSummary rows={rows} />
            <div>
              <section className="terms-section" aria-labelledby="terms-heading">
                <h2 className="heading-md" id="terms-heading">
                  {REVIEW.termsHeading}
                </h2>
                {terms.paragraphs.map((p) => (
                  <p key={p}>{p}</p>
                ))}
                <p className="terms-links">
                  <TextLink href="/terms">Terms</TextLink>
                  <TextLink href="/privacy">Privacy notice</TextLink>
                </p>
              </section>
              {amount ? (
                <>
                  <TermsCheckbox
                    checked={accepted}
                    onChange={setAccepted}
                    error={showErrors && !accepted ? REVIEW.acceptTerms : null}
                  />
                  <div className="pay-row">
                    <PrimaryButton onClick={pay} aria-busy={paying ? 'true' : undefined}>
                      {paying ? REVIEW.processing : REVIEW.pay(amount)}
                    </PrimaryButton>
                    <p className="pay-note">{SIMULATED_PAYMENT}</p>
                  </div>
                </>
              ) : (
                <Notice>{REVIEW.loadFailed}</Notice>
              )}
            </div>
          </div>
        )}
      </div>
    </GuestShell>
  );
}
