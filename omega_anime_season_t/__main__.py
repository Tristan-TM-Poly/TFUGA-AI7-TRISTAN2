"""CLI for Ω-ANIME-SEASON-T∞ R4."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .compiler import compile_season_bundle
from .season import build_eighth_fire_season_01_r4


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-anime-season")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate-season-01", help="validate 12 episodes × 20 minutes")
    compile_parser = sub.add_parser(
        "compile-season-01", help="compile all episode bundles and season ledgers"
    )
    compile_parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    season = build_eighth_fire_season_01_r4()
    if args.command == "validate-season-01":
        errors = season.validate()
        print(
            json.dumps(
                {
                    "valid": not errors,
                    "errors": errors,
                    "episodes": len(season.episodes),
                    "duration_s": season.total_duration_s,
                    "scenes": season.total_scenes,
                    "shots": season.total_shots,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if not errors else 1
    manifest = compile_season_bundle(season, args.output_dir)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
