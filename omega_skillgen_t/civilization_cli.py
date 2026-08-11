from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adversary import enrich_with_adversarial_evals
from .core import load_json, validate_spec
from .lineage import lineage_audit
from .planner import plan_expansion


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="omega-skillgen-civilization",
        description="Adversarial eval compiler, lineage DAG auditor, and skill-ecology expansion planner.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    adversary = sub.add_parser("adversary")
    adversary.add_argument("spec")
    adversary.add_argument("out")
    adversary.add_argument("--limit-per-axis", type=int)

    lineage = sub.add_parser("lineage")
    lineage.add_argument("specs", nargs="+")

    plan = sub.add_parser("plan")
    plan.add_argument("capabilities")
    plan.add_argument("specs", nargs="+")
    plan.add_argument("--nearest", type=int, default=3)

    args = parser.parse_args()

    if args.cmd == "adversary":
        output = enrich_with_adversarial_evals(load_json(args.spec), args.limit_per_axis)
        errors = validate_spec(output)
        Path(args.out).write_text(
            json.dumps(output, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        emit(
            {
                "status": "PASS" if not errors else "FAIL",
                "errors": errors,
                "out": args.out,
                "generated": output["adversarial_generation"]["generated_count"],
            }
        )
        return 0 if not errors else 2

    if args.cmd == "lineage":
        emit(lineage_audit([load_json(path) for path in args.specs]))
        return 0

    if args.cmd == "plan":
        capabilities = load_json(args.capabilities)
        if isinstance(capabilities, dict):
            capabilities = capabilities.get("capabilities", [])
        emit(
            plan_expansion(
                [load_json(path) for path in args.specs],
                capabilities,
                args.nearest,
            )
        )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
