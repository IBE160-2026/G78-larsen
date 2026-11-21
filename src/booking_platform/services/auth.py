"""Accounts and sign-in (FR-15, FR-19, PW-1 to PW-6, AD-11).

- `check_password_rules(password, email)` is the one password rule check, used by the seed, `create-admin` and
  (later) sign-up. A password must have at least 15 characters after NFC, must not be on the packaged common list
  (`data/common-passwords.txt`, compared lower-cased) and must not equal the email (case-insensitive). There are no
  composition rules and no upper limit below 1024 characters (the API caps the field there).
- Passwords are hashed with Argon2id at `argon2-cffi`'s defaults, in PHC format, after NFC normalisation (so the
  same password typed on another keyboard verifies). The same password gives a new salt, so a new hash, each time.
- `sign_in(session, email, password)` runs in one `db.run(work)`: it upserts and locks the email's throttle row,
  verifies (against a dummy hash when the email has no account, so timing says nothing), then decides. Every
  refusal (wrong password, unknown email, throttled email) is the same `sign_in_refused`. A refusal is returned
  from `work`, not raised, so its count commits. After 5 failures in a row the email is refused for 15 minutes,
  even with the right password; a locked attempt counts but never extends the lock. A success resets the count and
  rotates the session's token on the same row, with the Administrator role and lifetime (AD-8).

Nothing here logs a password, a hash, a token or an email.
"""

from __future__ import annotations

import functools
import logging
import re
import unicodedata
from importlib import resources

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from .. import db
from ..db import accounts as aq
from ..db import sessions as sq
from . import sessions
from .errors import Refused

log = logging.getLogger("booking_platform.auth")

MIN_LENGTH = 15  # PW-2
MAX_LENGTH = 1024  # the API's cap on the field; the rules themselves have no upper limit below it
EMAIL_MAX = 254
MAX_FAILURES = 5  # PW-6: failures in a row before the email is locked
LOCK_MINUTES = 15
ROLE_ADMIN = "admin"
# The shape of an email for the seed and `create-admin` (the same as a Guest's, FR-5).
EMAIL = re.compile(r"^[^@\s\x00-\x1f\x7f]+@[^@\s\x00-\x1f\x7f]+\.[^@\s\x00-\x1f\x7f]+$")

_hasher = PasswordHasher()  # Argon2id, argon2-cffi defaults (AD-11)
# Verified against when the email has no account, so an unknown email costs one Argon2 verify like a known one.
_DUMMY_HASH = _hasher.hash("no account has this password; it only spends the time of a verify")


class PasswordRuleError(Exception):
    """A password that breaks a rule of PW-2. `reason` is `too_short`, `common` or `equals_email`. Not a `Refused`:
    no endpoint sets passwords yet."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


@functools.cache
def common_passwords() -> frozenset[str]:
    """The packaged common-password list: entries of 15 or more characters, lower-cased (ASSETS.md)."""
    text = resources.files("booking_platform").joinpath("data", "common-passwords.txt").read_text(encoding="utf-8")
    return frozenset(line for line in text.splitlines() if line)


def check_password_rules(password: str, email: str) -> None:
    """The one rule check (PW-2, PW-3, AD-11); raises PasswordRuleError."""
    p = _nfc(password)
    if len(p) < MIN_LENGTH:
        raise PasswordRuleError("too_short")
    if p.lower() in common_passwords():
        raise PasswordRuleError("common")
    if p.casefold() == _nfc(email.strip()).casefold():
        raise PasswordRuleError("equals_email")


def hash_password(password: str) -> str:
    """An Argon2id hash in PHC format (`$argon2id$…`), with a fresh salt."""
    return _hasher.hash(_nfc(password))


def _verify(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def sign_in(session: sessions.Session | None, email: str, password: str) -> str:
    """Sign the browser session in (FR-15). Returns the new cookie token. Raises `Refused('no_session')` without a
    valid session (no throttle row is touched) and `Refused('sign_in_refused')` for every refusal."""
    if session is None:
        raise Refused("no_session")
    email = email.strip()
    password = _nfc(password)
    token = sessions.new_token()

    def work(c) -> str | None:
        failures, locked = aq.lock_throttle(c, email)
        account = aq.find(c, email)
        matches = _verify(account[1] if account else _DUMMY_HASH, password) and account is not None
        if locked or not matches:
            lock = not locked and failures + 1 >= MAX_FAILURES
            aq.record_failure(c, email, LOCK_MINUTES if lock else None)
            return None  # returned, not raised, so the count commits (AD-11)
        account_id, password_hash, _role = account
        if not sq.rotate(c, session.id, sessions.token_hash(token), account_id):
            raise Refused("no_session")  # the row expired or was deleted meanwhile; nothing is written
        aq.reset_throttle(c, email)
        if _hasher.check_needs_rehash(password_hash):
            aq.set_hash(c, account_id, _hasher.hash(password))
        return token

    result = db.run(work)
    if result is None:
        log.info("sign-in refused")
        raise Refused("sign_in_refused")
    log.info("signed in: session %d", session.id)
    return result


def sign_out(session: sessions.Session) -> None:
    """Delete the session row (FR-15): its token names nothing afterwards."""
    db.run(lambda c: sq.delete(c, session.id))
    log.info("signed out: session %d", session.id)


def set_account(c, email: str, password: str, *, overwrite: bool) -> bool:
    """Store an Administrator with this email and password after `check_password_rules` (raises PasswordRuleError
    and writes nothing). With `overwrite` (create-admin) an existing account gets the new hash; without it (the seed)
    an existing account is left alone and nothing is hashed. A changed password ends every session of the account in
    the same transaction. Returns True when the account is new."""
    check_password_rules(password, email)
    if overwrite:
        account_id, inserted = aq.upsert(c, email, hash_password(password), ROLE_ADMIN)
        if not inserted:
            aq.end_sessions(c, account_id)
        return inserted
    if aq.exists(c, email):
        return False
    return aq.insert_if_absent(c, email, hash_password(password), ROLE_ADMIN)
