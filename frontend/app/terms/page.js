// Booking terms (FR-5, UX-DR28): the text of mockups/key-terms.html, verbatim. Static: no API call.
import GuestShell from '@/components/GuestShell';
import TextLink from '@/components/TextLink';
import Wordmark from '@/components/Wordmark';

export const metadata = { title: 'Booking terms' };

export default function Terms() {
  return (
    <GuestShell rail={<Wordmark />}>
      <article className="col page-text">
        <h1 className="heading-xl" tabIndex={-1}>
          Booking terms
        </h1>
        <section className="section">
          <h2 className="heading-md">Who we are</h2>
          <p>Saunalöyly, Badstubrygga 4, 0000 Havbukta. hello@saunaloyly.example, +47&nbsp;01&nbsp;23&nbsp;45&nbsp;67.</p>
        </section>
        <section className="section">
          <h2 className="heading-md">What you book</h2>
          <p>
            A booking gives you seats in the shared saunas open during your session. A session lasts 1&nbsp;h&nbsp;30&nbsp;min,
            and changing time is part of it. You do not book a specific sauna.
          </p>
        </section>
        <section className="section">
          <h2 className="heading-md">Price and payment</h2>
          <p>
            A seat costs NOK 250 incl. VAT. You see the total before you pay, and you pay when you book. In this version,
            payment is simulated and no money moves.
          </p>
        </section>
        <section className="section">
          <h2 className="heading-md">How to book</h2>
          <p>
            Choose a date, the number of seats and a session. Enter your name and email. On Review, check everything,
            accept these terms and press Pay. Until you press Pay, nothing is booked, and you can go back and correct
            anything without losing what you have entered.
          </p>
        </section>
        <section className="section">
          <h2 className="heading-md">Confirmation</h2>
          <p>You get a booking reference on the page and by email. Keep the reference.</p>
        </section>
        <section className="section">
          <h2 className="heading-md">No right of withdrawal</h2>
          <p>A booking for a fixed date has no right of withdrawal (angrerettloven §&nbsp;22&nbsp;m).</p>
        </section>
        <section className="section">
          <h2 className="heading-md">Changes and refunds</h2>
          <p>
            Up to 12 hours before the session starts, you can move some or all seats to another session, or give them
            up for a voucher. Money is not refunded.
          </p>
        </section>
        <section className="section">
          <h2 className="heading-md">If Saunalöyly cancels</h2>
          <p>
            If we cancel your session, we email you, and you choose a refund or a voucher. If you have not chosen within
            30 days, you get a refund.
          </p>
        </section>
        <section className="section">
          <h2 className="heading-md">At the venue</h2>
          <p>
            Read <TextLink href="/#before-you-come">Before you come</TextLink>. Follow the safety rules there and the
            staff&apos;s instructions.
          </p>
        </section>
        <section className="section">
          <h2 className="heading-md">Language</h2>
          <p>These terms and the booking are in English.</p>
        </section>
        <section className="section">
          <h2 className="heading-md">Your data</h2>
          <p>
            How we handle your name and email is described in the <TextLink href="/privacy">Privacy notice</TextLink>.
          </p>
        </section>
      </article>
    </GuestShell>
  );
}
