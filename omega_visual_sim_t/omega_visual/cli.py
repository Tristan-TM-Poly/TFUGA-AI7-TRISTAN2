from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import SpecError, compile_visual, verify_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-visual")
    commands = parser.add_subparsers(dest="command", required=True)
    render = commands.add_parser("render", help="compile a VisualSpec")
    render.add_argument("spec", type=Path)
    render.add_argument("--output", type=Path, required=True)
    verify = commands.add_parser("verify", help="verify artifact hashes")
    verify.add_argument("manifest", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "render":
            manifest = compile_visual(args.spec, args.output)
            print(json.dumps(manifest, indent=2))
            return 0
        errors = verify_manifest(args.manifest)
        print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}, indent=2))
        return 0 if not errors else 1
    except (OSError, ValueError, KeyError, SpecError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
