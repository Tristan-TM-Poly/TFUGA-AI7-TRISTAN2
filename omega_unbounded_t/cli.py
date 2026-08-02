from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .core import (
    AdaptiveController,
    CapacityPolicy,
    ListWorkSource,
    MMinusLedger,
    SyntheticCapacityExecutor,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-unbounded",
        description="Ω-SANS-PLAFOND-T∞ adaptive frontier-discovery engine.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    simulate = sub.add_parser(
        "simulate",
        help="Run a finite synthetic workload while discovering and surpassing temporary capacity frontiers.",
    )
    simulate.add_argument("--work-items", type=int, default=50_000)
    simulate.add_argument("--initial-batch", type=int, default=256)
    simulate.add_argument("--initial-capacity", type=int, default=1_024)
    simulate.add_argument("--redesign-factor", type=float, default=2.0)
    simulate.add_argument("--quality-floor", type=float, default=0.95)
    simulate.add_argument("--output-dir", default="generated/omega_unbounded_t")
    simulate.add_argument(
        "--no-redesign",
        action="store_true",
        help="Pause at the first discovered frontier instead of adapting the synthetic executor.",
    )
    return parser


def _simulate(args: argparse.Namespace) -> int:
    if args.work_items < 0:
        raise ValueError("--work-items cannot be negative")

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source = ListWorkSource(range(args.work_items))
    executor = SyntheticCapacityExecutor(
        capacity=args.initial_capacity,
        redesign_factor=args.redesign_factor,
        allow_redesign=not args.no_redesign,
    )
    ledger = MMinusLedger(output / "m_minus.jsonl")
    controller = AdaptiveController(
        source,
        executor,
        initial_batch=args.initial_batch,
        policy=CapacityPolicy(quality_floor=args.quality_floor),
        ledger=ledger,
        checkpoint_path=output / "checkpoint.json",
    )
    report = controller.run()
    payload = {
        **report.to_dict(),
        "frontier_history": executor.frontier_history,
        "boundary": (
            "No permanent addition-count cap is used. This run is still bounded by its finite workload, "
            "recoverability, quality policy, available resources, and external service rules."
        ),
    }
    (output / "report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report.status == "completed" else 2


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "simulate":
            return _simulate(args)
    except (OSError, ValueError) as exc:
        print(f"omega-unbounded: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
