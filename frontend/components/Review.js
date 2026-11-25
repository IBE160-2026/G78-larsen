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
// - The Voucher field (FR-28, Story 4.4) sits above the booking terms in the same column, always visible: "Voucher
//   code" with the Text link "Apply voucher" beside it (Enter in the field applies too). The typed code is kept in the
//   draft (`voucher_code`); a successful `POST /api/vouchers/quote` keeps the parts in page state only, adds the
//   "Voucher" and "To pay by card" rows after Total and makes Pay "Pay NOK {card}", or "Book with voucher" with no
//   payment note when the Voucher covers the total. Editing the field removes the applied Voucher until it is applied
//   again. `voucher_invalid` (on apply or at Pay) is one Field error and Error summary entry for every cause, the input
//   kept; a quote that cannot be checked is a Field error only. A stored code is quoted again when Review opens and
//   after a nearest Session is chosen. Pay sends only an applied code with its Voucher part.
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import BookingSummary from './BookingSummary';
import ErrorSummary from './ErrorSummary';
import FieldError from './FieldError';
import GuestShell from './GuestShell';
import NearestSessions from './NearestSessions';
import Notice from './Notice';
import PrimaryButton from './PrimaryButton';
import TermsCheckbox from './TermsCheckbox';
import TextLink from './TextLink';
import Wordmark from './Wordmark';
import terms from '@/content/terms-seats.json';
import { ApiError, api } from '@/lib/api';
import { holdConfirmation } from '@/lib/confirmation';
import { REVIEW, SIMULATED_PAYMENT, SUMMARY, VOUCHER_FIELD, reviewRefusal, seatsWord } from '@/lib/copy';
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
  // The Voucher field: the text as typed, the applied Voucher ({code, voucher_part_ore, card_part_ore}) and the
  // field's error ('invalid' or 'failed'). `quoteSeq` drops the answer of a quote the Guest has typed past.
  const [voucherInput, setVoucherInput] = useState('');
  const [applied, setApplied] = useState(null);
  const [voucherError, setVoucherError] = useState(null);
  const quoteSeq = useRef(0);
  const quoting = useRef(false);
  const requote = useRef(false);

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
    const code = typeof stored.voucher_code === 'string' ? stored.voucher_code : '';
    setVoucherInput(code);
    requote.current = code.trim() !== '';
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

  /** Quote `code` for the draft's Window and Seats; on success it is the applied Voucher. */
  const quoteVoucher = async (code, d, moveFocus) => {
    const seq = ++quoteSeq.current;
    quoting.current = true;
    setApplied(null);
    setVoucherError(null);
    let error = null;
    let parts = null;
    try {
      parts = await api('/api/vouchers/quote', {
        method: 'POST',
        body: { code, kind: 'seats', window_id: d.window_id, seats: d.seats },
      });
    } catch (err) {
      const c = err instanceof ApiError ? err.code : 'unavailable';
      if (c === 'no_session') await api('/api/session', { method: 'POST', body: {} }).catch(() => {});
      error = c === 'voucher_invalid' ? 'invalid' : 'failed';
    }
    if (seq !== quoteSeq.current) return; // the field changed meanwhile
    quoting.current = false;
    if (parts) {
      setApplied({ code, voucher_part_ore: parts.voucher_part_ore, card_part_ore: parts.card_part_ore });
      return;
    }
    setVoucherError(error);
    if (error === 'invalid' && moveFocus) setFocusKey((k) => k + 1);
  };

  // A code kept in the draft is quoted again once the session is known: when Review opens, and after a nearest
  // Session is chosen (UX-DR26).
  useEffect(() => {
    if (!draft || !session || !requote.current) return;
    requote.current = false;
    if (voucherInput.trim() !== '') quoteVoucher(voucherInput, draft, false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draft, session]);

  const applyVoucher = () => {
    if (!draft || busy.current) return;
    quoteVoucher(voucherInput, draft, true);
  };

  const editVoucher = (value) => {
    quoteSeq.current += 1; // an answer still on its way no longer applies
    quoting.current = false;
    setVoucherInput(value);
    setApplied(null);
    setVoucherError(null);
    writeDraft({ voucher_code: value });
  };

  const pay = async () => {
    if (busy.current || quoting.current) return; // no second press while paying, and no Pay while a quote is out
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
        body: {
          window_id: draft.window_id,
          seats: draft.seats,
          name: draft.name,
          email: draft.email,
          ...(applied ? { voucher_code: applied.code, voucher_part_ore: applied.voucher_part_ore } : {}),
        },
        idempotencyKey: draft.key,
      });
      const reference = body.booking.reference;
      replaceDraft({ reference }); // Back can never reach a page that pays again
      // Read the Confirmation before navigating, so its h1 is there at once and takes focus (lib/confirmation.js).
      // If the read fails, Confirmation reads it itself, as on a reload.
      await api(`/api/bookings/${encodeURIComponent(reference)}/confirmation`)
        .then((conf) => holdConfirmation(reference, conf))
        .catch(() => {});
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
      if (r.kind === 'voucher') {
        // the Voucher cannot be used: the field says so, the input stays, and Pay is for the whole total again
        setApplied(null);
        setVoucherError('invalid');
        setFocusKey((k) => k + 1);
        busy.current = false;
        setPaying(false);
        return;
      }
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
    quoteSeq.current += 1; // the Voucher is quoted again for the new session
    quoting.current = false;
    setApplied(null);
    setVoucherError(null);
    requote.current = true;
    setHeadingKey((k) => k + 1);
  };

  // Book seats after `invalid_key`: a new draft, so Review will make a new key (AD-9); the name and email stay.
  const startNewDraft = () => {
    replaceDraft({ name: draft?.name, email: draft?.email });
  };

  const errors = [
    ...(voucherError === 'invalid' ? [{ key: 'voucher-code', text: VOUCHER_FIELD.invalid, href: '#voucher-code' }] : []),
    ...(showErrors && !accepted ? [{ key: 'terms', text: REVIEW.acceptTerms, href: '#terms' }] : []),
    ...(refusal?.kind === 'failed' ? [{ key: 'payment', text: refusal.text }] : []),
  ];
  const price = venue?.price_per_seat_ore;
  const amount = draft && Number.isInteger(price) ? nok(draft.seats * price) : null;
  const payGone = refusal?.kind === 'closed' || refusal?.kind === 'paid';
  const cardPart = applied ? applied.card_part_ore : null;
  const payLabel = !applied ? REVIEW.pay(amount) : cardPart > 0 ? REVIEW.pay(nok(cardPart)) : REVIEW.bookWithVoucher;
  const cardPaid = !applied || cardPart > 0; // the payment note only where a card payment is made
  const voucherFieldError =
    voucherError === 'invalid' ? VOUCHER_FIELD.invalid : voucherError === 'failed' ? VOUCHER_FIELD.failed : null;

  const rows = draft
    ? [
        { label: SUMMARY.date, value: longDate(draft.date) },
        { label: SUMMARY.session, value: session ? `${clockTime(session.start)}–${clockTime(session.end)}` : '' },
        { label: SUMMARY.seats, value: seatsWord(draft.seats) },
        ...(amount ? [{ label: SUMMARY.total, value: `${amount} incl. VAT` }] : []),
        ...(applied ? [{ label: SUMMARY.voucher, value: SUMMARY.voucherPart(nok(applied.voucher_part_ore)) }] : []),
        ...(applied && cardPart > 0 ? [{ label: SUMMARY.toPayByCard, value: nok(cardPart) }] : []),
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
          <ErrorSummary errors={errors} focusKey={focusKey} onChoose={(key) => document.getElementById(key)?.focus()} />
        )}
        {notice}
        {loadFailed && <Notice>{REVIEW.loadFailed}</Notice>}
        {draft && session && (
          <div className="review-cols">
            <BookingSummary rows={rows} />
            <div>
              <div className="voucher-field">
                <label className="field-label" htmlFor="voucher-code">
                  {VOUCHER_FIELD.label}
                </label>
                <div className="voucher-row">
                  <input
                    id="voucher-code"
                    className="text-field"
                    type="text"
                    value={voucherInput}
                    autoComplete="off"
                    autoCapitalize="characters"
                    spellCheck={false}
                    onChange={(e) => editVoucher(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        applyVoucher();
                      }
                    }}
                    aria-invalid={voucherFieldError ? 'true' : undefined}
                    aria-describedby={voucherFieldError ? 'voucher-code-error' : undefined}
                  />
                  <button type="button" className="text-link text-button" onClick={applyVoucher}>
                    {VOUCHER_FIELD.apply}
                  </button>
                </div>
                <FieldError id="voucher-code-error">{voucherFieldError}</FieldError>
              </div>
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
                      {paying ? REVIEW.processing : payLabel}
                    </PrimaryButton>
                    {cardPaid && <p className="pay-note">{SIMULATED_PAYMENT}</p>}
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
