---
title: 'Back link on Terms and Privacy notice'
type: 'feature'
created: '2026-11-25'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Terms (`/terms`) and the Privacy notice (`/privacy`) have no Back link. A Guest who opens them from Details or Review in either booking flow (or from Landing or the rail) can only return with the browser's own back button.

**Approach:** Add a "Back" Text link under the h1 of both pages, placed and styled as Back on Details and Review. When the Guest reached the page from another page of the site, it goes back in the browser history, so Details or Review is restored from the draft in `sessionStorage` with everything entered. When the page was opened directly (bookmark, new tab, link in an email), it goes to Landing (`/`). It is a real link to `/`, so it works without JavaScript. Record the decision in EXPERIENCE.md (Lisa, 2026-11-25). e2e tests: back to Review with everything kept, and to Landing when opened directly.

</frozen-after-approval>

## Implementation Notes

- The Terms and Privacy pages are server components; the history decision needs a small client component (`components/BackLink.js`): an `<a class="text-link" href="/">Back</a>` whose click, only when the page was reached by an in-site navigation, calls `router.back()` instead.
- "Reached in-site": Next's client navigation does not update `document.referrer`, so a same-origin `document.referrer` alone is not enough. The component records whether the current page was entered by a client navigation (a flag set by a navigation from another site page) or by a full load with a same-origin referrer.
- `tests/e2e/test_fr22_terms_privacy_a11y.py` compares the page text with `mockups/key-terms.html` and `key-privacy.html` verbatim and fixes the tab order and the list of site links; the mockups get the same Back line, and the tab-order and link lists gain Back.
- Built: `frontend/components/BackLink.js` (`next/link` to `/`, so the Landing fallback is a client navigation and focus moves as after any site link; a plain left click from a site page calls `router.back()`), `frontend/lib/nav.js` (count of client navigations, noted by `FocusMover`), Back in `app/terms/page.js` and `app/privacy/page.js` under the h1 (`p.back`, as Details/Review), the Back line in `mockups/key-terms.html` and `key-privacy.html`, EXPERIENCE.md ("Back" fixed-copy row and the Terms/Privacy layout row).
- "Came from the site" uses the Navigation API where it exists (the previous history entry is one of this origin's), else a client navigation in this document or a same-origin `document.referrer`. Known limit of the fallback only: the signal covers the whole document, so once any client navigation has happened, Back goes back in history even when the page was reached with the browser's own back or forward button.
- Tests: `tests/e2e/test_fr22_terms_privacy_a11y.py` — Back in both tab orders, Back followed from a direct open lands on Landing with focus on its h1, Review → Terms → Privacy notice → Back → Back returns to Review with Seats, name, email and key kept, and without JavaScript Back is a link to `/`. 32 passed; the other e2e modules that visit Terms or Privacy (fr01, fr05, fr21, fr23 ×2, stack routing) 79 passed; `npm --prefix frontend run build` ok.
- Review fixes: Back text from `lib/copy.js` (`LEGAL_PAGE.back`); `BackLink` renders `TextLink`; the mockups' intro lines describe Back; the round-trip test checks focus on Review's h1; a new test removes `window.navigation` and checks the fallback (direct open → Landing, Terms → Privacy notice → Back → Terms). `test_fr22` 33 passed; build ok.

## Review Triage Log

| # | Finding | Verdict | Route | Evidence |
|---|---|---|---|---|
| 1 | Fallback without the Navigation API is never tested | medium | patch | Chromium has `window.navigation`; Firefox/Safari users get the untested branch. Test added with `window.navigation` removed. |
| 2 | No round trip from Details or the Private sauna flow | low | reject | Same mechanism as the Review round trip (history back + draft); Details round trip via history is already in `test_fr05`. |
| 3 | Round trip does not check focus after Back | low | patch | One assertion; FocusMover moves focus to h1 on the pathname change. |
| 4 | Previous same-origin entry may be an Administrator page or the same path | low | reject | Going back to where the tab came from is the intended behaviour; no fragment-only links lead to Terms/Privacy. |
| 5 | Fallback signal is per document, not per page | low | patch | Real; fix is the wording of the known limit in Implementation Notes. |
| 6 | "Back" hard-coded in the pages | low | patch | Other Back links use `lib/copy.js`; moved to `LEGAL_PAGE.back`. |
| 7 | `BackLink` duplicates `TextLink` | low | patch | `TextLink` takes `onClick`; now reused. |
| 8 | Spec front matter out of date | false | reject | Status is set when the spec is finalized (this step). |
| 9 | Mockup intro lines describe the old behaviour | low | patch | Intro lines now describe Back. |
| 10 | No-JS test does not check class or placement | low | reject | Markup is the same server-rendered `p.back` + Text link; placement is covered by the tab-order and mockup-text tests. |
