// The only module that calls `fetch` in the browser (AD-17). Relative `/api/…` URLs, same-origin cookies,
// an optional `Idempotency-Key` (AD-9), and one error type built from the envelope
// `{"detail": {"error", "message"?, …facts}}` (AD-16).

// The frontend's one mirror of `api/errors.py`'s code -> status table.
export const STATUS = Object.freeze({
  no_session: 401,
  not_signed_in: 401,
  sign_in_refused: 401,
  cross_origin: 403,
  not_allowed: 403,
  not_found: 404,
  no_seat_free: 409,
  rule_refused: 409,
  already_exists: 409,
  deadline_passed: 409,
  outside_horizon: 409,
  sauna_unavailable: 409,
  price_differs: 409,
  release_after_deadline: 409,
  cutoff_passed: 409,
  booking_cancelled: 409,
  booking_changed: 409,
  change_invalid: 409,
  voucher_invalid: 409,
  invalid_key: 409,
  payment_pending: 409,
  payment_failed: 409,
  invalid_input: 422,
  internal_error: 500,
  try_again: 503,
});

export class ApiError extends Error {
  /**
   * @param {number} status HTTP status, or 0 when no response arrived
   * @param {string} code the envelope's `error`, or `unavailable` when no envelope arrived
   * @param {object} facts every other field of the envelope (`message`, `fields`, `seats_left`, …)
   */
  constructor(status, code, facts = {}) {
    super(code);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.facts = facts;
  }
}

/**
 * Call the backend through the site's own origin.
 * @param {string} path a path that starts with `/api/`
 * @param {{method?: string, body?: unknown, idempotencyKey?: string, signal?: AbortSignal}} [options]
 * @returns {Promise<any>} the parsed JSON body
 * @throws {ApiError}
 */
export async function api(path, { method = 'GET', body, idempotencyKey, signal } = {}) {
  if (!path.startsWith('/api/')) throw new Error(`api(): ${path} is not an /api/ path`);
  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (idempotencyKey) headers['Idempotency-Key'] = idempotencyKey;

  let response;
  try {
    response = await fetch(path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials: 'same-origin',
      cache: 'no-store',
      signal,
    });
  } catch {
    throw new ApiError(0, 'unavailable');
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }
  if (response.ok) return data;

  const detail = data && typeof data.detail === 'object' && data.detail !== null ? data.detail : {};
  const { error, ...facts } = detail;
  throw new ApiError(response.status, typeof error === 'string' ? error : 'unavailable', facts);
}
