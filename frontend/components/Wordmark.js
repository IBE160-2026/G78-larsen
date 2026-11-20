// Wordmark (UX-DR7): "Saunalöyly" as typeset text. On Landing it is the page's one h1 (the focus target);
// everywhere else it is a link to Landing.
import Link from 'next/link';

export default function Wordmark({ heading = false }) {
  if (heading) {
    return (
      <h1 className="wordmark" tabIndex={-1}>
        Saunalöyly
      </h1>
    );
  }
  return (
    <Link className="wordmark" href="/">
      Saunalöyly
    </Link>
  );
}
