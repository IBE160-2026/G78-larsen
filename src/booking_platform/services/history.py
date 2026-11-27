"""The Change history of Bookings (AD-29). `record` is the only writer of `booking_changes`; no trigger writes it.
`of_bookings` is the one read, shared by the Manage read and the Administrator's Booking list. An entry never holds a
name, an email, a token or a Voucher code (FR-4, AD-30): only what moved or was given up, when, between which Windows,
the new reference of a split and the value of a Voucher issued. Only an entry of a Whole-sauna booking names a Sauna
(`from_sauna`, `to_sauna`, Story 5.3); an entry of a Seat booking never holds a Sauna."""

from __future__ import annotations

from zoneinfo import ZoneInfo

import psycopg

from ..db import changes as q


def record(c: psycopg.Connection, booking_id: int, action: str, **cols) -> int:
    """Write one history row for a Change of the Booking, in the caller's transaction; returns its id (the
    `change_id` of the Change's emails and key)."""
    unknown = set(cols) - q.HISTORY_COLUMNS
    if unknown:
        raise ValueError(f"unknown history columns: {sorted(unknown)}")
    return q.insert_change(c, booking_id, action, cols)


def _window(wid, start, end, tz: ZoneInfo) -> dict | None:
    if wid is None:
        return None
    return {"id": wid, "start": start.astimezone(tz).isoformat(), "end": end.astimezone(tz).isoformat()}


def _sauna(sid, name) -> dict | None:
    return None if sid is None else {"id": sid, "name": name}


def of_bookings(c: psycopg.Connection, booking_ids: list[int], tz: ZoneInfo) -> dict[int, list[dict]]:
    """Booking id -> its history entries, oldest first: `{action, at, seats, from_window, to_window,
    new_reference, voucher_value_ore}`, and for a Whole-sauna booking also `from_sauna` and `to_sauna` (`{id, name}`,
    null except for a move). Times are ISO strings in Venue time; `new_reference` is null unless the move split the
    Booking; `voucher_value_ore` is null for a move (`action` `voucher`: the Voucher's value)."""
    out: dict[int, list[dict]] = {bid: [] for bid in booking_ids}
    if not booking_ids:
        return out
    for (_cid, bid, action, at, seats, fw, fw_start, fw_end, tw, tw_start, tw_end,
         new_reference, voucher_value, kind, fs, fs_name, ts, ts_name) in q.history_of(c, booking_ids):
        entry = {
            "action": action,
            "at": at.astimezone(tz).isoformat(),
            "seats": seats,
            "from_window": _window(fw, fw_start, fw_end, tz),
            "to_window": _window(tw, tw_start, tw_end, tz),
            "new_reference": new_reference,
            "voucher_value_ore": voucher_value,
        }
        if kind == "whole":  # a Seat booking's entry never names a Sauna (FR-4)
            entry["from_sauna"] = _sauna(fs, fs_name)
            entry["to_sauna"] = _sauna(ts, ts_name)
        out[bid].append(entry)
    return out


def of_booking(c: psycopg.Connection, booking_id: int, tz: ZoneInfo) -> list[dict]:
    return of_bookings(c, [booking_id], tz)[booking_id]
