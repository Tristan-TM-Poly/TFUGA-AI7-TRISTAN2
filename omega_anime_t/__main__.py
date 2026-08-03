"""CLI for Ω-ANIME-T∞ R0.1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import NarrativeLinter, build_eighth_fire_project, compile_project_bundle


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m omega_anime_t",
        description="Compile and audit an OAK-safe anime preproduction bundle.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_demo = subparsers.add_parser(
        "compile-demo", help="Compile the canonical Le Huitième Feu pilot bundle."
    )
    compile_demo.add_argument(
        "--output-dir",
        type=Path,
        default=Path("generated/omega_anime_t/eighth_fire_r0_1"),
    )

    subparsers.add_parser("lint-demo", help="Print deterministic narrative findings as JSON.")
    subparsers.add_parser("show-demo", help="Print the canonical project payload as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    project = build_eighth_fire_project()

    if args.command == "compile-demo":
        manifest = compile_project_bundle(project, args.output_dir)
        print(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2))
        return 0

    if args.command == "lint-demo":
        linter = NarrativeLinter()
        findings = linter.lint(project)
        payload = {
            "decision": linter.decision(findings),
            "findings": [finding.to_dict() for finding in findings],
        }
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
        return 0 if payload["decision"] == "PROCEED" else 2

    if args.command == "show-demo":
        print(json.dumps(project.to_dict(), ensure_ascii=False, sort_keys=True, indent=2))
        return 0

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
