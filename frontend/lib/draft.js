// The Booking draft (AD-9, UX-DR26): `sessionStorage` key `draft:seats`, so the Guest's choices survive a reload in
// the same tab and disappear with the tab. It holds `{date, seats, window_id, name, email, key}`: Book seats writes the
// choices, Details the name and email, and Review makes the idempotency key when the Guest first reaches it. After a
// payment the draft is `{reference}` only, so Details and Review replace themselves with Confirmation and nothing can
// be paid twice; Book seats then starts a new draft. Call these only inside effects: `sessionStorage` does not exist
// while rendering on the server. Storage that is unavailable or full is ignored, so the page still works without a
// draft.
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

/** Replace the stored draft with `value`. */
export function replaceDraft(value) {
  try {
    window.sessionStorage.setItem(KEY, JSON.stringify(value));
  } catch {
    // no storage: the draft is a convenience, never needed to book
  }
}

/** Merge `fields` into the stored draft. */
export function writeDraft(fields) {
  replaceDraft({ ...readDraft(), ...fields });
}

/** The reference of a paid Booking when the draft is `{reference}` only (after a payment), else null. */
export function paidReference(draft) {
  return typeof draft.reference === 'string' && /^[0-9A-HJKMNP-TV-Z]{8}$/.test(draft.reference) ? draft.reference
    : null;
}

/** A random UUID (version 4) for the idempotency key (AD-9), also where `crypto.randomUUID` is missing. */
export function newKey() {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID();
  const b = crypto.getRandomValues(new Uint8Array(16));
  b[6] = (b[6] & 0x0f) | 0x40;
  b[8] = (b[8] & 0x3f) | 0x80;
  const hex = Array.from(b, (x) => x.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

// The key slot of a Change (AD-9, Story 4.2): `sessionStorage` key `draft:change:<reference>:<action>`, holding the
// idempotency key of the confirming step. It is made when the step opens, reused on a reload, and deleted on success,
// on every refusal except `503 try_again`, and when the Guest leaves the step.
const changeSlot = (reference, action) => `draft:change:${reference}:${action}`;
// Without `sessionStorage` the key lives in memory per slot, so a retry from the same page sends the same key.
const memoryKeys = new Map();

/** The stored key of the Change, or null. */
export function readChangeKey(reference, action) {
  try {
    const value = window.sessionStorage.getItem(changeSlot(reference, action));
    if (typeof value === 'string' && value) return value;
  } catch {
    // no storage: the in-memory key below
  }
  return memoryKeys.get(changeSlot(reference, action)) ?? null;
}

/** The stored key of the Change, made and stored first when there is none. */
export function changeKey(reference, action) {
  const stored = readChangeKey(reference, action);
  if (stored) return stored;
  const key = newKey();
  try {
    window.sessionStorage.setItem(changeSlot(reference, action), key);
  } catch {
    memoryKeys.set(changeSlot(reference, action), key); // no storage: the key lives as long as the page
  }
  return key;
}

/** Delete the Change's key slot. */
export function dropChangeKey(reference, action) {
  memoryKeys.delete(changeSlot(reference, action));
  try {
    window.sessionStorage.removeItem(changeSlot(reference, action));
  } catch {
    // nothing stored
  }
}
