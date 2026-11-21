// Calendar arithmetic on Venue dates written `yyyy-mm-dd` (AD-16). No function here reads a clock: "today" and the
// horizon always come from the API (AD-4). `Date.UTC` is used only to count days and find weekdays of a given date.

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
  'November', 'December'];
const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
export const WEEKDAYS_SHORT = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const pad = (n, width = 2) => String(n).padStart(width, '0');

/** "2026-12-01" from year, month (1–12) and day. */
export function isoDate(year, month, day) {
  return `${pad(year, 4)}-${pad(month)}-${pad(day)}`;
}

/** {year, month (1–12), day} of "2026-12-01". */
export function parts(iso) {
  const [year, month, day] = iso.split('-').map(Number);
  return { year, month, day };
}

export function daysInMonth(year, month) {
  return new Date(Date.UTC(year, month, 0)).getUTCDate();
}

/** 0 for Monday … 6 for Sunday. */
export function weekdayIndex(iso) {
  const { year, month, day } = parts(iso);
  return (new Date(Date.UTC(year, month - 1, day)).getUTCDay() + 6) % 7;
}

/** "Saturday". */
export function weekdayName(iso) {
  return WEEKDAYS[weekdayIndex(iso)];
}

/** "December 2026" for a month key {year, month}. */
export function monthLabel({ year, month }) {
  return `${MONTHS[month - 1]} ${year}`;
}

/** "14 November 2026". */
export function fullDate(iso) {
  const { year, month, day } = parts(iso);
  return `${day} ${MONTHS[month - 1]} ${year}`;
}

/** "Saturday 14 November 2026". */
export function longDate(iso) {
  return `${weekdayName(iso)} ${fullDate(iso)}`;
}

/** "Saturday 14 November". */
export function dayAndMonth(iso) {
  const { month, day } = parts(iso);
  return `${weekdayName(iso)} ${day} ${MONTHS[month - 1]}`;
}

/** "14.11.2026" from "2026-11-14". */
export function dotted(iso) {
  const { year, month, day } = parts(iso);
  return `${pad(day)}.${pad(month)}.${pad(year, 4)}`;
}

/** "2026-11-14" from a typed "14.11.2026" (one-digit day and month allowed), or null when it is not a real date. */
export function parseDotted(text) {
  const m = /^\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s*$/.exec(text);
  if (!m) return null;
  const [day, month, year] = [Number(m[1]), Number(m[2]), Number(m[3])];
  if (month < 1 || month > 12 || day < 1 || day > daysInMonth(year, month)) return null;
  return isoDate(year, month, day);
}

/** The month key {year, month} of a date. */
export function monthOf(iso) {
  const { year, month } = parts(iso);
  return { year, month };
}

export function addMonths({ year, month }, n) {
  const index = year * 12 + (month - 1) + n;
  return { year: Math.floor(index / 12), month: (index % 12) + 1 };
}

/** -1, 0 or 1 comparing two month keys. */
export function compareMonths(a, b) {
  return Math.sign(a.year * 12 + a.month - (b.year * 12 + b.month));
}

/** "HH:MM" of an ISO timestamp the API writes in Venue time ("2026-12-01T10:00:00+01:00"). */
export function clockTime(timestamp) {
  return timestamp.slice(11, 16);
}

/** "01.12.2026 10:00" of an ISO timestamp the API writes in Venue time, sliced from the text (no clock, no Intl). */
export function dottedTime(timestamp) {
  return `${dotted(timestamp.slice(0, 10))} ${clockTime(timestamp)}`;
}

/** The date `n` days after (or before, for a negative `n`) a date: "2026-12-02" from ("2026-12-01", 1). */
export function addDays(iso, n) {
  const { year, month, day } = parts(iso);
  const d = new Date(Date.UTC(year, month - 1, day + n));
  return isoDate(d.getUTCFullYear(), d.getUTCMonth() + 1, d.getUTCDate());
}

/** "4 weeks" for 28 days, "10 days" otherwise. */
export function horizonPhrase(days) {
  if (days % 7 === 0) return days === 7 ? '1 week' : `${days / 7} weeks`;
  return days === 1 ? '1 day' : `${days} days`;
}
