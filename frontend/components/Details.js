'use client';

// Details (FR-5, UX-DR9/12/23/26/33): "Your details", Back, the name and email Text fields, the Privacy notice link
// and "Continue booking", with only the Wordmark in the rail.
//
// - Two flows share this page (`flow`, lib/flows.js, Story 5.2): the Seat flow (`/book-seats/details`, draft
//   `draft:seats`) and the Private sauna flow (`/private-sauna/details`, draft `draft:whole`). Back goes to the flow's
//   first page and Continue to its Review.
// - The draft is read only in effects. Without a chosen session (and, for a Private sauna, a Sauna) this page goes to
//   the flow's first page; after a payment (a `{reference}`-only draft) it replaces itself with Confirmation, so it can
//   never lead to a second payment.
// - What the Guest types is written to the draft at once, so Back, the browser's back button and a visit to the
//   Privacy notice keep it.
// - Empty or invalid fields give an Error summary and Field errors, with the input kept. The server checks again
//   (FR-18).
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import ErrorSummary from './ErrorSummary';
import FieldError from './FieldError';
import GuestShell from './GuestShell';
import PrimaryButton from './PrimaryButton';
import TextLink from './TextLink';
import Wordmark from './Wordmark';
import { DETAILS } from '@/lib/copy';
import { paidReference, readDraft, writeDraft } from '@/lib/draft';
import { flowOf } from '@/lib/flows';

const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

/** The Field error of each field for the values given, or null. The server's rules (FR-5). */
export function detailErrors(name, email) {
  const n = name.trim();
  const e = email.trim();
  return {
    name: n.length < 1 || n.length > 100 ? DETAILS.enterName : null,
    email: e.length > 254 || !EMAIL.test(e) ? DETAILS.enterEmail : null,
  };
}

export default function Details({ flow: flowName = 'seats' }) {
  const flow = flowOf(flowName);
  const router = useRouter();
  const [back, setBack] = useState(flow.start());
  const [ready, setReady] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [showErrors, setShowErrors] = useState(false);
  const [focusKey, setFocusKey] = useState(0);

  useEffect(() => {
    const draft = readDraft(flow.slot);
    const paid = paidReference(draft);
    if (paid) {
      router.replace(`/confirmation/${paid}`);
      return;
    }
    if (!flow.chosen(draft)) {
      router.replace(flow.start(draft));
      return;
    }
    if (typeof draft.name === 'string') setName(draft.name);
    if (typeof draft.email === 'string') setEmail(draft.email);
    setBack(flow.start(draft));
    setReady(true);
  }, [router, flow]);

  const change = (field, value) => {
    if (field === 'name') setName(value);
    else setEmail(value);
    writeDraft({ [field]: value }, flow.slot);
  };

  const errors = detailErrors(name, email);
  const summary = showErrors
    ? [
        errors.name ? { key: 'name', text: errors.name, href: '#name' } : null,
        errors.email ? { key: 'email', text: errors.email, href: '#email' } : null,
      ].filter(Boolean)
    : [];

  const onSubmit = (event) => {
    event.preventDefault();
    if (errors.name || errors.email) {
      setShowErrors(true);
      setFocusKey((k) => k + 1);
      return;
    }
    writeDraft({ name: name.trim(), email: email.trim() }, flow.slot);
    router.push(flow.review);
  };

  const field = (id, label, value, type, autoComplete, maxLength, error) => (
    <div className="form-field">
      <label className="field-label" htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        className="text-field"
        type={type}
        value={value}
        autoComplete={autoComplete}
        maxLength={maxLength}
        spellCheck={false}
        onChange={(e) => change(id, e.target.value)}
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
      />
      <FieldError id={`${id}-error`}>{error}</FieldError>
    </div>
  );

  return (
    <GuestShell rail={<Wordmark />}>
      <div className="col">
        <h1 className="heading-xl" tabIndex={-1}>
          {DETAILS.heading}
        </h1>
        <p className="back">
          <TextLink href={back}>{DETAILS.back}</TextLink>
        </p>
        {ready && (
          <form noValidate onSubmit={onSubmit}>
            {summary.length > 0 && (
              <ErrorSummary errors={summary} focusKey={focusKey} onChoose={(key) => document.getElementById(key)?.focus()} />
            )}
            {field('name', DETAILS.name, name, 'text', 'name', 100, showErrors ? errors.name : null)}
            {field('email', DETAILS.email, email, 'email', 'email', 254, showErrors ? errors.email : null)}
            <p className="privacy-link">
              <TextLink href="/privacy">Privacy notice</TextLink>
            </p>
            <div className="form-actions">
              <PrimaryButton type="submit">{DETAILS.continue}</PrimaryButton>
            </div>
          </form>
        )}
      </div>
    </GuestShell>
  );
}
