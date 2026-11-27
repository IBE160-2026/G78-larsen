'use client';

// Move private sauna (FR-33, AD-9, AD-24, AD-29, UX-DR40, Story 5.3 part 2): the confirming step of a Whole-sauna move
// and its result, at `/manage/[reference]/move-sauna`. Built like MoveSeats and CancelPrivateSauna.
//
// - The Booking is read with this browser's session from `GET /api/manage/{reference}`; a 404, and a Seat booking (the
//   API refuses it as a route of the other kind), are "This page is not available." (FR-20). Loading changes nothing.
//   After the 72-hour Cutoff the page shows the Cutoff text.
// - "1. Choose a date" is the Date calendar of Book seats, fed by `GET /api/windows`. "2. Choose a sauna and a
//   session" lists the Sauna cards of the Private sauna page, fed by the move list
//   `GET /api/manage/{reference}/whole/move-list?date=` (the AD-24 listing judged as if this Booking were absent). The
//   Booking's own Sauna comes first, marked "Your sauna"; its own pair is a disabled button "Your current session". A
//   Sauna whose price differs from the total paid shows its price and why it cannot be chosen, and no session
//   buttons (Lisa, 2026-11-26). The cards are one radio group in a fieldset with a legend: one tab stop, arrow keys
//   inside.
// - Once a pair is chosen, the shared ConfirmingStep states what will happen: From, To, Price "(unchanged)", and that
//   nothing changes until the Guest confirms "Move booking".
// - The idempotency key lives in the slot `draft:change:<reference>:move` (lib/draft.js), with the other steps' rules:
//   made when the step opens, reused on a reload, deleted on success, on every refusal except `503 try_again` (and no
//   answer at all), and when the Guest leaves the step.
// - A refusal shows a Notice from `wholeMoveRefusal` and keeps the date; a new date or pair clears it. After
//   `sauna_unavailable`, `price_differs`, `outside_horizon` or `deadline_passed` the date's list is read again. After `booking_changed` or `invalid_key` the Booking is read again and the step
//   opens fresh with a new key. After `cutoff_passed` the page shows the Cutoff text. After `booking_cancelled` the
//   Booking is read again, so the step closes.
// - On success the page shows the result: "Booking moved", "Your booking has been changed.", the email under "Sent by
//   email:" (ChangeResult), then "Back to your booking". Focus moves to its h1.
// Wording: Lisa, 2026-11-26 (EXPERIENCE.md "Move private sauna wording"). No clock is read here: dates and times come
// from the API (AD-4); the price rule is judged again by the API (`409 price_differs`).
import { useCallback, useEffect, useRef, useState } from 'react';
import ChangeResult from './ChangeResult';
import ConfirmingStep from './ConfirmingStep';
import DateCalendar from './DateCalendar';
import GuestShell from './GuestShell';
import NotAvailable from './NotAvailable';
import Notice from './Notice';
import { SaunaHead, sessionText } from './PrivateSauna';
import TextLink from './TextLink';
import Wordmark from './Wordmark';
import { ApiError, api } from '@/lib/api';
import { BOOK, MANAGE, MOVE_WHOLE, PRIVATE, wholeMoveRefusal } from '@/lib/copy';
import { clockTime, dotted, longDate, monthOf, parseDotted } from '@/lib/dates';
import { changeKey, dropChangeKey } from '@/lib/draft';
import { SAUNA_COPY } from '@/lib/sauna-copy';
import { nok } from '@/lib/venue-format';

const ACTION = 'move';

const when = (saunaName, date, w) => `${saunaName}, ${longDate(date)}, ${clockTime(w.start)}–${clockTime(w.end)}`;

/** The listing in the step's order: the Booking's own Sauna first, then the others in Fill order. The move list
 * always holds the Booking's own pair on its own date (the API lists it); it is shown as "Your current session". */
function ordered(saunas, b) {
  const own = b.sauna?.id;
  return [...saunas.filter((s) => s.id === own), ...saunas.filter((s) => s.id !== own)];
}

function PairCards({ saunas, booking, saunaId, windowId, onChoose }) {
  const own = booking.sauna?.id;
  return (
    <fieldset className="question question-pairs" id="saunas">
      <legend className="q">{MOVE_WHOLE.pairQuestion}</legend>
      <div className="private-cards">
        {saunas.map((s) => {
          const mine = s.id === own;
          const otherPrice = !mine && s.whole_price_ore !== booking.total_ore;
          const described = [
            SAUNA_COPY[s.id]?.description ? `sauna-text-${s.id}` : null,
            otherPrice ? `sauna-price-${s.id}` : null,
          ].filter(Boolean).join(' ');
          return (
            <div
              key={s.id}
              className={mine ? 'private-card private-card-mine' : 'private-card'}
              role="group"
              aria-labelledby={mine ? `sauna-mine-${s.id} sauna-name-${s.id}` : `sauna-name-${s.id}`}
              aria-describedby={described || undefined}
            >
              {mine && (
                <span className="private-card-label" id={`sauna-mine-${s.id}`}>
                  {MOVE_WHOLE.yourSauna}
                </span>
              )}
              <SaunaHead sauna={s} />
              {otherPrice ? (
                <p className="private-card-other" id={`sauna-price-${s.id}`}>
                  {MOVE_WHOLE.otherPrice}
                </p>
              ) : (
                <span className="slot-grid">
                  {s.windows.map((w) => {
                    const t = sessionText(w);
                    const current = mine && w.id === booking.window.id;
                    return (
                      <label key={w.id} className={current ? 'cell slot current' : 'cell slot'}>
                        <input
                          type="radio"
                          name="pair"
                          id={`pair-${s.id}-${w.id}`}
                          value={`${s.id}-${w.id}`}
                          checked={!current && saunaId === s.id && windowId === w.id}
                          disabled={current}
                          aria-label={`${s.name}, ${t.spoken}${current ? `, ${MOVE_WHOLE.currentSession}` : ''}`}
                          onChange={() => onChoose(s.id, w.id)}
                        />
                        <span aria-hidden="true">
                          {t.shown}
                          {current && <small>{MOVE_WHOLE.currentSession}</small>}
                          {!current && w.already_started && <small>{BOOK.alreadyStarted}</small>}
                        </span>
                      </label>
                    );
                  })}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </fieldset>
  );
}

export default function MovePrivateSauna({ reference }) {
  const [load, setLoad] = useState({ status: 'loading', booking: null });
  const [reloadKey, setReloadKey] = useState(0);
  const [listKey, setListKey] = useState(0); // a re-read of the date's list after `sauna_unavailable`/`price_differs`
  const [facts, setFacts] = useState(null); // {today, horizon_end, horizon_days, dates}
  const [factsFailed, setFactsFailed] = useState(false);
  const [date, setDate] = useState(null);
  const [text, setText] = useState('');
  const [dateError, setDateError] = useState(null);
  const [month, setMonth] = useState(null);
  const [saunas, setSaunas] = useState([]);
  const [listing, setListing] = useState('idle');
  const [saunaId, setSaunaId] = useState(null);
  const [windowId, setWindowId] = useState(null);
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState(null); // {text, n}: a new `n` moves focus to the Notice
  const [cutoffAt, setCutoffAt] = useState(null);
  const [result, setResult] = useState(null);
  const sending = useRef(false);
  const heading = useRef(null);
  const resultHeading = useRef(null);

  const b = load.booking;
  const open = Boolean(b && b.status === 'active' && b.change_allowed && !cutoffAt);

  // Read the Booking (again after `booking_changed`, `invalid_key` or `booking_cancelled`). The key is made when the
  // step opens.
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

  // The calendar facts: the bookable dates and the horizon, from the server (AD-4).
  useEffect(() => {
    if (!open) return undefined;
    const controller = new AbortController();
    api('/api/windows', { signal: controller.signal })
      .then((body) => {
        if (controller.signal.aborted) return;
        setFacts({ today: body.today, horizon_end: body.horizon_end, horizon_days: body.horizon_days,
          dates: body.dates });
        setFactsFailed(false);
      })
      .catch(() => {
        if (!controller.signal.aborted) setFactsFailed(true);
      });
    return () => controller.abort();
  }, [open, reloadKey]);

  // The move list of the chosen date.
  useEffect(() => {
    if (!open || !date) return undefined;
    const controller = new AbortController();
    setListing('loading');
    api(`/api/manage/${encodeURIComponent(reference)}/whole/move-list?date=${encodeURIComponent(date)}`,
      { signal: controller.signal })
      .then((body) => {
        if (controller.signal.aborted) return;
        setSaunas(body.saunas || []);
        setListing('ok');
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && err.code === 'outside_horizon') {
          setDateError(BOOK.dateNotBookable);
          setDate(null);
          setListing('idle');
          return;
        }
        if (err instanceof ApiError && err.status === 404) {
          setLoad({ status: 'not_available', booking: null });
          return;
        }
        setListing('failed');
      });
    return () => controller.abort();
  }, [open, reference, date, listKey]);

  const shown = b ? ordered(saunas, b) : [];
  const sauna = shown.find((s) => s.id === saunaId) || null;
  const target = sauna && b && !(sauna.id === b.sauna?.id && windowId === b.window.id)
    ? sauna.windows.find((w) => w.id === windowId) || null : null;
  const samePrice = sauna && b && (sauna.id === b.sauna?.id || sauna.whole_price_ore === b.total_ore);
  const ready = open && target && samePrice;

  // After a re-read, a chosen pair the list no longer offers is no longer chosen.
  useEffect(() => {
    if (listing !== 'ok' || saunaId == null) return;
    const s = saunas.find((x) => x.id === saunaId);
    if (!s || !s.windows.some((w) => w.id === windowId)) {
      setSaunaId(null);
      setWindowId(null);
    }
    // only a new read decides (deliberately not keyed on the choices)
  }, [saunas, listing]);

  const pickDate = useCallback((iso) => {
    setDateError(null);
    setRefusal(null);
    setText(dotted(iso));
    setMonth(monthOf(iso));
    if (iso === date) {
      if (listing === 'failed') setListKey((k) => k + 1); // read the same date again
      return;
    }
    setDate(iso);
    setSaunas([]);
    setSaunaId(null);
    setWindowId(null);
  }, [date, listing]);

  const commitText = () => {
    const typed = text.trim();
    if (!typed) {
      setDateError(null);
      setDate(null);
      setSaunas([]);
      setSaunaId(null);
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

  const choosePair = (sid, wid) => {
    setRefusal(null);
    setSaunaId(sid);
    setWindowId(wid);
  };

  const confirm = async () => {
    if (sending.current || !ready) return;
    sending.current = true;
    setBusy(true);
    const key = changeKey(reference, ACTION);
    try {
      const body = await api(`/api/manage/${encodeURIComponent(reference)}/whole/move`, {
        method: 'POST',
        body: { window_id: target.id, sauna_id: sauna.id, version: b.version },
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
        const r = wholeMoveRefusal(code, errFacts);
        if (r.kind === 'cutoff') {
          setCutoffAt(typeof errFacts.cutoff_at === 'string' ? errFacts.cutoff_at : b.cutoff_at);
          setRefusal(null);
        } else {
          if (r.kind === 'reload' || code === 'booking_cancelled') {
            // a fresh step: the Booking is read again and a new key is made when it opens
            setDate(null);
            setText('');
            setMonth(null);
            setSaunas([]);
            setSaunaId(null);
            setWindowId(null);
            setReloadKey((k) => k + 1);
          } else if (['sauna_unavailable', 'price_differs', 'outside_horizon', 'deadline_passed'].includes(code)) {
            setListKey((k) => k + 1); // the date's list changed: read it again, keep the date
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
    return (
      <GuestShell rail={<Wordmark />}>
        <title>{`${MOVE_WHOLE.resultHeading} – Saunalöyly`}</title>
        <div className="col page-text">
          <h1 className="heading-xl heading-success" tabIndex={-1} ref={resultHeading}>
            {MOVE_WHOLE.resultHeading}
          </h1>
          <p className="after-heading">{MOVE_WHOLE.resultLine}</p>
          <ChangeResult emails={result.emails} />
          <p className="move-result-back">
            <TextLink href={`/manage/${encodeURIComponent(reference)}`}>{MOVE_WHOLE.backToBooking}</TextLink>
          </p>
        </div>
      </GuestShell>
    );
  }

  const cutoffText = () => MANAGE.cutoffPassed(MANAGE.wholeHours);
  const shownCutoff = cutoffAt || (b && b.status === 'active' && !b.change_allowed ? b.cutoff_at : null);
  const cancelledAt = b && b.status === 'cancelled' && b.cancelled_at && b.cancel_remedy ? b.cancelled_at : null;

  // `message` sits in a polite live region (as on the Private sauna page); the cards do not.
  let message = null;
  if (date && listing === 'loading') message = <p className="loading">{BOOK.loadingSessions}</p>;
  else if (date && listing === 'failed') message = <Notice>{BOOK.sessionsUnavailable}</Notice>;
  else if (date && listing === 'ok' && shown.length === 0) {
    message = <p className="private-empty">{PRIVATE.noSauna(longDate(date))}</p>;
  }

  return (
    <GuestShell rail={<Wordmark />} mainClass="book private">
      {load.status !== 'loading' && (
        <h1 className="heading-xl" tabIndex={-1} ref={heading}>
          {MOVE_WHOLE.heading}
        </h1>
      )}
      <p className="back">
        <TextLink href={`/manage/${encodeURIComponent(reference)}`}>{MOVE_WHOLE.back}</TextLink>
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
              readFailed={!facts && factsFailed}
              label={MOVE_WHOLE.dateQuestion}
            />
            <div className="book-rest private-choices">
              <div className="private-status" role="status">
                {message}
              </div>
              {date && listing === 'ok' && shown.length > 0 && (
                <PairCards saunas={shown} booking={b} saunaId={saunaId} windowId={windowId} onChoose={choosePair} />
              )}
            </div>
          </div>
          {ready && (
            <ConfirmingStep
              heading={MOVE_WHOLE.summaryHeading}
              rows={[
                { label: MOVE_WHOLE.from, value: when(b.sauna?.name ?? '', b.window.date, b.window) },
                { label: MOVE_WHOLE.to, value: when(sauna.name, date, target) },
                { label: MOVE_WHOLE.price, value: MOVE_WHOLE.unchanged(nok(b.total_ore)) },
              ]}
              confirmLabel={MOVE_WHOLE.confirm}
              onConfirm={confirm}
              busy={busy}
            >
              <p className="move-note">{MOVE_WHOLE.nothingYet}</p>
            </ConfirmingStep>
          )}
        </>
      )}
    </GuestShell>
  );
}
