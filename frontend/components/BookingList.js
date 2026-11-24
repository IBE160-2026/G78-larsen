'use client';

// The Booking list of one day (FR-16, UX-DR31, UX-DR37): a date Text field with "Previous day" and "Next day", then
// one Session group per session in time order.
//
// - The day lives in the address (`/admin/bookings?date=yyyy-mm-dd`), so reload and Back keep it. Without `?date`
//   the API answers for its own `today`; the browser clock is never read (AD-4, AD-16).
// - "Previous day" and "Next day" are real Text links to the neighbouring dates. The date field commits on Enter or
//   blur and replaces the address; a malformed date shows the Field error "Enter the date as dd.mm.yyyy".
// - Each group: the time in session-time-selected (named "Session 10:00 to 11:30") and the figures on one line in
//   tabular figures, with "No bookings" on that same line when the session is empty; otherwise the Booking table. A session with no Seats left has the unavailable header with
//   "Seats left 0" and "Sold out" in weight 600, so the state is said in words.
// - Each Booking shows its status (Active or Cancelled; a cancelled one takes no Seats) and, under its row, one line
//   per entry of its Change history: "Moved 1 seat on 24.11.2026 14:05 from 01.12.2026 10:00–11:30 to
//   01.12.2026 11:30–13:00 · new booking ABCD1234" (Story 4.2, Lisa 2026-11-24), or "Gave up 1 seat on 24.11.2026
//   14:05 for a voucher of NOK 250" (never the code). A cancelled Booking's Status is "Cancelled 24.11.2026 14:05 ·
//   Guest · Voucher" (Story 4.3, Lisa 2026-11-24).
// - Stored text (name, email) is rendered as React text, never as HTML (IV-5).
// - A 401 goes to Sign-in; any other failure shows the "please try again" Notice.
import { useRouter, useSearchParams } from 'next/navigation';
import { Fragment, useEffect, useState } from 'react';
import { SIGN_IN_PATH } from './AdminBar';
import FieldError from './FieldError';
import Notice from './Notice';
import TextLink from './TextLink';
import { ApiError, api } from '@/lib/api';
import { BOOK, BOOKING_LIST } from '@/lib/copy';
import { addDays, clockTime, dotted, dottedTime, parseDotted } from '@/lib/dates';
import { nok } from '@/lib/venue-format';

export const BOOKINGS_PATH = '/admin/bookings';
const ISO = /^\d{4}-\d{2}-\d{2}$/;
const C = BOOKING_LIST.columns;

const dayHref = (iso) => `${BOOKINGS_PATH}?date=${iso}`;
const COLUMNS = 7;

/** "01.12.2026 10:00–11:30" of a Window `{start, end}` in Venue time. */
const sessionText = (w) => `${dottedTime(w.start)}–${clockTime(w.end)}`;

/** One history line of a Booking: a move (Story 4.2) or a Voucher Change (Story 4.3). */
function historyLine(entry) {
  if (entry.action === 'voucher') {
    return BOOKING_LIST.gaveUp(entry.seats, dottedTime(entry.at), nok(entry.voucher_value_ore));
  }
  const line = BOOKING_LIST.moved(entry.seats, dottedTime(entry.at), sessionText(entry.from_window),
    sessionText(entry.to_window));
  return entry.new_reference ? line + BOOKING_LIST.newBooking(entry.new_reference) : line;
}

/** The Status cell: "Active", or "Cancelled 24.11.2026 14:05 · Guest · Voucher" (Story 4.3). */
function statusText(b) {
  if (b.status === 'cancelled' && b.cancelled_at) {
    return BOOKING_LIST.cancelledAt(dottedTime(b.cancelled_at), BOOKING_LIST.cause[b.cancel_cause],
      BOOKING_LIST.remedy[b.cancel_remedy]);
  }
  return BOOKING_LIST.status[b.status] ?? b.status;
}

function SessionGroup({ session }) {
  const start = clockTime(session.start);
  const end = clockTime(session.end);
  const full = session.seats_left <= 0;
  return (
    <section className={full ? 'session-group session-group-full' : 'session-group'}>
      <div className="session-group-header">
        <h2 className="session-group-time tabular" aria-label={BOOKING_LIST.session(start, end)}>
          {start}–{end}
        </h2>
        <p className="session-group-figures tabular">
          <span>{BOOKING_LIST.seatCapacity(session.seat_capacity)}</span>
          <span aria-hidden="true"> · </span>
          <span>{BOOKING_LIST.seatsBooked(session.seats_booked)}</span>
          <span aria-hidden="true"> · </span>
          {full ? (
            <>
              <strong>{BOOKING_LIST.seatsLeft(session.seats_left)}</strong>
              <span aria-hidden="true"> · </span>
              <strong>{BOOKING_LIST.soldOut}</strong>
            </>
          ) : (
            <span>{BOOKING_LIST.seatsLeft(session.seats_left)}</span>
          )}
        </p>
        {session.bookings.length === 0 && <p className="session-group-none">{BOOKING_LIST.noBookings}</p>}
      </div>
      {session.bookings.length > 0 && (
        <table className="booking-table">
          <caption className="visually-hidden">{BOOKING_LIST.caption(start, end)}</caption>
          <colgroup>
            <col className="col-reference" />
            <col className="col-name" />
            <col />
            <col className="col-seats" />
            <col className="col-total" />
            <col className="col-time" />
            <col className="col-status" />
          </colgroup>
          <thead>
            <tr>
              <th scope="col">{C.reference}</th>
              <th scope="col">{C.name}</th>
              <th scope="col">{C.email}</th>
              <th scope="col" className="num">
                {C.seats}
              </th>
              <th scope="col" className="num">
                {C.total}
              </th>
              <th scope="col" className="num">
                {C.time}
              </th>
              <th scope="col">{C.status}</th>
            </tr>
          </thead>
          <tbody>
            {session.bookings.map((b) => (
              <Fragment key={b.reference}>
                <tr className="booking-row">
                  <td className="tabular">{b.reference}</td>
                  <td>{b.name}</td>
                  <td>{b.email}</td>
                  <td className="num">{b.seats}</td>
                  <td className="num">{nok(b.total_ore)}</td>
                  <td className="num">{dottedTime(b.created_at)}</td>
                  <td>{statusText(b)}</td>
                </tr>
                {(b.history || []).map((entry, i) => (
                  <tr className="booking-history" key={i}>
                    <td colSpan={COLUMNS} className="tabular">
                      {historyLine(entry)}
                    </td>
                  </tr>
                ))}
              </Fragment>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

export default function BookingList() {
  const router = useRouter();
  const params = useSearchParams();
  const raw = params.get('date');
  // a malformed address, or a date that does not exist (2026-02-30), shows the API's today
  const asked = raw && ISO.test(raw) && parseDotted(dotted(raw)) === raw ? raw : null;
  const [result, setResult] = useState({ status: 'loading', data: null });
  const [text, setText] = useState(asked ? dotted(asked) : '');
  const [error, setError] = useState(null);

  useEffect(() => {
    let live = true;
    // the previous day's sessions never stay on screen under the new address
    setResult({ status: 'loading', data: null });
    if (asked) {
      setText(dotted(asked));
      setError(null);
    }
    api(asked ? `/api/admin/bookings?date=${asked}` : '/api/admin/bookings')
      .then((data) => {
        if (!live) return;
        setResult({ status: 'ok', data });
        setText(dotted(data.date));
        setError(null);
      })
      .catch((err) => {
        if (!live) return;
        if (err instanceof ApiError && err.status === 401) {
          router.replace(SIGN_IN_PATH);
          return;
        }
        setResult({ status: 'failed', data: null });
      });
    return () => {
      live = false;
    };
  }, [asked, router]);

  const shown = asked || (result.data && result.data.date);

  const commit = () => {
    const iso = parseDotted(text);
    if (!iso) {
      setError(BOOK.dateFormat);
      return;
    }
    setError(null);
    setText(dotted(iso));
    if (iso !== shown) router.replace(dayHref(iso));
  };

  return (
    <>
      {shown && (
        <div className="date-bar">
          <div className="date-bar-field">
            <label className="field-label" htmlFor="date">
              {BOOKING_LIST.date}
            </label>
            <input
              className="text-field"
              id="date"
              type="text"
              inputMode="numeric"
              autoComplete="off"
              value={text}
              aria-describedby={error ? 'date-error' : undefined}
              aria-invalid={error ? true : undefined}
              onChange={(e) => setText(e.target.value)}
              onBlur={commit}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  commit();
                }
              }}
            />
            <FieldError id="date-error">{error}</FieldError>
          </div>
          <p className="date-bar-links">
            <TextLink href={dayHref(addDays(shown, -1))}>{BOOKING_LIST.previousDay}</TextLink>
            <TextLink href={dayHref(addDays(shown, 1))}>{BOOKING_LIST.nextDay}</TextLink>
          </p>
        </div>
      )}
      {result.status === 'failed' && <Notice>{BOOKING_LIST.failed}</Notice>}
      {result.data && result.data.windows.length === 0 && (
        <p className="session-groups-none">{BOOKING_LIST.noSessions}</p>
      )}
      {result.data && result.data.windows.length > 0 && (
        <div className="session-groups">
          {result.data.windows.map((w) => (
            <SessionGroup key={w.id} session={w} />
          ))}
        </div>
      )}
    </>
  );
}
