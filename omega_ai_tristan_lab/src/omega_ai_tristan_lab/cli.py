"""Command-line interface for Ω-AI-TRISTAN-LAB."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from .agent_harness import AgentHarness


def _json_default(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Ω-AI-TRISTAN-LAB on one idea.")
    parser.add_argument("--idea", required=True, help="Raw idea to formalize and evaluate.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    report = AgentHarness().run(args.idea)
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
