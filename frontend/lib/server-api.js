// The only server-side caller of the backend (AD-17). Public GETs only: no session, no cookie, no Seats left,
// never a write, always `cache: 'no-store'`. It never throws: a failed or slow call returns
// `{ ok: false }`, and the page renders its Notice from that. A page that uses it awaits `connection()` from
// `next/server` before the call, so it is rendered per request and never prerendered.
import { unstable_rethrow } from 'next/navigation';

const TIMEOUT_MS = 3000;

/**
 * @param {string} path a path that starts with `/api/`
 * @returns {Promise<{ok: true, data: any} | {ok: false}>}
 */
export async function getPublic(path) {
  try {
    if (!path.startsWith('/api/')) return { ok: false };
    const base = process.env.API_INTERNAL_URL || 'http://127.0.0.1:8001';
    const response = await fetch(base + path, {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    if (!response.ok) return { ok: false };
    return { ok: true, data: await response.json() };
  } catch (err) {
    unstable_rethrow(err);
    return { ok: false };
  }
}
