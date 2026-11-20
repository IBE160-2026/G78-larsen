// Nearest sessions (UX-DR13, FR-3): up to three Text links inside a Notice, each with the date, time and Seats
// left, each its own tab stop. Not radios, because choosing one changes the page (WCAG 3.2.2). `onChoose` gets the
// chosen Window ({id, date, start, end, seats_left}).
import { BOOK } from '@/lib/copy';
import { clockTime, dayAndMonth } from '@/lib/dates';

export default function NearestSessions({ sessions, onChoose }) {
  return (
    <ul className="nearest">
      {sessions.map((s) => (
        <li key={s.id}>
          <a
            className="text-link"
            href={`#session-${s.id}`}
            onClick={(event) => {
              event.preventDefault();
              onChoose(s);
            }}
          >
            {dayAndMonth(s.date)}, {clockTime(s.start)}–{clockTime(s.end)}, {BOOK.seatsLeft(s.seats_left)}
          </a>
        </li>
      ))}
    </ul>
  );
}
