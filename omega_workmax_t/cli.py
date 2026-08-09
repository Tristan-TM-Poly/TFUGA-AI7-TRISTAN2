from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .actions_bridge import collect_trigger_hotspots
from .engine import build_report


def _load(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("input must be a JSON object")
    return payload


def _write_or_print(payload: dict[str, Any], output: str | None) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-workmax")
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="compile a WorkPacket campaign into an OAK review report")
    plan.add_argument("input")
    plan.add_argument("--output")

    hotspots = sub.add_parser("actions-hotspots", help="reuse Ω-ACTIONS trigger-hotspot analysis")
    hotspots.add_argument("--root", default=".")
    hotspots.add_argument("--output")

    args = parser.parse_args(argv)
    if args.command == "plan":
        _write_or_print(build_report(_load(args.input)), args.output)
        return 0
    if args.command == "actions-hotspots":
        _write_or_print(collect_trigger_hotspots(args.root), args.output)
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
