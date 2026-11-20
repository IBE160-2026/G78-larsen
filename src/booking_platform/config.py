"""Deployment settings and test switches (AD-14, AD-22). A leaf module: it imports nothing from the package.

`config` is the only reader of the `BP_*` environment variables. Every variable has a working local default,
so no file is needed. Venue rules never live here (AD-4); they are columns of the `settings` row.
"""

from __future__ import annotations

import functools
import os
import tomllib
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_DATABASE_URL = "postgresql://postgres:booking@127.0.0.1:55432/booking_dev"
DEFAULT_BASE_URL = "http://127.0.0.1:3000"


class ConfigError(Exception):
    """The configuration cannot be used. The message is one line, fit to print before exiting."""


class paths:  # noqa: N801 - a namespace, read as config.paths.ROOT
    """`ROOT` is the only base for `migrations/`, `seeds/`, `content/` and `config/` (AD-22)."""

    ROOT = Path(os.environ["BP_ROOT"]).resolve() if os.environ.get("BP_ROOT") else Path(__file__).resolve().parents[2]
    MIGRATIONS = ROOT / "migrations"
    CONFIG = ROOT / "config"


def _flag(name: str, value: str) -> bool:
    v = value.strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("", "0", "false", "no", "off"):
        return False
    raise ConfigError(f"{name}={value!r} is not on or off")


def origin_of(url: str) -> str:
    """scheme://host[:port] of a URL, lower-cased, without path."""
    parts = urlsplit(url)
    return f"{parts.scheme.lower()}://{parts.netloc.lower()}"


@dataclass(frozen=True)
class Settings:
    database_url: str
    base_url: str
    https: bool
    host: str
    port: int
    test_switches: Path

    @property
    def base_origin(self) -> str:
        return origin_of(self.base_url)


def load_settings(env: dict[str, str] | None = None) -> Settings:
    env = os.environ if env is None else env
    base_url = env.get("BP_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    parts = urlsplit(base_url)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ConfigError(f"BP_BASE_URL={base_url!r} is not an http:// or https:// origin")
    https = _flag("BP_HTTPS", env.get("BP_HTTPS", "off"))
    if https and parts.scheme != "https":
        raise ConfigError(f"BP_HTTPS is on but BP_BASE_URL={base_url!r} does not start with https://")
    port_text = env.get("BP_PORT", "8001")
    try:
        port = int(port_text)
    except ValueError:
        raise ConfigError(f"BP_PORT={port_text!r} is not a port number") from None
    return Settings(
        database_url=env.get("BP_DATABASE_URL", DEFAULT_DATABASE_URL),
        base_url=base_url,
        https=https,
        host=env.get("BP_HOST", "127.0.0.1"),
        port=port,
        test_switches=Path(env.get("BP_TEST_SWITCHES", str(paths.CONFIG / "test-switches.toml"))),
    )


@functools.cache
def settings() -> Settings:
    """The settings of this process, read once."""
    return load_settings()


# ------------------------------------------------------------------ test switches (AD-14)

PAYMENT_OUTCOMES = ("ok", "fail", "hold")


@dataclass(frozen=True)
class Switches:
    payment: str = "ok"  # read only by payment.charge (Story 1.5)
    force_conflict: bool = False  # read only by db.run, for runs made for an HTTP request


def load_switches(path: Path) -> Switches:
    """A missing file, or a path that is not a regular file, means every switch is off. A file that exists but
    cannot be read or parsed is a ConfigError whose one-line message names the file."""
    if not path.is_file():
        return Switches()
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise ConfigError(f"test switch file {path} cannot be read: {type(e).__name__}") from None
    unknown = sorted(set(data) - {"payment", "force_conflict"})
    if unknown:
        raise ConfigError(f"test switch file {path} has unknown switches: {', '.join(unknown)}")
    payment = data.get("payment", "ok")
    if payment not in PAYMENT_OUTCOMES:
        raise ConfigError(f"test switch file {path}: payment must be one of {', '.join(PAYMENT_OUTCOMES)}")
    force_conflict = data.get("force_conflict", False)
    if not isinstance(force_conflict, bool):
        raise ConfigError(f"test switch file {path}: force_conflict must be true or false")
    return Switches(payment=payment, force_conflict=force_conflict)


@functools.cache
def switches() -> Switches:
    """The switches of this process, read once at startup and frozen."""
    return load_switches(settings().test_switches)


def load() -> tuple[Settings, Switches]:
    """Read and check everything at startup; raises ConfigError."""
    return settings(), switches()


# True while the code runs for an HTTP request (set by the app's middleware). `force_conflict` applies only then,
# never to migrations or startup work.
in_request: ContextVar[bool] = ContextVar("in_request", default=False)
