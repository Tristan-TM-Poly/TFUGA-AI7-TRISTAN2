"""Command line interface."""

from __future__ import annotations

import argparse
import json

from .export import export_pack
from .io import load_seed
from .seed import example_seed
from .summary import short_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-patent-thesis")
    parser.add_argument("mode", choices=("demo", "summary", "export"))
    parser.add_argument("--input", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    seed = example_seed() if not args.input else load_seed(args.input)
    if args.mode == "summary":
        print(short_summary(seed), end="")
        return 0
    payload = seed.to_dict() if args.mode == "demo" else export_pack(seed)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0
