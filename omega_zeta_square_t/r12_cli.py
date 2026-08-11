"""CLI for the R12 CVCD Hankel constraint atlas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .constraint_atlas import build_constraint_atlas


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-zeta-square-r12",
        description="Generate a CVCD-deduplicated finite R10 constraint atlas.",
    )
    parser.add_argument("--max-size", type=int, default=3)
    parser.add_argument("--shifts", type=int, nargs="+", default=[0, 1])
    parser.add_argument("--output", type=Path)
    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    atlas = build_constraint_atlas(args.max_size, tuple(args.shifts))
    text = json.dumps(atlas, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
