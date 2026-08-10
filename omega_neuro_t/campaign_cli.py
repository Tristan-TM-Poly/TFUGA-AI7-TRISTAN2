from __future__ import annotations

import argparse
import json

from .hypothesis_campaign import run_p2_benchmark, run_p2_p3_campaign, run_p3_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Ω-NEURO P2/P3 synthetic evidence campaign")
    parser.add_argument(
        "--hypothesis",
        choices=("p2", "p3", "all"),
        default="all",
        help="select one synthetic evidence harness or run the combined campaign",
    )
    parser.add_argument("--pretty", action="store_true", help="pretty-print deterministic JSON")
    args = parser.parse_args()

    if args.hypothesis == "p2":
        report = run_p2_benchmark()
    elif args.hypothesis == "p3":
        report = run_p3_benchmark()
    else:
        report = run_p2_p3_campaign()

    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
