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
  }),
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
