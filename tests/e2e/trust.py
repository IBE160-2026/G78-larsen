"""The TLS trust of the e2e layer (FR-24, AD-27 Tests): one `ssl.SSLContext` that trusts Caddy's local root alone.

The `stack` fixture copies the root out of the proxy and calls `load()`. Every e2e HTTP call verifies TLS with
`context()`; the helper modules take it from here because they get only `base_url` (test modules do not import
conftest). Tests can also ask for the `tls` fixture, which is the same object.
"""

from __future__ import annotations

import ssl
from pathlib import Path

_CONTEXT: ssl.SSLContext | None = None


def load(root: Path) -> ssl.SSLContext:
    """Build the one context from Caddy's root certificate (no system roots: only the stack's own CA is trusted)."""
    global _CONTEXT
    _CONTEXT = ssl.create_default_context(cafile=str(root))
    return _CONTEXT


def context() -> ssl.SSLContext:
    if _CONTEXT is None:
        raise RuntimeError("trust.context() is called before the stack fixture copied Caddy's root")
    return _CONTEXT
