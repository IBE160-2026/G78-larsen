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
| Seat placement | Seats are placed in one sauna until it is full, then in the next. A group may therefore be split across saunas. The booking flow must make clear that the guest books seats, not a sauna; a group that wants to stay together must book a whole sauna. The administrator sets the fill order. When a cancellation frees seats in an earlier sauna, existing seats are moved there, only from the saunas that were filled last. Moving keeps the last saunas free so they can be booked in full. Moves are allowed at any time, also shortly before the start. A move must be complete before the freed sauna can be booked in full. Guests are not told which sauna their seats are in, so no notice is sent when seats move (except with one-sauna access, where all seats in a booking stay in one sauna; see Door codes). The administrator can see in the system which sauna the seats are placed in. On site, guests can move freely between all saunas that are not booked in full and choose their own seat, so the placement is the system's way of keeping count and is not an assignment guests must follow. With one-sauna access, the placement is the sauna the guest uses. |
| Gradual opening | Optional, set by the administrator. Off: seats draw on all saunas not booked in full, as described above. On: saunas open for individual seats one at a time in the fill order. When the open sauna is full, the next sauna that is not booked in full opens automatically, until the maximum number of saunas the administrator has set is reached, and as long as a sauna is free. Guests see only the free seats in the open saunas; saunas not yet opened stay free for whole-sauna booking. If no whole sauna is booked in a window and the maximum is the number of saunas, all saunas can end up open for individual seats. An individual-seat booker gets the door codes for the open saunas only. [ASSUMPTION: when seat moves after a cancellation empty the last opened sauna, it closes again and is free for whole-sauna booking.] |
| Whole-sauna booking | Configurable per sauna. A sauna booked in full leaves the individual-seat capacity for that window. Allowed only if no individual seat is placed in that sauna in that window. Because seats fill one sauna at a time, the saunas later in the fill order usually stay empty and can still be booked in full. |
| Whole-booking-only windows | The administrator can mark a sauna's window as whole-booking-only and reverse it. |
| 06:00 rule | Per time window and sauna: if a sauna is not booked in full for a window (for example 18:00), its seats open for individual booking at 06:00 the same morning. The administrator can reverse it. The administrator can also set another time than 06:00, or turn the rule off; with the rule off, the seats do not open for individual booking and the sauna stays available only for whole-sauna booking in that window. [ASSUMPTION: "off" means the seats never open, not that they are open from the start.] |
| Children | Under 14 years by default. A child uses one seat of capacity. The administrator chooses whether children have a lower price than adults or pay the adult price; by default they pay the adult price. |
| Pricing | Individual seats are priced per person (an adult price, plus a child price if the administrator turns it on); a whole sauna has one price. The per-person price is the same across saunas; the whole-sauna price is set per sauna. Applies to a time window (for example 15:00 to 16:30). Several windows can be booked, consecutive or not, together or as separate bookings one after another, paying for each window. |
| Booking deadline | A time window can be booked until a deadline the administrator sets, 5 minutes after the window starts by default. The administrator can set it earlier or later, also before the start. After the deadline, the window is no longer offered. [ASSUMPTION: applies to both individual seats and whole saunas, and to changing a booking into that window.] |
| Seat hold | Seats are held and hidden from other guests while a booking is in progress. Hold time set by the administrator, 10 minutes by default; released if not completed. |
| Overbooking fallback | If overbooking still occurs, the latest booking loses and is refunded. The guest gets an apology email that says the amount will be refunded and that it may take a few days to arrive in the recipient's account. If door codes have already been sent, the same email says they must not be used. |
| Cancellation and change | Individual seats are not offered a cash refund. Up to 12 hours before the window starts, a guest can either change individual seats (one at a time, for example 1 of 4, or all together, e.g. to a different time window), or, on that same notice, choose a voucher (tilgodebevis) issued by email instead of changing. Capacity is restored either way and the administrator sees it. A whole-sauna booking can be cancelled or changed to a different time up to 72 hours before the window starts. On cancellation, the guest chooses a simulated refund or a voucher (tilgodebevis) issued by email, which expires one year after issue. Capacity is restored, and the administrator sees the cancellation or change. |
| Door codes | Door codes apply only to saunas with self-service door locks. The administrator marks per sauna whether it has one; a sauna without one gets no codes, and a booking that only gives access to such saunas gets no door-code email. [ASSUMPTION: the fictional venue has self-service locks on all its saunas, so the door-code rules can be shown and tested; with one-sauna access, a booker whose sauna has no self-service lock is still told which sauna it is, by email at the same time, without codes.] At a time the administrator chooses before a booked window starts (20 minutes by default), the booker receives an email with the codes that unlock the doors they may use. Simulated in the first version: no real lock is connected, and the email is simulated like all other email. Each door has its own code per time window, so a sauna with more than one door can have a different code on each. [ASSUMPTION: the administrator registers the doors and which sauna each one belongs to.] A code is shared by everyone who may use that door in that window, and is valid from the send time until the window ends. A whole-sauna booking gets the codes for that sauna. An individual-seat booking gets the codes only for the saunas open for individual seats in that window: not booked in full, not held back as whole-booking-only, and, with gradual opening on, already opened. Seat guests move freely between those saunas and are not told which one their seats are placed in. If another sauna opens for individual seats after the codes are sent (for example with gradual opening), those bookers get an extra email with its codes. One-sauna access (optional, set by the administrator, who can turn it on and off): seat guests may not move between saunas, so an individual-seat booking gives access to one sauna only, and all seats in the booking are placed in the same sauna. [ASSUMPTION: seats go to the first open sauna in the fill order with room for the whole booking; with gradual opening, the next sauna opens if no open sauna has room; seat moves after a cancellation move whole bookings, never part of one.] The door-code email then names that sauna and gives only its codes. If the seats are moved to another sauna after the email is sent, the booker gets a new email with the new sauna and its codes, and the extra email for newly opened saunas is not sent. A booking made after the send time gets the email at once. If a booking later loses to the overbooking fallback, the apology email also says the door codes must not be used. The administrator can see and resend the codes. [ASSUMPTION: one email per booking, sent to the booker, who shares the codes with their group.] |
| Heater and temperature control | The administrator marks per sauna whether its heater has external control. For those saunas, the administrator sets per sauna when heating starts, as a time before the window starts, and when it is turned off. Heating starts only for windows where that sauna has at least one booking; a sauna without bookings in a window is not heated. Simulated in the first version: no real heater is connected, and the platform only records and shows when heating would start and stop. [ASSUMPTION: the off time is set relative to the end of the window, and if the next window in the same sauna is also booked, the heater stays on instead of turning off and on again.] Temperature control: the administrator marks per sauna whether it has temperature control. For those saunas, the guest normally sets the temperature during the visit, and the administrator can see the current temperature, turn the heating on and off, and override the guest's setting, for example if it is too hot or too cold. The administrator's override takes precedence over the guest's setting. Simulated in the first version: temperatures are simulated values. [ASSUMPTION: the guest sets the temperature on a control panel in the sauna, not through the website or platform; the override lasts until the administrator removes it or the window ends.] |
| Gift cards | A guest buys a gift card, no account needed, and pays (simulated); it is emailed to the buyer's own address as a coupon code. The buyer can print it or forward it to someone else. The value is either a fixed denomination or an amount the buyer chooses, up to a set limit; the administrator sets the denominations and the limit. Whoever holds the code books a sauna with it, with or without an account; it can be used for both individual seats and whole-sauna bookings. A gift card can be used in part, with the remaining balance kept for later bookings, and a booking can be paid partly by gift card and the rest by the ordinary (simulated) payment. A gift card expires one year after it is issued, same as a cancellation voucher. |
| Membership | Optional, off by default; the administrator turns it on and off. The administrator sets the membership periods offered (for example one year) and their prices, and the member prices: a per-person member price for individual seats, per time window like the ordinary prices. The administrator also decides whether a member who books a whole sauna gets a whole-sauna member price, set per sauna; if not, the member pays the ordinary whole-sauna price. On by default. A guest buys a membership with the ordinary (simulated) payment and, while it is valid, books at the member price. The member price covers only the member in the booking; other seats in the same booking pay the ordinary price. A membership is not refunded. [ASSUMPTION: a membership is tied to a guest account and the member must be logged in to get the member price; it is valid from the purchase date for the chosen period; the price is settled when the booking is made, so a membership that expires before the window keeps the member price for bookings already made.] Renewal and payment: see Renewal and payment of memberships and period cards. |
| Period cards | Optional, off by default; the administrator turns them on and off. The administrator sets the card periods offered (for example one month) and their prices. A guest buys a period card with the ordinary (simulated) payment and, while it is valid, books individual seats with no extra payment. Card bookings follow the ordinary booking rules: capacity, seat hold, booking deadline, seat placement and door codes. The administrator sets how many future bookings a cardholder can hold at once, meaning card bookings whose window has not yet started; one by default. The limit keeps the card from being used to block many seats at no cost. A period card is not valid for whole-sauna bookings, and it is not refunded. [ASSUMPTION: a period card is tied to a guest account and the cardholder must be logged in to use it; it covers the cardholder's own seat, one per time window, and other seats in the same booking pay the ordinary price; it covers windows that start while the card is valid; a card booking can be changed or cancelled up to the change cut-off for individual seats, but gives no voucher, since nothing was paid for it.] Renewal and payment: see Renewal and payment of memberships and period cards. |
| Renewal and payment of memberships and period cards | The administrator chooses whether memberships and period cards renew automatically at the end of the period; automatic renewal is the default. A guest can turn off automatic renewal of their own membership or period card in their account; it then stays valid until the end of the period already paid for. By default, a membership or period card cannot be paid with a gift card or voucher, only with the ordinary (simulated) payment; the administrator can allow gift cards and vouchers. [ASSUMPTION: a renewal is charged through the simulated payment for a new period of the same length at the current price, and the guest gets an email about it; the renewal setting and the payment setting apply to memberships and period cards alike; a renewal is paid only with the ordinary (simulated) payment, never drawn from a gift card or voucher.] |
| Accounts | An account is optional: a guest can book with or without one, and buying a gift card also needs no account. Either way, the booker receives a confirmation email with a booking reference and a link to change or cancel that booking; the link is how an account-less guest manages their own booking afterwards. Bookings made without an account are not attached to an account created later. [ASSUMPTION: buying and using a membership or period card requires an account.] There can be one or more administrator accounts. |
| Time windows | Set freely by the administrator (no fixed length per sauna). |
| Email | Simulated (no real provider) in the first version. |

Times, limits and options in this table are defaults the administrator can change; see Administrator settings.

## Administrator settings

Rules that may differ between venues and websites are settings, not fixed code, so a new website can be connected without code changes. Tests run against the defaults.

| Setting | Default |
|---|---|
| Last time a window can be booked | 5 minutes after the window starts |
| Deadline to change individual seats or take a voucher | 12 hours before the window starts |
| Deadline to cancel or change a whole-sauna booking | 72 hours before the window starts |
| Options when a whole-sauna booking is cancelled | Guest chooses a simulated refund or a voucher |
| When the door-code email is sent | 20 minutes before the window starts (the codes are valid from then until the window ends) |
| When seats open for individual booking | 06:00 the same morning; the administrator can set another time or turn the rule off |
| Gradual opening of saunas for individual seats | Off (all saunas not booked in full are open for individual seats) |
| Maximum number of saunas open for individual seats (gradual opening) | All saunas |
| Door access for an individual-seat booking | All saunas open for individual seats; guests may move between them (alternative: one sauna only, with all seats in a booking in the same sauna) |
| Self-service door lock | Set per sauna by the administrator |
| Temperature control | Off for every sauna |
| External heater control | Off for every sauna; when turned on, the administrator sets per sauna when heating starts and when it is turned off (no default times) |
| Separate child price | Off (children pay the adult price) |
| Child age limit | Under 14 |
| Seat hold during booking | 10 minutes |
| Validity of gift cards and vouchers | One year from issue |
| Memberships | Off; when turned on, the administrator sets the periods, their prices and the member prices (no defaults) |
| Period cards | Off; when turned on, the administrator sets the periods and their prices (no defaults) |
| Future bookings a cardholder can hold at once | 1 |
| Automatic renewal of memberships and period cards | On (a guest can turn it off for their own membership or card) |
| Whole-sauna member price | On (a member who books a whole sauna gets the whole-sauna member price the administrator sets per sauna) |
| Gift cards and vouchers as payment for memberships and period cards | Not allowed |

Already set by the administrator: time windows, capacity, prices, fill order, whole-booking-only windows, which saunas can be booked in full, and gift card denominations and limit.

A changed setting applies only to bookings made after the change; existing bookings keep the rules they were made under (for example, a guest who booked under a 72-hour cancellation cut-off keeps it if the administrator later changes it to 48 hours). [ASSUMPTION: in the same way, memberships and period cards already sold stay valid for their period and keep their terms if the administrator turns the offer off or changes prices.]

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

Answered: the administrator chooses when the codes are sent; each door has its own code per time window, shared by everyone who may use that door; a booking made after the send time gets the codes at once; an individual-seat booker never gets codes for a sauna that is not open for individual seats; if a booking loses to the overbooking fallback after the codes were sent, the apology email says they must not be used; the administrator can see and resend codes; a code is valid from the send time until the window ends.

Also answered: if a sauna opens for individual seats after the codes are sent, individual-seat bookers get an extra email with its codes. The administrator can choose one-sauna access, where an individual-seat booking gets the name and codes of one sauna only, and a new email is sent if the seats are moved to another sauna after the codes were sent.

Also answered: with one-sauna access, seat guests may not move between saunas, and all seats in a booking are placed in the same sauna. The administrator can turn this on and off.

Nothing on door codes is open now.

## Open questions on booking without an account

Answered: a guest receives a link in the confirmation email to change or cancel their booking; this is how an account-less guest manages it afterwards.

Also answered: an account-less guest who later creates an account does not get their past bookings attached to it; those bookings are still managed through the link in their confirmation email.

Nothing on booking without an account is open now.

## Open questions on memberships and period cards

Answered: the administrator chooses whether memberships and period cards are offered. A membership lasts a period, for example a year, and gives discounted member prices. A period card, for example a monthly card, lets the holder book individual seats with no extra payment.

Also answered: the administrator sets how many future bookings a cardholder can hold at once (one by default); the administrator chooses whether memberships and period cards renew automatically (on by default); by default they cannot be paid with a gift card or voucher, and the administrator can allow it.

Also answered: the member price covers only the member in the booking, and other seats pay the ordinary price. A period card is not valid for whole-sauna bookings.

Also answered: the administrator decides whether a member who books a whole sauna gets a whole-sauna member price. Memberships and period cards are not refunded. A guest can turn off automatic renewal of their own membership or period card in their account, and it stays valid until the end of the period already paid for. A whole-sauna member price is on by default.

Nothing on memberships and period cards is open now. The remaining details are assumptions in the Membership, Period cards and Renewal rows.
