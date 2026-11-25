// Whether this document has made a client navigation between site pages (Terms and Privacy notice Back, Lisa
// 2026-11-25). FocusMover, which is on every page, notes each one; the count lives in the module, so a full load
// starts again at zero. Used only where the browser lacks the Navigation API (see components/BackLink.js).
let clientNavigations = 0;

export function noteClientNavigation() {
  clientNavigations += 1;
}

export function hadClientNavigation() {
  return clientNavigations > 0;
}
