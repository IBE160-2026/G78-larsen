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

People who like Finnish saunas, or want to try one, need a simple way to see which times are open, and to reserve a place or book a whole sauna. The hard part is the mix of two booking types in the same venue: individual seats, where several guests share the open saunas, and private bookings where one group takes a whole sauna. Without clear rules, a private booking can collide with individual seats, capacity is double-sold, and cancellations leave the venue guessing.

For the exam, the problem is different: demonstrate that an AI-generated application can be made correct and trustworthy, not only that it can be generated.

## The Solution

A website that presents the sauna venue in a calm, Finnish-inspired style, connected to a booking platform that handles the full guest journey. The detailed rules, defaults and assumptions are in the addendum.

- **Individual seats:** guests book seats in a time window, not a particular sauna, and see the total number of free seats across the saunas not booked in full. The system fills one sauna at a time in an order the administrator sets, so a group can be split; a group that wants to stay together books a whole sauna.
- **Whole-sauna bookings:** saunas marked as bookable in full can be booked privately, as long as no individual seats are placed in them for that window.
- **Pricing:** set per time window: a per-person price for seats, with an optional child price, and one price per whole sauna. Guests can book several windows.
- **Payment, email and gift cards:** payment and email are simulated. Guests get a booking reference by email, and anyone can buy a gift card without an account.
- **Memberships and period cards (optional):** members book at member prices, and period cardholders book individual seats with no extra payment. Both are off by default.
- **Cancellation and change:** individual seats can be changed, or swapped for a voucher, up to 12 hours before the start; a whole sauna can be cancelled, with a refund or voucher, or changed up to 72 hours before.
- **Door codes and door control:** for saunas with self-service locks, bookers get their door codes by email shortly before the window. Where the lock allows it, the administrator can also open and lock doors remotely.
- **Heating:** for saunas with external heater or temperature control, heating starts only for booked windows, and the administrator can override the temperature.
- **Administration:** administrators manage time windows, capacity, prices, gift cards, memberships and period cards, and see every booking and cancellation. In a calendar, they can block one or all saunas for a period, for example for maintenance. Rules that may differ between venues, such as booking deadlines, cut-offs and limits, are settings with defaults; a changed setting applies only to new bookings.

## What Makes This Different

If it becomes a real service, it competes with other booking platforms on price, on how well it attracts guests, and on features. Its clearest differences are the Finnish-inspired identity for an audience that already likes saunas, and one system that handles individual seats and whole-sauna bookings side by side. None of this is proven yet: the exam version does not test prices or customer demand. Its strength for now is that the booking rules are defined precisely enough to be tested, and that the process is documented for assessment.

## Who This Serves

- **Sauna guests:** people who already enjoy Finnish saunas or are curious to try. They book for themselves or a group, and need to see availability and price clearly and cancel easily.
- **The venue administrator:** manages when saunas are open, at what capacity and price, and sees every booking and cancellation.
- **The assessor (exam):** reads the code and the documentation of AI use and quality assurance.

## Success Criteria

The project is done when the website is complete and the booking platform is connected and works as intended:

1. **Book seats:** a guest books four seats in a time window, pays and gets confirmation; the administrator sees the booking, and the seats are deducted from capacity.
2. **Book a whole sauna:** a guest books a whole sauna; for that window, it cannot be booked again and its seats are no longer available.
3. **Change seats or take a voucher:** up to the cut-off, a guest changes seats or takes a voucher, and capacity is restored.
4. **Cancel or change a whole sauna:** up to the cut-off, a guest cancels with a refund or voucher, or changes the time, and capacity is restored.
5. **Gift card:** a guest buys a gift card without an account, and whoever holds the code books with it.
6. **Door codes:** a booker receives the codes for exactly the doors they may use, at the time the administrator has chosen.
7. **Membership and period card:** a member books at the member price, and a cardholder books seats with no extra payment.
8. **Adjustable rules:** a changed setting applies to new bookings only; with the defaults, criteria 1 to 7 behave as described.
9. **Protection against hacking:** the website, the platform and personal data are protected, and the measures are documented and tested.
10. **Responsive design:** guests and administrators can use the site on mobile, tablet and desktop, and at any window size.
11. **Clean assets:** no licensed, trademarked or otherwise protected material; everything is AI-generated, freely licensed or checked by the author.
12. **Assessment deliverable:** working code, with documentation of how AI was used and how the code was quality-assured.

## Scope

**In the first version**

- One fictional venue with at least four saunas, and a website in English. Guest accounts are optional; administrator accounts are required.
- The booking rules, simulated payment, email, gift cards, door locks and heating, and optional memberships and period cards.
- Administrator tools for time windows, capacity, prices and the adjustable rules.
- Security measures, a responsive design, and automated tests of the booking rules and Success Criteria 1 to 8.
- A Python backend and JavaScript frontend, with the booking platform kept separate from the website so more websites can be connected later.

**Not in the first version**

- Real payment, email, door locks, lock systems, heaters and temperature sensors.
- Other languages, several venues, other bookable resources, and native mobile apps.
- More than one connected website, and per-website settings and access (see the addendum).

## Vision

If it succeeds, the platform becomes a real booking service: real payments and email, more languages, several venues, several websites connected to the same platform, and bookable resources beyond saunas. The first version is built so those steps are extensions, not rewrites.

## Open Questions

- The name of the fictional venue (must be invented and checked against existing names).
- Which concrete security measures are required. The PRD and architecture will turn "protected against hacking" into specific, testable measures.
