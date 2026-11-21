// Text link (UX-DR6): always underlined, never colour alone. Site paths use Next's client navigation, so the
// FocusMover runs; other origins are plain links (following one is the Guest's choice, not a page request).
// `onClick` runs before the navigation (Review's Book seats link starts a new draft with it).
import Link from 'next/link';

export default function TextLink({ href, children, onClick }) {
  if (href.startsWith('/')) {
    return (
      <Link className="text-link" href={href} onClick={onClick}>
        {children}
      </Link>
    );
  }
  return (
    <a className="text-link" href={href} onClick={onClick}>
      {children}
    </a>
  );
}
