"""Analysis-only command line interface for Ω-EMR-SOURCE-T∞.

The commands classify frequencies, inspect metadata and write simulation and
validation plans. They do not control equipment or emit fabrication steps.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .atlas import mechanism_atlas, search_mechanisms
from .classifier import classify_frequency
from .compiler import compile_source
from .models import SpectrumTarget
from .oak import audit_plan
from .reporting import write_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-emr-source")
    commands = parser.add_subparsers(dest="command", required=True)

    classify = commands.add_parser("classify")
    classify.add_argument("frequency_hz", type=float)

    atlas = commands.add_parser("atlas")
    atlas.add_argument("query", nargs="?", default="")

    plan = commands.add_parser("plan")
    plan.add_argument("target_json", type=Path)
    plan.add_argument(
        "--output-dir",
        type=Path,
        default=Path("generated/omega_emr_source_t"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "classify":
        payload = classify_frequency(args.frequency_hz).to_dict()
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
        return 0

    if args.command == "atlas":
        payload = (
            mechanism_atlas()
            if not args.query
            else tuple(item.to_dict() for item in search_mechanisms(args.query))
        )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
        return 0

    target = SpectrumTarget.from_dict(
        json.loads(args.target_json.read_text(encoding="utf-8"))
    )
    source_plan = compile_source(target)
    oak_report = audit_plan(source_plan)
    paths = write_bundle(source_plan, oak_report, args.output_dir)
    summary = {
        "oak_status": oak_report.status,
        "safety_status": source_plan.safety_status,
        "recommended": [item.mechanism_id for item in source_plan.recommended[:5]],
        "conditional": [item.mechanism_id for item in source_plan.conditional[:5]],
        "paths": paths,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 2 if oak_report.status == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
