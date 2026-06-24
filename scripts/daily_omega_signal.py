#!/usr/bin/env python
"""Reusable CLI for Daily Omega signal files.

Examples:

    python scripts/daily_omega_signal.py examples/daily_omega_signal_template.json
    python scripts/daily_omega_signal.py examples/daily_omega_signal_template.json --format json
    python scripts/daily_omega_signal.py examples/daily_omega_signal_template.json --create-mode

The default is dry-run Markdown. The script never calls GitHub APIs.
"""

from __future__ import annotations

import argparse

from sage_tristan.daily_omega_io import export_decision_json, export_decision_markdown, load_item_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review a Daily Omega signal JSON file.")
    parser.add_argument("signal_json", help="Path to a Daily Omega signal JSON file.")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format.",
    )
    parser.add_argument(
        "--create-mode",
        action="store_true",
        help="Evaluate as if explicit creation approval was given. This still does not call GitHub.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    item = load_item_json(args.signal_json)
    dry_run = not args.create_mode
    if args.format == "json":
        print(export_decision_json(item, dry_run=dry_run))
    else:
        print(export_decision_markdown(item, dry_run=dry_run))


if __name__ == "__main__":
    main()
