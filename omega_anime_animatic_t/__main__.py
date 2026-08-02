"""Command-line interface for Ω-ANIME-ANIMATIC-T R2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .compiler import compile_animatic_bundle
from .timeline import build_eighth_fire_animatic_r2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-anime-animatic")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate-demo", help="validate the canonical 180-second timeline")
    compile_parser = sub.add_parser("compile-demo", help="compile the self-contained R2 bundle")
    compile_parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    timeline = build_eighth_fire_animatic_r2()
    if args.command == "validate-demo":
        errors = timeline.validate()
        print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        return 0 if not errors else 1
    manifest = compile_animatic_bundle(timeline, args.output_dir)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
