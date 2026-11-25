'use client';

// Give up seats for a voucher (FR-27, AD-9, AD-29, AD-30, UX-DR40): the confirming step of the Voucher Change and its
// result, at `/manage/[reference]/voucher`. Modelled on MoveSeats, without a date or session.
//
// - The Booking is read with this browser's session from `GET /api/manage/{reference}`; a 404 is "This page is not
//   available." (FR-20). Loading changes nothing. After the Cutoff the page shows the Cutoff text of Story 4.1.
// - The question reuses the Seat picker (1 to the Booking's Seats; left out for a Booking of 1 Seat). Once a number is
//   chosen, the shared ConfirmingStep states what will happen: the Seats given up, the Seats left (only when some
//   remain), the Voucher value (Seats x the Booking's own price per Seat) and the last valid date (the Booking's
//   `voucher_last_valid_date`: one year ahead, or the date of a Voucher that paid the Booking, so giving up never
//   renews a Voucher); nothing changes until the Guest confirms.
// - The idempotency key lives in the slot `draft:change:<reference>:voucher` (lib/draft.js), with the move step's
//   rules: made when the step opens, reused on a reload, deleted on success, on every refusal except `503 try_again`
//   (and no answer at all), and when the Guest leaves the step.
// - A refusal reuses the move texts (`moveRefusal`) and keeps the choice. After `booking_changed` or `invalid_key` the
//   Booking is read again and the step opens fresh with a new key. After `cutoff_passed` the page shows the Cutoff text.
//   After `booking_cancelled` (the Booking was cancelled from another tab) the "please try again" Notice
//   shows and the Booking is read again, so the cancelled state replaces the step.
// - A cancelled Booking (all Seats given up; a reload of the result page) shows the Manage page's cancelled text in a
//   Notice and no step.
// - On success the page shows the result: "Seats given up", whether the Booking was changed or cancelled, that the
//   Voucher code is in the email, the email under "Sent by email:" (ChangeResult), then "Back to your booking". Focus
//   moves to its h1. The code reaches this page only inside the email body.
// No clock is read here: dates and times come from the API (AD-4).
import { useEffect, useRef, useState } from 'react';
import ChangeResult from './ChangeResult';
import ConfirmingStep from './ConfirmingStep';
import GuestShell from './GuestShell';
import NotAvailable from './NotAvailable';
import Notice from './Notice';
import SeatPicker from './SeatPicker';
import TextLink from './TextLink';
import Wordmark from './Wordmark';
import { ApiError, api } from '@/lib/api';
import { MANAGE, VOUCHER, moveRefusal, seatsWord } from '@/lib/copy';
import { clockTime, longDate } from '@/lib/dates';
import { changeKey, dropChangeKey } from '@/lib/draft';
import { nok } from '@/lib/venue-format';

const ACTION = 'voucher';

export default function GiveUpSeats({ reference }) {
  const [load, setLoad] = useState({ status: 'loading', booking: null });
  const [reloadKey, setReloadKey] = useState(0);
  const [seats, setSeats] = useState(null);
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState(null); // {text, n}: a new `n` moves focus to the Notice
  const [cutoffAt, setCutoffAt] = useState(null);
  const [result, setResult] = useState(null);
  const sending = useRef(false);
  const heading = useRef(null);
  const resultHeading = useRef(null);

  const b = load.booking;
  const open = Boolean(b && b.status === 'active' && b.change_allowed && !cutoffAt);
  const oneSeat = b ? b.seats === 1 : false;

  // Read the Booking (again after `booking_changed` or `invalid_key`). The step's key is made when it opens.
  useEffect(() => {
    const controller = new AbortController();
    api(`/api/manage/${encodeURIComponent(reference)}`, { signal: controller.signal })
      .then((booking) => {
        if (controller.signal.aborted) return;
        if (booking.kind !== 'seats') {
          // a Seat Change of a Whole-sauna booking: the API refuses it as a route of the other kind (Story 5.2)
          setLoad({ status: 'not_available', booking: null });
          return;
        }
        if (booking.status === 'active' && booking.change_allowed) changeKey(reference, ACTION);
        setLoad({ status: 'ok', booking });
        if (booking.seats === 1) setSeats(1);
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

  const ready = open && Number.isInteger(seats) && seats >= 1 && seats <= b.seats;

  const confirm = async () => {
    if (sending.current || !ready) return;
    sending.current = true;
    setBusy(true);
    const key = changeKey(reference, ACTION);
    try {
      const body = await api(`/api/manage/${encodeURIComponent(reference)}/seats/voucher`, {
        method: 'POST',
        body: { seats, version: b.version },
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
            setSeats(null);
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
    const cancelled = result.booking.status === 'cancelled';
    return (
      <GuestShell rail={<Wordmark />}>
        <title>{`${VOUCHER.resultHeading} – Saunalöyly`}</title>
        <div className="col page-text">
          <h1 className="heading-xl heading-success" tabIndex={-1} ref={resultHeading}>
            {VOUCHER.resultHeading}
          </h1>
          <p className="after-heading">{cancelled ? VOUCHER.resultCancelled : VOUCHER.resultChanged}</p>
          <p className="move-new-reference">{VOUCHER.codeInEmail}</p>
          <ChangeResult emails={result.emails} />
          <p className="move-result-back">
            <TextLink href={`/manage/${encodeURIComponent(reference)}`}>{VOUCHER.backToBooking}</TextLink>
          </p>
        </div>
      </GuestShell>
    );
  }

  const cutoffText = (at) => MANAGE.cutoffPassed(longDate(at.slice(0, 10)), clockTime(at));
  const shownCutoff = cutoffAt || (b && b.status === 'active' && !b.change_allowed ? b.cutoff_at : null);
  const cancelledAt = b && b.status === 'cancelled' && b.cancelled_at ? b.cancelled_at : null;
  const some = b && Number.isInteger(seats) && seats < b.seats;
  // the Booking's own price per Seat (AD-13): its total over its Seats
  const value = b && Number.isInteger(seats) ? seats * (b.total_ore / b.seats) : 0;

  return (
    <GuestShell rail={<Wordmark />} mainClass="book">
      {load.status !== 'loading' && (
        <h1 className="heading-xl" tabIndex={-1} ref={heading}>
          {VOUCHER.heading}
        </h1>
      )}
      <p className="back">
        <TextLink href={`/manage/${encodeURIComponent(reference)}`}>{VOUCHER.back}</TextLink>
      </p>
      {refusal && (
        <div className="move-notice">
          <Notice focusKey={refusal.n}>{refusal.text}</Notice>
        </div>
      )}
      {load.status === 'failed' && <div className="move-notice"><Notice>{MANAGE.loadFailed}</Notice></div>}
      {shownCutoff && <div className="move-notice"><Notice>{cutoffText(shownCutoff)}</Notice></div>}
      {cancelledAt && (
        <div className="move-notice">
          <Notice>{MANAGE.cancelled(longDate(cancelledAt.slice(0, 10)), clockTime(cancelledAt))}</Notice>
        </div>
      )}
      {open && (
        <>
          {!oneSeat && (
            <div className="move-seats">
              <SeatPicker seats={seats} onChange={setSeats} max={b.seats} legend={VOUCHER.seatsQuestion} />
            </div>
          )}
          {ready && (
            <ConfirmingStep
              heading={VOUCHER.summaryHeading}
              rows={[
                { label: VOUCHER.seatsGivenUp, value: seatsWord(seats) },
                ...(some ? [{ label: VOUCHER.seatsLeftInBooking, value: seatsWord(b.seats - seats) }] : []),
                { label: VOUCHER.value, value: nok(value) },
                { label: VOUCHER.validUntil, value: longDate(b.voucher_last_valid_date) },
              ]}
              confirmLabel={VOUCHER.confirm(seats)}
              onConfirm={confirm}
              busy={busy}
            >
              <p className="move-note">{VOUCHER.noMoney}</p>
              <p className="move-note">{VOUCHER.nothingYet}</p>
            </ConfirmingStep>
          )}
        </>
      )}
    </GuestShell>
  );
}
