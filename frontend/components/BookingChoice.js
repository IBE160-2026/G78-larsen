// Booking choice (UX-DR41, Lisa 2026-11-25): one of the two ways to book on Landing, Book seats and Book private
// sauna, drawn alike: the Primary button's fill, edge, type and height, the label centred, the same size as each other.
import Link from 'next/link';

export default function BookingChoice({ href, children }) {
  return (
    <Link className="booking-choice" href={href}>
      {children}
    </Link>
  );
}
