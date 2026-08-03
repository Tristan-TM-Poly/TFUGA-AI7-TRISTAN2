from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from .analyzer import LearningAnalyzer
from .benchmark import run_r03_benchmark
from .planner import LearningPlanner


def _read_receipts(paths: Sequence[str]) -> tuple[dict[str, Any], ...]:
    receipts: list[dict[str, Any]] = []
    for value in paths:
        payload = json.loads(Path(value).read_text(encoding="utf-8"))
        if isinstance(payload, dict) and "receipt" in payload:
            payload = payload["receipt"]
        if isinstance(payload, list):
            receipts.extend(payload)
        elif isinstance(payload, dict):
            receipts.append(payload)
        else:
            raise ValueError(f"{value}: expected JSON object or list")
    return tuple(receipts)


def _write(payload: object, output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-code-dojo-r03",
        description="R0.3 learning-intelligence analysis for campaign receipts.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    benchmark = sub.add_parser("benchmark")
    benchmark.add_argument("--output")

    analyze = sub.add_parser("analyze")
    analyze.add_argument("receipts", nargs="+")
    analyze.add_argument("--plateau-window", type=int, default=8)
    analyze.add_argument("--insight-limit", type=int, default=24)
    analyze.add_argument("--output")

    plan = sub.add_parser("plan")
    plan.add_argument("receipts", nargs="+")
    plan.add_argument("--plateau-window", type=int, default=8)
    plan.add_argument("--limit", type=int, default=12)
    plan.add_argument("--output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "benchmark":
        payload = run_r03_benchmark()
        _write(payload, args.output)
        return (
            0
            if payload["status"]
            == "CERTIFIED_LEARNING_INTELLIGENCE_FIXTURES_R0_3"
            else 1
        )

    receipts = _read_receipts(args.receipts)
    report = LearningAnalyzer().analyze(
        receipts,
        plateau_window=args.plateau_window,
        insight_limit=getattr(args, "insight_limit", 24),
    )
    if args.command == "analyze":
        _write(report.to_dict(), args.output)
        return 0

    actions = LearningPlanner().plan(report, limit=args.limit)
    _write(
        {
            "report_id": report.report_id,
            "report_sha256": report.report_sha256,
            "actions": [item.to_dict() for item in actions],
        },
        args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
