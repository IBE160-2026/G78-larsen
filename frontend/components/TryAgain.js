// The error page body: the "please try again" Notice in the Guest shell (UX-DR29). Shared by app/error.js and
// app/global-error.js; it sets its own <title> (AD-17).
import GuestShell from './GuestShell';
import Notice from './Notice';
import TextLink from './TextLink';
import Wordmark from './Wordmark';

export default function TryAgain() {
  return (
    <GuestShell rail={<Wordmark />}>
      <title>{'Something went wrong – Saunalöyly'}</title>
      <div className="col page-text">
        <h1 className="heading-xl" tabIndex={-1}>
          Something went wrong
        </h1>
        <Notice />
        <p className="after-heading">
          <TextLink href="/">Go to the Saunalöyly start page</TextLink>
        </p>
      </div>
    </GuestShell>
  );
}
