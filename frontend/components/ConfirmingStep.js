'use client';

// Confirming step (AD-9, AD-29; shared with Epic 5): states what a Change will do and changes nothing until the
// Guest confirms. Created in Story 4.1 and first used by the Changes of Story 4.2; 4.1 renders it nowhere.
//
// - `heading`: what the step is about; `rows`: the Booking summary rows of the outcome.
// - `confirmLabel` and `onConfirm`: the one Primary button; `busy` disables it while the request runs.
// - `children`: a Notice or anything else between the summary and the button.
import { useId } from 'react';
import BookingSummary from './BookingSummary';
import PrimaryButton from './PrimaryButton';

export default function ConfirmingStep({ heading, rows = [], confirmLabel, onConfirm, busy = false, children }) {
  const headingId = useId();
  return (
    <section className="confirming-step" aria-labelledby={headingId}>
      <h2 className="heading-md" id={headingId} tabIndex={-1}>
        {heading}
      </h2>
      {rows.length > 0 && <BookingSummary rows={rows} />}
      {children}
      <PrimaryButton onClick={onConfirm} disabled={busy}>
        {confirmLabel}
      </PrimaryButton>
    </section>
  );
}
