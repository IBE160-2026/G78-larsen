---
title: "Addendum: Booking platform brief"
created: 2026-09-20
updated: 2026-10-29
---

# Addendum: Booking platform

Detail that belongs in the PRD and architecture rather than the brief.

## Delivery phases

The brief splits delivery into the first version (v1), step 2 and the vision. The rules below are written in full, but are built in this order.

| Phase | Rows and settings |
|---|---|
| v1 core | Individual seats (name and email, no account; simulated instant payment; confirmation by simulated email), one price per seat (no distinction between children and adults), Time windows, capacity and prices set by seed or configuration without administrator screens, the capacity invariant with atomic booking, the booking horizon, booking deadline and cancellation cut-offs as fixed defaults, administrator login with a booking list, input validation, hashed passwords and role-based access with tests |
| v1 if time, in this order (cancelling before whole-sauna booking is decided; the rest of the order is a proposal, and item 7 was placed last on 2026-10-29) | 1 Change of individual seats or a voucher instead, with no refund (change first, voucher last); 2 Seat placement and Whole-sauna booking (with cancellation and change of a whole sauna); 3 "My booking" page that resends the booking link; 4 Seat hold; 5 Guest accounts; 6 Step 2 (below); 7 the rest of v1: administrator screens for windows, capacity and prices, the five adjustable settings, Blocked periods (without door-code and heating overrides), 06:00 rule, Whole-booking-only windows, Overbooking fallback (without door-code text) |
| Step 2 | Gradual opening and one-sauna access (seat placement options); Gift cards; Door codes (codes, send time, source, resend, extra and moved-sauna emails, one-sauna access as it affects codes, door-code text in the overbooking email and block overrides) |
| Vision | Several locations (A and B: location choice in the guest journey, per-location seat counts, fill order, overview, blocked periods and door codes, and no seat moves between locations); Children and adults (the distinction when booking seats, child age limit and separate child price); Membership; Period cards; Renewal and payment of memberships and period cards; Remote door control; Heater and temperature control (and the heating override in Blocked periods); and their settings |

The core is the smallest v1 that surely finishes (brainstorm of 2026-10-27; see Schedule and build order). Everything else in v1 is built in the order shown only if time allows. The Seat hold rule is item 4 of that order: simulated payment is instant, so the core books in one atomic step without a hold. Gradual opening and one-sauna access are built in step 2, so in v1 all saunas not booked in full are open for individual seats and guests may move between them; one-sauna access also affects door codes. Vouchers (tilgodebevis) are part of v1, since cancellation and change use them; gift cards in step 2 may share their mechanism.

## Guest journey

The guest first chooses **Individual seats** or **Private sauna**. Both paths end the same way: after pressing Book, the guest chooses whether to log in, then accepts the terms and goes on to (simulated) payment, as in the Seat hold rule.

**Individual seats**

1. **Date, window and Book.** The guest picks a date in a calendar, and can change it at any time. The guest gets a list of time windows and the free seats in each, not a list of saunas. The guest picks a time window and the number of seats, and presses Book.
2. **Log in or not.** The guest logs in or continues without an account (see Accounts).
3. **Terms and payment.** The guest accepts the terms and presses to pay.

**Private sauna**

1. **Date, window and Book.** The guest picks a date in a calendar, and can change it at any time. The guest gets a list of free private saunas and their time windows. Two routes:
   - Pick a time window directly.
   - Open a specific sauna, pick the time window, and press Book.
2. **Log in or not.** The guest logs in or continues without an account (see Accounts).
3. **Terms and payment.** The guest accepts the terms and presses to pay.

v1 has one location. Seats draw on the combined capacity of the saunas not booked in full in the chosen window. In the vision, locations A and B become two separate places: the guest first chooses all locations, location A, or location B, sees a list of locations with their time windows and free seats, and books at one of them; free seats are then counted per location. The guest is not told which sauna the seats are placed in (see Individual seats and Seat placement).

## Booking rules (as decided)

| Area | Rule |
|---|---|
| Individual seats | A booking reserves 1 or more seats in a time window. Seats are not tied to a particular sauna: they draw on the combined capacity of all saunas not booked in full in that window. Example: Sauna 1 = 7, Sauna 2 = 10, Sauna 3 = 12, Sauna 4 = 15. If Sauna 1 and Sauna 4 are booked in full, Sauna 2 and Sauna 3 (22 seats) are available for individual booking. Individual booking requires only that seats are available, meaning not every sauna is booked in full. Guests see the total number of free seats. |
| Seat placement | Seats are placed in one sauna until it is full, then in the next. A group may therefore be split across saunas. The booking flow must make clear that the guest books seats, not a sauna; a group that wants to stay together must book a whole sauna. The administrator sets the fill order. The fill order must keep holding after every cancellation, change, block and lifted block, so the last saunas stay free and can be booked in full: no sauna holds more seats than its capacity; a whole-booked or blocked sauna holds none; no sauna earlier in the fill order has free room while a later one holds seats. A whole-sauna booking is accepted only when these conditions hold with that sauna's seats removed, never over seats still in it. Whether this is done by moving stored seats or by deriving the placement from the window's seat count (the research recommends deriving) is an architecture decision; the PRD states the rule as these invariants and as worked examples. Guests are not told which sauna their seats are in, so no notice is sent when seats move (except with one-sauna access, where all seats in a booking stay in one sauna; see Door codes). With one-sauna access, placement is frozen at the send time: no seat is moved after the codes are sent. The administrator can see in the system which sauna the seats are placed in. On site, guests can move freely between all saunas that are not booked in full and choose their own seat, so the placement is the system's way of keeping count and is not an assignment guests must follow. With one-sauna access, the placement is the sauna the guest uses. |
| Gradual opening | Optional, set by the administrator. Off: seats draw on all saunas not booked in full, as described above. On: saunas open for individual seats one at a time in the fill order. When the open sauna is full, the next sauna that is not booked in full opens automatically, until the maximum number of saunas the administrator has set is reached, and as long as a sauna is free. Guests see only the free seats in the open saunas; saunas not yet opened stay free for whole-sauna booking. If no whole sauna is booked in a window and the maximum is the number of saunas, all saunas can end up open for individual seats. An individual-seat booker gets the door codes for the open saunas only. When seat moves after a cancellation empty the last opened sauna, it closes again and is free for whole-sauna booking. |
| Whole-sauna booking | Configurable per sauna. A sauna booked in full leaves the individual-seat capacity for that window. Allowed only if no individual seat is placed in that sauna in that window. Because seats fill one sauna at a time, the saunas later in the fill order usually stay empty and can still be booked in full. |
| Whole-booking-only windows | The administrator can mark a sauna's window as whole-booking-only and reverse it. |
| 06:00 rule | Per time window and sauna: if a sauna is not booked in full for a window (for example 18:00), its seats open for individual booking at 06:00 the same morning. The administrator can reverse it. The administrator can also set another time than 06:00, or turn the rule off; with the rule off, the seats do not open for individual booking and the sauna stays available only for whole-sauna booking in that window. [ASSUMPTION: "off" means the seats never open, not that they are open from the start.] |
| Children and adults | In v1 and step 2 there is no distinction: a guest books seats, and every seat uses one seat of capacity and costs the same, whoever sits in it. Vision: the guest states how many of the seats are for children and how many for adults; the administrator can set an age limit (under 14 by default) and choose whether children have a lower price than adults. |
| Pricing | Individual seats are priced per person (one price per seat; a separate child price is in the vision); a whole sauna has one price. The per-person price is the same across saunas; the whole-sauna price is set per sauna. Applies to a time window (for example 15:00 to 16:30). Several windows can be booked, consecutive or not, together or as separate bookings one after another, paying for each window. |
| Booking deadline | A time window can be booked until a deadline the administrator sets, 5 minutes after the window starts by default. The administrator can set it earlier or later, also before the start. After the deadline, the window is no longer offered. [ASSUMPTION: applies to both individual seats and whole saunas, and to changing a booking into that window.] |
| Booking horizon | A guest can book a time window only if it starts within a period the administrator sets, 4 weeks ahead by default. Windows further ahead are not yet offered to guests. [ASSUMPTION: the period is counted from the moment of booking to the start of the window, so new windows become bookable day by day; it applies to individual seats, whole saunas, period-card bookings and changing a booking into a later window; the administrator can still create and see windows further ahead.] |
| Seat hold | Built only if time allows. Until then, simulated payment is instant and the booking is confirmed in one atomic step that checks and reserves capacity, so there is no hold to expire and no payment after expiry; the atomic-check rule in this row applies to that step. When the hold is built: seats are held and hidden from other guests while a booking is in progress, for a fixed 10 minutes, and released if the booking is not completed. The hold time is not an administrator setting: it depends on how long payment takes, not on the venue, and a wrong value would raise the risk of overbooking. The hold time does not by itself prevent double booking. The platform must check and reserve capacity in one atomic operation, both when seats are held and when a booking is confirmed, so concurrent bookings can never take the same seats. A payment completed after the hold has expired gives a booking only if the seats are still free; otherwise the payment is refunded. |
| Overbooking fallback | If overbooking still occurs, the latest booking loses and is refunded. The guest gets an apology email that says the amount will be refunded and that it may take a few days to arrive in the recipient's account. If door codes have already been sent, the same email says they must not be used. |
| Cancellation and change | Individual seats are not offered a cash refund. Up to 12 hours before the window starts, a guest can either change individual seats (one at a time, for example 1 of 4, or all together, e.g. to a different time window), or, on that same notice, choose a voucher (tilgodebevis) issued by email instead of changing. Capacity is restored either way and the administrator sees it. A whole-sauna booking can be cancelled or changed to a different time up to 72 hours before the window starts. On cancellation, the guest chooses a simulated refund or a voucher (tilgodebevis) issued by email, which expires one year after issue. Capacity is restored, and the administrator sees the cancellation or change. The administrator can change both cut-offs, 12 hours for individual seats and 72 hours for a whole sauna, to another time, but never to less than 2 hours before the window starts. |
| Gift cards | A guest buys a gift card, no account needed, and pays (simulated); it is emailed to the buyer's own address as a coupon code. The buyer can print it or forward it to someone else. The value is either a fixed denomination or an amount the buyer chooses, up to a set limit; the administrator sets the denominations and the limit. Whoever holds the code books a sauna with it, with or without an account; it can be used for both individual seats and whole-sauna bookings. A gift card can be used in part, with the remaining balance kept for later bookings, and a booking can be paid partly by gift card and the rest by the ordinary (simulated) payment. A gift card expires one year after it is issued, same as a cancellation voucher. |
| Accounts | An account is optional: a guest can book with or without one, and buying a gift card also needs no account. Either way, the booker receives a confirmation email with a booking reference and a link to change or cancel that booking; the link is how an account-less guest manages their own booking afterwards. The link carries a long, random token that cannot be guessed, so the booking reference alone gives no access, and the link is the only way into a booking. "My booking" (if time) does not show a booking: the guest enters the reference and the email, and if they match, the link is sent again to that email. The page gives the same answer whether or not they match, so it cannot be used to find out which bookings exist, and the number of attempts per email and per address is limited. [ASSUMPTION: how long a token stays valid, and whether it is stored hashed, are PRD decisions.] Bookings made without an account are not attached to an account created later. Buying and using a membership or period card requires an account. There can be one or more administrator accounts. The administrator has an overview of time windows, bookings, cancellations, prices, fill order and blocked periods. In the vision, with several locations, the overview is per location and an administrator account can switch between them. |
| Blocked periods | The administrator has a calendar and can block one sauna, several, or all of them for booking for a period, for example for maintenance. A blocked sauna cannot be booked in full and gives no seats for individual booking in that period. A blocked sauna gets no door codes and is not heated, unless the administrator overrides this. [ASSUMPTION: the override is chosen per block, separately for door codes and heating, for example so maintenance workers can get in or test the heater; with door codes overridden, codes are made for the blocked sauna and shown to the administrator, who shares them, and no guest gets them; with heating overridden, the sauna is heated in the blocked period as for a booked window; a block covers every window that overlaps the period; the calendar shows windows, bookings and blocks together; if the period already has bookings, the administrator sees them before confirming the block, and the affected guests are told by email and get a full refund or a voucher, as they choose, regardless of the cancellation cut-offs; seats that can move to another open sauna are moved instead, when the sauna has room; the administrator can lift a block, and the sauna is then bookable again.] |
| Time windows | Set by the administrator, the same for every sauna in the venue: a window applies to all saunas, and windows never partly overlap (a window that ends at 16:30 and one that starts at 16:30 do not overlap). The platform rejects an overlapping window. New windows get a standard length, 1 hour 30 minutes by default (for example 15:00 to 16:30). The administrator can set another standard length, and can give a single window another length for the whole venue, as long as no windows overlap. A sauna that is unavailable for part of a window is handled with a block, not with a different window for that sauna. [ASSUMPTION: changing the standard length does not change windows already created.] |
| Email | Simulated (no real provider) in the first version. |

Times, limits and options in this table are defaults. In v1 the administrator can change only the five settings listed under Administrator settings; the other rules are fixed until step 2 or the vision.

The rules for door codes, heater and temperature control, memberships, period cards, and renewal and payment are long and follow as subsections.

### Door codes

Door codes apply only to saunas with self-service door locks. The administrator marks per sauna whether it has one; a sauna without one gets no codes, and a booking that only gives access to such saunas gets no door-code email. [ASSUMPTION: the fictional venue has self-service locks on all its saunas, so the door-code rules can be shown and tested; with one-sauna access, a booker whose sauna has no self-service lock is still told which sauna it is, by email at the same time, without codes.] At a time the administrator chooses before a booked window starts (20 minutes by default), the booker receives an email with the codes that unlock the doors they may use. Simulated in the first version: no real lock is connected, and the email is simulated like all other email. Each door has its own code per time window, so a sauna with more than one door can have a different code on each. The administrator registers the doors and which sauna each one belongs to. The codes come from one of two sources: the administrator enters them, or the platform fetches them from a connected lock system. Simulated in the first version: no real lock system is connected, and the simulated lock system supplies the codes. [ASSUMPTION: the administrator chooses the source per door; a code entered by the administrator can be changed until the door-code email is sent; if a code is missing when the email is due, the administrator is alerted, and the email is sent as soon as the code is in place.] A code is shared by everyone who may use that door in that window, and is valid from the send time until the window ends. A whole-sauna booking gets the codes for that sauna. An individual-seat booking gets the codes only for the saunas open for individual seats in that window: not booked in full, not held back as whole-booking-only, and, with gradual opening on, already opened. Seat guests move freely between those saunas and are not told which one their seats are placed in. If another sauna opens for individual seats after the codes are sent (for example with gradual opening), those bookers get an extra email with its codes. One-sauna access (optional, set by the administrator, who can turn it on and off): seat guests may not move between saunas, so an individual-seat booking gives access to one sauna only, and all seats in the booking are placed in the same sauna. [ASSUMPTION: seats go to the first open sauna in the fill order with room for the whole booking; with gradual opening, the next sauna opens if no open sauna has room; seat moves after a cancellation move whole bookings, never part of one.] The door-code email then names that sauna and gives only its codes. Placement is frozen at the send time, so seats are not moved to another sauna after the email is sent; moves happen only before it, and the email names the sauna the seats are in at that moment. What happens when a block or cancellation would otherwise force a move after the send time is a PRD decision (the research recommends the overbooking fallback). A booking made after the send time gets the email at once. No door-code rule depends on taking back a code already sent, since offline codes cannot be changed or revoked before they expire. After the send time, a whole-sauna booking of a sauna is refused while individual-seat bookers hold its code (in the default mode: while the window has any individual-seat booking and the sauna is open for individual seats). If a booking later loses to the overbooking fallback, the apology email also says the door codes must not be used. The administrator can see and resend the codes. One email is sent per booking, to the booker, who shares the codes with their group. Remote door control: where the lock allows it, the administrator can put a door in open mode, so it opens without a code, quick-open it once, for example to let a guest in, and lock it again at any time. A door in open mode is locked automatically when the window is over. By default, a door put in open mode outside a window is locked automatically when it closes; the administrator can change this rule. Simulated in the first version, like the locks themselves. [ASSUMPTION: the administrator marks per door whether its lock supports remote control; with the rule changed, a door put in open mode outside a window stays open until the administrator locks it; locking a door does not change its code; the platform records who opened or locked a door and when.]

### Heater and temperature control

The administrator marks per sauna whether its heater has external control. For those saunas, the administrator sets per sauna when heating starts, as a time before the window starts, and when it is turned off. Heating starts only for windows where that sauna has at least one booking; a sauna without bookings in a window is not heated. Simulated in the first version: no real heater is connected, and the platform only records and shows when heating would start and stop. [ASSUMPTION: the off time is set relative to the end of the window, and if the next window in the same sauna is also booked, the heater stays on instead of turning off and on again.] Temperature control: the administrator marks per sauna whether it has temperature control. For those saunas, the guest normally sets the temperature during the visit, and the administrator can see the current temperature, turn the heating on and off, and override the guest's setting, for example if it is too hot or too cold. The administrator's override takes precedence over the guest's setting. Simulated in the first version: temperatures are simulated values. [ASSUMPTION: the guest sets the temperature on a control panel in the sauna, not through the website or platform; the override lasts until the administrator removes it or the window ends.]

### Membership

Optional, off by default; the administrator turns it on and off. The administrator sets the membership periods offered (for example one year) and their prices, and the member prices: a per-person member price for individual seats, per time window like the ordinary prices. The administrator also decides whether a member who books a whole sauna gets a whole-sauna member price, set per sauna; if not, the member pays the ordinary whole-sauna price. On by default. A guest buys a membership with the ordinary (simulated) payment and, while it is valid, books at the member price. The member price covers only the member in the booking; other seats in the same booking pay the ordinary price. A membership is not refunded. A membership is tied to a guest account, and the member must be logged in to get the member price. [ASSUMPTION: a membership is valid from the purchase date for the chosen period; the price is settled when the booking is made, so a membership that expires before the window keeps the member price for bookings already made.] Renewal and payment: see Renewal and payment of memberships and period cards.

### Period cards

Optional, off by default; the administrator turns them on and off. The administrator sets the card periods offered (for example one month) and their prices. A guest buys a period card with the ordinary (simulated) payment and, while it is valid, books individual seats with no extra payment. Card bookings follow the ordinary booking rules: capacity, seat hold, booking deadline, seat placement and door codes. The administrator sets how many future bookings a cardholder can hold at once, meaning card bookings whose window has not yet started; one by default. The limit keeps the card from being used to block many seats at no cost. The administrator also sets how many period cards can be sold per period; 50 by default. Renewals come first: automatic renewals of cards from the previous period take their places before any new card is sold, and new cards are sold only from the places left. When the limit is reached, no more period cards are sold for that period. The limit applies to all card types together, and counts every card valid in the period, renewed or new. Periods follow the calendar, so a monthly card runs for a calendar month and all monthly cards share the same periods. Renewals always go through, also if the administrator has lowered the limit below the number of renewals (then no new cards are sold), unless the administrator chooses that renewals must also fit within the limit. If a limit across all card types together turns out not to be possible, the administrator must offer only one card type at a time, for example only monthly cards. [ASSUMPTION: with card types of different length, a card counts toward the limit in every calendar month it covers, so a three-month card takes a place in each of its three months; if renewals must fit within the limit and there are not enough places, the cards that have been held longest are renewed first, and the others get an email that their card was not renewed.] A period card is not valid for whole-sauna bookings, and it is not refunded. [ASSUMPTION: a period card is tied to a guest account and the cardholder must be logged in to use it; it covers the cardholder's own seat, one per time window, and other seats in the same booking pay the ordinary price; it covers windows that start while the card is valid; a card booking can be changed or cancelled up to the change cut-off for individual seats, but gives no voucher, since nothing was paid for it.] Renewal and payment: see Renewal and payment of memberships and period cards.

### Renewal and payment of memberships and period cards

The administrator chooses whether memberships and period cards renew automatically at the end of the period; automatic renewal is the default. A guest can turn off automatic renewal of their own membership or period card in their account; it then stays valid until the end of the period already paid for. By default, a membership or period card cannot be paid with a gift card or voucher, only with the ordinary (simulated) payment; the administrator can allow gift cards and vouchers. [ASSUMPTION: a renewal is charged through the simulated payment for a new period of the same length at the current price, and the guest gets an email about it; the renewal setting and the payment setting apply to memberships and period cards alike; a renewal is paid only with the ordinary (simulated) payment, never drawn from a gift card or voucher.]

## Administrator settings

In v1, only five rules are adjustable settings, each with a default. All other rules are fixed in v1 and work as described in this addendum; they become settings in step 2 or the vision. Tests run against the defaults.

| Setting (v1) | Default |
|---|---|
| How far ahead a guest can book | Up to 4 weeks before the window starts |
| Last time a window can be booked | 5 minutes after the window starts |
| Deadline to change individual seats or take a voucher | 12 hours before the window starts (no less than 2 hours) |
| Deadline to cancel or change a whole-sauna booking | 72 hours before the window starts (no less than 2 hours) |
| When seats open for individual booking | 06:00 the same morning; the administrator can set another time or turn the rule off |

### Fixed in v1 (settings later)

Not adjustable in v1. The value shown is the one the platform uses; where a rule is optional or belongs to a later step, it is off or not built in v1.

| Rule | Value in v1 |
|---|---|
| Standard length of a time window | 1 hour 30 minutes (the administrator can still give a single window another length for the whole venue, if no windows overlap) |
| Options when a whole-sauna booking is cancelled | Guest chooses a simulated refund or a voucher |
| When the door-code email is sent | 20 minutes before the window starts (the codes are valid from then until the window ends) |
| Gradual opening of saunas for individual seats (step 2) | Off (all saunas not booked in full are open for individual seats) |
| Maximum number of saunas open for individual seats (gradual opening) | All saunas |
| Door access for an individual-seat booking | All saunas open for individual seats; guests may move between them (alternative: one sauna only, with all seats in a booking in the same sauna) |
| Self-service door lock | Set per sauna by the administrator |
| Remote door control (open mode, quick-open, lock) | Set per door by the administrator, where the lock allows it; a door in open mode is locked automatically when the window is over |
| Door put in open mode outside a window | Locked automatically when it closes (alternative: stays open until the administrator locks it) |
| Source of door codes | Set per door: entered by the administrator or fetched from a connected lock system (simulated in the first version) |
| Temperature control | Off for every sauna |
| External heater control | Off for every sauna; when turned on, the administrator sets per sauna when heating starts and when it is turned off (no default times) |
| Distinction between children and adults when booking seats (vision) | Off (a guest books seats only) |
| Separate child price (vision) | Off (every seat costs the same) |
| Child age limit (vision) | Under 14 |
| Validity of gift cards and vouchers | One year from issue |
| Memberships | Off; when turned on, the administrator sets the periods, their prices and the member prices (no defaults) |
| Period cards | Off; when turned on, the administrator sets the periods and their prices (no defaults) |
| Future bookings a cardholder can hold at once | 1 |
| Period cards that can be sold per period | 50, all card types together (renewals first, new cards from the places left) |
| Renewals of period cards go through even above the limit | On |
| Automatic renewal of memberships and period cards | On (a guest can turn it off for their own membership or card) |
| Whole-sauna member price | On (a member who books a whole sauna gets the whole-sauna member price the administrator sets per sauna) |
| Gift cards and vouchers as payment for memberships and period cards | Not allowed |

Already set by the administrator: time windows, capacity, prices, fill order, whole-booking-only windows, which saunas can be booked in full, and gift card denominations and limit.

A changed setting applies only to bookings made after the change; existing bookings keep the rules they were made under (for example, a guest who booked under a 72-hour cancellation cut-off keeps it if the administrator later changes it to 48 hours). [ASSUMPTION: in the same way, memberships and period cards already sold stay valid for their period and keep their terms if the administrator turns the offer off or changes prices.]

### Per-website settings and access (after the exam)

Not built in the first version, which has a single API between the platform and its one website and no support for several websites. The architecture should leave room for them:

- Registered websites: which websites may use the platform, each with its own key or allowed domain, and the option to switch one off.
- Which venue and saunas each website shows.
- The venue's name, logo, colours and contact details.
- Email sender name and address, and templates for confirmation, door code, voucher and apology emails.
- Time zone and currency.
- Languages offered.
- Terms and privacy statement.
- Administrator roles limited to one website, so an administrator of one website cannot see or change another's bookings or personal data.

## Research input

Three technical research runs fed the update of 2026-10-29, all under `.docs/planning-artifacts/research/`: `technical-booking-concurrency-seat-holds-2026-10-27`, `technical-kapasitetsmodell-enkeltplasser-2026-10-28` (85 examples in groups A to I) and `technical-smart-lock-door-code-overlap-and-revoke-2026-10-28`. Each report marks what is sourced and what is the lead's inference. Limits that carry over: the database findings cover PostgreSQL only, no performance figure could be sourced, no sauna comparable was found, and lock behaviour is known mostly through integrator and forum material.

**Decided (2026-10-29):** see the Time windows, Seat placement and Door codes rows (E1, E3, H12, H21).

**Recommended, to be decided in the PRD.** The research gives each case an answer; none is a decision yet.

| Case | Research ID | Recommended answer |
|---|---|---|
| A block is lifted | D7 | Seats move back so the fill-order rule holds again |
| A sauna is marked whole-booking-only while it holds seats | D8 | Refused, or treated as a block |
| A block leaves too little capacity | D3 | The latest booking loses, whole bookings only, with refund or voucher; the administrator sees the list before confirming |
| Capacity is lowered | F1 | Refused while a future window would exceed it, or handled like D3 |
| The fill order is changed | F2 | Applies to windows that have not started |
| A cancellation or block affects a window that has started | F3 | No seat moves; the overbooking fallback applies |
| Two codes valid on one door at back-to-back windows | H6 | Accept the overlap and say so (or start validity at the window start); the codes must differ; the simulated lock rejects a duplicate PIN on a door |
| The send time is changed | H10 | Applies only to windows whose email is not yet sent |
| A code is not in place at the send time | H11 | Send only when the lock confirms the code; alert the administrator if it is not confirmed in time; delete expired codes |
| A block after the codes are sent | H13 | Correction email to every seat booker of the window; where a door's codes are online, also replace the code; mark per door whether its codes can be replaced |
| A block is lifted after the codes are sent | H14 | Extra email with the code |
| One booker cancels after the codes are sent | H15 | "Must not be used" is a request; replacing the code is best effort |
| One-sauna access is turned on while future bookings are split | H23 | Refused while any future window has a split booking |
| Heating (vision) | I11 to I23 | Decided when heating is built; the report gives an answer per case. Unknown: how long a heater takes to warm up |

**Concurrency requirements the PRD can state** (from the concurrency research, beyond the Seat hold and Concurrency tests rows): when the hold is built, it is stored with an expiry and ignored once expired, even if cleanup has not run (low confidence, one weak source); payment callbacks are idempotent; a seat change is atomic and cannot interleave with a whole-sauna booking; serialization failures and deadlocks are retried a bounded number of times, then the guest gets a clean error; no speed or throughput figure is stated, and any load-test target is set after measuring.

**Test approach.** Run group C of the capacity-model report as parallel tests. Add a model-based test that generates sequences of bookings, cancellations and blocks, checks the placement invariants after each step, and compares the derived formula with a brute-force reference.

## Schedule and build order

From the brainstorm on the smallest v1 (`.docs/brainstorming/brainstorm-minste-v1-mvp-2026-10-27/brainstorm-intent.md`). Marking: **decided** by Lisa in the session; **proposal** from the coach, not yet confirmed.

- **Constraints (decided):** one person, 27 October to 15 December 2026; two other exams, 16 November and 8 December; Claude tokens and long-running tasks are a real limit; frontend, design and extensive testing are the likeliest overruns. Planning (PRD and architecture) takes 7 to 8 of the first 12 days, then coding as tokens allow.
- **Core (decided):** booking individual seats end to end, with time windows, capacity and prices in the database, a free-text name, simulated instant payment, confirmation with a booking reference by email, the database enforcing that booked seats never exceed capacity, and the administrator as a password login with a booking list. **Proposal:** no guest account; one booking page and one confirmation page; the browser's date picker; windows as a list with free seats; the simulated email as an outbox table, also shown on the confirmation page; one seeded administrator account.
- **Build order (proposal):** planning limited to the core; database engine, schema and the capacity invariant; a thin end-to-end booking first, so an interruption always leaves a running app; the rest of the core with tests written in each story; administrator login and list; a freeze from 9 to 15 December for tests, README (test users, sample data, how to start the frontend) and the AI-use documentation, with no new features. Windows: 27 October to about 8 November, 17 November to about 1 December, and the freeze.
- **Risk handling (proposal, tokens partly decided):** small stories with acceptance criteria taken from the brief, a token budget per story logged in the session log as evidence of how the AI was steered, mechanical tasks at lower effort; one stylesheet with a Finnish-inspired palette, mobile first, no design system; test depth on concurrency, capacity, validation and criterion 1, breadth only for the rest.
- **Decisions from the brainstorm of 2026-10-27 that changed the rules above.** The "My booking" page only resends the link and never gives access by itself (decided 2026-10-29; see Accounts), so the brainstorm's lookup by reference plus email is dropped. Individual seats never get a cash refund, only a change or a voucher (decided 2026-10-29), so the brainstorm's idea of a simulated refund first is dropped.

## Constraints

- Delivery by 15 December 2026, by one person; then optional further development.
- No licensed, trademarked, copyrighted or otherwise protected material on the site or in the platform. Images, fonts, icons and names must be AI-generated or freely licensed, unless the author has found or invented something and checked it.
- Website and platform in English; more languages may be added later.
- Technology direction: Python backend, JavaScript frontend. Specific frameworks are left to the architecture phase.
- The booking platform must be separate from the website, and in v1 the separation is a single API the website calls. The first version builds and connects one website only, with no support for several websites: no website registration, no per-website keys or settings. Connecting more websites after the exam is possible later, but is not built or prepared beyond keeping the API clean.

## Exam requirements (source)

Project code and functionality: an AI-generated application. Documentation must show how AI was used and how the students quality-assured the code.

## Security and personal data note

Requirement: the website and the booking platform must be protected against hacking, and all personal data in particular. Guest and administrator accounts store personal data (name, email, credentials). Even in a fictional service, the documentation should state what is stored, why, and how it is protected.

Starting points for the PRD and architecture (not yet decided): hashed passwords, input validation against injection and cross-site scripting, role-based access so guests cannot reach administrator functions, protection against brute-force login attempts, up-to-date dependencies, storing only the data needed, and security tests as part of quality assurance.

## Concurrency tests

The Seat hold rule requires capacity to be checked and reserved in one atomic operation. v1 proves it with automated tests that run bookings in parallel, not one after another. The main case is two guests booking the last free seat in a window at the same time. The cases about holds (the first, fourth and fifth rows) apply once the hold is built; without it, the confirm case and the free-seats case are tested.

| Case | Expected result |
|---|---|
| Two guests hold the last free seat at the same moment | Exactly one hold succeeds. The other guest is told no seat is free and nothing is held for them. |
| Two guests confirm a booking for the last free seat at the same moment | Exactly one booking is confirmed. The other is rejected and not charged (simulated), and gets no confirmation email. |
| Free seats after either case | Zero, never negative. The administrator sees one booking, not two. |
| The first guest's hold expires and the second guest then books | The second booking succeeds, since the seat is free again. |
| A payment completes after the hold has expired, and the seat was taken meanwhile | No booking is made and the payment is refunded (simulated), as in the Seat hold rule. |

[ASSUMPTION: the test repeats the race many times, for example 100, because a single run can pass by luck. It runs against the same storage the platform uses, since a test against a stand-in without the same locking would prove nothing. How the atomic operation is built is an architecture decision.] The overbooking fallback is a safety net for failures outside the platform's control, not an expected outcome of this race: in these cases the losing booking is never created.

## Input validation tests

Success Criterion 9 requires input validation that can be tested. The platform validates every input on the server, whatever the website already checks, and a rejected request changes no data (no hold, booking or payment). v1 proves it with automated tests against the API.

| Case | Expected result |
|---|---|
| Seat count is zero, negative, fractional, not a number, or above the free seats | Rejected with a clear error; nothing is held |
| Date or time window is malformed, does not exist, or is outside the booking horizon or past the booking deadline | Rejected; no booking |
| Required field is missing, or an unknown field is sent | Rejected |
| Text (name, email, notes) is empty, far too long, or has the wrong format, for example an invalid email address | Rejected |
| Text contains SQL injection strings, script tags or HTML | Never run or shown as markup; either rejected or stored and shown only as escaped text |
| Administrator input is invalid, for example a negative price or capacity, or a window that ends before it starts | Rejected |
| A guest sends an administrator request | Rejected as not allowed (role-based access) |

[ASSUMPTION: the exact limits (maximum text lengths, maximum seats per booking) are set in the PRD; the tests use those limits and the cases above as a minimum.]

## Password tests

Success Criterion 9 also requires hashed administrator passwords and strong passwords for user accounts. v1 proves it with automated tests.

| Case | Expected result |
|---|---|
| An administrator account is created or its password changed | Only a salted hash from a slow password-hashing algorithm is stored; the plain password is never stored, logged or returned by the API |
| A user (guest) account is created with a weak password: too short, too common, or equal to the email address | Rejected with a clear error; no account is made |
| A user account is created with a strong password | Accepted, and stored hashed as for administrators |
| The stored account data is read directly | No password can be read from it, and the same password gives different hashes for different accounts |
| Login with the correct and with a wrong password | Correct password logs in; wrong password is refused with an error that does not say whether the email exists |

[ASSUMPTION: "strong" is set in the PRD, for example at least 12 characters and not on a list of common passwords, following current guidance rather than forced mixes of character types; the hashing algorithm (for example Argon2id or bcrypt) is an architecture decision. Guest accounts are optional, so the strong-password rule applies only to those who create one.]

## Role-based access tests

Success Criterion 9 also requires role-based access. The platform checks the caller's role on the server for every request, whatever the website shows. v1 proves it with automated tests against the API.

| Case | Expected result |
|---|---|
| Administrator function (time windows, prices, settings, blocks, all bookings) is called without logging in | Refused as not logged in; nothing changes |
| The same function is called by a logged-in guest | Refused as not allowed; nothing changes |
| The same function is called by a logged-in administrator | Allowed |
| A guest opens, changes or cancels another guest's booking, by account or by guessing a booking reference or link | Refused; the response does not reveal whether the booking exists |
| An account-less guest uses the link from their own confirmation email | Allowed for that booking only |
| A guest account tries to change its own role | Refused |

The link in the confirmation email carries a long, random token that cannot be guessed, so the booking reference alone gives no access.

## HTTPS tests

Success Criterion 9 also requires encrypted connections. The website and the API are served only over HTTPS, so passwords, login sessions and booking links cannot be read on the way. v1 proves it with automated tests against the running platform.

| Case | Expected result |
|---|---|
| A request is sent over plain HTTP to the website or the API | Redirected to the HTTPS address; no data is returned or changed over HTTP |
| An HTTPS response is inspected | Carries a Strict-Transport-Security header, so browsers keep using HTTPS |
| A login session is created | The session cookie is marked Secure and HttpOnly, and is never sent over HTTP |
| The confirmation email is generated | The change-or-cancel link starts with https:// |

[ASSUMPTION: the fictional service runs locally during the exam, so the tests use a local development certificate; the certificate setup for a real deployment (for example a free certificate from Let's Encrypt) is an architecture decision.]

## Open questions on individual seats

Answered: seats are placed in one sauna until it is full and then in the next; the administrator sets the fill order; a group may be split; a group that wants to stay together must book a whole sauna; guests see the total number of free seats; the per-person price is the same across saunas; after a cancellation, seats move into earlier saunas from the saunas filled last. The late whole-sauna question is resolved by the rule that a sauna holding individual seats cannot be booked in full.

Also answered: guests are not told which sauna their seats are in, so moves need no notice; a freed sauna can be booked in full only once no seats are left in it. "Moves are allowed at any time" was replaced on 2026-10-29: see Seat placement.

Open: how placement is kept correct under concurrent bookings, and whether it is stored or derived, are design tasks for the architecture. The cases this addendum is silent on are listed under Research input.

## Open questions on gift cards

Answered: buying a gift card needs no account. The value is either a fixed denomination or an amount the buyer chooses, up to a set limit. A gift card can be used for both individual seats and whole-sauna bookings. A gift card expires one year after issue, the same rule as a cancellation voucher (tilgodebevis) — which points toward the two sharing a coupon-code mechanism, though that is still an architecture decision, not a stated one.

Also answered: the administrator sets the fixed denominations and the limit on a buyer-chosen amount. A gift card can be used in part, with the remaining balance kept for later bookings, and a booking can be paid partly by gift card and the rest by the ordinary (simulated) payment.

Nothing on gift cards is open now.

## Open questions on door codes

Answered: the administrator chooses when the codes are sent; each door has its own code per time window, shared by everyone who may use that door; a booking made after the send time gets the codes at once; an individual-seat booker never gets codes for a sauna that is not open for individual seats; if a booking loses to the overbooking fallback after the codes were sent, the apology email says they must not be used; the administrator can see and resend codes; a code is valid from the send time until the window ends.

Also answered: if a sauna opens for individual seats after the codes are sent, individual-seat bookers get an extra email with its codes. The administrator can choose one-sauna access, where an individual-seat booking gets the name and codes of one sauna only, and placement is frozen at the send time, so no new email is needed for a move (replaced on 2026-10-29).

Also answered: with one-sauna access, seat guests may not move between saunas, and all seats in a booking are placed in the same sauna. The administrator can turn this on and off.

Open: the door-code cases under Research input (H6, H10, H11, H13 to H15, H23).

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
