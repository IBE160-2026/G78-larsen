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
const seatsWord = (n) => (n === 1 ? '1 seat' : `${n} seats`);

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
