"""The booking platform backend. `booking-platform dev` (auto-reload) or `booking-platform serve` start one uvicorn
process on BP_HOST:BP_PORT (default 127.0.0.1:8001) (AD-22)."""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="booking-platform", description="Saunalöyly booking platform backend")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("dev", help="run the API with auto-reload (development)")
    sub.add_parser("serve", help="run the API")
    args = parser.parse_args(argv)

    from . import config
    from .services import seed

    try:
        settings, _ = config.load()
        seed.load()  # the seed file is checked before anything starts; it is applied after the migrations (AD-18)
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
