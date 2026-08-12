"""CLI for Ω-META-COMPUTE-PHYSICS-T∞ R0.4."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .atlas import ResourceSample
from .representation import search_representations
from .repo_scanner import benchmark_priority, scan_repository
from .theory_foundry import generate_theory_competition


def _load_samples(path: str | Path) -> list[ResourceSample]:
    rows: list[ResourceSample] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        try:
            rows.append(
                ResourceSample(
                    variables=payload["variables"],
                    resources=payload["resources"],
                    metadata=payload.get("metadata", {}),
                )
            )
        except KeyError as exc:
            raise ValueError(f"line {line_number} missing key: {exc}") from exc
    return rows


def _write(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def _cmd_scan(args: argparse.Namespace) -> None:
    genome = scan_repository(args.root)
    priority = benchmark_priority(genome, limit=args.limit)
    payload = genome.to_dict()
    payload["benchmark_priority"] = [
        {
            "module": row.module,
            "function": row.qualified_name,
            "structural_scaling_candidate": row.structural_scaling_candidate,
            "max_loop_depth": row.max_loop_depth,
            "loc": row.loc,
        }
        for row in priority
    ]
    _write(payload, args.output)


def _cmd_represent(args: argparse.Namespace) -> None:
    rows = search_representations(
        _load_samples(args.samples),
        args.target,
        max_candidates=args.max_candidates,
        seed=args.seed,
    )
    _write(
        {
            "schema": "omega-meta-compute/representation-search/v0.4",
            "target": args.target,
            "candidates": [row.to_dict() for row in rows[: args.limit]],
        },
        args.output,
    )


def _cmd_theories(args: argparse.Namespace) -> None:
    theories = generate_theory_competition(
        _load_samples(args.samples),
        args.target,
        max_representations=args.max_candidates,
        seed=args.seed,
    )
    _write(
        {
            "schema": "omega-meta-compute/theory-ecology/v0.4",
            "target": args.target,
            "theories": [row.to_dict() for row in theories[: args.limit]],
        },
        args.output,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-compute-meta",
        description="Meta-compute discovery, representation search and repository genome scanner.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="scan a local Python repository without executing it")
    scan.add_argument("root")
    scan.add_argument("--limit", type=int, default=50)
    scan.add_argument("--output")
    scan.set_defaults(func=_cmd_scan)

    represent = sub.add_parser("represent", help="search compact derived coordinates from JSONL samples")
    represent.add_argument("samples")
    represent.add_argument("target")
    represent.add_argument("--max-candidates", type=int, default=64)
    represent.add_argument("--limit", type=int, default=20)
    represent.add_argument("--seed", type=int, default=0)
    represent.add_argument("--output")
    represent.set_defaults(func=_cmd_represent)

    theories = sub.add_parser("theories", help="generate and rank an empirical theory ecology")
    theories.add_argument("samples")
    theories.add_argument("target")
    theories.add_argument("--max-candidates", type=int, default=24)
    theories.add_argument("--limit", type=int, default=20)
    theories.add_argument("--seed", type=int, default=0)
    theories.add_argument("--output")
    theories.set_defaults(func=_cmd_theories)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
