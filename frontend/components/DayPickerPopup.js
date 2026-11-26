'use client';

// "Choose from calendar" on the Booking list (FR-16, FR-23; spec-booking-list-date-picker): a toggle button that
// opens a pop-up month calendar under the date field. Every day of every month can be picked, past and future, so
// "Previous month" and "Next month" are never bounded. No clock is read (AD-4): the pop-up opens on the month of the
// date shown, which the Booking list takes from the address or the API.
//
// - The toggle states `aria-expanded`; the pop-up is a group named "Pick a day, November 2026"; each day is a button
//   named with its full date ("14 November 2026"), the shown one with `aria-current="date"` and the selected look.
// - On open, focus goes to the shown day; if the shown date changes while it is open (a typed date committed by the
//   click on the toggle), the calendar moves to the new month and focus to the new day. The month line is a polite
//   live region, so "Previous month" and "Next month" are announced.
// - Escape (wherever focus is) closes and returns focus to the toggle; a press outside the toggle and pop-up, or Tab
//   out of them, closes it. A pick closes it, returns focus to the toggle and hands the date to `onPick`.
// - Modelled on the guest Date calendar's markup and `cal-*` classes, but separate: that one is radio-based and ends
//   at the booking horizon.
import { useEffect, useId, useRef, useState } from 'react';
import { BOOK, BOOKING_LIST } from '@/lib/copy';
import {
  WEEKDAYS_SHORT, addMonths, daysInMonth, fullDate, isoDate, monthLabel, monthOf, weekdayIndex,
} from '@/lib/dates';

export default function DayPickerPopup({ date, onPick }) {
  const [open, setOpen] = useState(false);
  const [month, setMonth] = useState(() => monthOf(date));
  const rootRef = useRef(null);
  const toggleRef = useRef(null);
  const popRef = useRef(null);
  const popId = useId();
  const wantFocus = useRef(false); // focus the shown day once it is rendered

  // a new date on screen (a typed date, Previous/Next day) puts the calendar back on its month
  useEffect(() => {
    setMonth(monthOf(date));
    if (open) wantFocus.current = true;
    // only a new date moves the month here; `open` is read, not watched (the toggle sets the month on open)
  }, [date]);

  const close = (refocus) => {
    setOpen(false);
    if (refocus && toggleRef.current) toggleRef.current.focus();
  };

  // on open (and after a new date while open), focus the shown day as soon as its month is on screen
  useEffect(() => {
    if (!wantFocus.current || !open || !popRef.current) return;
    const target = popRef.current.querySelector('[aria-current="date"]');
    if (target) {
      wantFocus.current = false;
      target.focus();
    }
  });

  // a press outside the toggle and the pop-up closes it
  useEffect(() => {
    if (!open) return undefined;
    const onDown = (e) => {
      if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false);
    };
    // Escape wherever focus is: a mouse click on a month button does not focus it in every browser
    const onKey = (e) => {
      if (e.key !== 'Escape') return;
      e.preventDefault();
      setOpen(false);
      if (toggleRef.current) toggleRef.current.focus();
    };
    document.addEventListener('pointerdown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('pointerdown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  // Tab (or Shift+Tab) out of the toggle and pop-up closes it; a click on a blank part of the pop-up does not
  const onBlur = (e) => {
    if (open && e.relatedTarget && rootRef.current && !rootRef.current.contains(e.relatedTarget)) setOpen(false);
  };

  const pick = (iso) => {
    close(true);
    onPick(iso);
  };

  const label = monthLabel(month);
  const cells = [];
  const first = isoDate(month.year, month.month, 1);
  for (let i = 0; i < weekdayIndex(first); i += 1) {
    cells.push(<span key={`lead-${i}`} className="cal-empty" aria-hidden="true" />);
  }
  for (let day = 1; day <= daysInMonth(month.year, month.month); day += 1) {
    const iso = isoDate(month.year, month.month, day);
    const current = iso === date;
    cells.push(
      <button
        key={iso}
        type="button"
        className={current ? 'cal-pick cal-pick-current' : 'cal-pick'}
        aria-label={fullDate(iso)}
        aria-current={current ? 'date' : undefined}
        onClick={() => pick(iso)}
      >
        {day}
      </button>,
    );
  }

  return (
    <div className="date-pick" ref={rootRef} onBlur={onBlur}>
      <button
        type="button"
        className="link-button date-pick-toggle"
        ref={toggleRef}
        aria-expanded={open}
        aria-controls={open ? popId : undefined}
        onClick={() => {
          if (open) {
            setOpen(false);
          } else {
            setMonth(monthOf(date));
            wantFocus.current = true;
            setOpen(true);
          }
        }}
      >
        {BOOKING_LIST.chooseFromCalendar}
      </button>
      {open && (
        <div className="date-pop" id={popId} ref={popRef} role="group" aria-label={BOOK.pickADay(label)}>
          <div className="cal-head">
            <span className="cal-month" aria-live="polite">{label}</span>
            <span className="cal-nav">
              <button type="button" className="link-button" onClick={() => setMonth(addMonths(month, -1))}>
                {BOOK.previousMonth}
              </button>
              <button type="button" className="link-button" onClick={() => setMonth(addMonths(month, 1))}>
                {BOOK.nextMonth}
              </button>
            </span>
          </div>
          <div className="cal-weekdays" aria-hidden="true">
            {WEEKDAYS_SHORT.map((d) => (
              <span key={d}>{d}</span>
            ))}
          </div>
          <div className="cal-grid">{cells}</div>
        </div>
      )}
    </div>
  );
}
