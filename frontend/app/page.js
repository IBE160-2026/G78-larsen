// Landing stub (Lisa, 2026-11-20): until Story 1.3 builds Landing, `/` is the Wordmark as h1 and Text links to
// Terms and the Privacy notice. It makes no API call. Story 1.3 replaces this file.
import GuestShell from '@/components/GuestShell';
import TextLink from '@/components/TextLink';
import Wordmark from '@/components/Wordmark';

// Landing is just "Saunalöyly" (EXPERIENCE.md, Page titles).
export const metadata = { title: { absolute: 'Saunalöyly' } };

export default function Landing() {
  return (
    <GuestShell rail={<Wordmark heading />}>
      <ul className="stub-links">
        <li>
          <TextLink href="/terms">Terms</TextLink>
        </li>
        <li>
          <TextLink href="/privacy">Privacy notice</TextLink>
        </li>
      </ul>
    </GuestShell>
  );
}
