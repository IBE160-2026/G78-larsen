'use client';

// Private sauna (FR-29, FR-30, UX-DR41, Story 5.1): a date, then the Saunas that can be booked whole that day with
// their free sessions. The Guest always picks the Sauna.
//
// - The calendar facts (`today`, `horizon_end`, `horizon_days`, `dates`) come from `GET /api/windows` with no date;
//   the pairs from `GET /api/private-saunas?date=`. No clock is read here (AD-4), and no session is opened (AD-8).
// - Both views are built from the one listing response by regrouping only (AD-24). "Show by sauna" (chosen first,
//   proposal H, Lisa 2026-11-25) shows one card per Sauna (photo, name, size, price, description) with its free
//   sessions as buttons: one click chooses the Sauna and the session. "Show by session" (proposal K) shows the
//   sessions as buttons with how many Saunas are free in each, then the Saunas free in the chosen one as cards.
// - Each choice is a radio group in a fieldset with a legend, one tab stop with arrow keys inside; a radio's
//   accessible name says what its button shows, and a card's description is its accessible description. The
//   photos are decorative here (alt=""); their alt texts are on Landing. An empty date says so plainly, with no
//   urgency cue (NFR-9).
// - The loading line, the failed-read Notice and the empty-date sentence sit in one polite live region (`role="status"`, as the
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
import { SAUNA_COPY, SAUNA_IMAGE_SIZE } from '@/lib/sauna-copy';
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

/** "13:00–14:30" and its spoken form "13:00 to 14:30", with "Already started" when it has. */
function sessionText(w) {
  const start = clockTime(w.start);
  const end = clockTime(w.end);
  return { shown: `${start}–${end}`, spoken: `${start} to ${end}${w.already_started ? `, ${BOOK.alreadyStarted}` : ''}` };
}

/** A Sauna's photo, name, size, price and description (Lisa 2026-11-25, proposal H). The photo is decorative here:
 * the name and the description say what the Guest needs, and the alt texts are on Landing. */
function SaunaHead({ sauna }) {
  const copy = SAUNA_COPY[sauna.id];
  return (
    <>
      {copy && (
        <img
          className="private-card-image"
          src={copy.image}
          alt=""
          width={SAUNA_IMAGE_SIZE.width}
          height={SAUNA_IMAGE_SIZE.height}
        />
      )}
      <span className="private-card-top">
        <span className="private-card-name" id={`sauna-name-${sauna.id}`}>
          {sauna.name} <span className="private-card-size">· {holds(sauna.capacity)}</span>
        </span>
        <span className="private-card-price tabular">{nok(sauna.whole_price_ore)}</span>
      </span>
      {copy?.description && (
        <span className="private-card-text" id={`sauna-text-${sauna.id}`}>
          {copy.description}
        </span>
      )}
    </>
  );
}

// "Show by sauna" (proposal H): one card per Sauna with its free sessions as buttons. One radio group for the whole
// listing, so one click chooses the Sauna and the session, with one tab stop and arrow keys inside.
function SaunaCards({ saunas, saunaId, windowId, onChoose }) {
  return (
    <fieldset className="question question-pairs" id="saunas">
      <legend className="q">{PRIVATE.bySaunaQuestion}</legend>
      <div className="private-cards">
        {saunas.map((s) => (
          <div
            key={s.id}
            className="private-card"
            role="group"
            aria-labelledby={`sauna-name-${s.id}`}
            aria-describedby={SAUNA_COPY[s.id]?.description ? `sauna-text-${s.id}` : undefined}
          >
            <SaunaHead sauna={s} />
            <span className="slot-grid">
              {s.windows.map((w) => {
                const t = sessionText(w);
                return (
                  <label key={w.id} className="cell slot">
                    <input
                      type="radio"
                      name="pair"
                      id={`pair-${s.id}-${w.id}`}
                      value={`${s.id}-${w.id}`}
                      checked={saunaId === s.id && windowId === w.id}
                      aria-label={`${s.name}, ${t.spoken}`}
                      onChange={() => onChoose(s.id, w.id)}
                    />
                    <span aria-hidden="true">
                      {t.shown}
                      {w.already_started && <small>{BOOK.alreadyStarted}</small>}
                    </span>
                  </label>
                );
              })}
            </span>
          </div>
        ))}
      </div>
    </fieldset>
  );
}

// "Show by session" (proposal K): the sessions as buttons with how many Saunas are free in each, then the Saunas
// free in the chosen session as cards to choose from.
function SessionThenSauna({ sessions, saunas, windowId, saunaId, onWindow, onSauna }) {
  const freeIn = (id) => saunas.filter((s) => s.windows.some((w) => w.id === id));
  return (
    <fieldset className="question question-pairs" id="by-session">
      <legend className="q">{PRIVATE.bySessionQuestion}</legend>
      <fieldset className="question" id="sessions">
        <legend className="q-sub">{PRIVATE.sessionLegend}</legend>
        <span className="slot-grid">
          {sessions.map((w) => {
            const t = sessionText(w);
            const free = PRIVATE.saunasFree(freeIn(w.id).length);
            return (
              <label key={w.id} className="cell slot">
                <input
                  type="radio"
                  name="session"
                  id={`session-${w.id}`}
                  value={w.id}
                  checked={windowId === w.id}
                  aria-label={`${t.spoken}, ${free}`}
                  onChange={() => onWindow(w.id)}
                />
                <span aria-hidden="true">
                  {t.shown}
                  <small>{w.already_started ? BOOK.alreadyStarted : free}</small>
                </span>
              </label>
            );
          })}
        </span>
      </fieldset>
      {windowId != null && (
        <fieldset className="question question-saunas" id="saunas">
          <legend className="q-sub">{PRIVATE.saunaLegend}</legend>
          <div className="private-cards">
            {freeIn(windowId).map((s) => (
              <label key={s.id} className="private-card private-pick">
                <input
                  type="radio"
                  name="sauna"
                  id={`sauna-${s.id}`}
                  value={s.id}
                  checked={saunaId === s.id}
                  aria-label={`${s.name}, ${holds(s.capacity)}, ${nok(s.whole_price_ore)}`}
                  aria-describedby={SAUNA_COPY[s.id]?.description ? `sauna-text-${s.id}` : undefined}
                  onChange={() => onSauna(s.id)}
                />
                <SaunaHead sauna={s} />
              </label>
            ))}
          </div>
        </fieldset>
      )}
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
  const [factsReload, setFactsReload] = useState(0);

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
  }, [factsReload]);

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
          // the date has left the horizon (the page was open across Venue midnight): the date question asks again,
          // and the calendar reads its dates again, so it no longer offers the day that has left
          setDateError(BOOK.dateNotBookable);
          setFactsReload((k) => k + 1);
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

  const choosePair = (sid, wid) => {
    setSaunaId(sid);
    setWindowId(wid);
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

  // `message` sits in the polite live region; the choices do not, so a screen reader hears the loading line, the
  // Notice or the empty-date sentence, not every card and session button of the listing.
  let message = null;
  let result = null;
  if (date && status === 'loading') {
    message = <p className="loading">{BOOK.loadingSessions}</p>;
  } else if (date && status === 'failed') {
    message = <Notice>{BOOK.sessionsUnavailable}</Notice>;
  } else if (date && status === 'ok' && saunas.length === 0) {
    message = <p className="private-empty">{PRIVATE.noSauna(longDate(date))}</p>;
  } else if (date && status === 'ok') {
    result = (
      <>
        <ViewPicker view={view} onChange={chooseView} />
        {view === BY_SAUNA ? (
          <SaunaCards saunas={saunas} saunaId={saunaId} windowId={windowId} onChoose={choosePair} />
        ) : (
          <SessionThenSauna
            sessions={sessions}
            saunas={saunas}
            windowId={windowId}
            saunaId={saunaId}
            onWindow={chooseWindow}
            onSauna={setSaunaId}
          />
        )}
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
        <div className="book-rest private-choices">
          <div className="private-status" role="status">
            {message}
          </div>
          {result}
        </div>
      </div>
    </GuestShell>
  );
}
