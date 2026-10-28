# Digest A, round 1: Nuki, TTLock, igloohome, August/Yale

Assistant A, accessed 2026-10-28. Budget: 5 pages read in depth, 12 tool calls (spent). Evidence quotes are the fetch tool's summaries, so treat them as close paraphrases, not verbatim. Mostly third-party sources; only the igloohome help-center page is a vendor page.

Pages read in depth: igloohome help center (types of PINs); Seam igloohome offline-codes page; Nuki dev forum thread 35046; Nuki dev forum thread 54; Beds24 TTLock wiki.

| id | claim | Q | vendor | source | publisher | pub | read | conf | class |
|---|---|---|---|---|---|---|---|---|---|
| C1 | igloohome lock holds up to 199 PINs, online and offline counted together | Q1 | igloohome | https://www.seam.co/docs/device-and-system-integration-guides/igloohome-locks/creating-igloohome-offline-access-codes | Seam | n/d | full | medium | pattern |
| C2 | Nuki keypad stores 100 authorizations (older) or 200 (newer); delete expired ones | Q1 | Nuki | https://developer.nuki.io/t/limited-time-access-code/32726 | Nuki dev forum | n/d | snippet | low | pattern |
| C3 | No official TTLock slot limit found (Beds24 page states none) | Q1 | TTLock | https://wiki.beds24.com/index.php/TTLock | Beds24 | n/d | full | medium | pattern |
| C4 | TTLock online passcodes must be unique per lock ("Passcodes must be unique in each lock.") | Q2 | TTLock | Beds24 wiki | Beds24 | n/d | full | medium | pattern |
| C5 | TTLock offline passcodes on one lock cannot share the same start and end time; deleted ones count | Q2 | TTLock | Beds24 wiki | Beds24 | n/d | full | medium | pattern |
| C6 | Nuki: each PIN may occur once in the system ("each PIN may only occur once in the system!"); post 2018-10, may be outdated | Q2 | Nuki | https://developer.nuki.io/t/web-api-example-manage-pin-codes-for-your-nuki-keypad/54 | Nuki dev forum | 2018-10 | full | medium | pattern |
| C7 | Nuki keypad code: six digits, 1-9 only, must not start with 12 (2018) | Q2 | Nuki | thread 54 | Nuki dev forum | 2018-10 | full | medium | version-compat |
| C8 | One Nuki authorization allows one time window per day; cross-code overlap not stated (2019-20) | Q2 | Nuki | thread 54 | Nuki dev forum | n/d | full | low | pattern |
| C9 | No documented overlap rule for igloohome found on the Seam page (absence of evidence) | Q2 | igloohome | Seam page | Seam | n/d | full | medium | pattern |
| C10 | Seam caps igloohome offline codes: 3 hourly-bound per hour, 3 daily-bound per day, 5 one-time per start-date slot | Q2 | igloohome | Seam page | Seam | n/d | full | medium | pattern |
| C11 | Nuki: POST /auth/{id} overwrites existing values including the code; can disable (enable=false) or delete (2018) | Q3 | Nuki | thread 54 | Nuki dev forum | 2018-10 | full | medium | pattern |
| C12 | Nuki create call returns an empty response; look up the PIN id afterwards | Q3 | Nuki | thread 54 | Nuki dev forum | 2018-10 / 2019-03 | full | medium | pattern |
| C13 | Nuki: changing the date without resending the weekday bitmask cleared the time window; send all time fields on each update | Q3, Q4 | Nuki | thread 54 | Nuki dev forum | 2019-01 | full | medium | pattern |
| C14 | igloohome algoPINs cannot be modified and cannot have a custom code | Q3, Q5 | igloohome | Seam page | Seam | n/d | full | medium | pattern |
| C15 | igloohome algoPINs can be deleted only within Bluetooth range; Seam API cannot delete them, so no remote per-code revoke | Q3, Q5 | igloohome | Seam page | Seam | n/d | full | high | pattern |
| C16 | igloohome algoPINs work without a bridge; the lock need not be online | Q4, Q5 | igloohome | Seam page | Seam | n/d | full | medium | pattern |
| C17 | Offline algoPIN timestamps rounded (default max_time_rounding 1 hour); API errors if more rounding needed; Smoobu says only full-hour times | Q4, Q5 | igloohome | Seam page; https://support.smoobu.com/hc/en-us/articles/360012021720 | Seam; Smoobu | n/d | full / snippet | medium | pattern |
| C18 | igloohome offline codes over 24 h must be used within 24 h of start; creation is asynchronous (pending `creating`, then `access_code.issued`) | Q4, Q5 | igloohome | Seam page | Seam | n/d | full | medium | pattern |
| C19 | igloohome help center: validity types Once, Permanent, Duration, Weekly; custom PINs (4-6 digits) need Bluetooth range; AlgoPINs (7-9 digits) can be generated remotely | Q3, Q5 | igloohome | https://support.igloohome.co/support/solutions/articles/35000183356-what-types-of-pin-codes-can-i-create- | igloohome support | n/d | full | medium | other |
| C20 | That page does not say whether Duration PINs can be edited, revoked or counted | Q3 | igloohome | same | igloohome support | n/d | full | medium | other |
| C21 | TTLock online passcodes can be updated/deleted only while the lock is connected to the internet; offline passcodes cannot be updated or deleted | Q3, Q4, Q5 | TTLock | Beds24 wiki | Beds24 | n/d | full | medium | pattern |
| C22 | TTLock offline passcodes: auto-generated 6-9 digits, start snaps to the hour, must be used within 24 h of start | Q4, Q5 | TTLock | Beds24 wiki | Beds24 | n/d | full | medium | pattern |
| C23 | A deleted TTLock offline passcode cannot be recreated with the same start and end | Q2, Q5 | TTLock | Beds24 wiki | Beds24 | n/d | full | medium | pattern |
| C24 | Beds24 pushes TTLock changes about every 12 h or on manual export; latency here is the integrator's schedule, not the lock's | Q4 | TTLock | Beds24 wiki | Beds24 | n/d | full | medium | performance |
| C25 | TTLock sync errors: "The gateway is busy", "The Lock is not connected to any Gateway", "failed" (weak Bluetooth to gateway) | Q4 | TTLock | Beds24 wiki | Beds24 | n/d | full | medium | pattern |
| C26 | ex_ttlock client: custom passcodes 4-9 digits, type 2 permanent, type 3 period; add method 1 Bluetooth, 2 gateway | Q1, Q3, Q4 | TTLock | https://hexdocs.pm/ex_ttlock/TTlockClient.html | hexdocs (third party) | n/d | snippet | low | pattern |
| C27 | Nuki Web API can report success without the PIN reaching the keypad: Smart Lock 3.0 Pro fw 3.10.7, PUT returned 204 but PIN absent; only signal was a websocket event errorCode -1; thread auto-closed 2025-11 with no staff reply, no fix evidence | Q4 | Nuki | https://developer.nuki.io/t/adding-a-keypad-code-is-very-unreliable-for-months/35046 | Nuki dev forum | 2025-03-24 | full | high | pattern |
| C28 | Same thread: some PINs failed repeatedly, one for a day; author retried every 5 min | Q4 | Nuki | thread 35046 | Nuki dev forum | 2025-03-24 | full | medium | pattern |
| C29 | Nuki authorizations are stored on the lock and synced to the Web API later; a delay is possible; forced sync via PUT /smartlock/{id}/sync fixed one case (2019) | Q4 | Nuki | thread 54 | Nuki dev forum | 2019-03 / 2019-06 | full | medium | performance |
| C30 | Nuki keypad programming through the Bridge API is not possible (needs admin rights); Web API path is cloud (2019) | Q4 | Nuki | thread 54 | Nuki dev forum | 2019-06-21 | full | low | version-compat |
| C31 | Nuki times are UTC on the lock; web app shows local time (2019) | Q4 | Nuki | thread 54 | Nuki dev forum | 2019-03-08 | full | medium | version-compat |
| C32 | Nuki does not email the guest when a keypad code is created via Web API; the platform must deliver it | Q4 | Nuki | thread 54 | Nuki dev forum | 2019-10-22 | full | medium | other |
| C33 | Nuki time-restricted codes need allowedFromDate (allowedUntilDate recommended); send all values even when only setting the time window | Q3 | Nuki | thread 54; thread 32726 | Nuki dev forum | 2019-01 / n/d | full / snippet | medium | pattern |
| C34 | Yale/August: only unofficial libraries (yalexs, august-yale) using an unpublished API found; no official PIN-schedule docs | Q1-Q5 | August/Yale | https://pypi.org/project/yalexs ; https://npmjs.com/package/august-yale | PyPI / npm | n/d | snippet | low | other |

## Leads worth chasing
- TTLock Open Platform reference (keyboardPwd add/change/delete, addType, per-lock limits, clock): open.sciener.com / euapi.ttlock.com. All TTLock evidence above is third-party.
- Nuki official API reference for /smartlock/{id}/auth and the "Key API Concepts" page (https://docs.nuki.io/guide/overview/concepts/); also https://developer.nuki.io/t/integration-of-web-api-for-short-time-rentals/8273.
- igloohome first-party API reference for online (bridge) PINs: edit, delete, slot limits.
- Seam docs for Yale/August (access-code endpoints, "set on the lock" delay).
- Nuki thread 35046: check changelog/firmware notes for a fix; test on a real device before trusting 204.

## Searched but not found
- Official source for overlapping validity (Q2) on Nuki, TTLock online, igloohome online: only same-PIN and same-start/end rules found. Overlap of A 15:00-16:30 with B 16:10-17:30 on one lock is unverified.
- No clock-drift source for any vendor; timezone only for Nuki (2019).
- No measured latency figures for create/change/delete; only Beds24's 12 h batch and Nuki's "there can be a delay".
- No official statement on change/delete before vs after validity starts (Q3 before/after) for any vendor; igloohome offline codes cannot be changed at all.
- No official Yale Access / August guest-PIN docs.
- Searches: "igloohome API Algo PIN duration hourly PIN", "Nuki Web API keypad authorization time-limited", "TTLock open platform API add custom passcode", "TTLock keyboardPwd change delete gateway offline", "Yale Access August lock API guest PIN schedule".
