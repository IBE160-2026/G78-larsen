"""The booking platform backend. `booking-platform dev` (auto-reload) or `booking-platform serve` start one uvicorn
process on BP_HOST:BP_PORT (default 127.0.0.1:8001) (AD-22). `booking-platform create-admin` creates an
Administrator or sets a new password for one (AD-18, AD-19)."""

from __future__ import annotations

import argparse
import copy
import getpass
import sys
from pathlib import Path
from typing import NoReturn


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="booking-platform", description="Saunalöyly booking platform backend")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("dev", help="run the API with auto-reload (development)")
    sub.add_parser("serve", help="run the API")
    sub.add_parser("create-admin", help="create an Administrator, or set a new password for one (prompts)")
    args = parser.parse_args(argv)

    if args.command == "create-admin":
        create_admin()
        return

    from . import config
    from .services import seed

    try:
        settings, _ = config.load()
        seed.load()  # the seed files are checked before anything starts; they are applied after the migrations (AD-18)
        seed.load_bookings()
    except (config.ConfigError, seed.SeedError) as e:
        print(f"booking-platform: {e}", file=sys.stderr)
        sys.exit(2)

    import uvicorn
    from uvicorn.config import LOGGING_CONFIG

    # The app's own loggers (`booking_platform.*`) log ids, names and codes at INFO to stderr, through uvicorn's
    # formatter. Nothing logs request bodies, headers or cookies (AD-19).
    log_config = copy.deepcopy(LOGGING_CONFIG)
    log_config["loggers"]["booking_platform"] = {"handlers": ["default"], "level": "INFO", "propagate": False}

    if args.command == "dev":
        uvicorn.run("booking_platform.app:app", host=settings.host, port=settings.port, reload=True,
                    reload_dirs=[str(Path(__file__).resolve().parent)], log_config=log_config)
    else:
        uvicorn.run("booking_platform.app:app", host=settings.host, port=settings.port, log_config=log_config)


def _fail(message: str) -> NoReturn:
    print(f"booking-platform: {message}", file=sys.stderr)
    sys.exit(2)


def create_admin() -> None:
    """Prompt for the email and, twice without echo, the password; never from an argument or an environment variable
    (AD-19). The password must pass `check_password_rules` (FR-19); a refusal is one line and exit code 2, and nothing
    is written. Then migrate (creating `booking_dev` for the default URL) and create the account, or give the
    existing one the new hash. Prints the email and "created" or "password changed", never the password."""
    import psycopg

    from . import config
    from .db import migrate
    from .services import auth

    try:
        settings = config.settings()
    except config.ConfigError as e:
        _fail(str(e))
    try:
        email = input("Email: ").strip()
        password = getpass.getpass("Password: ")
        again = getpass.getpass("Password again: ")
    except (EOFError, KeyboardInterrupt):
        _fail("cancelled, nothing written")
    if len(email) > auth.EMAIL_MAX or not auth.EMAIL.fullmatch(email):
        _fail("that is not an email address, nothing written")
    if password != again:
        _fail("the two passwords differ, nothing written")
    if len(password) > auth.MAX_LENGTH:
        _fail(f"the password is longer than {auth.MAX_LENGTH} characters, nothing written")
    try:
        auth.check_password_rules(password, email)
    except auth.PasswordRuleError as e:
        _fail(f"password refused: {e.reason}, nothing written")
    try:
        migrate.ensure_database(settings.database_url)
        migrate.migrate(settings.database_url)
        with psycopg.connect(settings.database_url) as c:  # commits on leaving the block
            created = auth.set_account(c, email, password, overwrite=True)
    except (migrate.MigrationError, psycopg.Error) as e:
        _fail(f"the database could not be updated: {type(e).__name__}")
    print(f"{email.lower()}: {'created' if created else 'password changed'}")
