---
title: "Product Brief: Booking platform"
status: final
created: 2026-09-20
updated: 2026-10-30
---

# Product Brief: Booking platform

## Executive Summary

Booking platform is a reservation system for saunas, delivered together with a website inspired by Finnish sauna culture. Guests can reserve seats for themselves, their family or friends, or book an entire sauna privately. Payment is simulated, and the first version is built around one fictional sauna venue, Saunalöyly, with at least four saunas.

The project is a learning project delivered as an exam submission in 2026. Its purpose is twofold: to produce a working, AI-built application, and to document honestly how AI was used and how the result was quality-assured. It is built so it can grow into a real service later, but the exam version does not pretend to be one. The work is done by one person between 27 October and 15 December 2026, so the first version has a core that must finish, and additions that are built in a set order only if time allows.

## The Problem

People who like Finnish saunas, or want to try one, need a simple way to see which times are open, and to reserve a place or book a whole sauna. The hard part is the mix of two booking types in the same venue: individual seats, where several guests share the open saunas, and private bookings where one group takes a whole sauna. Without clear rules, a private booking can collide with individual seats, capacity is double-sold, and cancellations leave the venue guessing.

## The Solution

A website that presents the sauna venue in a calm, Finnish-inspired style, connected to a booking platform that handles the full guest journey. The detailed rules, defaults and assumptions are in the addendum.

- **Individual seats:** guests book seats in a time window, not a particular sauna, and see the total number of free seats across the saunas not booked in full. The system fills one sauna at a time in an order the administrator sets, so a group can be split; a group that wants to stay together books a whole sauna.
- **Whole-sauna bookings:** saunas marked as bookable in full can be booked privately, as long as no individual seats are placed in them for that window. When a cancellation frees seats, the system keeps the last saunas in the fill order free where it can; whether it does so by moving stored seats or by deriving placement from counts is left to the architecture.
- **Pricing:** set per time window: one price per seat and one price per whole sauna. Guests book seats, with no distinction between children and adults. Guests can book several windows.
- **Payment and email:** both are simulated. Guests get a booking reference by email.
- **Gift cards (step 2):** anyone can buy a gift card without an account, and whoever holds the code books with it.
- **Cancellation and change:** individual seats can be changed, or swapped for a voucher, up to 12 hours before the start; a whole sauna can be cancelled, with a refund or voucher, or changed up to 72 hours before.
- **Door codes (step 2):** for saunas with self-service locks, bookers get their door codes by email shortly before the window. The rules never depend on taking back a code already sent, since not every lock allows it: once codes are sent, a sauna cannot be booked in full while seat bookers hold its code.
- **Administration:** administrators manage time windows, capacity and prices, and see every booking and cancellation. Time windows are the same for every sauna and never partly overlap, because the capacity count is per window. In step 2 they also manage gift cards and door codes. In a calendar, they can block one or all saunas for a period, for example for maintenance. In v1, only five rules are settings with defaults; all other rules are fixed and become settings later. A changed setting applies only to new bookings.

### The guest's journey

The guest first chooses **Individual seats** or **Private sauna** (a whole sauna), picks a date in a calendar, and sees the time windows: with their free seats for individual seats, or the free private saunas and their windows for a whole sauna. The guest picks a window (and the number of seats), presses Book, logs in or continues without an account, accepts the terms and pays. In the core every guest continues without an account. The addendum has the full steps.

## What Makes This Different

If it becomes a real service, it competes with other booking platforms on price, on how well it attracts guests, and on features. Its clearest differences are the Finnish-inspired identity for an audience that already likes saunas, and one system that handles individual seats and whole-sauna bookings side by side. None of this is proven yet: the exam version does not test prices or customer demand. Its strength for now is that the booking rules are defined precisely enough to be tested, and that the process is documented for assessment.

## Who This Serves

- **Sauna guests:** people who already enjoy Finnish saunas or are curious to try. They book for themselves or a group, and need to see availability and price clearly and cancel easily.
- **The venue administrator:** manages when saunas are open, at what capacity and price, and sees every booking and cancellation.

## Scope

**Core of the first version (v1): must finish**

- One fictional sauna location with at least four saunas, and one website in English. A Python backend and JavaScript frontend, with the booking platform kept separate from the website through a single API. v1 supports one website only.
- Booking individual seats from start to finish: the guest picks a date, a number of seats and a time window, then books and pays (simulated, instant). The guest gives a name and an email, with no account, and gets a booking reference by simulated email.
- Time windows, capacity and prices are kept in the database and set by a seed or configuration file, with no administrator screens. The rules that become settings later (booking horizon, booking deadline, cancellation cut-offs) are fixed defaults.
- The database enforces that booked seats in a window never exceed capacity, and booking checks and reserves capacity in one atomic step because payment is instant (Success Criterion 1).
- Administrator: one account with password login, and a simple list of bookings.
- Input validation, hashed passwords and role-based access, each tested automatically (Success Criterion 9); HTTPS is not yet placed. A simple layout for a laptop screen; the mobile layout comes last in step 2, if time allows.

**If time allows, in this order**

1. Changing individual seats up to the cut-off, or taking a voucher instead, with capacity restored either way. Individual seats get no refund. Change (cancel plus a new booking) is built first and the voucher last [ASSUMPTION] (Success Criterion 3).
2. Whole-sauna booking (Success Criteria 2 and 4), which needs seats placed in specific saunas.
3. A "My booking" page for a guest without an account, where the guest enters the booking reference and email and gets the change-or-cancel link sent again. The link in the email remains the only way into a booking.
4. The 10-minute seat hold while a guest pays.
5. Guest accounts.
6. The rest of the v1 rules and tools: administrator screens for time windows, capacity, prices and the five adjustable settings (Success Criterion 8), the blocking calendar, the 06:00 rule, whole-booking-only windows, and the overbooking fallback.
7. Step 2, below.

It is decided that cancelling comes before whole-sauna booking, that v1 and everything in v1 that is if time come before step 2, and that the mobile layout comes last in step 2; the rest of the order is a proposal from the brainstorm of 27 October [ASSUMPTION].

**Step 2 (item 7 above), in this order**

- Gift cards: buying without an account, and booking with the code (Success Criterion 5).
- Door codes sent by email to exactly the bookers who may use each door, with the administrator's tools to set the timing (Success Criterion 6).
- Mobile layout, last, after the laptop layout works (Success Criterion 10).

**Not in the first version or step 2**

- Real payment, email, door locks, lock systems, heaters and temperature sensors.
- Other languages, more than one location, other bookable resources, and native mobile apps.
- Support for more than one website: v1 has a single API between the platform and its one website, with no website registration, keys or per-website settings and access (see the addendum).
- Memberships, period cards, the distinction between children and adults (with a separate child price), remote door control, one-sauna access and heating control: see the vision.

## Success Criteria

The core is done when the website is complete, the booking platform is connected, and criteria 1 and 9 and the laptop part of 10 work as intended. Criteria 2 to 4 and 8 follow the if-time order under Scope, and 5, 6 and the mobile part of 10 belong to step 2. A criterion not reached is reported as not delivered.

1. **Book seats:** a guest books four seats in a time window, pays and gets confirmation; the administrator sees the booking, and the seats are deducted from capacity. If two guests try to book the last free seat at the same moment, exactly one gets it and the other is told it is gone, without being charged. Parallel automated tests prove it; no speed figure is promised.
2. **Book a whole sauna (if time):** a guest books a whole sauna; for that window, it cannot be booked again and its seats are no longer available.
3. **Change seats or take a voucher (if time):** up to the cut-off, a guest changes seats or takes a voucher, and capacity is restored.
4. **Cancel or change a whole sauna (if time):** up to the cut-off, a guest cancels with a refund or voucher, or changes the time, and capacity is restored.
5. **Gift card (step 2):** a guest buys a gift card without an account, and whoever holds the code books with it.
6. **Door codes (step 2):** a booker receives the codes for exactly the doors they may use, at the time the administrator has chosen; no rule relies on taking back a code already sent.
7. **Membership and period card (vision):** a member books at the member price, and a cardholder books seats with no extra payment. Not part of the first version or step 2.
8. **Adjustable rules (if time, before step 2):** a changed setting (one of the five in v1) applies to new bookings only; with the defaults, criteria 1 to 4 behave as described (and 5 and 6 once step 2 is built).
9. **Protection against hacking:** the website, the platform and personal data are protected by four measures, each tested automatically (details and test cases in the addendum):
   - **Input validation:** the platform checks all input on the server and rejects invalid or malicious values with a clear error and without changing any data.
   - **Passwords:** administrator and guest passwords are stored hashed, and guest accounts require strong passwords.
   - **Role-based access:** only a logged-in administrator can reach administrator functions, and a guest can see and change only their own bookings.
   - **HTTPS:** the website and the API are served only over HTTPS, and login sessions and booking links never travel unencrypted. Whether HTTPS is core or if-time is not yet decided.
10. **Responsive design:** guests and administrators can use the site on a laptop screen (core), and then on mobile and at any window size (if time, last in step 2, after the laptop layout works). It is kept simple: one stylesheet.

## Delivery Requirements

What must be handed in with the exam submission, beyond the working product:

1. **Clean assets:** no licensed, trademarked or otherwise protected material; everything is AI-generated, freely licensed or checked by the author. The venue name Saunalöyly was checked on 2026-10-21: no hit in EUIPO TMview, and navnesok.no shows the domain name and company name as free and the name as possibly free as a trademark.
2. **Assessment deliverable:** working code, with documentation of how AI was used and how the code was quality-assured.

## Vision

If it succeeds, the platform may become a real booking service: real payments and email, more languages, several sauna locations (for example locations A and B, run as separate places, with a choice of location when booking and an overview per location for the administrator), several websites connected to the same platform, and bookable resources beyond saunas. It may also tell children and adults apart when booking seats, with an age limit and a separate, lower price for children, memberships (members book at member prices), period cards (cardholders book individual seats with no extra payment), remote opening and locking of doors for the administrator, one-sauna access (an individual-seat booking is placed whole in one sauna, and guests use only that sauna), and heating that starts only for booked windows, with the administrator able to override the temperature. The first version is built so those steps are extensions, not rewrites.

## Open Questions

- The exact limits for input validation and password strength (maximum text lengths and seats per booking, minimum password length), and the password-hashing algorithm. The PRD and architecture will decide them.
- **Architecture, from the research:** the database engine (the concurrency research covers PostgreSQL only, and no speed figure could be sourced, so any load-test target is set after measuring), and whether seat placement is stored or derived from counts.
- **PRD, from the research** (each case has a recommended answer in the addendum):
  - Administrator changes: lifting a block, marking a sauna whole-booking-only while it holds seats, lowering capacity, changing the fill order, and changes in a window that has started.
  - Door codes (step 2): two valid codes on one door at back-to-back windows, a changed send time, and a block after the codes are sent.
- **Core and schedule, from the brainstorm:** whether HTTPS is core or if-time; whether each seat carries its sauna from the first day, so whole-sauna booking is an extension and not a rewrite (architecture); and the backward check of the build order from 15 December, which was not run.
- **Not yet tested:** whether a real lock accepts two codes with different PINs on one door, and whether a code can be changed after its validity started. No source answers it; it needs a test on a real or sandbox lock.
