from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import constitution, demo_bundle, regeneration_receipt


def _write(payload: dict, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-ait-llmt-allt", description="Ω-AIT-LLMT-ALLT proof-carrying morphogenesis kernel R0.1")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("demo", "constitution", "regeneration"):
        child = sub.add_parser(name)
        child.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        payload = demo_bundle()
    elif args.command == "constitution":
        payload = constitution()
    else:
        payload = regeneration_receipt()
    _write(payload, args.output)
    return 0
