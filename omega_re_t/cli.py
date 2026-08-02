"""Command-line interface for the Ω-RE-T∞ finite-state-machine laboratory."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from json import dumps
from pathlib import Path
from typing import Sequence

from .benchmark import run_benchmark
from .campaign import reconstruct_fsm
from .fsm import canonical_demo_machine, enumerate_mealy_machines
from .models import AuthorizationMode, AuthorizationScope


def _population(state_count: int) -> tuple:
    return tuple(
        enumerate_mealy_machines(
            state_count=state_count,
            input_alphabet=("A", "B"),
            output_alphabet=("0", "1"),
            max_candidates=100_000,
        )
    )


def demo(args: argparse.Namespace) -> int:
    population = _population(args.states)
    oracle = canonical_demo_machine()
    authorization = AuthorizationScope(
        mode=AuthorizationMode.RESEARCH_SANDBOX,
        purpose="Reconstruct a synthetic machine generated inside the test sandbox",
        permitted_actions=("query_oracle", "store_observation", "generate_spec"),
        prohibited_actions=("extract_secret", "bypass_access_control"),
        reference="synthetic-demo",
    )
    result = reconstruct_fsm(
        oracle=oracle,
        candidates=population,
        authorization=authorization,
        max_rounds=args.max_rounds,
        max_experiment_length=args.max_length,
        validation_max_length=args.validation_length,
    )
    payload = asdict(result)
    if result.oak_report is not None:
        payload["oak_report"]["promoted_status"] = result.oak_report.promoted_status.value
    text = dumps(payload, indent=2, sort_keys=True, default=str)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if result.exact_behavior_recovered else 2


def benchmark(args: argparse.Namespace) -> int:
    population = _population(args.states)
    summary = run_benchmark(
        population,
        seeds=tuple(range(args.cases)),
        max_rounds=args.max_rounds,
        max_length=args.max_length,
    )
    text = dumps(summary.as_dict(), indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-re",
        description="OAK-safe active reverse-engineering laboratory for synthetic systems",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo_parser = subparsers.add_parser("demo", help="run the canonical active reconstruction demo")
    demo_parser.add_argument("--states", type=int, default=2)
    demo_parser.add_argument("--max-rounds", type=int, default=12)
    demo_parser.add_argument("--max-length", type=int, default=5)
    demo_parser.add_argument("--validation-length", type=int, default=8)
    demo_parser.add_argument("--output")
    demo_parser.set_defaults(func=demo)
    benchmark_parser = subparsers.add_parser("benchmark", help="compare active and passive queries")
    benchmark_parser.add_argument("--states", type=int, default=2)
    benchmark_parser.add_argument("--cases", type=int, default=16)
    benchmark_parser.add_argument("--max-rounds", type=int, default=12)
    benchmark_parser.add_argument("--max-length", type=int, default=5)
    benchmark_parser.add_argument("--output")
    benchmark_parser.set_defaults(func=benchmark)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
