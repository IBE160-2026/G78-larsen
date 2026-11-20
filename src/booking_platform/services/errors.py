"""The one refusal type (AD-1). `Refused(code, **facts)`: the code is declared once in `api/errors.py`.

Both classes are defined in `db.refusals`, so `db` can raise them without importing a layer above it.
"""

from __future__ import annotations

from ..db.refusals import Refused, StoreError

__all__ = ["Refused", "StoreError"]
