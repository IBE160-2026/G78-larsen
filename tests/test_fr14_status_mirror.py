"""AD-16: the frontend's one mirror of the code -> status table (`frontend/lib/api.js` STATUS) equals the
backend's (`booking_platform.api.errors.STATUS`)."""

from __future__ import annotations

import re
from pathlib import Path

from booking_platform.api.errors import STATUS

API_JS = Path(__file__).resolve().parents[1] / "frontend" / "lib" / "api.js"


def frontend_status() -> dict[str, int]:
    text = API_JS.read_text(encoding="utf-8")
    block = re.search(r"export const STATUS = Object\.freeze\(\{(.*?)\}\);", text, re.S)
    assert block, "STATUS not found in frontend/lib/api.js"
    return {code: int(status) for code, status in re.findall(r"(\w+):\s*(\d+)", block.group(1))}


def test_frontend_status_table_mirrors_the_backend():
    assert frontend_status() == STATUS
