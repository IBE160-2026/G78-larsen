"""The e2e layer (AD-27): the whole compose stack behind Caddy, as compose project `booking_e2e`.

The session fixture writes its own env file (free host ports for `HTTP_PORT`, `HTTPS_PORT` and `DB_PORT`, and its
own `SWITCHES_DIR`), runs `up --build --wait` and ends with `down -v`, so it never touches the dev stack on
8000/8443/55432. Every compose call goes through `compose()`. The site is HTTPS only (FR-24): the fixture copies
Caddy's local root out of the proxy and builds the one `ssl.SSLContext` (`trust`, the `tls` fixture) that every e2e
HTTP call verifies with; Playwright runs with `ignore_https_errors`. Every e2e test takes its URL from `base_url`,
never a literal. Nothing here uses the API layer's fixtures (`database`, `backend`).
"""

from __future__ import annotations

import os
import socket
import ssl
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

from . import trust

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "booking_e2e"
ENV_FILE: Path | None = None  # set by the `stack` fixture before the first compose call
CADDY_ROOT = "/data/caddy/pki/authorities/local/root.crt"  # Caddy's internal CA, in the `caddy_data` volume


def compose_env() -> dict[str, str]:
    """The shell environment without `HSTS_MAX_AGE`, so a developer's own value never reaches the e2e proxy (HT-2
    expects the Caddyfile's default)."""
    env = dict(os.environ)
    env.pop("HSTS_MAX_AGE", None)
    return env


def compose(*args: str, check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """`docker compose -p booking_e2e --env-file <its file> <args>`: the one shape of every e2e compose call. It runs
    with `compose_env()` unless the caller passes its own `env`."""
    if ENV_FILE is None:
        raise RuntimeError("compose() is called before the stack fixture wrote its env file")
    return subprocess.run(["docker", "compose", "-p", PROJECT, "--env-file", str(ENV_FILE), *args],
                          cwd=ROOT, capture_output=True, text=True, check=check, timeout=900,
                          env=compose_env() if env is None else env)


def _free_ports(n: int) -> list[int]:
    socks = []
    try:
        for _ in range(n):
            s = socket.socket()
            s.bind(("127.0.0.1", 0))
            socks.append(s)
        return [s.getsockname()[1] for s in socks]
    finally:
        for s in socks:
            s.close()


def _copy_root(dest: Path, wait_s: float = 60) -> Path:
    """Copy Caddy's root out of the proxy, retrying until the file exists (Caddy writes it once it issues the first
    `localhost` certificate)."""
    deadline = time.monotonic() + wait_s
    while True:
        r = compose("cp", f"proxy:{CADDY_ROOT}", str(dest), check=False)
        if r.returncode == 0 and dest.is_file() and dest.stat().st_size > 0:
            return dest
        if time.monotonic() > deadline:
            raise RuntimeError(f"Caddy's root {CADDY_ROOT} did not appear in the proxy:\n{r.stderr[-2000:]}")
        time.sleep(1)


@dataclass(frozen=True)
class Stack:
    http_port: int
    https_port: int
    db_port: int
    switches_dir: Path

    @property
    def base_url(self) -> str:
        # HTTPS only since FR-24; the site answers only for `localhost` (AD-27). Plain HTTP on `http_port` redirects.
        return f"https://localhost:{self.https_port}"

    def compose(self, *args: str, check: bool = True,
                env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        """For tests: the same one helper (test modules do not import conftest)."""
        return compose(*args, check=check, env=env)

    @staticmethod
    def compose_env() -> dict[str, str]:
        return compose_env()

    def wait(self) -> None:
        """Wait until every service is healthy again (after a stop, start or restart)."""
        compose("up", "--wait")


@pytest.fixture(scope="session")
def stack(tmp_path_factory) -> Stack:
    global ENV_FILE
    work = tmp_path_factory.mktemp("e2e")
    switches = work / "switches"
    switches.mkdir()
    os.chmod(switches, 0o755)  # AD-14: the backend container reads it as another user
    http_port, https_port, db_port = _free_ports(3)
    env_file = work / "e2e.env"
    env_file.write_text(f"HTTP_PORT={http_port}\nHTTPS_PORT={https_port}\nDB_PORT={db_port}\n"
                        f"SWITCHES_DIR={switches.as_posix()}\n", encoding="utf-8")
    ENV_FILE = env_file
    s = Stack(http_port, https_port, db_port, switches)
    try:
        compose("up", "--build", "--wait")
    except FileNotFoundError:
        pytest.exit("docker is not installed or not on PATH; the e2e layer needs Docker", 2)
    except subprocess.CalledProcessError as e:
        logs = compose("logs", "--no-color", "--tail", "40", check=False).stdout
        compose("down", "-v", check=False)
        pytest.exit(f"docker compose -p {PROJECT} up --build --wait failed:\n{e.stderr[-2000:]}\n{logs[-4000:]}", 2)
    except subprocess.TimeoutExpired:
        compose("down", "-v", check=False)
        pytest.exit(f"docker compose -p {PROJECT} up --build --wait timed out", 2)
    try:
        trust.load(_copy_root(work / "root.crt"))
    except RuntimeError as e:
        compose("down", "-v", check=False)
        pytest.exit(str(e), 2)
    try:
        yield s
    finally:
        compose("down", "-v", check=False)


@pytest.fixture(scope="session")
def base_url(stack: Stack) -> str:
    """The stack's one origin. Overrides pytest-playwright's `base_url`, so its `page` uses it too."""
    return stack.base_url


@pytest.fixture(scope="session")
def tls(stack: Stack) -> ssl.SSLContext:
    """The one context that trusts Caddy's root alone: pass it as `verify=` to every e2e HTTP call."""
    return trust.context()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """pytest-playwright's own contexts accept Caddy's certificate; an explicit `browser.new_context` passes
    `ignore_https_errors=True` itself."""
    return {**browser_context_args, "ignore_https_errors": True}
