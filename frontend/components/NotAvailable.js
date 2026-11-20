// "This page is not available." with a link to Landing (UX-DR29). Used by app/not-found.js, and by any client
// page after an API 404, so both look the same (FR-20). It sets its own <title>, because `metadata` works only
// in Server Components (AD-17).
import GuestShell from './GuestShell';
import TextLink from './TextLink';
import Wordmark from './Wordmark';

export const NOT_AVAILABLE = 'This page is not available.';

export default function NotAvailable() {
  return (
    <GuestShell rail={<Wordmark />}>
      <title>{'This page is not available – Saunalöyly'}</title>
      <div className="col page-text">
        <h1 className="heading-xl" tabIndex={-1}>
          {NOT_AVAILABLE}
        </h1>
        <p className="after-heading">
          <TextLink href="/">Go to the Saunalöyly start page</TextLink>
        </p>
      </div>
    </GuestShell>
  );
}
