#!/usr/bin/env python
"""CLI for Daily Omega PrototypeCompiler exports.

Examples:

    python scripts/daily_omega_prototype.py examples/daily_omega_signals --date 2026-06-24
    python scripts/daily_omega_prototype.py examples/daily_omega_signals --date 2026-06-24 --format json

The script reads local JSON files only. It never calls GitHub APIs, creates
issues, performs external actions, or promotes canon.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sage_tristan.daily_omega_batch import DEFAULT_TIMEZONE
from sage_tristan.daily_omega_prototype import build_prototype_from_directory, render_prototype_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Daily Omega prototype plans from signal JSON files.")
    parser.add_argument("signals_directory", help="Directory containing Daily Omega signal JSON files.")
    parser.add_argument("--date", required=True, help="Briefing date in YYYY-MM-DD format.")
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE, help="Briefing timezone label.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of ranked items.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument(
        "--create-mode",
        action="store_true",
        help="Evaluate decisions as if creation approval were being considered. Still no GitHub calls.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_prototype_from_directory(
        args.signals_directory,
        briefing_date=date.fromisoformat(args.date),
        timezone=args.timezone,
        limit=args.limit,
        dry_run=not args.create_mode,
    )
    if args.format == "json":
        print(result.to_json())
    else:
        print(render_prototype_markdown(result))


if __name__ == "__main__":
    main()
