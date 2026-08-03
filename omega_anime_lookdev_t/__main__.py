"""CLI for Ω-ANIME-LOOKDEV-T∞ R5."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bible import build_eighth_fire_lookdev_r5
from .compiler import compile_lookdev_bundle


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="omega-anime-lookdev")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("validate-lookdev-r5")
    compile_parser = commands.add_parser("compile-lookdev-r5")
    compile_parser.add_argument("--output-dir", type=Path, required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    bible = build_eighth_fire_lookdev_r5()
    if args.command == "validate-lookdev-r5":
        errors = bible.validate()
        print(json.dumps({
            "valid": not errors,
            "errors": errors,
            "characters": len(bible.characters),
            "episodes": len(bible.episodes),
            "style": bible.style_name,
        }, ensure_ascii=False, indent=2))
        return 0 if not errors else 1
    manifest = compile_lookdev_bundle(bible, args.output_dir)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
