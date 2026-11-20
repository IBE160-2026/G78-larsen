// Text link (UX-DR6): always underlined, never colour alone. Site paths use Next's client navigation, so the
// FocusMover runs; other origins are plain links (following one is the Guest's choice, not a page request).
import Link from 'next/link';

export default function TextLink({ href, children }) {
  if (href.startsWith('/')) {
    return (
      <Link className="text-link" href={href}>
        {children}
      </Link>
    );
  }
  return (
    <a className="text-link" href={href}>
      {children}
    </a>
  );
}
