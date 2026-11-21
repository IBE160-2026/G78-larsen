'use client';

// Review (FR-5, FR-6, FR-7, FR-11, FR-12, UX-DR5/10/13/14/24/25/26/33): "Review" and Back, then two columns down to
// 1200 px: the Booking summary (Date, Session, Seats, Total, Name, Email, Venue, Contact) on the left; on the right
// "Booking terms" with the shared statements (`content/terms-seats.json`), the Terms and Privacy notice links, the
// unticked Terms checkbox and "Pay NOK 500" with the payment note beside it.
//
// - The draft is read only in effects. After a payment (a `{reference}`-only draft) the page replaces itself with
//   Confirmation; without a session it goes to Book seats, without a name or email to Details (no error).
// - The idempotency key is made when the Guest first reaches Review and kept in the draft for every retry (AD-9).
// - The session's start and end are read from the Window listing of the draft's date; the total before payment is
//   the number of Seats times the price per Seat, as on Book seats. Confirmation shows the stored total.
// - Pay without the checkbox gives an Error summary and a Field error and charges nothing. While paying, Pay says
//   "Processing", keeps focus and takes no second press. On success the draft becomes `{reference}` and the page
//   replaces itself with Confirmation.
// - A refusal (Story 1.6, UX-DR25) keeps the Guest here with the name, email, draft and key; its message comes from
//   `reviewRefusal` in `lib/copy.js`. `no_seat_free`, `deadline_passed` and `outside_horizon` show a Notice under Back
//   with up to three Nearest sessions and remove Pay, the payment note and the checkbox; choosing one updates the
//   draft's date and session, reloads Review with them back (checkbox unticked) and moves focus to the heading. A
//   failed payment shows an Error summary with Pay kept. `invalid_key` shows a Notice with a Book seats link that
//   starts a new draft (keeping the name and email) and removes Pay. Anything else (`payment_pending`, `try_again`,
//   no answer) shows "please try again" with Pay kept; after `401 no_session` a new session is opened first. Every
//   refusal Notice takes focus. The same key is used for every retry (AD-9).
// - Nearest sessions are the draft date's other Sessions with room for the Seats, the three nearest in time to the
//   refused one, in time order; when the date has none, the listing's `nearest` (FR-3). Frontend only.
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import BookingSummary from './BookingSummary';
import ErrorSummary from './ErrorSummary';
import GuestShell from './GuestShell';
import NearestSessions from './NearestSessions';
import Notice from './Notice';
import PrimaryButton from './PrimaryButton';
import TermsCheckbox from './TermsCheckbox';
import TextLink from './TextLink';
import Wordmark from './Wordmark';
import terms from '@/content/terms-seats.json';
import { ApiError, api } from '@/lib/api';
import { REVIEW, SIMULATED_PAYMENT, SUMMARY, reviewRefusal, seatsWord } from '@/lib/copy';
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

/**
 * Up to three Sessions with room for `draft.seats`, never the refused one: the draft date's three nearest in time to
 * the refused Session, in time order; when the date has none, the listing's `nearest`. Each carries its `date`.
 * Never throws: a failed read gives none.
 */
async function nearestSessions(draft, refusedStart) {
  try {
    const query = `date=${encodeURIComponent(draft.date)}&seats=${encodeURIComponent(String(draft.seats))}`;
    const body = await api(`/api/windows?${query}`);
    const at = refusedStart ? Date.parse(refusedStart) : null;
    const same = (body.windows || [])
      .filter((w) => w.id !== draft.window_id && w.seats_left >= draft.seats)
      .map((w) => ({ ...w, date: draft.date }));
    if (same.length > 0) {
      const distance = (w) => Math.abs(Date.parse(w.start) - at);
      const near = at == null ? same : [...same].sort((a, b) => distance(a) - distance(b));
      return near.slice(0, 3).sort((a, b) => Date.parse(a.start) - Date.parse(b.start));
    }
    return (body.nearest || []).filter((w) => w.id !== draft.window_id).slice(0, 3);
  } catch {
    return [];
  }
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
  // the last refusal: {kind, text, nearest, n}; a new `n` moves focus to its Notice
  const [refusal, setRefusal] = useState(null);
  const [headingKey, setHeadingKey] = useState(0);
  const busy = useRef(false);
  const heading = useRef(null);

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

  const draftDate = draft?.date;
  const draftWindow = draft?.window_id;
  useEffect(() => {
    if (!draftDate) return undefined;
    const controller = new AbortController();
    api(`/api/windows?date=${encodeURIComponent(draftDate)}`, { signal: controller.signal })
      .then((body) => {
        if (controller.signal.aborted) return;
        const w = (body.windows || []).find((x) => x.id === draftWindow);
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
  }, [draftDate, draftWindow, router]);

  // After a nearest Session is chosen, focus moves to the Review heading (UX-DR13).
  useEffect(() => {
    if (headingKey > 0 && heading.current) heading.current.focus();
  }, [headingKey]);

  const pay = async () => {
    if (busy.current) return; // no second press while paying
    setRefusal(null);
    if (!accepted) {
      setShowErrors(true);
      setFocusKey((k) => k + 1);
      return;
    }
    busy.current = true;
    setPaying(true);
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
      const code = err instanceof ApiError ? err.code : 'unavailable';
      const facts = err instanceof ApiError ? err.facts : {};
      if (code === 'no_session') {
        // a new browser session; the draft and its key stay for the retry (UX-DR26)
        await api('/api/session', { method: 'POST', body: {} }).catch(() => {});
      }
      const r = reviewRefusal(code, facts);
      const nearest = r.kind === 'closed' ? await nearestSessions(draft, session?.start) : [];
      setRefusal((prev) => ({ ...r, nearest, n: (prev?.n ?? 0) + 1 }));
      if (r.kind === 'failed') setFocusKey((k) => k + 1);
    }
    busy.current = false;
    setPaying(false);
  };

  const chooseNearest = (w) => {
    writeDraft({ date: w.date, window_id: w.id });
    setDraft((d) => ({ ...d, date: w.date, window_id: w.id }));
    setSession(null);
    setLoadFailed(false);
    setRefusal(null);
    setAccepted(false);
    setShowErrors(false);
    setHeadingKey((k) => k + 1);
  };

  // Book seats after `invalid_key`: a new draft, so Review will make a new key (AD-9); the name and email stay.
  const startNewDraft = () => {
    replaceDraft({ name: draft?.name, email: draft?.email });
  };

  const errors = [
    ...(showErrors && !accepted ? [{ key: 'terms', text: REVIEW.acceptTerms, href: '#terms' }] : []),
    ...(refusal?.kind === 'failed' ? [{ key: 'payment', text: refusal.text }] : []),
  ];
  const price = venue?.price_per_seat_ore;
  const amount = draft && Number.isInteger(price) ? nok(draft.seats * price) : null;
  const payGone = refusal?.kind === 'closed' || refusal?.kind === 'paid';

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

  let notice = null;
  if (refusal?.kind === 'closed') {
    notice = (
      <Notice block focusKey={refusal.n}>
        <p>{refusal.text}</p>
        {refusal.nearest.length > 0 ? (
          <>
            <p className="notice-next">{REVIEW.nearest}</p>
            <NearestSessions sessions={refusal.nearest} onChoose={chooseNearest} />
          </>
        ) : (
          <p className="notice-next">
            <TextLink href="/book-seats">{REVIEW.bookSeats}</TextLink>
          </p>
        )}
      </Notice>
    );
  } else if (refusal?.kind === 'paid') {
    notice = (
      <Notice block focusKey={refusal.n}>
        <p>{refusal.text}</p>
        <p className="notice-next">
          <TextLink href="/book-seats" onClick={startNewDraft}>
            {REVIEW.bookSeats}
          </TextLink>
        </p>
      </Notice>
    );
  } else if (refusal?.kind === 'retry') {
    notice = <Notice focusKey={refusal.n}>{refusal.text}</Notice>;
  }

  return (
    <GuestShell rail={<Wordmark />}>
      <div className="review">
        <h1 className="heading-xl" tabIndex={-1} ref={heading}>
          {REVIEW.heading}
        </h1>
        <p className="back">
          <TextLink href="/book-seats/details">{REVIEW.back}</TextLink>
        </p>
        {errors.length > 0 && (
          <ErrorSummary errors={errors} focusKey={focusKey} onChoose={() => document.getElementById('terms')?.focus()} />
        )}
        {notice}
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
              {payGone ? null : amount ? (
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
