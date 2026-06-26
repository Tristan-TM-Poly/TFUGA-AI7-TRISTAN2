#!/usr/bin/env python
"""CLI for Daily Omega EvidenceGraph exports.

Examples:

    python scripts/daily_omega_evidence.py examples/daily_omega_signals --date 2026-06-24
    python scripts/daily_omega_evidence.py examples/daily_omega_signals --date 2026-06-24 --format json

The script reads local JSON files only. It never calls GitHub APIs and never
creates issues or canon promotions.
"""

from __future__ import annotations

import argparse
from datetime import date

from sage_tristan.daily_omega_batch import DEFAULT_TIMEZONE
from sage_tristan.daily_omega_evidence import build_evidence_from_directory, render_evidence_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Daily Omega EvidenceGraphs from signal JSON files.")
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
    result = build_evidence_from_directory(
        args.signals_directory,
        briefing_date=date.fromisoformat(args.date),
        timezone=args.timezone,
        limit=args.limit,
        dry_run=not args.create_mode,
    )
    if args.format == "json":
        print(result.to_json())
    else:
        print(render_evidence_markdown(result))


if __name__ == "__main__":
    main()
