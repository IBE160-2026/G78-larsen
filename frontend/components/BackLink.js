'use client';

// "Back" on Terms and the Privacy notice (Lisa 2026-11-25, EXPERIENCE.md): under the h1, as Back on Details and Review.
// It is a real link to Landing (a Text link, so focus moves as after any site link): it works without JavaScript and
// when the page was opened directly (a bookmark, a new tab, a link in an email). When the Guest came from another page
// of the site, a click goes back in the browser history instead, so Details or Review comes back from the draft with
// everything entered (FR-5, UX-DR26).
//
// "Came from the site": with the Navigation API, the history entry before this one is a site page (`entries()` holds
// only this origin's entries next to the current one). Without it: a client navigation in this document
// (lib/nav.js) or a full load whose referrer is this origin.
import { useRouter } from 'next/navigation';
import TextLink from './TextLink';
import { LEGAL_PAGE } from '@/lib/copy';
import { hadClientNavigation } from '@/lib/nav';

function cameFromSite() {
  try {
    const nav = window.navigation;
    if (nav && nav.currentEntry && typeof nav.entries === 'function') {
      return nav.currentEntry.index > 0 && nav.entries().some((e) => e.index === nav.currentEntry.index - 1);
    }
    if (hadClientNavigation()) return true;
    return Boolean(document.referrer) && new URL(document.referrer).origin === window.location.origin;
  } catch {
    return false;
  }
}

export default function BackLink() {
  const router = useRouter();
  const onClick = (e) => {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    if (!cameFromSite()) return; // the link itself goes to Landing
    e.preventDefault();
    router.back();
  };
  return (
    <TextLink href="/" onClick={onClick}>
      {LEGAL_PAGE.back}
    </TextLink>
  );
}
