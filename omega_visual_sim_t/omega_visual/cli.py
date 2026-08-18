from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import SpecError, compile_visual, verify_manifest
from .world import compile_sim_capsule, validate_executable_world, visual_spec_to_world


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-visual")
    commands = parser.add_subparsers(dest="command", required=True)

    render = commands.add_parser("render", help="compile a VisualSpec")
    render.add_argument("spec", type=Path)
    render.add_argument("--output", type=Path, required=True)

    verify = commands.add_parser("verify", help="verify artifact hashes")
    verify.add_argument("manifest", type=Path)

    capsule = commands.add_parser("capsule", help="compile a web-attachable SimCapsule")
    capsule.add_argument("spec", type=Path)
    capsule.add_argument("--input-kind", choices=("visual-spec", "world"), default="visual-spec")
    capsule.add_argument("--seed", type=int, default=0)
    capsule.add_argument("--output", type=Path, required=True)
    return parser


def _compile_capsule(args: argparse.Namespace) -> dict:
    payload = json.loads(args.spec.read_text(encoding="utf-8"))
    world = visual_spec_to_world(payload) if args.input_kind == "visual-spec" else validate_executable_world(payload)
    capsule = compile_sim_capsule(world, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(capsule, indent=2, ensure_ascii=False), encoding="utf-8")
    return capsule


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "render":
            manifest = compile_visual(args.spec, args.output)
            print(json.dumps(manifest, indent=2))
            return 0
        if args.command == "capsule":
            capsule = _compile_capsule(args)
            print(json.dumps(capsule, indent=2, ensure_ascii=False))
            return 0
        errors = verify_manifest(args.manifest)
        print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}, indent=2))
        return 0 if not errors else 1
    except (OSError, ValueError, KeyError, SpecError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
