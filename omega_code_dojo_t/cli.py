from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .benchmark import run_oak_benchmark
from .catalog import original_catalog


def _write(payload: object, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-code-dojo",
        description="OAK-safe local algorithmic training and mutation benchmark.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    catalog = subparsers.add_parser(
        "catalog", help="Print the original local curriculum."
    )
    catalog.add_argument("--output")

    benchmark = subparsers.add_parser(
        "benchmark", help="Run references and deliberate mutants."
    )
    benchmark.add_argument("--output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "catalog":
        payload = {
            "system": "omega-code-dojo-t",
            "tasks": [
                {
                    "task_id": task.task_id,
                    "title": task.title,
                    "function_name": task.function_name,
                    "difficulty": task.difficulty,
                    "tags": list(task.tags),
                    "case_count": len(task.cases),
                    "origin": task.origin,
                }
                for task in original_catalog()
            ],
        }
        _write(payload, args.output)
        return 0

    payload = run_oak_benchmark()
    _write(payload, args.output)
    return 0 if payload["status"] == "CERTIFIED_SOFTWARE_FIXTURES_R0_1" else 1


if __name__ == "__main__":
    raise SystemExit(main())
