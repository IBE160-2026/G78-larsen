'use client';

// Move seats (FR-26, AD-9, AD-29, UX-DR17-19/40): the confirming step of the Seat move and its result, at
// `/manage/[reference]/move`.
//
// - The Booking is read with this browser's session from `GET /api/manage/{reference}`; a 404 is "This page is not
//   available." (FR-20). Loading changes nothing. After the Cutoff the page shows the Cutoff text of Story 4.1.
// - The questions reuse the Seat picker (1 to the Booking's Seats; left out for a Booking of 1 Seat), the Date
//   calendar and the Session list of Book seats, fed by `GET /api/windows`. The Booking's own session is a disabled
//   row, "Your current session" (Lisa, 2026-11-24). Once a number and a session are chosen, the shared
//   ConfirmingStep states what will happen; nothing changes until the Guest confirms.
// - The idempotency key lives in the slot `draft:change:<reference>:move` (lib/draft.js): made when the step opens,
//   reused on a reload, deleted on success, on every refusal except `503 try_again` (and no answer at all), and when
//   the Guest leaves the step.
// - A refusal shows a Notice from `moveRefusal` (lib/copy.js) and keeps the choices. After `booking_changed` or
//   `invalid_key` the Booking is read again and the step opens fresh with a new key. After `cutoff_passed` the page
//   shows the Cutoff text.
// - On success the page shows the result: "Seats moved", the line, the new reference of a split, and every email the
//   Change sent under "Sent by email:" (ChangeResult). Focus moves to its h1.
// No clock is read here: dates and times come from the API (AD-4).
import { useCallback, useEffect, useRef, useState } from 'react';
import ChangeResult from './ChangeResult';
import ConfirmingStep from './ConfirmingStep';
import DateCalendar from './DateCalendar';
import GuestShell from './GuestShell';
import NotAvailable from './NotAvailable';
import Notice from './Notice';
import SeatPicker from './SeatPicker';
import SessionList, { availability } from './SessionList';
import TextLink from './TextLink';
import Wordmark from './Wordmark';
import { ApiError, api } from '@/lib/api';
import { BOOK, MANAGE, MOVE, moveRefusal, seatsWord } from '@/lib/copy';
import { clockTime, dotted, longDate, monthOf, parseDotted } from '@/lib/dates';
import { changeKey, dropChangeKey } from '@/lib/draft';

const ACTION = 'move';

const when = (date, w) => `${longDate(date)}, ${clockTime(w.start)}–${clockTime(w.end)}`;

export default function MoveSeats({ reference }) {
  const [load, setLoad] = useState({ status: 'loading', booking: null });
  const [reloadKey, setReloadKey] = useState(0);
  const [windowsKey, setWindowsKey] = useState(0); // a re-read of the Sessions after `no_seat_free`
  const [facts, setFacts] = useState(null); // {today, horizon_end, horizon_days, dates}
  const [date, setDate] = useState(null);
  const [text, setText] = useState('');
  const [dateError, setDateError] = useState(null);
  const [month, setMonth] = useState(null);
  const [seats, setSeats] = useState(null);
  const [windowId, setWindowId] = useState(null);
  const [windows, setWindows] = useState([]);
  const [listing, setListing] = useState('idle');
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

  // The Windows: the time facts and bookable dates always, the chosen date's Sessions once a date is chosen.
  useEffect(() => {
    if (!open) return undefined;
    const controller = new AbortController();
    if (date) setListing('loading');
    api(`/api/windows${date ? `?date=${encodeURIComponent(date)}` : ''}`, { signal: controller.signal })
      .then((body) => {
        if (controller.signal.aborted) return;
        setFacts({ today: body.today, horizon_end: body.horizon_end, horizon_days: body.horizon_days,
          dates: body.dates });
        setWindows(body.windows || []);
        setListing(date ? 'ok' : 'idle');
      })
      .catch(() => {
        if (!controller.signal.aborted) setListing('failed');
      });
    return () => controller.abort();
  }, [open, date, reloadKey, windowsKey]);

  // After a re-read, a chosen session that no longer has room for the chosen Seats is no longer chosen.
  useEffect(() => {
    const w = windows.find((x) => x.id === windowId);
    if (w && !availability(w, seats).open) setWindowId(null);
    // only a new read decides (deliberately not keyed on the choices)
  }, [windows]);

  const pickDate = useCallback((iso) => {
    setDateError(null);
    setText(dotted(iso));
    setMonth(monthOf(iso));
    if (iso === date) return;
    setDate(iso);
    setWindowId(null);
  }, [date]);

  const commitText = () => {
    const typed = text.trim();
    if (!typed) {
      setDateError(null);
      setDate(null);
      setWindowId(null);
      return;
    }
    const iso = parseDotted(typed);
    if (!iso) {
      setDateError(BOOK.dateFormat);
      return;
    }
    if (facts && !facts.dates.includes(iso)) {
      setDateError(BOOK.dateNotBookable);
      return;
    }
    pickDate(iso);
  };

  const chooseSeats = (n) => {
    setSeats(n);
    const w = windows.find((x) => x.id === windowId);
    if (w && !availability(w, n).open) setWindowId(null);
  };

  const target = windows.find((x) => x.id === windowId && x.id !== b?.window.id);
  const ready = open && Number.isInteger(seats) && target && availability(target, seats).open;

  const confirm = async () => {
    if (sending.current || !ready) return;
    sending.current = true;
    setBusy(true);
    const key = changeKey(reference, ACTION);
    try {
      const body = await api(`/api/manage/${encodeURIComponent(reference)}/seats/move`, {
        method: 'POST',
        body: { window_id: target.id, seats, version: b.version },
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
          if (r.kind === 'reload') {
            // a fresh step: the Booking is read again and a new key is made when it opens
            setDate(null);
            setText('');
            setMonth(null);
            setWindowId(null);
            setSeats(null);
            setReloadKey((k) => k + 1);
          } else if (code === 'no_seat_free') {
            setWindowsKey((k) => k + 1); // Seats left changed: read the date's Sessions again, keep the choices
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
    const moved = result.new_booking;
    return (
      <GuestShell rail={<Wordmark />}>
        <title>{`${MOVE.resultHeading} – Saunalöyly`}</title>
        <div className="col page-text">
          <h1 className="heading-xl heading-success" tabIndex={-1} ref={resultHeading}>
            {MOVE.resultHeading}
          </h1>
          <p className="after-heading">{MOVE.resultLine}</p>
          {moved && <p className="move-new-reference">{MOVE.newReference(moved.reference)}</p>}
          <ChangeResult emails={result.emails} />
        </div>
      </GuestShell>
    );
  }

  const cutoffText = (at) => MANAGE.cutoffPassed(longDate(at.slice(0, 10)), clockTime(at));
  const shownCutoff = cutoffAt || (b && b.status === 'active' && !b.change_allowed ? b.cutoff_at : null);
  // "Seats left in this booking" only for a split; a full move takes the whole Booking along (Lisa, 2026-11-24)
  const split = b && Number.isInteger(seats) && seats < b.seats;

  return (
    <GuestShell rail={<Wordmark />} mainClass="book">
      {load.status !== 'loading' && (
        <h1 className="heading-xl" tabIndex={-1} ref={heading}>
          {MOVE.heading}
        </h1>
      )}
      <p className="back">
        <TextLink href={`/manage/${encodeURIComponent(reference)}`}>{MOVE.back}</TextLink>
      </p>
      {refusal && (
        <div className="move-notice">
          <Notice focusKey={refusal.n}>{refusal.text}</Notice>
        </div>
      )}
      {load.status === 'failed' && <div className="move-notice"><Notice>{MANAGE.loadFailed}</Notice></div>}
      {shownCutoff && <div className="move-notice"><Notice>{cutoffText(shownCutoff)}</Notice></div>}
      {open && (
        <>
          {!oneSeat && (
            <div className="move-seats">
              <SeatPicker seats={seats} onChange={chooseSeats} max={b.seats} legend={MOVE.seatsQuestion} />
            </div>
          )}
          <div className="book-cols">
            <DateCalendar
              facts={facts}
              date={date}
              month={month ?? (facts ? monthOf(facts.today) : null)}
              onMonth={setMonth}
              text={text}
              onText={setText}
              onCommitText={commitText}
              onPick={pickDate}
              error={dateError}
              readFailed={!facts && listing === 'failed'}
              label={MOVE.dateQuestion}
            />
            <div className="book-rest">
              <SessionList
                date={date}
                seats={seats}
                status={listing}
                windows={windows}
                nearest={null}
                windowId={windowId}
                onChoose={setWindowId}
                currentWindowId={b.window.id}
              />
            </div>
          </div>
          {ready && (
            <ConfirmingStep
              heading={MOVE.summaryHeading}
              rows={[
                { label: MOVE.seatsMoved, value: seatsWord(seats) },
                { label: MOVE.from, value: when(b.window.date, b.window) },
                { label: MOVE.to, value: when(date, target) },
                ...(split ? [{ label: MOVE.seatsLeftInBooking, value: seatsWord(b.seats - seats) }] : []),
              ]}
              confirmLabel={MOVE.confirm(seats)}
              onConfirm={confirm}
              busy={busy}
            >
              <p className="move-note">{MOVE.nothingYet}</p>
            </ConfirmingStep>
          )}
        </>
      )}
    </GuestShell>
  );
}
