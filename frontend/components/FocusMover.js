'use client';

// The one client component that moves focus and keeps the "Error: " title prefix (AD-17, UX-DR33).
//
// - First document load: focus moves only when the URL fragment names an existing element, and then to it.
// - After each client navigation: to the fragment's element if it exists, otherwise to the page's h1.
// - Each client navigation is noted in lib/nav.js (Back on Terms and the Privacy notice).
// - Targets carry tabindex="-1"; a fragment target without one gets it here.
// - While an Error summary ([data-error-summary]) is on the page, the title starts with "Error: ".
import { usePathname } from 'next/navigation';
import { useEffect, useRef } from 'react';
import { noteClientNavigation } from '@/lib/nav';

const PREFIX = 'Error: ';

function fragmentTarget() {
  const id = window.location.hash.slice(1);
  if (!id) return null;
  try {
    return document.getElementById(decodeURIComponent(id));
  } catch {
    return null;
  }
}

function focus(el) {
  if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1');
  el.focus();
}

function syncTitle() {
  const bare = document.title.startsWith(PREFIX) ? document.title.slice(PREFIX.length) : document.title;
  const wanted = document.querySelector('[data-error-summary]') ? PREFIX + bare : bare;
  if (document.title !== wanted) document.title = wanted;
}

export default function FocusMover() {
  const pathname = usePathname();
  // The last pathname handled: an effect that reruns for the same pathname (React Strict Mode in `next dev`)
  // does nothing, so the first load is never treated as a navigation.
  const handled = useRef(null);

  useEffect(() => {
    syncTitle();
    if (handled.current === pathname) return;
    const firstLoad = handled.current === null;
    handled.current = pathname;
    const target = fragmentTarget();
    if (firstLoad) {
      if (target) focus(target);
      return;
    }
    noteClientNavigation(); // for Back on Terms and the Privacy notice (components/BackLink.js)
    const heading = target || document.querySelector('h1');
    if (heading) {
      focus(heading);
      return;
    }
    // A page that renders its h1 later (an Administrator page waits for its guard): focus the h1 when it appears,
    // unless something else has taken focus by then. Given up after 10 s. No effect cleanup: the observer ends itself
    // (a rerun for the same pathname in Strict Mode returns above without starting another).
    const observer = new MutationObserver(() => {
      const h1 = document.querySelector('h1');
      if (!h1) return;
      observer.disconnect();
      const active = document.activeElement;
      if (!active || active === document.body || active === document.documentElement) focus(h1);
    });
    observer.observe(document.body, { childList: true, subtree: true });
    setTimeout(() => observer.disconnect(), 10000);
  }, [pathname]);

  useEffect(() => {
    const observer = new MutationObserver(syncTitle);
    observer.observe(document.documentElement, { childList: true, subtree: true, characterData: true });
    return () => observer.disconnect();
  }, []);

  return null;
}
