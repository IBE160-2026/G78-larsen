// Copy shared by more than one page, verbatim from EXPERIENCE.md (Voice and Tone). Only wording lives here; facts
// such as the price, the dates and Seats left come from the API (AD-16).

// The Seat statement (FR-4): Landing ("The saunas") and the Book seats rail.
export const SEAT_STATEMENT =
  'A booking gives you seats in the shared saunas open during your session. On site you can move freely between them.';

// The changing-time note: Landing ("Before you come", Practical) and the Book seats rail.
export const CHANGING_TIME = 'Changing time is part of your session.';

// The rail's Notice when the Venue facts cannot be read (Landing, and the price on Book seats).
export const VENUE_UNAVAILABLE = 'The venue details could not be loaded, please try again.';

// Book seats (EXPERIENCE.md, Page and message wording). Functions take the facts the sentence needs.
export const seatsWord = (n) => (n === 1 ? '1 seat' : `${n} seats`);

export const BOOK = Object.freeze({
  heading: 'Book seats',
  continue: 'Continue booking',
  dateQuestion: '1. Choose a date',
  dateHint: 'Type it as dd.mm.yyyy, or pick a day below',
  seatsQuestion: '2. How many seats?',
  sessionQuestion: '3. Choose a session',
  nextMonth: 'Next month',
  previousMonth: 'Previous month',
  pickADay: (month) => `Pick a day, ${month}`,
  horizonLine: (phrase) => `Booking opens ${phrase} ahead.`,
  loadingSessions: 'Loading sessions',
  alreadyStarted: 'Already started',
  soldOut: 'Sold out',
  seatsLeft: (n) => `${seatsWord(n)} left`,
  notEnough: (left, seats) => `${seatsWord(left)} left, not enough for ${seats}`,
  perSeat: (price) => `${price} per seat in every session`,
  total: (amount) => `Total ${amount}`,
  inclVat: 'incl. VAT',
  noRoomOnDate: (seats, weekday) => `No room for ${seatsWord(seats)} on ${weekday}. The nearest sessions with room:`,
  noRoomInHorizon: (seats, phrase) => `There is no room for ${seatsWord(seats)} in the next ${phrase}.`,
  chooseDate: 'Choose a date',
  chooseSeats: 'Choose the number of seats',
  chooseSession: 'Choose a session',
  dateFormat: 'Enter the date as dd.mm.yyyy',
  dateNotBookable: 'This date cannot be booked. Pick a day below.',
  // Not in EXPERIENCE.md's wording tables (it says only that step 3 says so in a Notice): to be confirmed by Lisa.
  sessionCleared: (seats) => `The session you chose no longer has room for ${seatsWord(seats)}. Choose another session.`,
  // EXPERIENCE.md: a failed read shows a Notice with "please try again".
  sessionsUnavailable: 'The sessions could not be loaded, please try again.',
});

// The payment note: on Pay and in every email that mentions a payment (FR-6).
export const SIMULATED_PAYMENT = 'Simulated payment: no money moves';

// The Booking summary labels (EXPERIENCE.md), on Review and Confirmation.
export const SUMMARY = Object.freeze({
  date: 'Date',
  session: 'Session',
  seats: 'Seats',
  total: 'Total',
  name: 'Name',
  email: 'Email',
  venue: 'Venue',
  contact: 'Contact',
});

// Details (UX-DR23).
export const DETAILS = Object.freeze({
  heading: 'Your details',
  back: 'Back',
  name: 'Name',
  email: 'Email',
  continue: 'Continue booking',
  enterName: 'Enter your name',
  enterEmail: 'Enter a valid email address',
});

// Review (UX-DR24, UX-DR25).
export const REVIEW = Object.freeze({
  heading: 'Review',
  back: 'Back',
  termsHeading: 'Booking terms',
  accept: 'I accept the booking terms',
  pay: (amount) => `Pay ${amount}`,
  processing: 'Processing',
  // Not in EXPERIENCE.md's wording tables (it says only "Error summary and Field error"): to be confirmed by Lisa.
  acceptTerms: 'Accept the booking terms',
  // EXPERIENCE.md: a refusal shows a Notice with "please try again"; the first words are to be confirmed by Lisa.
  tryAgain: 'The booking could not be completed, please try again.',
  loadFailed: 'The booking could not be loaded, please try again.',
  // The refusals of Story 1.6, verbatim from EXPERIENCE.md (Page and message wording).
  seatsLeft: (n) => `Only ${seatsWord(n)} left in this session. You have not been charged.`,
  noSeatFree: 'No seat free. You have not been charged.',
  closed: 'This session can no longer be booked. You have not been charged.',
  paymentFailed: 'The payment failed. You have not been charged. You can pay again.',
  mayBePaid: 'This booking may already be paid. Check your email for a confirmation before you book again.',
  nearest: 'The nearest sessions with room:',
  bookSeats: 'Book seats',
});

/**
 * Review's one code -> message mapping (AD-16). Every code here is in `api/errors.py` and `lib/api.js` STATUS.
 * - `closed`: the session cannot be had (Notice with Nearest sessions; Pay, the note and the checkbox removed)
 * - `failed`: the payment failed (Error summary; Pay kept)
 * - `paid`: the key is known elsewhere (Notice with a Book seats link; Pay removed)
 * - `retry`: anything else, including `payment_pending`, `try_again`, `no_session` and no answer (Notice; Pay kept)
 * @param {string} code the envelope's `error`
 * @param {object} facts the envelope's facts (`seats_left` for `no_seat_free`)
 * @returns {{kind: 'closed'|'failed'|'paid'|'retry', text: string}}
 */
export function reviewRefusal(code, facts = {}) {
  switch (code) {
    case 'no_seat_free': {
      const n = facts.seats_left;
      return { kind: 'closed', text: Number.isInteger(n) && n >= 1 ? REVIEW.seatsLeft(n) : REVIEW.noSeatFree };
    }
    case 'deadline_passed':
    case 'outside_horizon':
      return { kind: 'closed', text: REVIEW.closed };
    case 'payment_failed':
      return { kind: 'failed', text: REVIEW.paymentFailed };
    case 'invalid_key':
      return { kind: 'paid', text: REVIEW.mayBePaid };
    default:
      return { kind: 'retry', text: REVIEW.tryAgain };
  }
}

// Confirmation (UX-DR27).
export const CONFIRMATION = Object.freeze({
  heading: 'Booking confirmed',
  reference: 'Booking reference',
  beforeYouCome: 'Before you come',
  sentByEmail: 'Sent by email:',
  loadFailed: 'The booking could not be loaded, please try again.',
});

// The Manage page (FR-25, Story 4.1). Approved by Lisa 2026-11-24. The dates and times come from the API's `cutoff_at`
// (Venue time); "12 hours" is fixed copy, as Administrators cannot change the Seat Cutoff in v1.
export const MANAGE = Object.freeze({
  heading: 'Manage booking',
  untilText: (longDate, time) => `You can change this booking until ${longDate} at ${time}.`,
  // The reason for the refusal `cutoff_passed` (fact `cutoff_at`), and the page's text after the Cutoff.
  cutoffPassed: (longDate, time) =>
    `This booking can no longer be changed. Changes are possible until 12 hours before the session starts, and that was ${longDate} at ${time}.`,
  // EXPERIENCE.md: a failed read shows a Notice with "please try again".
  loadFailed: 'The booking could not be loaded, please try again.',
  // Story 4.2 (Lisa, 2026-11-24): the Manage page's link to the move step.
  moveSeats: 'Move seats',
});

// Move seats (FR-26, Story 4.2): the confirming step and its result. Verbatim from Lisa's decisions of 2026-11-24.
export const MOVE = Object.freeze({
  heading: 'Move seats',
  back: 'Back',
  seatsQuestion: '1. How many seats do you want to move?',
  dateQuestion: '2. Choose a date',
  currentSession: 'Your current session',
  summaryHeading: 'What will happen',
  seatsMoved: 'Seats moved',
  from: 'From',
  to: 'To',
  seatsLeftInBooking: 'Seats left in this booking',
  nothingYet: 'Nothing changes until you confirm.',
  confirm: (n) => `Move ${seatsWord(n)}`,
  resultHeading: 'Seats moved',
  resultLine: 'Your booking has been changed.',
  newReference: (ref) => `Your moved seats have a new booking reference: ${ref}.`,
  // Lisa, 2026-11-24: the result page links back to the Manage page of the Booking that was changed.
  backToBooking: 'Back to your booking',
  seatsLeft: (n) => `Only ${seatsWord(n)} left in this session. Nothing has changed.`,
  noSeatFree: 'No seat free in this session. Nothing has changed.',
  closed: 'This session can no longer be booked. Nothing has changed.',
  changed: 'This booking was changed in the meantime. Check it and choose again.',
  tryAgain: 'The change could not be completed, please try again.',
});

/**
 * The move step's one code -> message mapping (AD-16). Every code here is in `api/errors.py` and `lib/api.js` STATUS.
 * - `stay`: the step stays with the Guest's choices (`no_seat_free`, `outside_horizon`, `deadline_passed`, and
 *   anything else with "please try again")
 * - `reload`: the Booking is read again and the step opens fresh with a new key (`booking_changed`, `invalid_key`)
 * - `cutoff`: the page shows the Cutoff state of Story 4.1 (`cutoff_passed`, fact `cutoff_at`)
 * @param {string} code the envelope's `error`
 * @param {object} facts the envelope's facts (`seats_left` for `no_seat_free`)
 * @returns {{kind: 'stay'|'reload'|'cutoff', text: string|null}}
 */
export function moveRefusal(code, facts = {}) {
  switch (code) {
    case 'no_seat_free': {
      const n = facts.seats_left;
      return { kind: 'stay', text: Number.isInteger(n) && n >= 1 ? MOVE.seatsLeft(n) : MOVE.noSeatFree };
    }
    case 'outside_horizon':
    case 'deadline_passed':
      return { kind: 'stay', text: MOVE.closed };
    case 'booking_changed':
    case 'invalid_key':
      return { kind: 'reload', text: MOVE.changed };
    case 'cutoff_passed':
      return { kind: 'cutoff', text: null };
    default:
      return { kind: 'stay', text: MOVE.tryAgain };
  }
}

// The Administrator pages (UX-DR3, UX-DR30, EXPERIENCE.md). The copy never uses the word "session" for a sign-in.
export const ADMIN = Object.freeze({
  name: 'Saunalöyly',
  nav: 'Administrator',
  bookingList: 'Booking list',
  outbox: 'Outbox',
  signOut: 'Sign out',
  // Not in EXPERIENCE.md's wording tables (it says only "please try again"); approved by Lisa 2026-11-21.
  signOutFailed: 'Sign-out could not be completed, please try again.',
});

// The Booking list (FR-16, UX-DR31, UX-DR37): every Window is a "session" in the copy. A malformed typed date uses
// BOOK.dateFormat.
export const BOOKING_LIST = Object.freeze({
  date: 'Date',
  previousDay: 'Previous day',
  nextDay: 'Next day',
  noSessions: 'No sessions on this day', // Lisa, 2026-11-21
  noBookings: 'No bookings',
  soldOut: 'Sold out',
  seatCapacity: (n) => `Seat capacity ${n}`,
  seatsBooked: (n) => `Seats booked ${n}`,
  seatsLeft: (n) => `Seats left ${n}`,
  session: (start, end) => `Session ${start} to ${end}`,
  caption: (start, end) => `Bookings in the session ${start} to ${end}`,
  columns: Object.freeze({
    reference: 'Reference',
    name: 'Name',
    email: 'Email',
    seats: 'Seats',
    total: 'Total',
    time: 'Time of booking',
    status: 'Status',
  }),
  // Story 4.2 (Lisa, 2026-11-24): each Booking's status, and one line per history entry under it.
  status: Object.freeze({ active: 'Active', cancelled: 'Cancelled' }),
  moved: (seats, at, from, to) => `Moved ${seatsWord(seats)} on ${at} from ${from} to ${to}`,
  newBooking: (ref) => ` · new booking ${ref}`,
  // EXPERIENCE.md: a failed read shows a Notice with "please try again".
  failed: 'The booking list could not be loaded, please try again.',
});

// The Outbox (FR-17, FR-21, UX-DR32). A recipient or body masked for retention arrives as '' (Lisa, 2026-11-21).
export const OUTBOX = Object.freeze({
  heading: 'Outbox',
  noEmails: 'No emails',
  sent: (time) => `Sent ${time}`,
  to: (recipient) => `To ${recipient}`,
  anonymised: 'Anonymised',
  removed: 'Removed after 12 months.',
  failed: 'The outbox could not be loaded, please try again.',
});

// Sign-in (FR-15, UX-DR30). Every refusal is the one message, in an Error summary with no Field error (PW-5).
export const SIGN_IN = Object.freeze({
  heading: 'Sign in',
  email: 'Email',
  password: 'Password',
  submit: 'Sign in',
  refused: 'Wrong email or password',
  failed: 'Sign-in could not be completed, please try again.',
});
