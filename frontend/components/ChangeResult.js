// Change result (AD-29; shared with Epic 5): the emails a Change sent, each under "Sent by email:" as stored
// (EmailAsSent). Created in Story 4.1 and first used by the Changes of Story 4.2.
import EmailAsSent from './EmailAsSent';

export default function ChangeResult({ emails = [], children }) {
  return (
    <>
      {children}
      {emails.map((email, i) => (
        <EmailAsSent key={email.id ?? i} index={i} email={email} />
      ))}
    </>
  );
}
