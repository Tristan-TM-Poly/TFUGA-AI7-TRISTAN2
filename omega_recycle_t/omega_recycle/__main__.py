from __future__ import annotations

import argparse

from .bench import render_oakbench


def main() -> int:
    parser = argparse.ArgumentParser(prog="omega-recycle", description="Ω-RECYCLE-T∞ research CLI")
    parser.add_argument("command", nargs="?", default="oakbench", choices=("oakbench",), help="deterministic research action")
    args = parser.parse_args()
    if args.command == "oakbench":
        print(render_oakbench())
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
