// Email as sent (UX-DR14, FR-8, AD-12): the stored email with its line breaks kept, only as text. It shows the
// Outbox row the action wrote, never a rebuilt email.
//
// - By default (Confirmation) the block is labelled "Sent by email:".
// - The Outbox entry (UX-DR32) passes its own `heading` (the subject), header `lines` (time and recipient) shown in
//   `label` between the heading and the body, an `id` for the heading and a `className` for its spacing. The body
//   block is the same, so the two never drift.
import { CONFIRMATION } from '@/lib/copy';

export default function EmailAsSent({
  email,
  index = 0,
  id = `sent-by-email-${index}`,
  heading = CONFIRMATION.sentByEmail,
  lines = [],
  className,
}) {
  return (
    <section className={className ? `email-as-sent ${className}` : 'email-as-sent'} aria-labelledby={id}>
      <h2 className="reference-label" id={id}>
        {heading}
      </h2>
      {lines.map((line, i) => (
        <p className="reference-label" key={i}>
          {line}
        </p>
      ))}
      <div className="email-body">{email.body}</div>
    </section>
  );
}
