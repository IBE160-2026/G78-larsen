# Digest algo-r1-1: algorithm and comparable domains

Accessed 2026-10-28. Method: 6 searches/fetches. Only 3 pages were actually opened (aleno, GuestCentric, arXiv abs); other claims rest on search-result snippets and are marked as such.

## Findings

- Online bin packing with repacking is a studied model: a bounded amount of already-packed items may be moved when a new item arrives; the bound is the "migration factor" (total size moved relative to the arriving item). | https://macau.uni-kiel.de/receive/macau_mods_00001800 (snippet only, not opened) ; https://arxiv.org/abs/1706.04939 (opened, strip-packing variant, same definition) | Univ. Kiel / arXiv | 2017 | 2026-10-28 | medium | theory
- Fully dynamic bin packing (items also leave, as with cancellations): for asymptotic ratio 1+eps the migration factor needs Omega(1/eps), with an upper bound O(1/eps^4 log(1/eps)). | https://research.uni-luebeck.de/en/publications/fully-dynamic-bin-packing-revisited/ (snippet only) | Univ. Lübeck (Berndt, Jansen, Klein) | n/d (approx. 2018-2020) | 2026-10-28 | medium | theory
- In the strip-packing variant, no constant migration factor beats asymptotic ratio 4/3; amortized migration is needed to approach 1+eps. Signals that bounded per-event moves cannot fully prevent fragmentation. | https://arxiv.org/abs/1706.04939 | arXiv (Jansen, Klein, Kosche, Ladewig) | 2017-06-15 (rev. 2018-02-20) | 2026-10-28 | high (for this variant; transfer to saunas is INFERENCE) | theory
- Hotel domain: assigning a physical room at booking time makes availability look smaller; worked example with 2 rooms where Mon-Wed and Fri-Sun bookings pinned to different rooms force rejection of Tue-Sat although a non-overlapping reuse exists. Recommended: sell by room type, assign on arrival day. | https://blog.guestcentric.com/?p=12293 | GuestCentric (repost of hetras blog) | 2013-03-20 | 2026-10-28 | medium (vendor blog) | pattern
- Same source: if booking comes via channel that only knows room types, hotel must shift existing bookings; options are limited once a guest has checked in; moving a guest during a stay is "generally not in anyone's interest". Exceptions to late assignment: guests needing a specific room (accessibility). | https://blog.guestcentric.com/?p=12293 | GuestCentric | 2013-03-20 | 2026-10-28 | medium | pattern
- Academic "Room Committing Problem" / RoomTetris: committing rooms at booking is suboptimal and causes unnecessary rejections at high occupancy; standard assumption is that guests are not relocated after check-in. | https://www.emerald.com/jhtt/article/11/4/589/223396/RoomTetris-an-optimal-procedure-for-committing ; https://www.emerald.com/ijchm/article/33/11/4017/126227/RoomTetris-in-room-committing-why-the-role-of (snippets only, not opened) | Emerald (JHTT / IJCHM) | n/d | 2026-10-28 | medium | theory
- PMS tape charts support manual drag-and-drop moves of a booked guest to another room of the same class to free a room for an unassigned reservation (moves are a manual operator action). | https://support.innroad.com/support/solutions/articles/153000146671-unassigned-reservations-3rd-party-reservations (snippet only) | innRoad | n/d | 2026-10-28 | low-medium | pattern
- Restaurant table assignment (aleno): rule-based hierarchical config (table capacities, combinations, priorities, exclusions; shift and day overrides); manual assignments are never changed by the system; "already assigned tables are not moved automatically". So a comparable vendor chooses NO automatic re-moves. The page only poses "which tables should be preferred or deliberately kept free?" as a question; no mechanism documented. | https://knowledge.aleno.me/en/kb/1.1-automatische-tischzuteilung-was-ist-das-en | aleno | n/d | 2026-10-28 | medium | pattern
- A patent filing argues that systems allocating each booking to a table/combination on arrival and then freezing it block efficient allocation of later requests (applicant's own claim, not independent). | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12045744 (snippet only) | USPTO | n/d | 2026-10-28 | low | failure-claim (single-source anecdote)
- Restaurant vendors (Eat App, TableCheck, Tabit, EasyTable) document table combining for large parties; Tabit: connected tables are disconnected automatically when the reservation closes (combination is per-booking and released). | search snippets of support pages | vendors | n/d | 2026-10-28 | low-medium | pattern

## Synthesis (INFERENCE, not sourced)

- INFERENCE: the sauna problem is dynamic bin packing with bins of different capacity, ordered fill (a first-fit variant with admin-set order), interval-dependent bins, and a "bin must be empty" constraint for whole-sauna bookings. Time windows make each sauna a separate bin per overlapping window, so misaligned windows are the main place where "empty in window" gets hard.
- INFERENCE: moving from the LAST sauna keeps migrations bounded per cancellation, but literature suggests bounded moves cannot guarantee zero fragmentation; the PRD should state the guarantee as "best effort after a deterministic move rule", with examples.
- INFERENCE: no-split groups turn each placement into a bin-packing decision (order-dependent: the same set of bookings can fit or not depending on arrival order); first-fit with no repacking can reject feasible sets. PRD examples should include one such order-dependence case.
- INFERENCE: count-based capacity plus late assignment (hotel room-type model) is the simpler alternative; it is sufficient when only seat counts matter and no whole-sauna sale is needed or whole-sauna is handled as a capacity block. Late assignment cannot guarantee whole-sauna availability by itself unless assignment still reserves feasibility.

## Leads worth chasing

- Berndt, Jansen, Klein "Fully Dynamic Bin Packing Revisited" full text (migration bounds under deletions).
- RoomTetris paper full text (rejection cost of early assignment; algorithm).
- Competitive ratio of First-Fit / known no-repack lower bounds (not retrieved).
- Spa/sauna/escape-room/coworking/fitness vendor docs on private-vs-shared booking and moves; Mews/Cloudbeds/Opera docs on room moves and "room blocking" and overbooking after maintenance.
- Group no-split variant: bin packing with item groups / class constraints; NP-hardness of fixed bin packing (standard, but source not retrieved).

## What I looked for and could not find

- A source naming this exact problem or a "keep last unit free for whole-unit booking" consolidation rule in a booking product.
- Reported failures (two independent sources) of move cascades, guests surprised by moves, or oversubscription after capacity change. Only the single-source hotel remark on moves being disliked.
- Documentation on maintenance/blocks created after bookings exist.
- Sauna/spa/escape-room/coworking comparables; airline and event seat inventory; fitness class booking (not searched, budget).
- First-fit competitive-ratio results and NP-hardness for co-located groups (not retrieved).
