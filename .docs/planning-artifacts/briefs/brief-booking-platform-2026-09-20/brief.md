---
title: "Product Brief: Booking platform"
status: final
created: 2026-09-20
updated: 2026-10-21
---

# Product Brief: Booking platform

## Executive Summary

Booking platform is a reservation system for saunas, delivered together with a website inspired by Finnish sauna culture. Guests can reserve seats for themselves, their family or friends, or book an entire sauna privately. Payment is simulated, and the first version is built around one fictional sauna venue, Saunalöyly, with at least four saunas.

The project is a learning project delivered as an exam submission in 2026. Its purpose is twofold: to produce a working, AI-built application, and to document honestly how AI was used and how the result was quality-assured. It is built so it can grow into a real service later, but the exam version does not pretend to be one.

## The Problem

People who like Finnish saunas, or want to try one, need a simple way to see which times are open, and to reserve a place or book a whole sauna. The hard part is the mix of two booking types in the same venue: individual seats, where several guests share the open saunas, and private bookings where one group takes a whole sauna. Without clear rules, a private booking can collide with individual seats, capacity is double-sold, and cancellations leave the venue guessing.

The documentation must also show how AI was used, and how the student has quality-assured the code.

## The Solution

A website that presents the sauna venue in a calm, Finnish-inspired style, connected to a booking platform that handles the full guest journey. The detailed rules, defaults and assumptions are in the addendum.

- **Individual seats:** guests book seats in a time window, not a particular sauna, and see the total number of free seats across the saunas not booked in full. The system fills one sauna at a time in an order the administrator sets, so a group can be split; a group that wants to stay together books a whole sauna.
- **Whole-sauna bookings:** saunas marked as bookable in full can be booked privately, as long as no individual seats are placed in them for that window.
- **Pricing:** set per time window: one price per seat and one price per whole sauna. Guests book seats, with no distinction between children and adults. Guests can book several windows.
- **Payment and email:** both are simulated. Guests get a booking reference by email.
- **Gift cards (step 2):** anyone can buy a gift card without an account, and whoever holds the code books with it.
- **Cancellation and change:** individual seats can be changed, or swapped for a voucher, up to 12 hours before the start; a whole sauna can be cancelled, with a refund or voucher, or changed up to 72 hours before.
- **Door codes (step 2):** for saunas with self-service locks, bookers get their door codes by email shortly before the window.
- **Administration:** administrators manage time windows, capacity and prices, and see every booking and cancellation. In step 2 they also manage gift cards and door codes. In a calendar, they can block one or all saunas for a period, for example for maintenance. In v1, only a few rules are settings with defaults (the booking horizon, the booking deadline, the two cancellation and change cut-offs, and the time seats open for individual booking); all other rules are fixed and become settings later. A changed setting applies only to new bookings.

### The guest's journey

The guest first chooses between two paths: **Individual seats** or **Private sauna** (a whole sauna).

**Individual seats**
1. The guest picks a date in a calendar, and can change it at any time. The guest sees a list of time windows with free seats, not a list of saunas, picks a time window and the number of seats, and presses Book.
2. The guest chooses to log in or to continue without an account.
3. The guest accepts the terms and presses to pay.

**Private sauna**
1. The guest picks a date in a calendar, and can change it at any time. The guest sees the free private saunas and their time windows, and either picks a time window directly, or opens a specific sauna, picks the time window, and presses Book.
2. The guest chooses to log in or to continue without an account.
3. The guest accepts the terms and presses to pay.

## What Makes This Different

If it becomes a real service, it competes with other booking platforms on price, on how well it attracts guests, and on features. Its clearest differences are the Finnish-inspired identity for an audience that already likes saunas, and one system that handles individual seats and whole-sauna bookings side by side. None of this is proven yet: the exam version does not test prices or customer demand. Its strength for now is that the booking rules are defined precisely enough to be tested, and that the process is documented for assessment.

## Who This Serves

- **Sauna guests:** people who already enjoy Finnish saunas or are curious to try. They book for themselves or a group, and need to see availability and price clearly and cancel easily.
- **The venue administrator:** manages when saunas are open, at what capacity and price, and sees every booking and cancellation.

## Success Criteria

The project is done when the website is complete and the booking platform is connected and works as intended:

1. **Book seats:** a guest books four seats in a time window, pays and gets confirmation; the administrator sees the booking, and the seats are deducted from capacity. If two guests try to book the last free seat at the same moment, exactly one gets it and the other is told it is gone, without being charged.
2. **Book a whole sauna:** a guest books a whole sauna; for that window, it cannot be booked again and its seats are no longer available.
3. **Change seats or take a voucher:** up to the cut-off, a guest changes seats or takes a voucher, and capacity is restored.
4. **Cancel or change a whole sauna:** up to the cut-off, a guest cancels with a refund or voucher, or changes the time, and capacity is restored.
5. **Gift card (step 2):** a guest buys a gift card without an account, and whoever holds the code books with it.
6. **Door codes (step 2):** a booker receives the codes for exactly the doors they may use, at the time the administrator has chosen.
7. **Membership and period card (vision):** a member books at the member price, and a cardholder books seats with no extra payment. Not part of the first version or step 2.
8. **Adjustable rules:** a changed setting (one of the five in v1) applies to new bookings only; with the defaults, criteria 1 to 4 behave as described (and 5 and 6 once step 2 is built).
9. **Protection against hacking:** the website, the platform and personal data are protected by four measures, each documented and tested automatically (details in the addendum):
   - **Input validation:** the platform checks all input on the server and rejects invalid or malicious values (wrong type or format, seat counts outside the allowed range, oversized text, injection or script strings) with a clear error and without changing any data. Tests send such input and check that it is rejected.
   - **Passwords:** administrator passwords are stored hashed, and guest accounts require strong passwords, also stored hashed. Tests check that weak passwords are refused and that no password can be read from the stored data.
   - **Role-based access:** only a logged-in administrator can reach administrator functions, and a guest can see and change only their own bookings. Tests call administrator functions as a guest and without logging in, and try to open another guest's booking, and check that each is refused.
   - **HTTPS:** the website and the API are served only over encrypted connections (HTTPS); plain HTTP requests are redirected to HTTPS, and login sessions and booking links are never sent over an unencrypted connection. Tests check the redirect and the secure cookie settings.
10. **Responsive design:** guests and administrators can use the site on mobile, tablet and desktop, and at any window size.

## Delivery Requirements

What must be handed in with the exam submission, beyond the working product:

1. **Clean assets:** no licensed, trademarked or otherwise protected material; everything is AI-generated, freely licensed or checked by the author. The venue name Saunalöyly was checked on 2026-10-21: no hit in EUIPO TMview, and navnesok.no shows the domain name and company name as free and the name as possibly free as a trademark.
2. **Assessment deliverable:** working code, with documentation of how AI was used and how the code was quality-assured.

## Scope

**In the first version (v1)**

- One fictional sauna location with at least four saunas, and one website in English. Guest accounts are optional; administrator accounts are required.
- The booking rules for individual seats and whole saunas, including cancellation and change, with simulated payment and email (Success Criteria 1 to 4).
- Administrator tools for time windows, capacity, prices, the five adjustable settings, blocking saunas in a calendar, and an overview of all bookings and cancellations.
- Security measures (input validation, hashed and strong passwords, role-based access, HTTPS), a responsive design, and automated tests of the booking rules, Success Criteria 1 to 4, 8 and 9, including a concurrency test where two guests book the last seat at the same time.
- A Python backend and JavaScript frontend, with the booking platform kept separate from the website through a single API. v1 supports one website only.

**Step 2**

- Gift cards: buying without an account, and booking with the code (Success Criterion 5).
- Door codes sent by email to exactly the bookers who may use each door, with the administrator's tools to set the timing (Success Criterion 6).
- Tests of Success Criteria 5 and 6.

**Not in the first version or step 2**

- Real payment, email, door locks, lock systems, heaters and temperature sensors.
- Other languages, more than one location, other bookable resources, and native mobile apps.
- Support for more than one website: v1 has a single API between the platform and its one website, with no website registration, keys or per-website settings and access (see the addendum).
- Memberships, period cards, the distinction between children and adults (with a separate child price), remote door control and heating control: see the vision.

## Vision

If it succeeds, the platform may become a real booking service: real payments and email, more languages, several sauna locations (for example locations A and B, run as separate places, with a choice of location when booking and an overview per location for the administrator), several websites connected to the same platform, and bookable resources beyond saunas. It may also tell children and adults apart when booking seats, with an age limit and a separate, lower price for children, memberships (members book at member prices), period cards (cardholders book individual seats with no extra payment), remote opening and locking of doors for the administrator, and heating that starts only for booked windows, with the administrator able to override the temperature. The first version is built so those steps are extensions, not rewrites.

## Open Questions

- The exact limits for input validation and password strength (maximum text lengths and seats per booking, minimum password length), and the password-hashing algorithm. The PRD and architecture will decide them.
