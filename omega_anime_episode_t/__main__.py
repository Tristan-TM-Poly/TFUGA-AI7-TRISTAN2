"""CLI for Ω-ANIME-EPISODE-T R3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .compiler import compile_episode_bundle
from .episode import build_eighth_fire_episode_01_r3


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="omega-anime-episode")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("validate-episode-01")
    compile_parser = commands.add_parser("compile-episode-01")
    compile_parser.add_argument("--output-dir", type=Path, required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    episode = build_eighth_fire_episode_01_r3()
    if args.command == "validate-episode-01":
        errors = episode.validate()
        print(json.dumps({"valid": not errors, "errors": errors, "duration_s": episode.duration_s, "scenes": len(episode.scenes), "shots": len(episode.shots)}, ensure_ascii=False, indent=2))
        return 0 if not errors else 1
    manifest = compile_episode_bundle(episode, args.output_dir)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
