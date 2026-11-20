// Landing (FR-1, UX-DR15, UX-DR16): the Venue, how to prepare, the Saunas, where it is, and Book seats in the
// first view. The Venue facts (name, address, contact, hours, Session length, price, Saunas) come from
// `GET /api/venue` through server-api.js after `connection()`, so the page is rendered per request (AD-16, AD-17).
// Only copy is written here. If the read fails, the rail shows a Notice and Book seats still works; no fact is
// shown. No Landing load creates a session (AD-8).
import { connection } from 'next/server';
import GuestShell from '@/components/GuestShell';
import Notice from '@/components/Notice';
import PrimaryButton from '@/components/PrimaryButton';
import RuleList from '@/components/RuleList';
import SaunaCard from '@/components/SaunaCard';
import TextLink from '@/components/TextLink';
import Wordmark from '@/components/Wordmark';
import { getPublic } from '@/lib/server-api';
import { nok, openingHours, sessionLength } from '@/lib/venue-format';

// Landing is just "Saunalöyly" (EXPERIENCE.md, Page titles).
export const metadata = { title: { absolute: 'Saunalöyly' } };

const BOOK_SEATS = '/book-seats';
const VENUE_UNAVAILABLE = 'The venue details could not be loaded, please try again.';

// EXPERIENCE.md, Voice and Tone: Landing copy, verbatim.
const RULES = [
  {
    title: 'What to bring',
    items: [
      'Swimwear to wear at the venue.',
      'Two towels. One to sit on and one to dry yourself with.',
      'A bottle for water.',
    ],
  },
  {
    title: 'Safety',
    items: [
      'Drink enough water to avoid dehydration.',
      'Alcohol is not allowed at the venue.',
      'Keep rounds in the sauna to 10 minutes at most, and leave if you feel unwell.',
      'Ask the others before throwing water on the stones.',
      'Swim preferably with others, and never ice-bathe alone.',
      'Children must be supervised by an adult.',
    ],
  },
  {
    title: 'Practical',
    items: [
      'Changing time is part of your session.',
      'There is a wardrobe for your clothes.',
      'You can swim in the sea all year round.',
      'There are showers.',
      'There is a tap with drinking water.',
    ],
  },
];

const SEAT_STATEMENT =
  'A booking gives you seats in the shared saunas open during your session. On site you can move freely between them.';

function RailFacts({ venue }) {
  return (
    <>
      <p className="rail-fact">
        Open every day
        <br />
        <span className="tabular">{openingHours(venue.opening_time, venue.closing_time)}</span>
        <br />
        Sessions last {sessionLength(venue.session_minutes)}
      </p>
      <p className="rail-fact">
        {nok(venue.price_per_seat_ore)} per seat
        <br />
        incl. VAT
      </p>
    </>
  );
}

export default async function Landing() {
  await connection();
  const result = await getPublic('/api/venue');
  const venue = result.ok ? result.data : null;

  const rail = (
    <>
      <Wordmark heading />
      {venue ? <RailFacts venue={venue} /> : <Notice>{VENUE_UNAVAILABLE}</Notice>}
      <PrimaryButton href={BOOK_SEATS}>Book seats</PrimaryButton>
    </>
  );

  return (
    <GuestShell rail={rail} mainClass="landing">
      <img
        className="hero"
        src="/images/hero-sauna-by-the-water.jpg"
        alt="A dark wooden sauna with a railing on its roof, standing in calm water, with the low sun glowing softly over the open sea and golden light on the surface."
        width={2092}
        height={936}
      />
      <p className="venue-description">
        <span lang="fi">Löyly</span> is the steam that rises when water meets the hot stones. At Saunalöyly you come to
        Finnish saunas by the sea, where you can swim all year round.
      </p>

      <section id="before-you-come" className="before" tabIndex={-1} aria-labelledby="before-you-come-heading">
        <h2 id="before-you-come-heading" className="heading-xl">
          Before you come
        </h2>
        <div className="before-cols">
          {RULES.map((rule) => (
            <RuleList key={rule.title} title={rule.title} items={rule.items} />
          ))}
        </div>
        <img
          className="before-image"
          src="/images/before-towels.jpg"
          alt="A rolled grey towel beside a beige towel in a cork tray."
          width={1892}
          height={603}
        />
      </section>

      <section className="saunas" aria-labelledby="saunas-heading">
        <div className="saunas-intro">
          <h2 id="saunas-heading" className="heading-xl">
            The saunas
          </h2>
          <p>{SEAT_STATEMENT}</p>
        </div>
        {venue && (
          <ul className="sauna-grid">
            {venue.saunas.map((sauna) => (
              <SaunaCard key={sauna.id} sauna={sauna} />
            ))}
          </ul>
        )}
      </section>

      <img
        className="band"
        src="/images/band-loyly-steam.jpg"
        alt="Soft clouds of warm, brown-tinted steam drifting across the frame."
        width={2092}
        height={600}
      />

      <section className="find-us" aria-labelledby="find-us-heading">
        <h2 id="find-us-heading" className="heading-lg">
          Find us
        </h2>
        {venue && (
          <p className="find-us-contact">
            {venue.address_lines.map((line, i) => (
              <span key={i}>
                {line}
                <br />
              </span>
            ))}
            {venue.phone}
            <br />
            {venue.email}
          </p>
        )}
        <p>
          <TextLink href="/terms">Terms</TextLink>
          <br />
          <TextLink href="/privacy">Privacy notice</TextLink>
        </p>
      </section>
    </GuestShell>
  );
}
