'use client';

// Session list (FR-3, UX-DR19, UX-DR35): a fieldset with every Window of the chosen date in time order, unavailable
// ones included, so the schedule is visible. Each row is a label around its radio, so the whole row is the target.
// The radio's accessible name carries the Seats left text ("13:00 to 14:30, 12 seats left"); the visible text is
// aria-hidden, so a screen reader in browse mode reads each row once (manual NVDA pass, 2026-11-24). A row with too few
// Seats is a disabled radio that says why; a started Window says "Already started". No price, no Sauna and no
// urgency cue (FR-3, FR-4, NFR-9). The Notices of question 3 (cleared choice, no room, read failed) sit above the
// rows.
import FieldError from './FieldError';
import NearestSessions from './NearestSessions';
import Notice from './Notice';
import { BOOK } from '@/lib/copy';
import { clockTime, horizonPhrase, weekdayName } from '@/lib/dates';

/** The row's Seats-left text and whether it can be chosen for `seats` (any number when none is chosen yet). */
export function availability(w, seats) {
  if (w.seats_left <= 0) return { text: BOOK.soldOut, open: false };
  if (seats && w.seats_left < seats) return { text: BOOK.notEnough(w.seats_left, seats), open: false };
  return { text: BOOK.seatsLeft(w.seats_left), open: true };
}

function Rows({ windows, seats, windowId, onChoose }) {
  return (
    <div className="session-rows">
      {windows.map((w) => {
        const { text, open } = availability(w, seats);
        const start = clockTime(w.start);
        const end = clockTime(w.end);
        const started = w.already_started ? `, ${BOOK.alreadyStarted}` : '';
        const selected = windowId === w.id;
        const cls = ['session-row', selected ? 'selected' : '', open ? '' : 'unavailable'].filter(Boolean).join(' ');
        return (
          <label key={w.id} className={cls}>
            <input
              type="radio"
              name="session"
              id={`session-${w.id}`}
              value={w.id}
              checked={selected}
              disabled={!open}
              aria-label={`${start} to ${end}, ${text}${started}`}
              onChange={() => onChoose(w.id)}
            />
            {/* The radio's name says all of this; hidden from assistive technology so browse mode reads it once. */}
            <span className="session-time" aria-hidden="true">
              {start}–{end}
            </span>
            <span className="session-left" aria-hidden="true">
              {text}
            </span>
            {w.already_started && (
              <span className="session-started" aria-hidden="true">
                {BOOK.alreadyStarted}
              </span>
            )}
          </label>
        );
      })}
    </div>
  );
}

export default function SessionList({
  date, seats, status, windows, nearest, horizonDays, windowId, onChoose, onChooseNearest, clearedNotice, error,
}) {
  let body = null;
  if (date && status === 'loading') {
    body = <p className="loading">{BOOK.loadingSessions}</p>;
  } else if (date && status === 'failed') {
    body = <Notice>{BOOK.sessionsUnavailable}</Notice>;
  } else if (date) {
    body = (
      <>
        {clearedNotice && <Notice>{clearedNotice}</Notice>}
        {nearest && nearest.length > 0 && (
          <div className="notice" role="status">
            <p>{BOOK.noRoomOnDate(seats, weekdayName(date))}</p>
            <NearestSessions sessions={nearest} onChoose={onChooseNearest} />
          </div>
        )}
        {nearest && nearest.length === 0 && (
          <Notice>{BOOK.noRoomInHorizon(seats, horizonPhrase(horizonDays))}</Notice>
        )}
        <Rows windows={windows} seats={seats} windowId={windowId} onChoose={onChoose} />
      </>
    );
  }
  return (
    <fieldset
      className="question question-sessions"
      id="sessions"
      tabIndex={-1}
      aria-describedby={error ? 'sessions-error' : undefined}
    >
      <legend className="q">{BOOK.sessionQuestion}</legend>
      <FieldError id="sessions-error">{error}</FieldError>
      {body}
    </fieldset>
  );
}
