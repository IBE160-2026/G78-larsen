// Email as sent (UX-DR14, FR-8, AD-12): the stored email, labelled "Sent by email:", with its line breaks kept. It
// shows the Outbox row the action wrote, never a rebuilt email, and only as text.
import { CONFIRMATION } from '@/lib/copy';

export default function EmailAsSent({ email, index = 0 }) {
  const id = `sent-by-email-${index}`;
  return (
    <section className="email-as-sent" aria-labelledby={id}>
      <h2 className="reference-label" id={id}>
        {CONFIRMATION.sentByEmail}
      </h2>
      <div className="email-body">{email.body}</div>
    </section>
  );
}
