#!/usr/bin/env python
"""Batch CLI for Daily Omega signal folders.

Examples:

    python scripts/daily_omega_batch.py examples/daily_omega_signals --date 2026-06-24
    python scripts/daily_omega_batch.py examples/daily_omega_signals --date 2026-06-24 --output reports/daily_omega/generated

The script reads local JSON files and writes local outputs only. It never calls
GitHub APIs and never creates issues.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from sage_tristan.daily_omega_batch import (
    DEFAULT_TIMEZONE,
    build_batch_from_directory,
    summarize_batch,
    write_batch_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Daily Omega report from a folder of signal JSON files.")
    parser.add_argument("signals_directory", help="Directory containing Daily Omega signal JSON files.")
    parser.add_argument("--date", required=True, help="Briefing date in YYYY-MM-DD format.")
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE, help="Briefing timezone label.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of ranked items.")
    parser.add_argument("--output", help="Optional directory for Markdown and JSON outputs.")
    parser.add_argument(
        "--create-mode",
        action="store_true",
        help="Evaluate decisions as if creation approval were being considered. Still no GitHub calls.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_batch_from_directory(
        args.signals_directory,
        briefing_date=date.fromisoformat(args.date),
        timezone=args.timezone,
        limit=args.limit,
        dry_run=not args.create_mode,
    )
    print(summarize_batch(result))
    if args.output:
        markdown_path, json_path = write_batch_outputs(result, args.output, stem=args.date)
        genomes_path = Path(args.output) / f"{args.date}.genomes.json"
        print(f"Wrote {markdown_path}")
        print(f"Wrote {json_path}")
        print(f"Wrote {genomes_path}")
    else:
        print(result.markdown_report)


if __name__ == "__main__":
    main()
