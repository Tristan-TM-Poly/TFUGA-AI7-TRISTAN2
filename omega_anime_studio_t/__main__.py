"""CLI for Ω-ANIME-STUDIO-T∞ R1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .compiler import compile_project_bundle
from .eighth_fire import build_eighth_fire_r1
from .frontier import FrontierBudget, compile_frontier_sample
from .matrix import matrix_summary, validate_matrix, write_matrix_jsonl


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog='omega-anime-studio')
    commands = root.add_subparsers(dest='command', required=True)
    commands.add_parser('matrix-summary')
    matrix = commands.add_parser('write-matrix')
    matrix.add_argument('--output', type=Path, required=True)
    validate = commands.add_parser('validate-demo')
    compile_cmd = commands.add_parser('compile-demo')
    compile_cmd.add_argument('--output-dir', type=Path, required=True)
    compile_cmd.add_argument('--frontier-work-items', type=int, default=2048)
    frontier = commands.add_parser('frontier')
    frontier.add_argument('--output', type=Path, required=True)
    frontier.add_argument('--work-items', type=int, default=10000)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == 'matrix-summary':
        print(json.dumps(matrix_summary(), sort_keys=True, indent=2))
        return 0
    if args.command == 'write-matrix':
        print(json.dumps(write_matrix_jsonl(args.output), sort_keys=True, indent=2))
        return 0
    if args.command == 'validate-demo':
        project = build_eighth_fire_r1()
        errors = [*validate_matrix(), *project.validate()]
        print(json.dumps({'errors': errors, 'valid': not errors}, ensure_ascii=False, indent=2))
        return 0 if not errors else 2
    if args.command == 'compile-demo':
        manifest = compile_project_bundle(
            build_eighth_fire_r1(), args.output_dir,
            frontier_work_items=args.frontier_work_items,
        )
        print(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    if args.command == 'frontier':
        report = compile_frontier_sample(
            args.output,
            ('S01-NOISE','S02-NETWORK','S03-CORRECTION','S04-DISPLACEMENT','S05-EIGHTH-FIRE'),
            args.work_items,
            FrontierBudget(
                memory_bytes=64 * 1024 * 1024,
                wall_time_s=120.0,
                output_bytes=256 * 1024 * 1024,
            ),
        )
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    raise AssertionError(args.command)


if __name__ == '__main__':
    raise SystemExit(main())
