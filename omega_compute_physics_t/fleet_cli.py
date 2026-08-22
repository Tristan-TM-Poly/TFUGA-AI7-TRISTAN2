"""CLI for Omega Compute Physics R0.5 fleet execution primitives."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark_contract import gate_contract, load_contract
from .fleet_stage_a import scan_checkout_fleet
from .machine_genome import calibrate_machine, fingerprint_machine


def _repo_assignment(text: str) -> tuple[str, str]:
    if "=" not in text:
        raise argparse.ArgumentTypeError("repository checkout must be NAME=/path")
    name, path = text.split("=", 1)
    if not name or not path:
        raise argparse.ArgumentTypeError("repository checkout must be NAME=/path")
    return name, path


def _write(payload: object, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-compute-fleet")
    sub = parser.add_subparsers(dest="command", required=True)

    stage = sub.add_parser("stage-a", help="static-only scan of pinned local checkouts")
    stage.add_argument("--repo", action="append", type=_repo_assignment, required=True)
    stage.add_argument("--similarity", type=float, default=0.92)
    stage.add_argument("--limit", type=int, default=100)
    stage.add_argument("--output")

    machine = sub.add_parser("machine", help="machine fingerprint / bounded micro-calibration")
    machine.add_argument("--calibrate", action="store_true")
    machine.add_argument("--repeats", type=int, default=3)
    machine.add_argument("--output")

    gate = sub.add_parser("gate-contract", help="validate a dynamic benchmark contract without execution")
    gate.add_argument("contract")
    gate.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "stage-a":
        checkouts = dict(args.repo)
        _, report = scan_checkout_fleet(
            checkouts,
            similarity_threshold=args.similarity,
            benchmark_limit=args.limit,
        )
        _write(report.to_dict(), args.output)
        return 0
    if args.command == "machine":
        genome = calibrate_machine(repeats=args.repeats) if args.calibrate else fingerprint_machine()
        _write(genome.to_dict(), args.output)
        return 0
    if args.command == "gate-contract":
        decision = gate_contract(load_contract(args.contract))
        _write(decision, args.output)
        return 0 if decision["decision"] == "allow" else 2
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
