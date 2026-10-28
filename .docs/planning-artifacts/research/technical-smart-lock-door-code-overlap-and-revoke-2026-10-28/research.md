---
title: 'technical research: smart lock door codes, overlap and revoke'
type: 'technical'
topic: 'smart lock door codes: overlapping validity, replace and revoke of an already-sent code'
decision: 'How the PRD states door-code rules H6 (overlapping validity at back-to-back windows) and H12-H14 (sent code for a sauna later whole-booked or blocked), and whether these rules force seat moves'
source: 'native run'
status: complete
claims_verified: 3
claims_unverified: 7
preset: 'quick'
validation: 'normal'
created: '2026-10-28'
updated: '2026-10-28'
---

# technical research: smart lock door codes, overlap and revoke

**Decision this research serves:** How the PRD states door-code rules H6 (overlapping validity at back-to-back windows) and H12-H14 (sent code for a sauna later whole-booked or blocked), and whether these rules force seat moves.

## Executive summary

**Write the door-code rules so they work without revoking a sent code; treat replacing or deleting a code as a best-effort extra that only some locks support.**

- **Several codes on one door at once is normal.** Schlage Encode holds 100 codes [3]; igloohome 199 PINs, online and offline counted together [2]; Nuki 100 or 200 (forum snippet, low) [11]. For this project a door needs about two live codes (back-to-back windows), far below any cap found. Expired codes should still be deleted [11].
- **No vendor document states a rule against overlapping validity with different PINs, and none confirms it either.** The only collision rules found are about the same PIN: unique per lock (TTLock) [8], unique in the whole system (Nuki) [9], unique across the account (RemoteLock, via an integrator) [7], unique among your codes (Schlage) [3]. So H6 is technically allowed when the PINs differ. Absence of a rule is not proof, and the simulated lock in v1 must enforce "distinct PIN per door and window" (H6).
- **Revoking or replacing a sent code depends on the kind of code.** Online, updatable codes: Seam can change the PIN digits and times of an "active or upcoming" code [4]; Nuki can edit and delete [9] (2018 posts); TTLock online codes only while the lock is connected [8]. Offline, algorithmic codes (igloohome, dormakaba Oracode, Lockly, TTLock offline): cannot be modified, and cannot be revoked before expiry without a factory reset or, for igloohome, a Bluetooth visit to the lock [1][2][8]. Schlage's guide documents no single-code edit or delete [3].
- **Hour-resolution locks widen the H6 overlap.** igloohome rounds times (default one hour) [2], TTLock offline codes snap to the hour [8], and RemoteLock ResortLock guests had hour resolution in a 2016 changelog [6]. A "valid from 20 minutes before" code on such a lock is valid from the start of the hour.
- **Delivery is not instant and can fail silently.** Seam programs codes 72 hours ahead, or 60 minutes before start on locks without native scheduling [1]. RemoteLock Wi-Fi locks sync "the next time the lock wakes up" [6]. A 2025 Nuki report describes a 204 success response with no PIN on the keypad, one anecdote with no staff reply [10]. No latency figure was found for any vendor.
- **Seat moves (the user's added question, lead analysis, inference).** In the default mode, door codes do not require any seat to move: the codes follow from the set of open saunas, which follows from counts. The only case where moves matter is one-sauna access (H19-H23): each move after the codes were sent needs a new code, and the old shared code cannot be taken from one person. Recommended: freeze placement at the send time under one-sauna access. This is stricter than H21 (no moves after the window starts) and conflicts with the addendum's "moves are allowed at any time".
- **Biggest caveats.** Q2 (overlap) and Q3 before-versus-after-start edits are unanswered by any source. TTLock, Nuki and the Yale/August cloud are covered only through integrators and forum posts, not first-party reference. Nothing was tested on a real lock.

## Dimension 1. Landscape and maturity: what locks can hold

**Q1. Several valid codes on one door.**
- Every vendor reached stores many codes. Documented caps: Schlage Encode 100 via the Schlage Home API [3] (high, re-fetched; an Allegion KB snippet agrees [12]); igloohome 199 PINs, "including online and offline PINs" [2] (medium; the page does not say the limit is per lock, which is likely but not stated); Nuki 100 (older) or 200 (newer) authorizations, with advice to delete expired ones [11] (low, snippet).
- No slot limit was found for TTLock (the Beds24 page states none [8]), Seam in general (an error `no_space_for_access_code_on_device` exists, name from a snippet [4]) or RemoteLock [6]. Seam notes offline codes are bound by each manufacturer's maximum [1].
- For this project: one code per door per window (addendum). Even with gradual opening and several doors per sauna, a door holds a few live codes. Cap risk is expired codes left behind, not live ones.

**Q2. Overlapping validity on one door.**
- Not stated by any source. Seam's capability guide has no overlap rule [1] (re-fetched, "not found"); the Allegion guide has none [3] (re-fetched); the igloohome page has none [2] (re-fetched). Assistants found none for TTLock, Nuki or RemoteLock either.
- Collision rules found are all about identical PINs, see the executive summary [3][7][8][9]. RemoteLock's account-wide uniqueness comes from an integrator page, snippet only [7] (medium). A RemoteLock feedback thread asking for codes to repeat across non-overlapping times (found as a lead, not read) suggests the limit was still in force.
- Count limits that act like overlap limits exist for offline codes: Seam caps igloohome offline codes at 3 hourly-bound per hour, 3 daily-bound per day and 5 one-time per start-date slot [2]; TTLock offline codes on one lock cannot share the same start and end time, and deleted ones count [8]. Back-to-back windows have different start times, so these do not block H6, but they matter if many windows start at the same time.
- Time resolution: see the executive summary [2][6][8]. The 2016 RemoteLock note is older than 12 months and not rechecked.

**Maturity read.** The cloud platforms (Seam, RemoteLock) are documented and expose states and events; the lock-vendor APIs (Nuki, TTLock) are known here mainly through forum posts and integrator wikis, some from 2018-2019, which may be outdated.

## Dimension 2. Integration and interoperability: change, revoke, deliver

**Q3. Change or revoke a code that was already created.**
- Standard (online) codes: Seam `update` accepts `code`, `name`, `starts_at`, `ends_at` and `type` and applies to "active or upcoming" codes [4] (medium, fetch summary). Seam also deletes through a delete endpoint and removes a code at `ends_at` [1] (the delete endpoint is a snippet). Nuki: a POST to the authorization overwrites its values including the code, and it can be disabled or deleted [9] (medium, 2018). TTLock online codes can be updated or deleted only while the lock is connected to the internet [8].
- Offline codes: Seam says "You cannot modify a created offline access code" and that it cannot be revoked before expiry, only by factory reset or re-pairing [1] (high, re-fetched). igloohome algoPINs: no modification, and deletion only within Bluetooth range, so not through the Seam API [2] (high, re-fetched). TTLock offline passcodes: no update or delete, and a deleted one cannot be recreated with the same start and end [8]. RemoteLock's igloohome codes cannot be edited or deleted in the portal [14] (low, snippet).
- Schlage: the access-code guide lists no single-code edit or delete, only deletion of all codes to change the code length [3] (re-fetched). The API reference was not read, so this is a gap, not a "no".
- Before versus after validity starts: not documented for standard codes in any source read [4]. Seam says it keeps the device in sync with the declared timings and that changes before start are pushed [1][4]; whether an edit after the start works the same way is not stated. Open question.
- RemoteLock: a grant allows only a schedule update; changing which locks it covers needs revoke and a new grant [6] (low, snippet).

**Q4. Speed and failure.**
- No measured latency for any vendor. Lead times: Seam preloads codes 72 hours before `starts_at` where the lock supports scheduling, otherwise programs them 60 minutes before and removes them at `ends_at` [1] (high, re-fetched). A Seam update stays "pending" until the device confirms: `pending_mutations`, then events `code_changed` / `time_frame_changed`, or `failed_to_update` [4]; the deprecated `status` field has setting, set, unset, removing, unknown [5].
- Seam failure causes: connectivity, changes in the lock vendor's app, provider outages; a code removed externally is re-set until `ends_at` [1] (high, re-fetched). Seam also offers a Backup Access Code service [1].
- RemoteLock Wi-Fi locks sync a new code when they wake, guest states upcoming, current, expired, deactivated, and sync events `access_person_synced` / `access_person_sync_failed` / `access_guest_late_sync` [6]; backup PINs from a limited pool are emailed an hour before the start [6].
- TTLock via the Beds24 integration: errors "gateway is busy", "lock is not connected to any gateway", "failed" (weak Bluetooth to the gateway) [8]; Beds24 pushes changes about every 12 hours, which is the integrator's schedule, not the lock's [8].
- Nuki: authorizations are stored on the lock and synced to the Web API later, so a new PIN may not appear at once [9] (2019). A 2025 report on a Smart Lock 3.0 Pro says the API returned 204 while the PIN was absent, with failure only visible as a websocket event; the thread was auto-closed without staff reply and no fix was found [10]. One post is an anecdote; do not generalize.
- Timezones: Seam and the Schlage API use the lock's local timezone, RemoteLock reads guest times in the lock's configured timezone [6]; Nuki times are UTC on the lock [9] (2019). The platform must send times for the venue's timezone explicitly.

**Q5. Managed versus unmanaged, and code kinds.**
- Seam separates managed codes (created through Seam) from unmanaged ones (created outside it, only viewable or convertible) [5]. Revocation differs by kind: standard codes can be deleted, offline codes cannot [1]. igloohome algoPINs have 7-9 digits and cannot be custom; custom PINs (4-6 digits) need Bluetooth range [15].
- Nothing was found on automatic slot reuse beyond Seam re-setting removed codes [1] and RemoteLock's backup PIN pool [6].

## What this means for H6 and H12-H14

Notation as in group H of the capacity-model research. "Online code" = standard code the platform can change or delete; "offline code" = algorithmic code that cannot be changed.

| ID | Recommended PRD wording, given the findings | Basis |
|---|---|---|
| H6 | Each door has one code per window; codes of two windows on the same door must differ. Validity starts at the send time and ends at the window end. At back-to-back windows both codes are valid for the 20 minutes before the second window; accept this and say so, or start validity at the window start and accept that the email arrives before the code works. The simulated lock must reject a duplicate PIN on a door. On hour-resolution locks the overlap is longer | [2][3][6][8] and inference |
| H12 | Do not depend on revoke. Baseline: after the send time, refuse a whole booking of S while seat bookers hold K(S). That works on every lock kind. Optional extra for online codes: replace K(S) for the window and send the new code to the whole booker only, so the old code stops working. Offline codes cannot do this | [1][2][4] and inference |
| H13 | A block after the send time cannot recall a sent code on an offline lock. Send the correction email to every seat booker of W; where the door's code is online, also delete or replace K(S) so the instruction is enforced. Mark per door whether its codes can be replaced (as the addendum already marks per door whether remote control works) | [1][4] and inference |
| H14 | Lifting a block after the send time opens S for seat bookers, which needs a new code or the same code resent. Nothing in the findings blocks this; the code for S was either never created or can be created now | inference |
| H15 | The code is shared by the group, so cancelling one booking cannot revoke that booker's access without replacing the door's code and resending it to the others. State "must not be used" as a request (already the addendum's wording) and treat replacement as best effort | [4] and inference |
| Gate | Send the email only when the lock confirms the code (Seam `set`, no pending mutation) and alert the administrator if it is not confirmed by the send time, which matches the addendum's missing-code rule. Delete expired codes after the window | [4][5][6][11] and inference |

## Do door codes force seat moves anyway? (lead analysis, inference)

The question was added by the user at the plan gate and answered from the addendum plus the findings above. It is not sourced and was not sent to the research assistants.

- **Default mode: no.** The codes a seat booker gets depend on which saunas are open for seats: not whole-booked, not blocked, not whole-booking-only, and opened under gradual opening. All of these follow from counts, blocks and flags, so derived placement (capacity-model research) suffices. Replacing or deleting a code concerns a door, not a seat.
- **A consequence worth using: freeze compaction at the send time.** If H12's baseline is adopted (no whole booking of S after the send time while seat bookers hold K(S)), seat moves after the send time can no longer free a sauna for a whole booking in that window. Compaction after the send time then serves nothing in default mode, and the race "a move must finish before the freed sauna can be booked whole" (A3, C3) only exists before it. With derived placement this costs nothing either way.
- **One-sauna access: yes, and it is costly.** Each move changes which sauna a booker may use. The booker needs a new email with a new code, and the code for the old sauna is shared with other bookers, so it cannot be taken from this booker alone: that needs replacing the old door's code and resending it to everyone else, which offline locks cannot do. Recommended: under one-sauna access, no moves after the send time (extend H21 from the window start to the send time) and use the overbooking fallback instead. This conflicts with the addendum's "moves are allowed at any time, also shortly before the start" for the one-sauna case, so the PRD must decide.
- **Stored placement.** Unchanged from the capacity-model research: only one-sauna access needs it. The lock findings strengthen the case for stopping moves rather than for building a move-and-notify flow.

## Open questions

| Question | What would answer it |
|---|---|
| Can two codes with different PINs overlap in time on one lock for Nuki, TTLock, igloohome online, RemoteLock, Schlage, Seam? | A test on a real or sandbox lock; Seam offers sandbox devices (not run). Documentation states no rule |
| Can a standard code be edited or deleted after its validity started, and how fast does it take effect? | Seam sandbox or a real device; first-party API references for Nuki, TTLock, Schlage |
| Does the Schlage API offer single-code edit and delete? | The Allegion API reference (guide page read does not say) |
| Nuki and TTLock first-party behaviour in 2026 | Nuki Web API reference and developer thread 8273; TTLock Open Platform reference. All current evidence is forum or integrator material, partly 2018-2019 |
| RemoteLock update rules, PIN uniqueness, the rest of the API document | Read the API document from character 100000 (only 100k of 317k read) |
| Is the Nuki 204-without-PIN behaviour fixed? | Nuki changelog or firmware notes; a real device test |
| Latency of create, change and delete | Measure on a chosen lock; no vendor gives a number |

## Source appendix

| [n] | Supports | Publisher | Pub date | Accessed | Confidence |
|---|---|---|---|---|---|
| [1] | Seam offline codes cannot be modified or revoked; 72 h and 60 min programming lead times; re-set of removed codes; no overlap rule | [Seam docs, access codes capability guide](https://www.seam.co/docs/capability-guides/smart-locks/access-codes) | n/d | 2026-10-28 | high (re-fetched by lead) |
| [2] | igloohome algoPINs: no modification, Bluetooth-only deletion, 199 PINs, hour rounding, per-slot caps, 24 h rule | [Seam docs, igloohome offline codes](https://www.seam.co/docs/device-and-system-integration-guides/igloohome-locks/creating-igloohome-offline-access-codes) | n/d | 2026-10-28 | high (re-fetched by lead); per-lock reading of 199 medium |
| [3] | Schlage Encode 100 codes, unique among your codes, code length rule; no single-code edit or delete on the page | [Allegion developer portal, access codes guide](https://developer.allegion.com/en/products/schlage-home/getting_started_res_access_codes.html) | n/d | 2026-10-28 | high (re-fetched by lead) |
| [4] | Seam update of code, times and type on active or upcoming codes; mutation events; failure events | [Seam docs, modifying access codes](https://www.seam.co/docs/low-level-apis/smart-locks/access-codes/modifying-access-codes.md) | n/d | 2026-10-28 | medium (fetch summary, assistant only) |
| [5] | Seam status values, pending_mutations, managed vs unmanaged | [Seam docs, access code object](https://www.seam.co/docs/api/access_codes/object.md) | n/d | 2026-10-28 | medium (assistant only) |
| [6] | RemoteLock: 409 on duplicate, lock-wake sync, guest states and sync events, backup PINs, timezone, ResortLock hour resolution | [RemoteLock developer docs](https://developer.remotelock.com/api/docs) | n/d; ResortLock note 2016 | 2026-10-28 | medium (first 100k of 317k characters read) |
| [7] | RemoteLock one code per guest across the account | [OwnerRez, RemoteLock integration](https://www.ownerrez.com/support/articles/integration-remotelock-door-locks) | n/d | 2026-10-28 | medium (integrator, snippet only) |
| [8] | TTLock: online passcodes unique per lock, update/delete only online; offline codes fixed, hour snap, sync errors | [Beds24 wiki, TTLock](https://wiki.beds24.com/index.php/TTLock) | n/d | 2026-10-28 | medium (third-party wiki) |
| [9] | Nuki: PIN unique in system, edit and delete, delayed sync, UTC times, 204 behaviour 2018-2019 | [Nuki developer forum, managing PIN codes](https://developer.nuki.io/t/web-api-example-manage-pin-codes-for-your-nuki-keypad/54) | 2018-10 to 2019-10 | 2026-10-28 | medium; older than 12 months |
| [10] | Nuki Smart Lock 3.0 Pro: 204 without the PIN on the keypad | [Nuki developer forum, unreliable keypad codes](https://developer.nuki.io/t/adding-a-keypad-code-is-very-unreliable-for-months/35046) | 2025-03-24 | 2026-10-28 | high that it was reported; one post, anecdote |
| [11] | Nuki 100 or 200 authorizations, delete expired ones | [Nuki developer forum, limited time access code](https://developer.nuki.io/t/limited-time-access-code/32726) | n/d | 2026-10-28 | low (snippet) |
| [12] | Allegion KB: 100 user codes on Encode models | [Allegion knowledge base](https://kc.allegion.com/kb/article/how-many-user-codes-can-be-stored-in-schlage-encode-locks) | n/d | 2026-10-28 | medium (snippet) |
| [14] | RemoteLock igloohome codes cannot be edited or deleted in the portal | [RemoteLock support, igloohome integration](https://support.remotelock.com/articles/Knowledge/igloohome-Integration-Beta) | n/d | 2026-10-28 | low (snippet) |
| [15] | igloohome help center: PIN types, custom PINs need Bluetooth range, algoPINs 7-9 digits | [igloohome support](https://support.igloohome.co/support/solutions/articles/35000183356-what-types-of-pin-codes-can-i-create-) | n/d | 2026-10-28 | medium |

Not relied on: Seam troubleshooting page with the `duplicate_code_on_device` error (snippet only). The numbering skips 13 for that reason.
