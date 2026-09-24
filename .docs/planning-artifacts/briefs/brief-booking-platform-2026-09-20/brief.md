---
title: "Product Brief: Booking platform"
status: final
created: 2026-09-20
updated: 2026-09-24
---

# Product Brief: Booking platform

## Executive Summary

Booking platform is a reservation system for saunas, delivered together with a website inspired by Finnish sauna culture. Guests can reserve seats for themselves, their family or friends, or book an entire sauna privately. Payment is simulated, and the first version is built around one fictional sauna venue with at least four saunas.

The project is a learning project delivered as an exam submission in about three months. Its purpose is twofold: to produce a working, AI-built application, and to document honestly how AI was used and how the result was quality-assured. It is built so it can grow into a real service later, but the exam version does not pretend to be one.

## The Problem

People who like Finnish saunas, or want to try one, need a simple way to see which times are open, and to reserve a place or book a whole sauna. The hard part is the mix of two booking types in the same venue: individual seats, where several guests share the saunas that are open, and private bookings where one group takes a whole sauna. Without clear rules, a private booking can collide with individual seats, capacity is double-sold, and cancellations leave the venue guessing.

For the exam, the problem is different: demonstrate that an AI-generated application can be made correct and trustworthy, not only that it can be generated.

## The Solution

A website that presents the sauna venue in a calm, Finnish-inspired style, connected to a booking platform that handles the full guest journey.

- **Individual seats:** a guest books one or more seats for a time window. Seats are not tied to a particular sauna: they draw on the combined capacity of the saunas that are not booked in full at that time. For example, with saunas of 7, 10, 12 and 15 seats, if the 7-seat and 15-seat saunas are booked in full, the other two remain open and offer 22 seats for individual booking. Guests book seats, not a sauna, and see the total number of free seats. The system places seats in one sauna until it is full, then continues in the next, so a group of 8 can end up split across two saunas. A group that wants to stay together books a whole sauna, and the booking flow says so. The administrator sets the order in which saunas are filled. When a cancellation frees seats in an earlier sauna, existing seats are moved there, only from the saunas that were filled last, so those saunas free up again. By default, guests are not told which sauna their seats are in, so a move needs no notice, and on site they can move freely between all saunas open for individual seats, so the placement is the system's way of keeping count. The administrator can see in the system which sauna the seats are placed in. A move must be complete before the freed sauna can be booked in full. The administrator can change this behaviour: with gradual opening, saunas open for individual seats one at a time (see below); with one-sauna access, guests may not move between saunas, all seats in a booking are placed in the same sauna, and the booker is told which sauna it is and gets a new email if it changes after the door codes are sent.
- **Gradual opening (optional):** the administrator can choose to open saunas for individual seats one at a time instead of all at once. When the open sauna is full, the next sauna in the fill order that is not booked in full opens automatically, until a maximum number of saunas set by the administrator is reached. Guests then see only the free seats in the open saunas, and the other saunas stay free for whole-sauna booking. If no one has booked a whole sauna and the maximum allows it, all saunas can end up open for individual seats in that window.
- **Whole-sauna bookings:** available for the saunas the venue marks as bookable in full. A sauna booked in full leaves the individual-seat capacity for that time, and a sauna that already holds individual seats cannot be booked in full.
- **Pricing:** set per time window (for example 15:00 to 16:30). Individual seats are priced per person; the administrator chooses whether children under 14 get a lower price or pay the adult price; by default they pay the adult price. A whole sauna has one price. The per-person price is the same across saunas. Guests can book several windows, consecutive or not, in one booking or in separate bookings made one after another, and pay for each window.
- **Simulated payment and email:** a guest pays with a fictional payment flow and receives an email with a booking reference (the email is simulated).
- **Door codes:** door codes apply only to saunas with self-service door locks, which the administrator marks per sauna; saunas without them get no codes. At a time the administrator chooses before the window starts (20 minutes by default), the booker receives an email with the codes that unlock the doors they may use (simulated, like the email itself); a booking made later than that gets the email at once. Each door has its own code per time window, shared by everyone who may use that door, and valid from the send time until the window ends. A whole-sauna booker gets the codes for that sauna. An individual-seat booker gets the codes for the saunas that are open for individual seats in that window, since seat guests move freely between them, and never for a sauna that is not open for individual seats. If another sauna opens for individual seats after the codes are sent, those bookers get an extra email with its codes. The administrator can instead choose that seat guests may not move between saunas, and change that back. Then an individual-seat booking gives access to one sauna only, and all its seats are placed in the same sauna: the email names that one sauna and gives only its codes, and if the seats are moved to another sauna after the email is sent, the booker gets a new email with the new sauna and its codes. The administrator can see and resend the codes.
- **Heater and temperature control:** if a sauna has a heater with external control, the administrator can set, per sauna, when heating starts before a window, so the sauna is warm when guests arrive, and when it is turned off. Heating starts only for windows where that sauna has at least one booking. Simulated in the first version, like the door locks: no real heater is connected. If a sauna also has temperature control, the guest normally sets the temperature during the visit, but the administrator can see the current temperature, turn the heating on and off, and override the guest's setting, for example if it is too hot or too cold.
- **Gift cards:** a guest can buy a gift card, no account needed, and pay (simulated). The buyer picks a fixed denomination or chooses their own amount up to a set limit; the administrator sets both. It is emailed to the buyer's own address as a coupon code; the buyer can print it or forward it to someone else. Whoever holds the code books individual seats or a whole sauna with it, with or without an account. A gift card can be used in part, with the remaining balance kept for later bookings, and a booking can be paid partly by gift card and the rest by the ordinary (simulated) payment.
- **Membership and period cards (optional):** the administrator can choose to offer memberships, period cards, or both, and turn them off again. A guest can buy a membership for a period, for example a year, and book at discounted member prices while it is valid. A guest can also buy a sauna period card, for example a monthly card, and book individual seats while it is valid with no extra payment. The administrator sets which periods are offered, what they cost, the member prices, and how many future bookings a period card can hold at once (one by default). Both renew automatically unless the administrator turns that off. Both are paid with the ordinary (simulated) payment and are tied to a guest account, so the platform recognises the member or cardholder at booking. [ASSUMPTION: an account is required for both.] By default they cannot be paid with a gift card or voucher; the administrator can allow it.
- **Cancellation and change:** individual seats are not offered a cash refund; up to 12 hours before the start, a guest can either change them (for example to a different time window) or choose a voucher sent by email instead of changing. A whole-sauna booking can be cancelled or changed to a different time up to 72 hours before the start; on cancellation, the guest chooses between a simulated refund and a voucher sent by email.
- **Administration:** administrators have their own accounts. An administrator sets time windows freely, manages capacity and prices, sets the gift card denominations and the limit on buyer-chosen amounts, sets up memberships, member prices and period cards if they are offered, and can mark windows as whole-booking-only or reverse that. If a sauna is not booked in full for a window, its seats open for individual booking at 06:00 the same morning. The administrator can move this to another time or turn the rule off.
- **Adjustable rules:** the administrator can change the booking rules that may differ from one venue or website to another: the last time a window can be booked (5 minutes after the window starts by default), the cut-offs for changing seats and for cancelling or changing a whole sauna, when the door-code email is sent, when seats open for individual booking, or whether they open at all, whether saunas open for individual seats gradually and how many at most, whether seat guests may move between the open saunas or an individual-seat booking is kept to one sauna, the child age limit and whether children have their own price, how long seats are held during booking, how long gift cards and vouchers stay valid, whether memberships and period cards are offered, how many future bookings a period card can hold, whether they renew automatically and whether they can be paid with a gift card or voucher, and whether a cancelled whole-sauna booking offers a refund, a voucher or both. The times and limits stated elsewhere in this brief are the defaults. A changed setting applies only to bookings made after the change; existing bookings keep the rules they were made under.

## What Makes This Different

If it becomes a real service, it competes with other booking platforms on price, on how well it attracts guests, and on features. Its clearest differences are the Finnish-inspired identity for an audience that already likes saunas, and one system that handles individual seats and whole-sauna bookings side by side. None of this is proven yet: the exam version does not test prices or customer demand. Its strength for now is that the booking rules (individual versus whole, holds, cancellation cut-off) are defined precisely enough to be tested, and that the process is documented for assessment.

## Who This Serves

- **Sauna guests:** people who already enjoy Finnish saunas or are curious to try. They book for themselves or for a group or family, and need to see availability and price clearly and cancel easily.
- **The venue administrator:** manages when saunas are open, at what capacity and price, and sees every booking and cancellation.
- **The assessor (exam):** reads the code and the documentation of AI use and quality assurance.

## Success Criteria

The project is done when the website is complete and the booking platform is connected and works as intended. Specifically:

1. **Book seats:** a guest selects a time (not a specific sauna), books four seats for themselves and friends, pays (simulated) and gets confirmation. The administrator sees the booking and the seats are deducted from the available capacity.
2. **Book a whole sauna:** a guest books a whole sauna, pays and gets confirmation. The administrator sees it, and that sauna cannot be booked again, and its seats are no longer available for individual booking, for that time.
3. **Change seats, or take a voucher instead:** up to 12 hours before the start, a guest either changes an individual-seat booking (for example to a different time window) or chooses a voucher by email instead of changing; individual seats are not offered a cash refund. The administrator sees the change or voucher and capacity is restored.
4. **Cancel or change a whole sauna:** up to 72 hours before the start, a guest cancels a whole-sauna booking, choosing a simulated refund or a voucher by email, or changes it to a different time. The administrator sees the cancellation or change and capacity is restored.
5. **Buy and redeem a gift card:** a guest buys a gift card, no account needed, and pays (simulated); it arrives by email at the buyer's own address as a coupon code. Whoever holds the code books a sauna with it, with or without an account.
6. **Assessment deliverable:** code and working functionality, including documentation of how AI was used and how the code was quality-assured.
7. **Clean assets:** no licensed, trademarked or otherwise protected material on the site or in the platform. All images, fonts, icons and names are AI-generated or freely licensed, unless the author has verified something they found or invented themselves.
8. **Protection against hacking:** the website and the booking platform are protected against hacking, and all personal data (names, email addresses, credentials) is protected in particular. The measures are documented and tested.
9. **Responsive design:** the website adapts its layout to mobile, tablet and desktop, and to any window size, so guests can browse and book, and administrators can manage the venue, from any device.
10. **Door codes before the start:** for saunas with self-service door locks, at the time the administrator has chosen before the window starts, a guest with a booking receives an email with the codes that unlock the doors they may use (simulated), or at once if they booked later than that. A guest with individual seats gets the codes only for the saunas open for individual seats; a guest with a whole sauna gets that sauna's codes. The administrator can see and resend the codes.
11. **Adjustable rules:** the administrator changes a rule setting, for example the cut-off for cancelling a whole sauna or whether children have their own price, and the platform applies the new value to bookings made after the change, while existing bookings keep the old rules. With the default settings, criteria 1 to 10 behave as described.
12. **Membership and period card:** with memberships and period cards turned on, a guest with an account buys a membership (simulated payment) and books at the member price, and a guest buys a monthly card and books individual seats in that month with no extra payment. The administrator sees the memberships, period cards and bookings, and the seats are deducted from the available capacity as for any other booking.

## Scope

**In the first version**

- One fictional sauna venue with at least four saunas, and a Finnish-inspired website in English. Guest accounts are optional, since booking does not require an account or login; administrator accounts (one or more) are required.
- The booking rules: individual-seat and whole-sauna bookings, several windows per guest, adult pricing and optional child pricing, a seat hold (10 minutes by default) and the overbooking fallback.
- Simulated heater start, temperature readings and temperature control for saunas that have them.
- Optional memberships with member prices, and optional period cards, both turned off by default.
- Simulated payment, refunds, gift cards and email, including the door-code email at the time the administrator chooses (20 minutes before the start by default).
- Administrator tools for time windows, capacity, prices and whole-booking-only windows, and for the adjustable rules, with the values in this brief as defaults.
- Security measures that protect the website and the booking platform against hacking, and all personal data in particular.
- A responsive website design that adapts to mobile, tablet and desktop, and to any window size.
- Automated tests covering the booking rules and the scenarios in Success Criteria 1 to 5 and 10 to 12.
- Python backend and JavaScript frontend. Frameworks are left to the architecture phase.
- A booking platform kept separate from the website it serves, so that more websites can be connected to it after the exam if desired. The first version connects one website.

**Not in the first version**

- Real door locks, heater controls and temperature sensors; all are simulated.
- Real payment providers and real email delivery.
- Languages other than English.
- Multiple venues and other bookable things (rooms, equipment).
- More than one connected website. The platform is prepared for it, but only one website is built and connected.
- Per-website settings and access: registering which websites may use the platform, which venue each website shows, the venue's name and identity, email sender and templates, time zone, currency, languages, terms, and administrator roles limited to one website. The architecture should leave room for them.
- Native mobile apps (the responsive website itself is used through a browser on mobile, too).

## Vision

If it succeeds, the platform becomes a real booking service: real payments and email, more languages, several venues, several websites connected to the same platform, and bookable resources beyond saunas. The first version is built so those steps are extensions, not rewrites. [ASSUMPTION]

## Open Questions

- The name of the fictional venue (must be invented and checked against existing names).
- Which concrete security measures are required. The PRD and architecture will turn "protected against hacking" into specific, testable measures for the website, the booking platform and personal data.
- Memberships and period cards: whether the member price covers everyone in a booking or only the member, and whether a period card is valid for whole-sauna bookings. Proposed answers are in the addendum.
