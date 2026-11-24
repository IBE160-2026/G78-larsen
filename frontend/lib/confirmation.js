// The paying browser's Confirmation, read by Review before it navigates, so Confirmation's "Booking confirmed" h1
// is on the page from its first render. Without it the page first shows only the rail's Wordmark while it reads,
// and NVDA reads that and misses the focus that reaches the h1 a moment later (manual NVDA pass, 2026-11-24).
// Kept in memory only, for this tab and the one reference; a reload or another browser reads it from the API.
let held = null;

/** Keep the confirmation body of `reference` for Confirmation's first render. */
export function holdConfirmation(reference, body) {
  held = { reference, body };
}

/** The held confirmation body of `reference`, or null. Not consumed: React Strict Mode renders twice. */
export function heldConfirmation(reference) {
  return held && held.reference === reference ? held.body : null;
}
