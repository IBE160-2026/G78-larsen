'use client';

// Details (FR-5, UX-DR9/12/23/26/33): "Your details", Back, the name and email Text fields, the Privacy notice link
// and "Continue booking", with only the Wordmark in the rail.
//
// - The draft (`draft:seats`) is read only in effects. Without a chosen session this page goes to Book seats; after a
//   payment (a `{reference}`-only draft) it replaces itself with Confirmation, so it can never lead to a second payment.
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

export const REVIEW_PATH = '/book-seats/review';
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

export default function Details() {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [showErrors, setShowErrors] = useState(false);
  const [focusKey, setFocusKey] = useState(0);

  useEffect(() => {
    const draft = readDraft();
    const paid = paidReference(draft);
    if (paid) {
      router.replace(`/confirmation/${paid}`);
      return;
    }
    if (!Number.isInteger(draft.window_id) || !draft.date || !draft.seats) {
      router.replace('/book-seats');
      return;
    }
    if (typeof draft.name === 'string') setName(draft.name);
    if (typeof draft.email === 'string') setEmail(draft.email);
    setReady(true);
  }, [router]);

  const change = (field, value) => {
    if (field === 'name') setName(value);
    else setEmail(value);
    writeDraft({ [field]: value });
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
    writeDraft({ name: name.trim(), email: email.trim() });
    router.push(REVIEW_PATH);
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
          <TextLink href="/book-seats">{DETAILS.back}</TextLink>
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
