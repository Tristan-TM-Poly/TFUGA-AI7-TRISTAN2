from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import load_json, validate_spec
from .evolution import preservation_contracts_from_mplus, repair_from_mminus


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="omega-skillgen-evolution",
        description="Compile M-minus failures into repair candidates and M-plus successes into preservation contracts.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    repair = sub.add_parser("repair")
    repair.add_argument("spec")
    repair.add_argument("mminus")
    repair.add_argument("out")

    preserve = sub.add_parser("preserve")
    preserve.add_argument("mplus")

    args = parser.parse_args()

    if args.cmd == "repair":
        payload = load_json(args.mminus)
        records = payload.get("M_MINUS", payload.get("results", []))
        candidate = repair_from_mminus(load_json(args.spec), records)
        errors = validate_spec(candidate)
        Path(args.out).write_text(
            json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "status": "PASS" if not errors else "FAIL",
                    "errors": errors,
                    "out": args.out,
                    "lineage": candidate["lineage"],
                    "regression_cases_added": len(records),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if not errors else 2

    if args.cmd == "preserve":
        payload = load_json(args.mplus)
        records = payload.get("M_PLUS", payload.get("results", []))
        print(
            json.dumps(
                {
                    "contracts": preservation_contracts_from_mplus(records),
                    "note": "M-plus preservation contracts retain supplied success evidence but do not create new behavioral proof.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
