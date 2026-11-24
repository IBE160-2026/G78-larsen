'use client';

// Manage booking (FR-25, AD-28, UX-DR33): the Booking a Manage link opened, read with this browser's session from
// `GET /api/manage/{reference}`. Loading changes nothing (the read only touches the grant). The page shows the
// reference, date, session, Seats and total paid, then, before the Cutoff, until when the Booking can be changed, and
// after it the approved reason. Times come from the API in Venue time (`cutoff_at`); the browser clock decides
// nothing (AD-4). No grant, an idle or expired grant and an unknown reference are all a 404: "This page is not
// available." (FR-20). Before the Cutoff an active Booking offers its Changes: "Move seats" (Story 4.2) and "Give up
// seats for a voucher" (Story 4.3). A cancelled Booking (all Seats given up) shows its reference, date, session and
// the Seats given up, when it was cancelled, and no Changes (Lisa, 2026-11-24, EXPERIENCE.md Open Item 19).
// The two Changes are links shown as primary buttons, side by side (Lisa, 2026-11-24).
//
// As on Confirmation, the h1 appears only once the read has answered, so a browser without a grant never sees it
// before "This page is not available."; FocusMover focuses it after the navigation from `/manage`.
import { useEffect, useRef, useState } from 'react';
import GuestShell from './GuestShell';
import ManageBookingSummary from './ManageBookingSummary';
import NotAvailable from './NotAvailable';
import Notice from './Notice';
import Link from 'next/link';
import Wordmark from './Wordmark';
import { ApiError, api } from '@/lib/api';
import { MANAGE } from '@/lib/copy';
import { clockTime, longDate } from '@/lib/dates';

export default function ManageBooking({ reference }) {
  const [state, setState] = useState({ status: 'loading' });
  const heading = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    api(`/api/manage/${encodeURIComponent(reference)}`, { signal: controller.signal })
      .then((booking) => {
        if (!controller.signal.aborted) setState({ status: 'ok', booking });
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setState({ status: err instanceof ApiError && err.status === 404 ? 'not_available' : 'failed' });
      });
    return () => controller.abort();
  }, [reference]);

  // A direct load (a reload) gets no focus move from FocusMover; the heading takes focus when nothing else has it.
  useEffect(() => {
    const el = document.activeElement;
    if (state.status !== 'loading' && heading.current && (!el || el === document.body)) heading.current.focus();
  }, [state.status]);

  if (state.status === 'not_available') return <NotAvailable />;

  const b = state.booking;
  const cutoffDate = b ? longDate(b.cutoff_at.slice(0, 10)) : '';
  const cutoffTime = b ? clockTime(b.cutoff_at) : '';
  return (
    <GuestShell rail={<Wordmark />}>
      <div className="col">
        {state.status !== 'loading' && (
          <h1 className="heading-xl" tabIndex={-1} ref={heading}>
            {MANAGE.heading}
          </h1>
        )}
        {state.status === 'failed' && <Notice>{MANAGE.loadFailed}</Notice>}
        {b && b.status === 'cancelled' && (
          <>
            <ManageBookingSummary booking={b} />
            {b.cancelled_at && (
              <p className="manage-cancelled">
                {MANAGE.cancelled(longDate(b.cancelled_at.slice(0, 10)), clockTime(b.cancelled_at))}
              </p>
            )}
          </>
        )}
        {b && b.status !== 'cancelled' && (
          <>
            <ManageBookingSummary booking={b} />
            {b.change_allowed ? (
              <>
                <p className="manage-until">{MANAGE.untilText(cutoffDate, cutoffTime)}</p>
                {b.status === 'active' && (
                  <ul className="manage-changes">
                    <li>
                      <Link className="button-primary" href={`/manage/${encodeURIComponent(b.reference)}/move`}>
                        {MANAGE.moveSeats}
                      </Link>
                    </li>
                    <li>
                      <Link className="button-primary" href={`/manage/${encodeURIComponent(b.reference)}/voucher`}>
                        {MANAGE.giveUpSeats}
                      </Link>
                    </li>
                  </ul>
                )}
              </>
            ) : (
              <Notice>{MANAGE.cutoffPassed(cutoffDate, cutoffTime)}</Notice>
            )}
          </>
        )}
      </div>
    </GuestShell>
  );
}
