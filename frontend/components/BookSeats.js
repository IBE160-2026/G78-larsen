'use client';

// Book seats (FR-2, FR-3, FR-4, UX-DR9/12/13/17–21/26/33–35): the three questions in main (date, number of seats,
// session, nothing pre-selected) and the rail with the Total block, "Continue booking" (always enabled), the
// Wordmark, the Seat statement, the changing-time note and the Terms and Privacy links.
//
// - The page calls `POST /api/session` once, on load, so exactly one session cookie is set (AD-8).
// - Window listings go through lib/api.js; numbers and every time fact (`today`, `horizon_end`, `horizon_days`,
//   `already_started`) come from the API, never from a clock here (AD-4, AD-5). Sessions are read again when the
//   date or the number changes.
// - The Booking draft (`draft:seats`) is read and written only in effects (AD-9, UX-DR26).
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';
import DateCalendar from './DateCalendar';
import ErrorSummary from './ErrorSummary';
import GuestShell from './GuestShell';
import PrimaryButton from './PrimaryButton';
import SeatPicker, { SEAT_CHOICES } from './SeatPicker';
import SessionList, { availability } from './SessionList';
import TextLink from './TextLink';
import TotalBlock from './TotalBlock';
import Wordmark from './Wordmark';
import { ApiError, api } from '@/lib/api';
import { BOOK, CHANGING_TIME, SEAT_STATEMENT } from '@/lib/copy';
import { dotted, monthOf, parseDotted } from '@/lib/dates';
import { readDraft, writeDraft } from '@/lib/draft';

export const DETAILS = '/book-seats/details';
const ISO = /^\d{4}-\d{2}-\d{2}$/;

function focusById(id) {
  const el = document.getElementById(id);
  if (el) el.focus();
  return Boolean(el);
}

function focusRadio(name, fallbackId) {
  const radios = Array.from(document.querySelectorAll(`input[type=radio][name=${name}]`));
  const target = radios.find((r) => r.checked) || radios.find((r) => !r.disabled);
  if (target) target.focus();
  else focusById(fallbackId);
}

export default function BookSeats({ pricePerSeatOre }) {
  const router = useRouter();
  const sessionOpened = useRef(false);

  const [restored, setRestored] = useState(false);
  const [facts, setFacts] = useState(null); // {today, horizon_end, horizon_days, dates}
  const [date, setDate] = useState(null);
  const [text, setText] = useState('');
  const [dateError, setDateError] = useState(null);
  const [month, setMonth] = useState(null);
  const [seats, setSeats] = useState(null);
  const [windowId, setWindowId] = useState(null);
  const [pending, setPending] = useState(null); // {id, focus, fromDraft}: a Window to select once it is read
  const [status, setStatus] = useState('idle');
  const [windows, setWindows] = useState([]);
  const [nearest, setNearest] = useState(null);
  const [clearedNotice, setClearedNotice] = useState(null);
  const [reload, setReload] = useState(0);
  const [showErrors, setShowErrors] = useState(false);
  const [focusKey, setFocusKey] = useState(0);
  const [focusWindow, setFocusWindow] = useState(null);

  // One session, from Book seats only (AD-8). A failure is not shown: the Seat flow reads without a session.
  useEffect(() => {
    if (sessionOpened.current) return;
    sessionOpened.current = true;
    api('/api/session', { method: 'POST', body: {} }).catch(() => {});
  }, []);

  // Restore the draft (a reload, or a Guest coming back from Terms).
  useEffect(() => {
    const draft = readDraft();
    if (typeof draft.date === 'string' && ISO.test(draft.date)) {
      setDate(draft.date);
      setText(dotted(draft.date));
      setMonth(monthOf(draft.date));
    }
    if (SEAT_CHOICES.includes(draft.seats)) setSeats(draft.seats);
    if (Number.isInteger(draft.window_id) && draft.date) {
      setPending({ id: draft.window_id, focus: false, fromDraft: true });
    }
    setRestored(true);
  }, []);

  // Keep the draft in step with the choices.
  useEffect(() => {
    if (!restored) return;
    writeDraft({ date, seats, window_id: windowId ?? pending?.id ?? null });
  }, [restored, date, seats, windowId, pending]);

  // Read the Windows: the time facts and the bookable dates always, the date's Sessions once a date is chosen.
  const seatsKey = date ? seats : null;
  useEffect(() => {
    if (!restored) return undefined;
    const controller = new AbortController();
    const params = new URLSearchParams();
    if (date) params.set('date', date);
    if (date && seatsKey) params.set('seats', String(seatsKey));
    const query = params.toString();
    if (date) setStatus('loading');
    api(`/api/windows${query ? `?${query}` : ''}`, { signal: controller.signal })
      .then((body) => {
        if (controller.signal.aborted) return; // a newer read has started
        setFacts({ today: body.today, horizon_end: body.horizon_end, horizon_days: body.horizon_days,
          dates: body.dates });
        setWindows(body.windows || []);
        setNearest(body.nearest ?? null);
        setStatus(date ? 'ok' : 'idle');
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && err.code === 'outside_horizon') {
          // a restored date that has left the horizon: start the date question again
          setDate(null);
          setText('');
          setMonth(null);
          setPending(null);
          setWindowId(null);
          setStatus('idle');
          return;
        }
        setStatus('failed');
      });
    return () => controller.abort();
  }, [restored, date, seatsKey, reload]);

  // After each read: select a pending Window, or clear a chosen one that no longer fits the number.
  useEffect(() => {
    if (status !== 'ok') return;
    if (pending) {
      const w = windows.find((x) => x.id === pending.id);
      if (w && availability(w, seats).open) {
        setWindowId(w.id);
        if (pending.focus) setFocusWindow(w.id);
      } else if (w && seats) {
        setClearedNotice(BOOK.sessionCleared(seats));
      }
      setPending(null);
      return;
    }
    if (windowId == null) return;
    const w = windows.find((x) => x.id === windowId);
    if (!w) {
      setWindowId(null);
    } else if (!availability(w, seats).open) {
      setWindowId(null);
      setClearedNotice(BOOK.sessionCleared(seats));
    }
    // Only a new read decides (deliberately not keyed on the choices): a choice made between reads is the Guest's.
  }, [status, windows]);

  // Focus the Session chosen from Nearest sessions once its row is on the page.
  useEffect(() => {
    if (focusWindow == null) return;
    if (focusById(`session-${focusWindow}`)) setFocusWindow(null);
  }, [focusWindow, windowId, status]);

  const pickDate = useCallback((iso) => {
    setDateError(null);
    setText(dotted(iso));
    setMonth(monthOf(iso));
    if (iso === date) return;
    setDate(iso);
    setWindowId(null);
    setClearedNotice(null);
    setNearest(null);
  }, [date]);

  const commitText = () => {
    const typed = text.trim();
    if (!typed) {
      // an emptied field means no date: the field and the grid stay in step
      setDateError(null);
      setDate(null);
      setWindowId(null);
      setPending(null);
      setNearest(null);
      setClearedNotice(null);
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
    setClearedNotice(null);
  };

  const chooseWindow = (id) => {
    setWindowId(id);
    setClearedNotice(null);
  };

  const chooseNearest = (w) => {
    pickDate(w.date);
    setPending({ id: w.id, focus: true, fromDraft: false });
    setReload((k) => k + 1);
  };

  const dateFieldError = dateError || (showErrors && !date ? BOOK.chooseDate : null);
  const seatsError = showErrors && !seats ? BOOK.chooseSeats : null;
  const sessionError = showErrors && windowId == null ? BOOK.chooseSession : null;
  const errors = [
    dateFieldError && showErrors ? { key: 'date', text: dateFieldError, href: '#date' } : null,
    seatsError ? { key: 'seats', text: seatsError, href: '#seats' } : null,
    sessionError ? { key: 'session', text: sessionError, href: '#sessions' } : null,
  ].filter(Boolean);

  const onSummaryChoose = (key) => {
    if (key === 'date') focusById('date');
    else if (key === 'seats') focusRadio('seats', 'seats');
    else focusRadio('session', 'sessions');
  };

  const onContinue = () => {
    // the chosen Window must be in the last read and have room for the number now chosen (a re-read after a change
    // of number may still be loading or may have failed)
    let chosen = windowId;
    if (chosen != null) {
      const w = windows.find((x) => x.id === chosen);
      if (!w || !availability(w, seats).open) {
        chosen = null;
        setWindowId(null);
        if (seats) setClearedNotice(BOOK.sessionCleared(seats));
      }
    }
    const missing = !date || Boolean(dateError) || !seats || chosen == null;
    if (missing) {
      setShowErrors(true);
      setFocusKey((k) => k + 1);
      return;
    }
    router.push(DETAILS); // the draft is already in step (the effect above)
  };

  const rail = (
    <div className="rail-book">
      <TotalBlock pricePerSeatOre={pricePerSeatOre} seats={seats} />
      <PrimaryButton onClick={onContinue}>{BOOK.continue}</PrimaryButton>
      <Wordmark />
      <p className="rail-note">{SEAT_STATEMENT}</p>
      <p className="rail-note">{CHANGING_TIME}</p>
      <p className="rail-note rail-links">
        <TextLink href="/terms">Terms</TextLink>
        <TextLink href="/privacy">Privacy notice</TextLink>
      </p>
    </div>
  );

  return (
    <GuestShell rail={rail} mainClass="book">
      <h1 className="heading-xl" tabIndex={-1}>
        {BOOK.heading}
      </h1>
      {showErrors && <ErrorSummary errors={errors} focusKey={focusKey} onChoose={onSummaryChoose} />}
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
          error={dateFieldError}
          readFailed={!facts && status === 'failed'}
        />
        <div className="book-rest">
          <SeatPicker seats={seats} onChange={chooseSeats} error={seatsError} />
          <SessionList
            date={date}
            seats={seats}
            status={status}
            windows={windows}
            nearest={nearest}
            horizonDays={facts?.horizon_days}
            windowId={windowId}
            onChoose={chooseWindow}
            onChooseNearest={chooseNearest}
            clearedNotice={clearedNotice}
            error={sessionError}
          />
        </div>
      </div>
    </GuestShell>
  );
}
