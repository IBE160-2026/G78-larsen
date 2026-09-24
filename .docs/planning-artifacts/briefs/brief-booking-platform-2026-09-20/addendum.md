---
title: "Addendum: Booking platform brief"
created: 2026-09-20
---

# Addendum: Booking platform

Detail that belongs in the PRD and architecture rather than the brief.

## Booking rules (as decided)

| Area | Rule |
|---|---|
| Individual seats | A booking reserves 1 or more seats in a time window. Seats are not tied to a particular sauna: they draw on the combined capacity of all saunas not booked in full in that window. Example: Sauna 1 = 7, Sauna 2 = 10, Sauna 3 = 12, Sauna 4 = 15. If Sauna 1 and Sauna 4 are booked in full, Sauna 2 and Sauna 3 (22 seats) are available for individual booking. Individual booking requires only that seats are available, meaning not every sauna is booked in full. Guests see the total number of free seats. |
| Seat placement | Seats are placed in one sauna until it is full, then in the next. A group may therefore be split across saunas. The booking flow must make clear that the guest books seats, not a sauna; a group that wants to stay together must book a whole sauna. The administrator sets the fill order. When a cancellation frees seats in an earlier sauna, existing seats are moved there, only from the saunas that were filled last. Moving keeps the last saunas free so they can be booked in full. Moves are allowed at any time, also shortly before the start. A move must be complete before the freed sauna can be booked in full. Guests are not told which sauna their seats are in, so no notice is sent when seats move. The administrator can see in the system which sauna the seats are placed in. On site, guests can move freely between all saunas that are not booked in full and choose their own seat, so the placement is the system's way of keeping count and is not an assignment guests must follow. |
| Whole-sauna booking | Configurable per sauna. A sauna booked in full leaves the individual-seat capacity for that window. Allowed only if no individual seat is placed in that sauna in that window. Because seats fill one sauna at a time, the saunas later in the fill order usually stay empty and can still be booked in full. |
| Whole-booking-only windows | The administrator can mark a sauna's window as whole-booking-only and reverse it. |
| 06:00 rule | Per time window and sauna: if a sauna is not booked in full for a window (for example 18:00), its seats open for individual booking at 06:00 the same morning. The administrator can reverse it. |
| Children | Under 14 years by default. A child uses one seat of capacity. The administrator chooses whether children have a lower price than adults or pay the adult price; by default they pay the adult price. |
| Pricing | Individual seats are priced per person (an adult price, plus a child price if the administrator turns it on); a whole sauna has one price. The per-person price is the same across saunas; the whole-sauna price is set per sauna. Applies to a time window (for example 15:00 to 16:30). Several windows can be booked, consecutive or not, together or as separate bookings one after another, paying for each window. |
| Seat hold | Seats are held and hidden from other guests while a booking is in progress. Hold time set by the administrator, 10 minutes by default; released if not completed. |
| Overbooking fallback | If overbooking still occurs, the latest booking loses and is refunded. The guest gets an apology email that says the amount will be refunded and that it may take a few days to arrive in the recipient's account. If a door code has already been sent, the same email says it must not be used. |
| Cancellation and change | Individual seats are not offered a cash refund. Up to 12 hours before the window starts, a guest can either change individual seats (one at a time, for example 1 of 4, or all together, e.g. to a different time window), or, on that same notice, choose a voucher (tilgodebevis) issued by email instead of changing. Capacity is restored either way and the administrator sees it. A whole-sauna booking can be cancelled or changed to a different time up to 72 hours before the window starts. On cancellation, the guest chooses a simulated refund or a voucher (tilgodebevis) issued by email, which expires one year after issue. Capacity is restored, and the administrator sees the cancellation or change. |
| Door codes | 20 minutes before a booked window starts, the booker receives an email with a code that unlocks the sauna door. Simulated in the first version: no real lock is connected, and the email is simulated like all other email. The code is shared per sauna and time window: everyone booked into that sauna for that window gets the same code. The code is valid from 20 minutes before the start until the window ends. A whole-sauna booking gets that sauna's code. An individual-seat booking gets the codes for the saunas that are not booked in full in that window, since seat guests move freely between them and are not told which sauna their seats are placed in. A booking made less than 20 minutes before the start gets the email at once. If a booking later loses to the overbooking fallback, the apology email also says the door code must not be used. The administrator can see and resend the codes. [ASSUMPTION: one email per booking, sent to the booker, who shares the code with their group.] |
| Gift cards | A guest buys a gift card, no account needed, and pays (simulated); it is emailed to the buyer's own address as a coupon code. The buyer can print it or forward it to someone else. The value is either a fixed denomination or an amount the buyer chooses, up to a set limit; the administrator sets the denominations and the limit. Whoever holds the code books a sauna with it, with or without an account; it can be used for both individual seats and whole-sauna bookings. A gift card can be used in part, with the remaining balance kept for later bookings, and a booking can be paid partly by gift card and the rest by the ordinary (simulated) payment. A gift card expires one year after it is issued, same as a cancellation voucher. |
| Accounts | An account is optional: a guest can book with or without one, and buying a gift card also needs no account. Either way, the booker receives a confirmation email with a booking reference and a link to change or cancel that booking; the link is how an account-less guest manages their own booking afterwards. Bookings made without an account are not attached to an account created later. There can be one or more administrator accounts. |
| Time windows | Set freely by the administrator (no fixed length per sauna). |
| Email | Simulated (no real provider) in the first version. |

Times, limits and options in this table are defaults the administrator can change; see Administrator settings.

## Administrator settings

Rules that may differ between venues and websites are settings, not fixed code, so a new website can be connected without code changes. Tests run against the defaults.

| Setting | Default |
|---|---|
| Deadline to change individual seats or take a voucher | 12 hours before the window starts |
| Deadline to cancel or change a whole-sauna booking | 72 hours before the window starts |
| Options when a whole-sauna booking is cancelled | Guest chooses a simulated refund or a voucher |
| When the door-code email is sent | 20 minutes before the window starts (the code is valid from then until the window ends) |
| When seats open for individual booking | 06:00 the same morning |
| Separate child price | Off (children pay the adult price) |
| Child age limit | Under 14 |
| Seat hold during booking | 10 minutes |
| Validity of gift cards and vouchers | One year from issue |

Already set by the administrator: time windows, capacity, prices, fill order, whole-booking-only windows, which saunas can be booked in full, and gift card denominations and limit.

A changed setting applies only to bookings made after the change; existing bookings keep the rules they were made under (for example, a guest who booked under a 72-hour cancellation cut-off keeps it if the administrator later changes it to 48 hours).

### Per-website settings and access (after the exam)

Not built in the first version, but the architecture should leave room for them:

- Registered websites: which websites may use the platform, each with its own key or allowed domain, and the option to switch one off.
- Which venue and saunas each website shows.
- The venue's name, logo, colours and contact details.
- Email sender name and address, and templates for confirmation, door code, voucher and apology emails.
- Time zone and currency.
- Languages offered.
- Terms and privacy statement.
- Administrator roles limited to one website, so an administrator of one website cannot see or change another's bookings or personal data.

## Constraints

- Delivery in about 3 months; then optional further development.
- No licensed, trademarked, copyrighted or otherwise protected material on the site or in the platform. Images, fonts, icons and names must be AI-generated or freely licensed, unless the author has found or invented something and checked it.
- Website and platform in English; more languages may be added later.
- Technology direction: Python backend, JavaScript frontend. Specific frameworks are left to the architecture phase.
- The booking platform must be separate from the website, so that more websites can be connected to it after the exam if desired. The first version builds and connects one website. How the separation is made (for example an API the website calls, and how a website identifies itself to the platform) is an architecture decision.

## Exam requirements (source)

Project code and functionality: an AI-generated application. Documentation must show how AI was used and how the students quality-assured the code.

## Security and personal data note

Requirement: the website and the booking platform must be protected against hacking, and all personal data in particular. Guest and administrator accounts store personal data (name, email, credentials). Even in a fictional service, the documentation should state what is stored, why, and how it is protected.

Starting points for the PRD and architecture (not yet decided): hashed passwords, encrypted connections (HTTPS), input validation against injection and cross-site scripting, role-based access so guests cannot reach administrator functions, protection against brute-force login attempts, up-to-date dependencies, storing only the data needed, and security tests as part of quality assurance.

## Open questions on individual seats

Answered: seats are placed in one sauna until it is full and then in the next; the administrator sets the fill order; a group may be split; a group that wants to stay together must book a whole sauna; guests see the total number of free seats; the per-person price is the same across saunas; after a cancellation, seats move into earlier saunas from the saunas filled last. The late whole-sauna question is resolved by the rule that a sauna holding individual seats cannot be booked in full.

Also answered: guests are not told which sauna their seats are in, so moves need no notice; moves are allowed at any time; a move must be complete before the freed sauna can be booked in full.

Nothing on individual seats is open now. How the move is made safe against concurrent bookings is a design task for the architecture.

## Open questions on gift cards

Answered: buying a gift card needs no account. The value is either a fixed denomination or an amount the buyer chooses, up to a set limit. A gift card can be used for both individual seats and whole-sauna bookings. A gift card expires one year after issue, the same rule as a cancellation voucher (tilgodebevis) — which points toward the two sharing a coupon-code mechanism, though that is still an architecture decision, not a stated one.

Also answered: the administrator sets the fixed denominations and the limit on a buyer-chosen amount. A gift card can be used in part, with the remaining balance kept for later bookings, and a booking can be paid partly by gift card and the rest by the ordinary (simulated) payment.

Nothing on gift cards is open now.

## Open questions on door codes

Answered: the code is shared per sauna and time window; a booking made less than 20 minutes before the start gets the code at once; if a booking loses to the overbooking fallback after the code was sent, the apology email says the code must not be used; the administrator can see and resend codes; a code is valid from 20 minutes before the start until the window ends.

Nothing on door codes is open now.

## Open questions on booking without an account

Answered: a guest receives a link in the confirmation email to change or cancel their booking; this is how an account-less guest manages it afterwards.

Also answered: an account-less guest who later creates an account does not get their past bookings attached to it; those bookings are still managed through the link in their confirmation email.

Nothing on booking without an account is open now.
