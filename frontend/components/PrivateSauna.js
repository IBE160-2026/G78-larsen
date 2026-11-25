'use client';

// Private sauna (FR-29, FR-30, UX-DR41, Story 5.1): a date, then the Saunas that can be booked whole that day with
// their free sessions. The Guest always picks the Sauna.
//
// - The calendar facts (`today`, `horizon_end`, `horizon_days`, `dates`) come from `GET /api/windows` with no date;
//   the pairs from `GET /api/private-saunas?date=`. No clock is read here (AD-4), and no session is opened (AD-8).
// - Both views are built from the one listing response by regrouping only (AD-24): "Show by sauna" (chosen first)
//   asks for the Sauna, then one of its free sessions; "Show by session" asks for the session, then a Sauna free in
//   it. The second group appears once the first is answered and lists only what is free with that choice.
// - Each choice is a radio group in a fieldset with its question as legend, one tab stop with arrow keys inside.
//   The rows reuse the Session row look; a Sauna option shows its name, "Holds 7", its price and its free sessions,
//   and the radio's accessible name says all of it (the visible text is hidden from assistive technology, as in the
//   Session list). An empty date says so plainly, with no urgency cue (NFR-9).
// - The loading line, the result and the empty-date sentence sit in one polite live region (`role="status"`, as the
//   Notices of Book seats), so a screen reader hears them. A date the API refuses as outside the horizon gets the
//   date's Field error; after a failed read, picking the same date again reads it again.
// - Booking and paying for the chosen pair is Story 5.2.
import { useEffect, useMemo, useState } from 'react';
import DateCalendar from './DateCalendar';
import GuestShell from './GuestShell';
import Notice from './Notice';
import Wordmark from './Wordmark';
import TextLink from './TextLink';
import { ApiError, api } from '@/lib/api';
import { BOOK, PRIVATE } from '@/lib/copy';
import { clockTime, dotted, longDate, monthOf, parseDotted } from '@/lib/dates';
import { holds, nok } from '@/lib/venue-format';

const BY_SAUNA = 'sauna';
const BY_SESSION = 'session';

/** Every free session of the listing once, in time order. */
function sessionsOf(saunas) {
  const byId = new Map();
  for (const s of saunas) for (const w of s.windows) if (!byId.has(w.id)) byId.set(w.id, w);
  return Array.from(byId.values()).sort((a, b) => (a.start < b.start ? -1 : a.start > b.start ? 1 : 0));
}

function ViewPicker({ view, onChange }) {
  return (
    <fieldset className="question" id="view">
      <legend className="q">{PRIVATE.view}</legend>
      <div className="view-picker">
        {[
          [BY_SAUNA, PRIVATE.bySauna],
          [BY_SESSION, PRIVATE.bySession],
        ].map(([value, text]) => (
          <label key={value} className="cell">
            <input
              type="radio"
              name="view"
              id={`view-${value}`}
              value={value}
              checked={view === value}
              onChange={() => onChange(value)}
            />
            <span>{text}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function SaunaOptions({ legend, saunas, saunaId, onChoose }) {
  return (
    <fieldset className="question question-saunas" id="saunas">
      <legend className="q">{legend}</legend>
      <div className="session-rows">
        {saunas.map((s) => {
          const size = holds(s.capacity);
          const price = nok(s.whole_price_ore);
          const free = PRIVATE.freeSessions(s.windows.length);
          const selected = saunaId === s.id;
          return (
            <label key={s.id} className={selected ? 'session-row sauna-option selected' : 'session-row sauna-option'}>
              <input
                type="radio"
                name="sauna"
                id={`sauna-${s.id}`}
                value={s.id}
                checked={selected}
                aria-label={`${s.name}, ${size}, ${price}, ${free}`}
                onChange={() => onChoose(s.id)}
              />
              <span className="session-time" aria-hidden="true">
                {s.name}
              </span>
              <span aria-hidden="true">{size}</span>
              <span className="tabular" aria-hidden="true">
                {price}
              </span>
              <span className="sauna-free" aria-hidden="true">
                {free}
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

function SessionOptions({ legend, sessions, windowId, onChoose }) {
  return (
    <fieldset className="question question-sessions" id="sessions">
      <legend className="q">{legend}</legend>
      <div className="session-rows">
        {sessions.map((w) => {
          const start = clockTime(w.start);
          const end = clockTime(w.end);
          const started = w.already_started ? `, ${BOOK.alreadyStarted}` : '';
          const selected = windowId === w.id;
          return (
            <label key={w.id} className={selected ? 'session-row selected' : 'session-row'}>
              <input
                type="radio"
                name="session"
                id={`session-${w.id}`}
                value={w.id}
                checked={selected}
                aria-label={`${start} to ${end}${started}`}
                onChange={() => onChoose(w.id)}
              />
              <span className="session-time" aria-hidden="true">
                {start}–{end}
              </span>
              <span aria-hidden="true" />
              {w.already_started && (
                <span className="session-started" aria-hidden="true">
                  {BOOK.alreadyStarted}
                </span>
              )}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

export default function PrivateSauna() {
  const [facts, setFacts] = useState(null); // {today, horizon_end, horizon_days, dates}
  const [factsFailed, setFactsFailed] = useState(false);
  const [date, setDate] = useState(null);
  const [text, setText] = useState('');
  const [dateError, setDateError] = useState(null);
  const [month, setMonth] = useState(null);
  const [status, setStatus] = useState('idle');
  const [saunas, setSaunas] = useState([]);
  const [view, setView] = useState(BY_SAUNA);
  const [saunaId, setSaunaId] = useState(null);
  const [windowId, setWindowId] = useState(null);
  const [reload, setReload] = useState(0);

  // The calendar facts: the bookable dates and the horizon, from the server (AD-4).
  useEffect(() => {
    const controller = new AbortController();
    api('/api/windows', { signal: controller.signal })
      .then((body) => {
        setFacts({ today: body.today, horizon_end: body.horizon_end, horizon_days: body.horizon_days,
          dates: body.dates });
      })
      .catch(() => {
        if (!controller.signal.aborted) setFactsFailed(true);
      });
    return () => controller.abort();
  }, []);

  // The pairs of the chosen date.
  useEffect(() => {
    if (!date) return undefined;
    const controller = new AbortController();
    setStatus('loading');
    api(`/api/private-saunas?date=${date}`, { signal: controller.signal })
      .then((body) => {
        if (controller.signal.aborted) return;
        setSaunas(body.saunas || []);
        setStatus('ok');
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && err.code === 'outside_horizon') {
          // the date has left the horizon: the date question asks again
          setDateError(BOOK.dateNotBookable);
          setDate(null);
          setStatus('idle');
          return;
        }
        setStatus('failed');
      });
    return () => controller.abort();
  }, [date, reload]);

  const sessions = useMemo(() => sessionsOf(saunas), [saunas]);
  const sauna = saunas.find((s) => s.id === saunaId) || null;

  const pickDate = (iso) => {
    setDateError(null);
    setText(dotted(iso));
    setMonth(monthOf(iso));
    if (iso === date) {
      if (status === 'failed') setReload((k) => k + 1); // read the same date again
      return;
    }
    setDate(iso);
    setStatus('loading');
    setSaunas([]);
    setSaunaId(null);
    setWindowId(null);
  };

  const commitText = () => {
    const typed = text.trim();
    if (!typed) {
      setDateError(null);
      setDate(null);
      setStatus('idle');
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

  const chooseSauna = (id) => {
    setSaunaId(id);
    const s = saunas.find((x) => x.id === id);
    if (view === BY_SAUNA && windowId != null && !(s && s.windows.some((w) => w.id === windowId))) {
      setWindowId(null);
    }
  };

  const chooseWindow = (id) => {
    setWindowId(id);
    if (view === BY_SESSION && saunaId != null && !(sauna && sauna.windows.some((w) => w.id === id))) {
      setSaunaId(null);
    }
  };

  // Switching the view keeps a complete choice; otherwise only the new view's first question keeps its answer.
  const chooseView = (v) => {
    setView(v);
    if (saunaId != null && windowId != null) return;
    if (v === BY_SAUNA) setWindowId(null);
    else setSaunaId(null);
  };

  let result = null;
  if (date && status === 'loading') {
    result = <p className="loading">{BOOK.loadingSessions}</p>;
  } else if (date && status === 'failed') {
    result = <Notice>{BOOK.sessionsUnavailable}</Notice>;
  } else if (date && status === 'ok' && saunas.length === 0) {
    result = <p className="private-empty">{PRIVATE.noSauna(longDate(date))}</p>;
  } else if (date && status === 'ok') {
    const second = view === BY_SAUNA
      ? sauna && (
        <SessionOptions
          legend={PRIVATE.sessionQuestion(3)}
          sessions={sauna.windows}
          windowId={windowId}
          onChoose={chooseWindow}
        />
      )
      : windowId != null && (
        <SaunaOptions
          legend={PRIVATE.saunaQuestion(3)}
          saunas={saunas.filter((s) => s.windows.some((w) => w.id === windowId))}
          saunaId={saunaId}
          onChoose={chooseSauna}
        />
      );
    result = (
      <>
        <ViewPicker view={view} onChange={chooseView} />
        {view === BY_SAUNA ? (
          <SaunaOptions legend={PRIVATE.saunaQuestion(2)} saunas={saunas} saunaId={saunaId} onChoose={chooseSauna} />
        ) : (
          <SessionOptions
            legend={PRIVATE.sessionQuestion(2)}
            sessions={sessions}
            windowId={windowId}
            onChoose={chooseWindow}
          />
        )}
        {second}
      </>
    );
  }

  const rail = (
    <>
      <Wordmark />
      <p className="rail-note rail-links">
        <TextLink href="/terms">Terms</TextLink>
        <TextLink href="/privacy">Privacy notice</TextLink>
      </p>
    </>
  );

  return (
    <GuestShell rail={rail} mainClass="book private">
      <h1 className="heading-xl" tabIndex={-1}>
        {PRIVATE.heading}
      </h1>
      <p className="private-lead">{PRIVATE.lead}</p>
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
          readFailed={factsFailed}
          label={PRIVATE.dateQuestion}
        />
        <div className="book-rest private-choices" role="status">
          {result}
        </div>
      </div>
    </GuestShell>
  );
}
