// Privacy notice (FR-21, UX-DR28): the text of mockups/key-privacy.html, verbatim. Static: no API call, so it
// renders with the backend stopped (it is also the frontend's healthcheck route, AD-27).
import GuestShell from '@/components/GuestShell';
import TextLink from '@/components/TextLink';
import Wordmark from '@/components/Wordmark';

export const metadata = { title: 'Privacy notice' };

export default function Privacy() {
  return (
    <GuestShell rail={<Wordmark />}>
      <article className="col page-text">
        <h1 className="heading-xl" tabIndex={-1}>
          Privacy notice
        </h1>
        <section className="section">
          <h2 className="heading-md">Who is responsible</h2>
          <p>
            Saunalöyly is responsible for your personal data, as the data controller. You can reach us at Badstubrygga 4,
            0000 Havbukta, at hello@saunaloyly.example or on +47&nbsp;01&nbsp;23&nbsp;45&nbsp;67.
          </p>
        </section>
        <section className="section">
          <h2 className="heading-md">What we store and why</h2>
          <p>
            When you book, we store your name and email with your booking: the date, the session, the number of seats,
            the price and your booking reference. We use them to deliver your booking: to send your confirmation, and to
            find your booking when you arrive. We do not send marketing email.
          </p>
        </section>
        <section className="section">
          <h2 className="heading-md">Legal basis</h2>
          <p>
            We use this data because we need it to carry out the contract you make when you book (GDPR art.&nbsp;6(1)(b)).
            Without your name and email we cannot take your booking.
          </p>
        </section>
        <section className="section">
          <h2 className="heading-md">In your browser</h2>
          <p>
            While you book, your name and email are kept in this browser tab, so that you can go back without losing them.
            They are gone when you close the tab.
          </p>
          <p>
            We set one cookie when you open Book seats. It holds a random code that keeps your booking together and lets
            this browser show your confirmation. It expires 24 hours after your last visit. We set no other cookies.
          </p>
        </section>
        <section className="section">
          <h2 className="heading-md">Who sees your data</h2>
          <p>
            Saunalöyly&apos;s staff see your name, email and booking in the booking list, including at reception. We do not
            give your data to anyone else, and our pages load nothing from other companies.
          </p>
          <p>
            In this version, payment is simulated and emails are not sent anywhere. Your confirmation email is shown on the
            confirmation page and kept in a simulated mailbox that staff can read.
          </p>
        </section>
        <section className="section">
          <h2 className="heading-md">How long we keep it</h2>
          <p>
            We delete or anonymise your name and email 12 months after your session, including the confirmation email. If
            you have a voucher from the booking, we keep them until the voucher expires, if that is later.
          </p>
        </section>
        <section className="section">
          <h2 className="heading-md">How we protect it</h2>
          <p>
            Only signed-in staff can open the booking list, and the server checks this on every request. Staff passwords
            are stored only in hashed form.
          </p>
        </section>
        <section className="section">
          <h2 className="heading-md">Your rights</h2>
          <p>
            You can ask to see the data we hold about you, to correct or delete it, to limit how we use it, and to get a
            copy of it. Contact us at the address above, and we will answer within one month.
          </p>
          <p>
            You can also complain to Datatilsynet, the Norwegian data protection authority, at{' '}
            <TextLink href="https://www.datatilsynet.no">datatilsynet.no</TextLink>.
          </p>
        </section>
      </article>
    </GuestShell>
  );
}
