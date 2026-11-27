'use client';

// Cancel private sauna (FR-33, AD-9, AD-29, AD-31, UX-DR40): the confirming step of a Whole-sauna cancel and its
// result, at `/manage/[reference]/cancel`. Built like GiveUpSeats, with the remedy in place of the Seats.
//
// - The Booking is read with this browser's session from `GET /api/manage/{reference}`; a 404, and a Seat booking (the
//   API refuses it as a route of the other kind), are "This page is not available." (FR-20). Loading changes nothing.
//   After the 72-hour Cutoff the page shows the Cutoff text.
// - The question "What do you want back?" is a radio group in a fieldset with a legend, one tab stop with arrow keys
//   inside: "A refund" (paid back the way the Guest paid) or "A voucher" (for the full total, valid for one year).
//   Nothing is pre-selected. Once a remedy is chosen, the shared ConfirmingStep states what will happen: the Sauna and
//   the session, then for a refund the card refund and any new Voucher with its last valid date (`refund_split`,
//   computed by the API), for a voucher its value, last valid date and that no money is paid back. Nothing changes
//   until the Guest confirms "Cancel booking".
// - The idempotency key lives in the slot `draft:change:<reference>:cancel` (lib/draft.js), with the other steps'
//   rules: made when the step opens, reused on a reload, deleted on success, on every refusal except `503 try_again`
//   (and no answer at all), and when the Guest leaves the step.
// - A refusal reuses the move texts (`moveRefusal`) and keeps the choice. After `booking_changed` or `invalid_key` the
//   Booking is read again and the step opens fresh with a new key. After `cutoff_passed` the page shows the Cutoff
//   text. After `booking_cancelled` the "please try again" Notice shows and the Booking is read again, so the cancelled
//   state replaces the step.
// - A cancelled Booking (a reload of the result page) shows the Manage page's cancelled text in a Notice and no step.
// - On success the page shows the result: "Booking cancelled", that the refund or the Voucher code is in the email,
//   the email under "Sent by email:" (ChangeResult), then "Back to your booking". Focus moves to its h1. A Voucher code
//   reaches this page only inside the email body.
// Wording: Lisa, 2026-11-26 (EXPERIENCE.md "Cancel private sauna wording"). No clock is read here: dates and times
// come from the API (AD-4).
import { useEffect, useRef, useState } from 'react';
import ChangeResult from './ChangeResult';
import ConfirmingStep from './ConfirmingStep';
import GuestShell from './GuestShell';
import NotAvailable from './NotAvailable';
import Notice from './Notice';
import TextLink from './TextLink';
import Wordmark from './Wordmark';
import { ApiError, api } from '@/lib/api';
import { CANCEL_WHOLE, MANAGE, moveRefusal } from '@/lib/copy';
import { clockTime, longDate } from '@/lib/dates';
import { changeKey, dropChangeKey } from '@/lib/draft';
import { nok } from '@/lib/venue-format';

const ACTION = 'cancel';
const REMEDIES = ['refund', 'voucher'];

const when = (w) => `${longDate(w.date)}, ${clockTime(w.start)}–${clockTime(w.end)}`;

function RemedyPicker({ remedy, onChange, total }) {
  const hints = { refund: CANCEL_WHOLE.refundHint, voucher: CANCEL_WHOLE.voucherHint(nok(total)) };
  const labels = { refund: CANCEL_WHOLE.refund, voucher: CANCEL_WHOLE.voucher };
  return (
    <fieldset className="question" id="remedy">
      <legend className="q">{CANCEL_WHOLE.remedyQuestion}</legend>
      <div className="remedy-options">
        {REMEDIES.map((value) => (
          <label key={value} className={remedy === value ? 'remedy-option selected' : 'remedy-option'}>
            <input
              type="radio"
              name="remedy"
              id={`remedy-${value}`}
              value={value}
              checked={remedy === value}
              aria-describedby={`remedy-${value}-hint`}
              onChange={() => onChange(value)}
            />
            <span className="remedy-text">
              <span className="remedy-label">{labels[value]}</span>
              <span className="hint" id={`remedy-${value}-hint`}>
                {hints[value]}
              </span>
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export default function CancelPrivateSauna({ reference }) {
  const [load, setLoad] = useState({ status: 'loading', booking: null });
  const [reloadKey, setReloadKey] = useState(0);
  const [remedy, setRemedy] = useState(null);
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState(null); // {text, n}: a new `n` moves focus to the Notice
  const [cutoffAt, setCutoffAt] = useState(null);
  const [result, setResult] = useState(null);
  const sending = useRef(false);
  const heading = useRef(null);
  const resultHeading = useRef(null);

  const b = load.booking;
  const open = Boolean(b && b.status === 'active' && b.change_allowed && !cutoffAt);

  // Read the Booking (again after `booking_changed` or `invalid_key`). The step's key is made when it opens.
  useEffect(() => {
    const controller = new AbortController();
    api(`/api/manage/${encodeURIComponent(reference)}`, { signal: controller.signal })
      .then((booking) => {
        if (controller.signal.aborted) return;
        if (booking.kind !== 'whole') {
          // a Whole-sauna Change of a Seat booking: the API refuses it as a route of the other kind (AD-28)
          setLoad({ status: 'not_available', booking: null });
          return;
        }
        if (booking.status === 'active' && booking.change_allowed) changeKey(reference, ACTION);
        setLoad({ status: 'ok', booking });
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setLoad((prev) => ({
          status: err instanceof ApiError && err.status === 404 ? 'not_available' : 'failed',
          booking: prev.booking,
        }));
      });
    return () => controller.abort();
  }, [reference, reloadKey]);

  // Leaving the step deletes its key (a reload does not run this, so a reload reuses it).
  useEffect(() => () => dropChangeKey(reference, ACTION), [reference]);

  // A direct load (a reload) gets no focus move from FocusMover; the heading takes focus when nothing else has it.
  useEffect(() => {
    const el = document.activeElement;
    if (load.status !== 'loading' && heading.current && (!el || el === document.body)) heading.current.focus();
  }, [load.status]);

  useEffect(() => {
    if (result && resultHeading.current) resultHeading.current.focus();
  }, [result]);

  const ready = open && REMEDIES.includes(remedy);

  const confirm = async () => {
    if (sending.current || !ready) return;
    sending.current = true;
    setBusy(true);
    const key = changeKey(reference, ACTION);
    try {
      const body = await api(`/api/manage/${encodeURIComponent(reference)}/whole/cancel`, {
        method: 'POST',
        body: { remedy, version: b.version },
        idempotencyKey: key,
      });
      dropChangeKey(reference, ACTION);
      setRefusal(null);
      setResult(body);
    } catch (err) {
      const status = err instanceof ApiError ? err.status : 0;
      const code = err instanceof ApiError ? err.code : 'unavailable';
      const errFacts = err instanceof ApiError ? err.facts : {};
      if (status !== 0 && status !== 503) dropChangeKey(reference, ACTION); // no answer, or try_again: same key
      if (status === 404) {
        setLoad({ status: 'not_available', booking: null });
      } else {
        const r = moveRefusal(code, errFacts);
        if (r.kind === 'cutoff') {
          setCutoffAt(typeof errFacts.cutoff_at === 'string' ? errFacts.cutoff_at : b.cutoff_at);
          setRefusal(null);
        } else {
          if (r.kind === 'reload' || code === 'booking_cancelled') {
            // a fresh step: the Booking is read again and a new key is made when it opens
            setRemedy(null);
            setReloadKey((k) => k + 1);
          }
          setRefusal((prev) => ({ text: r.text, n: (prev?.n ?? 0) + 1 }));
        }
      }
    }
    sending.current = false;
    setBusy(false);
  };

  if (load.status === 'not_available') return <NotAvailable />;

  if (result) {
    const refunded = result.booking.cancel_remedy === 'refund';
    return (
      <GuestShell rail={<Wordmark />}>
        <title>{`${CANCEL_WHOLE.resultHeading} – Saunalöyly`}</title>
        <div className="col page-text">
          <h1 className="heading-xl heading-success" tabIndex={-1} ref={resultHeading}>
            {CANCEL_WHOLE.resultHeading}
          </h1>
          <p className="after-heading">{CANCEL_WHOLE.resultLine}</p>
          <p className="move-new-reference">{refunded ? CANCEL_WHOLE.refundInEmail : CANCEL_WHOLE.codeInEmail}</p>
          <ChangeResult emails={result.emails} />
          <p className="move-result-back">
            <TextLink href={`/manage/${encodeURIComponent(reference)}`}>{CANCEL_WHOLE.backToBooking}</TextLink>
          </p>
        </div>
      </GuestShell>
    );
  }

  const cutoffText = () => MANAGE.cutoffPassed(MANAGE.wholeHours);
  const shownCutoff = cutoffAt || (b && b.status === 'active' && !b.change_allowed ? b.cutoff_at : null);
  const cancelledAt = b && b.status === 'cancelled' && b.cancelled_at && b.cancel_remedy ? b.cancelled_at : null;

  let rows = [];
  const notes = [];
  if (ready) {
    rows = [
      { label: CANCEL_WHOLE.sauna, value: b.sauna?.name ?? '' },
      { label: CANCEL_WHOLE.session, value: when(b.window) },
    ];
    if (remedy === 'refund') {
      const split = b.refund_split || { card_ore: b.total_ore, voucher_ore: 0, voucher_last_valid_date: null };
      if (split.card_ore > 0) rows.push({ label: CANCEL_WHOLE.refundToCard, value: nok(split.card_ore) });
      if (split.voucher_ore > 0) {
        rows.push({ label: CANCEL_WHOLE.newVoucher, value: nok(split.voucher_ore) });
        if (split.voucher_last_valid_date) {
          rows.push({ label: CANCEL_WHOLE.validUntil, value: longDate(split.voucher_last_valid_date) });
        }
      }
    } else {
      rows.push({ label: CANCEL_WHOLE.voucherValue, value: nok(b.total_ore) });
      rows.push({ label: CANCEL_WHOLE.validUntil, value: longDate(b.voucher_last_valid_date) });
      notes.push(CANCEL_WHOLE.noMoney);
    }
    notes.push(CANCEL_WHOLE.nothingYet);
  }

  return (
    <GuestShell rail={<Wordmark />} mainClass="book">
      {load.status !== 'loading' && (
        <h1 className="heading-xl" tabIndex={-1} ref={heading}>
          {CANCEL_WHOLE.heading}
        </h1>
      )}
      <p className="back">
        <TextLink href={`/manage/${encodeURIComponent(reference)}`}>{CANCEL_WHOLE.back}</TextLink>
      </p>
      {refusal && (
        <div className="move-notice">
          <Notice focusKey={refusal.n}>{refusal.text}</Notice>
        </div>
      )}
      {load.status === 'failed' && <div className="move-notice"><Notice>{MANAGE.loadFailed}</Notice></div>}
      {shownCutoff && <div className="move-notice"><Notice>{cutoffText()}</Notice></div>}
      {cancelledAt && (
        <div className="move-notice">
          <Notice>
            {MANAGE.cancelledWhole(longDate(cancelledAt.slice(0, 10)), clockTime(cancelledAt), b.cancel_remedy)}
          </Notice>
        </div>
      )}
      {open && (
        <>
          <div className="move-seats">
            <RemedyPicker remedy={remedy} onChange={setRemedy} total={b.total_ore} />
          </div>
          {ready && (
            <ConfirmingStep
              heading={CANCEL_WHOLE.summaryHeading}
              rows={rows}
              confirmLabel={CANCEL_WHOLE.confirm}
              onConfirm={confirm}
              busy={busy}
            >
              {notes.map((text) => (
                <p className="move-note" key={text}>
                  {text}
                </p>
              ))}
            </ConfirmingStep>
          )}
        </>
      )}
    </GuestShell>
  );
}
