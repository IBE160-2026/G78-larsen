'use client';

// Date calendar (FR-2, UX-DR9, UX-DR17, UX-DR34): question 1. The date can be typed (dd.mm.yyyy) or picked, and the
// field and the grid stay in step. A typed date is checked on blur or Enter: a malformed one gets "Enter the date as
// dd.mm.yyyy", one that cannot be booked "This date cannot be booked. Pick a day below." as a Field error, focus
// stays and the calendar is unchanged. Only the API's `dates` (a Window inside the horizon and before its deadline)
// are radios; other days are plain numbers. The grid is one radio group named "Pick a day, <Month> <Year>", one
// tab stop with arrow keys, days with full names. It ends at `horizon_end` with "Booking opens 4 weeks ahead."
// "Next month" and, once forward, "Previous month" move the month. No clock is read here: today and the horizon
// come from the API (AD-4). The move step (Story 4.2) passes its own `label` ("2. Choose a date").
import { useEffect, useRef } from 'react';
import FieldError from './FieldError';
import Notice from './Notice';
import { BOOK } from '@/lib/copy';
import {
  WEEKDAYS_SHORT, addMonths, compareMonths, daysInMonth, fullDate, horizonPhrase, isoDate, monthLabel, monthOf,
  weekdayIndex,
} from '@/lib/dates';

function MonthGrid({ month, today, horizonEnd, bookable, date, onPick }) {
  const first = isoDate(month.year, month.month, 1);
  const lead = weekdayIndex(first);
  const cells = [];
  for (let i = 0; i < lead; i += 1) cells.push(<span key={`lead-${i}`} className="cal-empty" aria-hidden="true" />);
  for (let day = 1; day <= daysInMonth(month.year, month.month); day += 1) {
    const iso = isoDate(month.year, month.month, day);
    if (iso > horizonEnd) break; // the calendar ends at the horizon
    if (bookable.has(iso)) {
      cells.push(
        <label key={iso} className="cal-day">
          <input
            type="radio"
            name="day"
            value={iso}
            checked={date === iso}
            aria-label={fullDate(iso)}
            onChange={() => onPick(iso)}
          />
          <span>{day}</span>
        </label>,
      );
    } else {
      cells.push(
        <span key={iso} className={iso < today ? 'cal-no cal-past' : 'cal-no'}>
          {day}
        </span>,
      );
    }
  }
  return (
    <div className="cal-grid" role="radiogroup" aria-label={BOOK.pickADay(monthLabel(month))}>
      {cells}
    </div>
  );
}

export default function DateCalendar({
  facts, date, month, onMonth, text, onText, onCommitText, onPick, error, readFailed, label = BOOK.dateQuestion,
}) {
  // A month button that disappears after its press (Next on the second-to-last month, Previous on the second)
  // hands keyboard focus to the other month button, so focus never drops to the page body.
  const prevRef = useRef(null);
  const nextRef = useRef(null);
  const focusAfter = useRef(null);
  const shownKey = month ? `${month.year}-${month.month}` : '';
  useEffect(() => {
    const target = focusAfter.current === 'prev' ? prevRef.current : focusAfter.current === 'next' ? nextRef.current
      : null;
    focusAfter.current = null;
    if (target) target.focus();
  }, [shownKey]);

  const describedBy = ['date-hint', error ? 'date-error' : null].filter(Boolean).join(' ');
  let calendar = null;
  if (facts) {
    const first = monthOf(facts.today);
    const last = monthOf(facts.horizon_end);
    const shown = compareMonths(month, first) < 0 || compareMonths(month, last) > 0 ? first : month;
    const bookable = new Set(facts.dates);
    calendar = (
      <>
        <div className="cal-head">
          <span className="cal-month">{monthLabel(shown)}</span>
          <span className="cal-nav">
            {compareMonths(shown, first) > 0 && (
              <button
                type="button"
                className="link-button"
                ref={prevRef}
                onClick={() => {
                  const to = addMonths(shown, -1);
                  if (compareMonths(to, first) === 0) focusAfter.current = 'next';
                  onMonth(to);
                }}
              >
                {BOOK.previousMonth}
              </button>
            )}
            {compareMonths(shown, last) < 0 && (
              <button
                type="button"
                className="link-button"
                ref={nextRef}
                onClick={() => {
                  const to = addMonths(shown, 1);
                  if (compareMonths(to, last) === 0) focusAfter.current = 'prev';
                  onMonth(to);
                }}
              >
                {BOOK.nextMonth}
              </button>
            )}
          </span>
        </div>
        <div className="cal-weekdays" aria-hidden="true">
          {WEEKDAYS_SHORT.map((d) => (
            <span key={d}>{d}</span>
          ))}
        </div>
        <MonthGrid
          month={shown}
          today={facts.today}
          horizonEnd={facts.horizon_end}
          bookable={bookable}
          date={date}
          onPick={onPick}
        />
        {compareMonths(shown, last) === 0 && (
          <p className="cal-end">{BOOK.horizonLine(horizonPhrase(facts.horizon_days))}</p>
        )}
      </>
    );
  }
  return (
    <div className="question question-date">
      <label className="q" htmlFor="date">
        {label}
      </label>
      <input
        className="text-field"
        id="date"
        type="text"
        inputMode="numeric"
        autoComplete="off"
        value={text}
        aria-describedby={describedBy}
        aria-invalid={error ? true : undefined}
        onChange={(e) => onText(e.target.value)}
        onBlur={() => onCommitText()}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            onCommitText();
          }
        }}
      />
      <span className="hint" id="date-hint">
        {BOOK.dateHint}
      </span>
      <FieldError id="date-error">{error}</FieldError>
      {readFailed && <Notice>{BOOK.sessionsUnavailable}</Notice>}
      {calendar}
    </div>
  );
}
