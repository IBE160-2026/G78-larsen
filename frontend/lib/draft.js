// The Booking draft (AD-9, UX-DR26): `sessionStorage` key `draft:seats`, so the Guest's choices survive a reload in
// the same tab and disappear with the tab. Story 1.4 stores `{date, seats, window_id}`; Story 1.5 adds name, email
// and the idempotency key. Call these only inside effects: `sessionStorage` does not exist while rendering on the
// server. Storage that is unavailable or full is ignored, so the page still works without a draft.
const KEY = 'draft:seats';

/** @returns {object} the stored draft, or an empty object */
export function readDraft() {
  try {
    const raw = window.sessionStorage.getItem(KEY);
    const value = raw ? JSON.parse(raw) : null;
    return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  } catch {
    return {};
  }
}

/** Merge `fields` into the stored draft. */
export function writeDraft(fields) {
  try {
    window.sessionStorage.setItem(KEY, JSON.stringify({ ...readDraft(), ...fields }));
  } catch {
    // no storage: the draft is a convenience, never needed to book
  }
}
