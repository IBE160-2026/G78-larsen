// The two booking flows that share Details, Review and Confirmation (Story 5.2, UX-DR26): the Seat flow and the
// Private sauna flow. Each has its own draft slot (lib/draft.js) and its own pages; the components take a `flow` prop
// and read everything flow-specific from here.
import { SEATS_SLOT, WHOLE_SLOT } from './draft';

const ISO = /^\d{4}-\d{2}-\d{2}$/;

export const FLOWS = Object.freeze({
  seats: Object.freeze({
    kind: 'seats',
    slot: SEATS_SLOT,
    details: '/book-seats/details',
    review: '/book-seats/review',
    /** The flow's first page, where the choices are made. */
    start: () => '/book-seats',
    /** True when the draft holds every choice of the first page. */
    chosen: (d) => Number.isInteger(d.window_id) && Boolean(d.date) && Boolean(d.seats),
  }),
  whole: Object.freeze({
    kind: 'whole',
    slot: WHOLE_SLOT,
    details: '/private-sauna/details',
    review: '/private-sauna/review',
    // The Private sauna page for the draft's date, so the Guest is back where they chose (UX-DR25, UX-DR26).
    start: (d) => (d && typeof d.date === 'string' && ISO.test(d.date) ? `/private-sauna?date=${d.date}` : '/private-sauna'),
    chosen: (d) => Number.isInteger(d.window_id) && Number.isInteger(d.sauna_id) && Boolean(d.date),
  }),
});

/** The flow named `name`; the Seat flow for anything else. */
export function flowOf(name) {
  return FLOWS[name] || FLOWS.seats;
}
