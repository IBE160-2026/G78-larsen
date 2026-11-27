// Copy shared by more than one page, verbatim from EXPERIENCE.md (Voice and Tone). Only wording lives here; facts
// such as the price, the dates and Seats left come from the API (AD-16).

// The Seat statement (FR-4): Landing ("The saunas") and the Book seats rail.
export const SEAT_STATEMENT =
  'A booking gives you seats in the shared saunas open during your session. On site you can move freely between them.';

// The group sentence (FR-4, Story 5.1): after the Seat statement on Landing ("The saunas") and in the Book seats rail.
export const GROUP_SENTENCE = 'A group that wants to stay together should book a private sauna.';

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
  // Story 5.2: a Whole-sauna booking's summary names its Sauna where a Seat booking's states its Seats.
  sauna: 'Sauna',
  total: 'Total',
  name: 'Name',
  email: 'Email',
  venue: 'Venue',
  contact: 'Contact',
  // Story 4.4 (Lisa, 2026-11-24): on Review after Total, only while a Voucher is applied; the card row left out when 0.
  voucher: 'Voucher',
  voucherPart: (amount) => `−${amount}`,
  toPayByCard: 'To pay by card',
});

// Details (UX-DR23).
// Terms and the Privacy notice (Lisa 2026-11-25): Back under the heading (components/BackLink.js).
export const LEGAL_PAGE = Object.freeze({
  back: 'Back',
});

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
  // Story 4.4 (Lisa, 2026-11-24; EXPERIENCE.md Open Item 23): Pay when the Voucher covers the whole total.
  bookWithVoucher: 'Book with voucher',
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
 * - `closed`: the session (or, for a Private sauna, the Sauna in it) cannot be had (Notice with Nearest sessions, or
 *   in the Private sauna flow the link back to the Private sauna page; Pay, the note and the checkbox removed)
 * - `failed`: the payment failed (Error summary; Pay kept)
 * - `paid`: the key is known elsewhere (Notice with a Book seats link; Pay removed)
 * - `voucher`: the Voucher cannot be used (Field error and Error summary on the Voucher field; Pay kept)
 * - `retry`: anything else, including `payment_pending`, `try_again`, `no_session` and no answer (Notice; Pay kept)
 * @param {string} code the envelope's `error`
 * @param {object} facts the envelope's facts (`seats_left` for `no_seat_free`)
 * @returns {{kind: 'closed'|'failed'|'paid'|'voucher'|'retry', text: string}}
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
    case 'sauna_unavailable':
      return { kind: 'closed', text: PRIVATE.unavailable };
    case 'payment_failed':
      return { kind: 'failed', text: REVIEW.paymentFailed };
    case 'invalid_key':
      return { kind: 'paid', text: REVIEW.mayBePaid };
    case 'voucher_invalid':
      return { kind: 'voucher', text: VOUCHER_FIELD.invalid };
    default:
      return { kind: 'retry', text: REVIEW.tryAgain };
  }
}

// The Voucher field on Review (FR-28, Story 4.4). Verbatim from Lisa's decisions of 2026-11-24 (EXPERIENCE.md, Pay with
// a voucher wording): one message for every invalid code, never saying which cause applies.
export const VOUCHER_FIELD = Object.freeze({
  label: 'Voucher code',
  apply: 'Apply voucher',
  invalid: 'This voucher code cannot be used. It may be mistyped, used up or expired. Check the code and try again.',
  failed: 'The voucher could not be checked, please try again.',
});

// Confirmation (UX-DR27).
export const CONFIRMATION = Object.freeze({
  heading: 'Booking confirmed',
  reference: 'Booking reference',
  beforeYouCome: 'Before you come',
  sentByEmail: 'Sent by email:',
  loadFailed: 'The booking could not be loaded, please try again.',
  // Story 4.4 (Lisa, 2026-11-24): after Total, a zero part left out; without a Voucher no new rows.
  paidWithVoucher: 'Paid with voucher',
  paidByCard: 'Paid by card',
});

// The Manage page (FR-25, Story 4.1). Approved by Lisa 2026-11-24. The dates and times come from the API's `cutoff_at`
// (Venue time); the hours are fixed copy, as Administrators cannot change a Cutoff in v1: 12 for a Seat booking, 72 for
// a Private sauna (Story 5.3, Lisa 2026-11-26).
export const MANAGE = Object.freeze({
  heading: 'Manage booking',
  untilText: (longDate, time) => `You can change this booking until ${longDate} at ${time}.`,
  // The reason for the refusal `cutoff_passed` (fact `cutoff_at`), and the page's text after the Cutoff.
  cutoffPassed: (longDate, time, hours = 12) =>
    `This booking can no longer be changed. Changes are possible until ${hours} hours before the session starts, and that was ${longDate} at ${time}.`,
  // The Cutoff of a Private sauna, in hours (`cutoffPassed`'s third argument; a Seat booking's 12 is the default).
  wholeHours: 72,
  // EXPERIENCE.md: a failed read shows a Notice with "please try again".
  loadFailed: 'The booking could not be loaded, please try again.',
  // Story 4.2 (Lisa, 2026-11-24): the Manage page's link to the move step.
  moveSeats: 'Move seats',
  // Story 4.3 (Lisa, 2026-11-24): the link to the voucher step, and the page of a cancelled Booking (Open Item 19).
  giveUpSeats: 'Give up seats for a voucher',
  cancelled: (longDate, time) =>
    `This booking was cancelled on ${longDate} at ${time}. You gave up all seats for a voucher, which was sent by email.`,
  // Story 5.3 (Lisa, 2026-11-26, EXPERIENCE.md "Cancel private sauna wording"): the link to the cancel step of a Private
  // sauna, and the page of a cancelled one.
  cancelPrivateSauna: 'Cancel private sauna',
  // Story 5.3 part 2 (Lisa, 2026-11-26, EXPERIENCE.md "Move private sauna wording"): the link to the move step.
  movePrivateSauna: 'Move private sauna',
  cancelledWhole: (longDate, time, remedy) =>
    `This booking was cancelled on ${longDate} at ${time}. You chose ${remedy === 'refund' ? 'a refund' : 'a voucher'}, which was sent by email.`,
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

// Give up seats for a voucher (FR-27, Story 4.3): the confirming step and its result. Verbatim from Lisa's decisions of
// 2026-11-24. Refusals reuse the move texts (`moveRefusal`).
export const VOUCHER = Object.freeze({
  heading: 'Give up seats',
  back: 'Back',
  seatsQuestion: 'How many seats do you want to give up?',
  summaryHeading: 'What will happen',
  seatsGivenUp: 'Seats given up',
  seatsLeftInBooking: 'Seats left in this booking',
  value: 'Voucher value',
  validUntil: 'Valid until',
  noMoney: 'No money is paid back. The voucher can pay for a new booking until it expires.',
  nothingYet: 'Nothing changes until you confirm.',
  confirm: (n) => `Give up ${seatsWord(n)}`,
  resultHeading: 'Seats given up',
  resultChanged: 'Your booking has been changed.',
  resultCancelled: 'Your booking has been cancelled.',
  codeInEmail: 'Your voucher code is in the email below.',
  backToBooking: 'Back to your booking',
});

// Cancel private sauna (FR-33, Story 5.3): the confirming step and its result. Verbatim from Lisa's decisions of
// 2026-11-26 (EXPERIENCE.md "Cancel private sauna wording"). Refusals reuse the move texts (`moveRefusal`).
export const CANCEL_WHOLE = Object.freeze({
  heading: 'Cancel private sauna',
  back: 'Back',
  remedyQuestion: 'What do you want back?',
  refund: 'A refund',
  refundHint: 'Paid back the way you paid.',
  voucher: 'A voucher',
  voucherHint: (total) => `A voucher for the full ${total}, valid for one year.`,
  summaryHeading: 'What will happen',
  sauna: 'Sauna',
  session: 'Session',
  refundToCard: 'Refund to card',
  newVoucher: 'New voucher',
  voucherValue: 'Voucher value',
  validUntil: 'Valid until',
  noMoney: 'No money is paid back. The voucher can pay for a new booking until it expires.',
  nothingYet: 'Nothing changes until you confirm.',
  confirm: 'Cancel booking',
  resultHeading: 'Booking cancelled',
  resultLine: 'Your booking has been cancelled.',
  refundInEmail: 'Your refund is in the email below.',
  codeInEmail: 'Your voucher code is in the email below.',
  backToBooking: 'Back to your booking',
});

// Move private sauna (FR-33, Story 5.3 part 2): the confirming step and its result. Verbatim from Lisa's decisions of
// 2026-11-26 (EXPERIENCE.md "Move private sauna wording"). Refusals: `wholeMoveRefusal`.
export const MOVE_WHOLE = Object.freeze({
  heading: 'Move private sauna',
  back: 'Back',
  dateQuestion: '1. Choose a date',
  pairQuestion: '2. Choose a sauna and a session',
  yourSauna: 'Your sauna',
  currentSession: 'Your current session',
  otherPrice: 'This sauna has another price than you paid. To book it, cancel this booking and book again.',
  summaryHeading: 'What will happen',
  from: 'From',
  to: 'To',
  price: 'Price',
  unchanged: (total) => `${total} (unchanged)`,
  nothingYet: 'Nothing changes until you confirm.',
  confirm: 'Move booking',
  resultHeading: 'Booking moved',
  resultLine: 'Your booking has been changed.',
  backToBooking: 'Back to your booking',
  unavailable: 'This sauna can no longer be booked for this session. Nothing has changed.',
  sameTarget: 'This is your current session. Nothing has changed.',
});

/**
 * The move step's one code -> message mapping (AD-16). The voucher step (Story 4.3) uses it too: it never gets the
 * move-only codes (`no_seat_free`, `outside_horizon`, `deadline_passed`). Every code here is in `api/errors.py` and `lib/api.js` STATUS.
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

/**
 * The Private sauna move step's mapping (Story 5.3 part 2, Lisa 2026-11-26): `sauna_unavailable`, `price_differs` and
 * `change_invalid`/`same_target` have their own texts and keep the step; every other code is `moveRefusal`'s
 * (`cutoff_passed` shows the 72-hour Cutoff text).
 * @returns {{kind: 'stay'|'reload'|'cutoff', text: string|null}}
 */
export function wholeMoveRefusal(code, facts = {}) {
  if (code === 'sauna_unavailable') return { kind: 'stay', text: MOVE_WHOLE.unavailable };
  if (code === 'price_differs') return { kind: 'stay', text: MOVE_WHOLE.otherPrice };
  if (code === 'change_invalid' && facts.reason === 'same_target') return { kind: 'stay', text: MOVE_WHOLE.sameTarget };
  return moveRefusal(code, facts);
}

// Landing's two Booking choices (UX-DR41, Lisa 2026-11-25). Verbatim from EXPERIENCE.md (Private sauna wording).
export const LANDING_CHOICES = Object.freeze({
  seats: 'Book seats',
  private: 'Book private sauna',
});

// The Private sauna page (FR-29, FR-30, Story 5.1) and its booking (Story 5.2). Verbatim from EXPERIENCE.md (Private
// sauna wording, and the required statement "Private sauna is not held").
export const PRIVATE = Object.freeze({
  heading: 'Private sauna',
  link: 'Private sauna',
  lead: 'Book a whole sauna for your group for one session. Nobody else can book it, or a seat in it.',
  dateQuestion: '1. Choose a date',
  view: 'View',
  bySauna: 'Show by sauna',
  bySession: 'Show by session',
  // One question per view (Lisa 2026-11-25): proposal H by sauna, proposal K by session.
  bySaunaQuestion: '2. Choose a sauna and a session',
  bySessionQuestion: '2. Choose a session and a sauna',
  sessionLegend: 'Session',
  saunaLegend: 'Sauna',
  saunasFree: (n) => (n === 1 ? '1 sauna free' : `${n} saunas free`),
  // The Sauna card's price line on Landing, only for a Sauna offered whole.
  cardPrice: (price) => `Private sauna: ${price}`,
  noSauna: (longDate) => `No sauna can be booked whole on ${longDate}.`,
  // Story 5.2: the rail's Continue (as on Book seats) and its Error summary entry when no pair is chosen.
  continue: 'Continue booking',
  choosePair: 'Choose a sauna and a session',
  // Review (FR-29, UX-DR25).
  notHeld: 'The sauna is not held while you pay.',
  unavailable: 'This sauna can no longer be booked for this session. You have not been charged.',
  chooseAnother: 'Choose another sauna or session',
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
  chooseFromCalendar: 'Choose from calendar', // spec-booking-list-date-picker, Lisa 2026-11-26
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
  // Story 4.3 (Lisa, 2026-11-24): a Voucher Change (the value issued, never the code), and a cancelled Booking's Status
  // cell (time, cause, remedy).
  gaveUp: (seats, at, value) => `Gave up ${seatsWord(seats)} on ${at} for a voucher of ${value}`,
  // Story 5.3 (Lisa, 2026-11-26): a Private sauna cancelled by the Guest (the Voucher's value, never the code).
  cancelledFor: (at, value) => (value ? `Cancelled on ${at} for a voucher of ${value}` : `Cancelled on ${at} for a refund`),
  // Story 5.3 part 2 (Lisa, 2026-11-26): a Private sauna moved by the Guest, with both Saunas.
  movedWhole: (at, fromSauna, from, toSauna, to) => `Moved on ${at} from ${fromSauna} ${from} to ${toSauna} ${to}`,
  cancelledAt: (at, cause, remedy) => [`Cancelled ${at}`, cause, remedy].filter(Boolean).join(' · '),
  cause: Object.freeze({ guest: 'Guest', block: 'Block', overbooking: 'Overbooking' }),
  remedy: Object.freeze({ voucher: 'Voucher', refund: 'Refund' }),
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
