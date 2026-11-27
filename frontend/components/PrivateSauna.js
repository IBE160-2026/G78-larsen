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
// - Story 5.2: the rail's "Continue booking" (as on Book seats) writes the chosen pair to the draft `draft:whole`
//   (`{date, window_id, sauna_id, sauna_name, whole_price_ore}`, lib/draft.js), opens the browser session the booking
//   needs (AD-8; viewing the page opens none) and goes to the shared Details. Without a date or a pair it shows an
//   Error summary instead. The page reads `?date=` (Review's "Choose another sauna or session" and Details' Back come
//   here with the date) and otherwise the draft's date; a pair kept in the draft is chosen again only while the
//   listing still offers it. After a payment the draft is `{reference}` only, and this page then starts a new one.
import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useRef, useState } from 'react';
import DateCalendar from './DateCalendar';
import ErrorSummary from './ErrorSummary';
import GuestShell from './GuestShell';
import Notice from './Notice';
import PrimaryButton from './PrimaryButton';
import Wordmark from './Wordmark';
import TextLink from './TextLink';
import { ApiError, api } from '@/lib/api';
import { BOOK, PRIVATE } from '@/lib/copy';
import { SAUNA_COPY, SAUNA_IMAGE_SIZE } from '@/lib/sauna-copy';
import { clockTime, dotted, longDate, monthOf, parseDotted } from '@/lib/dates';
import { WHOLE_SLOT, paidReference, readDraft, replaceDraft, writeDraft } from '@/lib/draft';
import { FLOWS } from '@/lib/flows';
import { holds, nok } from '@/lib/venue-format';

const BY_SAUNA = 'sauna';
const BY_SESSION = 'session';
const ISO = /^\d{4}-\d{2}-\d{2}$/;

function focusFirst(selector, fallbackId) {
  const radios = Array.from(document.querySelectorAll(selector));
  const target = radios.find((r) => r.checked) || radios[0] || document.getElementById(fallbackId);
  if (target) target.focus();
}

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

/** "13:00–14:30" and its spoken form "13:00 to 14:30", with "Already started" when it has. Shared with the Private
 * sauna move step (Story 5.3). */
export function sessionText(w) {
  const start = clockTime(w.start);
  const end = clockTime(w.end);
  return { shown: `${start}–${end}`, spoken: `${start} to ${end}${w.already_started ? `, ${BOOK.alreadyStarted}` : ''}` };
}

/** A Sauna's photo, name, size, price and description (Lisa 2026-11-25, proposal H). The photo is decorative here:
 * the name and the description say what the Guest needs, and the alt texts are on Landing. Shared with the Private
 * sauna move step (Story 5.3). */
export function SaunaHead({ sauna }) {
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
  const router = useRouter();
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
  const [pending, setPending] = useState(null); // {saunaId, windowId}: a pair from the draft, chosen once listed
  const [showErrors, setShowErrors] = useState(false);
  const [focusKey, setFocusKey] = useState(0);
  const continuing = useRef(false);

  // The date from `?date=` or the draft, and the draft's pair (UX-DR26). Read in an effect: no `window` on the server.
  useEffect(() => {
    if (paidReference(readDraft(WHOLE_SLOT))) replaceDraft({}, WHOLE_SLOT);
    const draft = readDraft(WHOLE_SLOT);
    let fromQuery = null;
    try {
      fromQuery = new URLSearchParams(window.location.search).get('date');
    } catch {
      fromQuery = null;
    }
    const draftDate = typeof draft.date === 'string' && ISO.test(draft.date) ? draft.date : null;
    const d = fromQuery && ISO.test(fromQuery) ? fromQuery : draftDate;
    if (!d) return;
    setDate(d);
    setText(dotted(d));
    setMonth(monthOf(d));
    setStatus('loading');
    if (d === draftDate && Number.isInteger(draft.sauna_id) && Number.isInteger(draft.window_id)) {
      setPending({ saunaId: draft.sauna_id, windowId: draft.window_id });
    }
  }, []);

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

  // A pair kept in the draft is chosen again once the listing shows it is still offered.
  useEffect(() => {
    if (status !== 'ok' || !pending) return;
    const s = saunas.find((x) => x.id === pending.saunaId);
    if (s && s.windows.some((w) => w.id === pending.windowId)) {
      setSaunaId(s.id);
      setWindowId(pending.windowId);
    }
    setPending(null);
  }, [status, pending, saunas]);

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
    setPending(null);
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

  const chosen = sauna && windowId != null ? sauna.windows.find((w) => w.id === windowId) || null : null;
  const dateFieldError = dateError || (showErrors && !date ? BOOK.chooseDate : null);
  const pairError = showErrors && date && !chosen ? PRIVATE.choosePair : null;
  const errors = [
    dateFieldError && showErrors ? { key: 'date', text: dateFieldError, href: '#date' } : null,
    pairError ? { key: 'pair', text: pairError, href: '#saunas' } : null,
  ].filter(Boolean);

  const onSummaryChoose = (key) => {
    if (key === 'date') document.getElementById('date')?.focus();
    else if (view === BY_SESSION && windowId == null) focusFirst('#sessions input[type=radio]', 'sessions');
    else focusFirst('#saunas input[type=radio]', 'saunas');
  };

  // "Continue booking": the pair goes to the draft, the browser gets its session (AD-8), and Details opens.
  const onContinue = async () => {
    if (continuing.current) return;
    if (!date || dateError || !chosen) {
      setShowErrors(true);
      setFocusKey((k) => k + 1);
      return;
    }
    continuing.current = true;
    writeDraft({ date, window_id: chosen.id, sauna_id: sauna.id, sauna_name: sauna.name,
      whole_price_ore: sauna.whole_price_ore }, WHOLE_SLOT);
    await api('/api/session', { method: 'POST', body: {} }).catch(() => {}); // Review opens one again if needed
    router.push(FLOWS.whole.details);
    continuing.current = false;
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
    <div className="rail-book">
      <PrimaryButton onClick={onContinue}>{PRIVATE.continue}</PrimaryButton>
      <Wordmark />
      <p className="rail-note rail-links">
        <TextLink href="/terms">Terms</TextLink>
        <TextLink href="/privacy">Privacy notice</TextLink>
      </p>
    </div>
  );

  return (
    <GuestShell rail={rail} mainClass="book private">
      <h1 className="heading-xl" tabIndex={-1}>
        {PRIVATE.heading}
      </h1>
      <p className="private-lead">{PRIVATE.lead}</p>
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
