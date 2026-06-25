#!/usr/bin/env python
"""CLI for the Daily Omega Intelligence OS compiler.

Examples:

    python scripts/daily_omega_intelligence_os.py examples/daily_omega_signal_template.json
    python scripts/daily_omega_intelligence_os.py examples/daily_omega_signal_template.json --format json

This script is local-only. It does not call GitHub APIs and does not create issues.
"""

from __future__ import annotations

import argparse
import json

from sage_tristan.daily_omega_intelligence_os import compile_signal_genome, render_intelligence_os_markdown
from sage_tristan.daily_omega_io import load_item_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile a Daily Omega signal into a SignalGenome.")
    parser.add_argument("signal_json", help="Path to a Daily Omega signal JSON file.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--create-mode", action="store_true", help="Evaluate as non-dry-run. Still no GitHub calls.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    item = load_item_json(args.signal_json)
    genome = compile_signal_genome(item, dry_run=not args.create_mode)
    if args.format == "json":
        print(json.dumps(genome.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(render_intelligence_os_markdown([genome]))


if __name__ == "__main__":
    main()
