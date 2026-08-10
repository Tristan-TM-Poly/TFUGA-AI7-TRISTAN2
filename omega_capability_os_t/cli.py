from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import Intent, load_registry, make_evidence_receipt, plan, suggest_fallback, validate_registry


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-capability-os")
    sub = parser.add_subparsers(dest="command", required=True)

    describe = sub.add_parser("describe")
    describe.add_argument("registry")

    planner = sub.add_parser("plan")
    planner.add_argument("registry")
    planner.add_argument("intent")
    planner.add_argument("--health")

    oak = sub.add_parser("oak")
    oak.add_argument("registry")
    oak.add_argument("intent")
    oak.add_argument("--health")
    oak.add_argument("--candidate-sha", required=True)
    oak.add_argument("--evidence-sha", required=True)

    fallback = sub.add_parser("fallback")
    fallback.add_argument("registry")
    fallback.add_argument("capability_id")
    fallback.add_argument("--health")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    registry = load_registry(_load(args.registry))

    if args.command == "describe":
        print(json.dumps(validate_registry(registry), indent=2, sort_keys=True))
        return 0

    health = _load(args.health) if getattr(args, "health", None) else {}
    if args.command == "fallback":
        print(json.dumps(suggest_fallback(registry, args.capability_id, health), indent=2, sort_keys=True))
        return 0

    intent = Intent.from_dict(_load(args.intent))
    plan_payload = plan(registry, intent, health)
    if args.command == "plan":
        print(json.dumps(plan_payload, indent=2, sort_keys=True))
        return 0 if plan_payload["status"] == "READY" else 2

    receipt = make_evidence_receipt(
        plan_payload,
        candidate_sha=args.candidate_sha,
        evidence_sha=args.evidence_sha,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["oak"]["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
