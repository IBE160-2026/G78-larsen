"""The `/api/admin` router (AD-10). Its one dependency requires an Administrator session: anonymous callers get
401 `not_signed_in`, other sessions 403 `not_allowed`, and neither changes anything."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..services import blocks, marks, settings, whole
from .deps import require_admin
from .schemas import BlockIn, MarkIn, SettingsIn, WholeIn

router = APIRouter(prefix="/api/admin", redirect_slashes=False, dependencies=[Depends(require_admin)])


@router.post("/whole-bookings", status_code=201)
def book_whole(body: WholeIn):
    return {"whole_booking_id": whole.book_whole(body.window_id, body.sauna_id)}


@router.post("/blocks", status_code=201)
def block(body: BlockIn):
    return {"block_id": blocks.block(body.sauna_id, body.start, body.end)}


@router.delete("/blocks/{block_id}")
def lift_block(block_id: int):
    return {"lifted": blocks.lift(block_id)}


@router.post("/marks", status_code=201)
def mark(body: MarkIn):
    return {"mark_id": marks.mark(body.window_id, body.sauna_id)}


@router.delete("/marks")
def unmark(window_id: int, sauna_id: int):
    return {"removed": marks.unmark(window_id, sauna_id)}


@router.put("/settings")
def put_settings(body: SettingsIn):
    settings.put(body.release_on, body.release_time, body.booking_deadline_minutes)
    return {"ok": True}
