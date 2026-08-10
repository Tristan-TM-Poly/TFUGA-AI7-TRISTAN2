from __future__ import annotations

import argparse

from .bench import render_oakbench
from .r05_evidence import render_r05_evidence
from .r06_evidence import render_r06_evidence


def main() -> int:
    parser = argparse.ArgumentParser(prog="omega-recycle", description="Ω-RECYCLE-T∞ research CLI")
    parser.add_argument(
        "command",
        nargs="?",
        default="oakbench",
        choices=("oakbench", "evidence-r05", "evidence-r06"),
        help="deterministic research action",
    )
    args = parser.parse_args()
    if args.command == "oakbench":
        print(render_oakbench())
        return 0
    if args.command == "evidence-r05":
        print(render_r05_evidence())
        return 0
    if args.command == "evidence-r06":
        print(render_r06_evidence())
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
