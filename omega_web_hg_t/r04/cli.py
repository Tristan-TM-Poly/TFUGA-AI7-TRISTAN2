from __future__ import annotations

import argparse
import json
from typing import Sequence

from .catalog import BEST_SITES_V1
from .models import audit_profiles
from .planner import PlannerOptions, build_plan, materialize_plan


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="omega-web-hg-r04", description="Planificateur OAK-safe des meilleures sources Web autoritatives.")
    sub = root.add_subparsers(dest="command", required=True)

    catalog = sub.add_parser("catalog", help="Afficher le catalogue de sources.")
    catalog.add_argument("--tier", type=int, action="append")

    plan = sub.add_parser("plan", help="Construire un plan déterministe sans accès réseau.")
    plan.add_argument("--output-dir", default="generated/omega_web_hg_best_sites_v1")
    plan.add_argument("--tier", type=int, action="append", default=[0, 1])
    plan.add_argument("--include-review-required", action="store_true")
    plan.add_argument("--include-key-required", action="store_true")
    plan.add_argument("--allow-open-full-text", action="store_true")

    sub.add_parser("audit", help="Auditer le catalogue, les budgets et les gates.")
    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "catalog":
        profiles = [item for item in BEST_SITES_V1 if not args.tier or item.tier in args.tier]
        print(json.dumps([item.to_dict() for item in profiles], ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "audit":
        report = audit_profiles(BEST_SITES_V1)
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if report["status"] == "PASS" else 2
    if args.command == "plan":
        options = PlannerOptions(
            include_tiers=tuple(sorted(set(args.tier))),
            include_review_required=args.include_review_required,
            include_key_required=args.include_key_required,
            metadata_only=not args.allow_open_full_text,
            execute_network=False,
        )
        plan = build_plan(options=options)
        output = materialize_plan(plan, args.output_dir)
        print(json.dumps({"output_dir": str(output), **plan.to_dict()}, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
