from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterator
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .engine import assess_sponsor_tier, evaluate_artifact, stream_frontier
from .ledger import AppendOnlyLedger, SensitiveDataError
from .models import (
    Artifact,
    DisclosureClass,
    Evidence,
    OAKStatus,
    RevenueEvent,
    RevenuePath,
    SponsorTier,
)


def _json_default(value: Any) -> Any:
    if hasattr(value, "value"):
        return value.value
    raise TypeError(f"cannot serialize {type(value).__name__}")


def _read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid JSON at {path}:{line_number}: {error}") from error
            if not isinstance(payload, dict):
                raise ValueError(f"record at {path}:{line_number} must be an object")
            yield payload


def _demo_artifact() -> Artifact:
    return Artifact(
        artifact_id="OAKGATE-REPO-AUDIT-001",
        title="OAKGate Repository Audit",
        problem="Repository owners need a bounded, reproducible quality and risk assessment.",
        actor="small R&D and open-source teams",
        oak_status=OAKStatus.DEMONSTRATED,
        disclosure=DisclosureClass.OPEN_PUBLIC,
        revenue_paths=(RevenuePath.FIXED_SCOPE_SERVICE, RevenuePath.GITHUB_APP),
        evidence=Evidence(
            tests=24,
            reproducible_demo=True,
            benchmark=True,
            limitations_documented=True,
        ),
        utility=0.86,
        reuse=0.82,
        discoverability=0.65,
        trust=0.78,
        conversion_clarity=0.84,
        noise=0.15,
        maintenance_burden=0.38,
        ip_legal_risk=0.12,
        safety_privacy_risk=0.20,
        risks=("false positives", "private repository data exposure"),
        next_action="run one consented external pilot audit",
    )


def command_demo(_: argparse.Namespace) -> int:
    artifact = _demo_artifact()
    tier = SponsorTier(
        name="Research Follower",
        monthly_minor=1500,
        currency="USD",
        monthly_delivery_minutes=5,
        benefits=("public progress note", "roadmap digest"),
    )
    output = {
        "artifact": artifact.to_dict(),
        "assessment": evaluate_artifact(artifact),
        "sponsor_tier": assess_sponsor_tier(tier),
        "non_claims": [
            "no guaranteed sponsorship",
            "no guaranteed revenue",
            "no banking data stored",
        ],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, default=_json_default))
    return 0


def command_audit(args: argparse.Namespace) -> int:
    source = Path(args.input)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    accepted = 0
    with destination.open("w", encoding="utf-8") as handle:
        for result in stream_frontier(
            _read_jsonl(source),
            minimum_score=args.minimum_score,
            review_approved=args.review_approved,
        ):
            handle.write(json.dumps(result, ensure_ascii=False, default=_json_default) + "\n")
            accepted += 1
    print(json.dumps({"accepted": accepted, "output": str(destination)}, indent=2))
    return 0


def command_ledger(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.event).read_text(encoding="utf-8"))
    event = RevenueEvent(**payload)
    event.validate()
    ledger = AppendOnlyLedger(args.ledger)
    record = ledger.append(event.to_dict())
    valid, count, reason = ledger.verify()
    print(
        json.dumps(
            {
                "record_hash": record["record_hash"],
                "ledger_valid": valid,
                "record_count": count,
                "reason": reason,
            },
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-github-revenue",
        description="OAK-safe GitHub asset, sponsorship, offer, and revenue-routing prototype.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="run the bounded OAKGate economic demo")
    demo.set_defaults(func=command_demo)

    audit = subparsers.add_parser("audit", help="stream-evaluate artifact JSONL")
    audit.add_argument("input")
    audit.add_argument("--output", required=True)
    audit.add_argument("--minimum-score", type=float, default=0.0)
    audit.add_argument("--review-approved", action="store_true")
    audit.set_defaults(func=command_audit)

    ledger = subparsers.add_parser("ledger", help="append a privacy-minimized revenue event")
    ledger.add_argument("event", help="path to a RevenueEvent JSON object")
    ledger.add_argument("--ledger", required=True, help="append-only JSONL destination")
    ledger.set_defaults(func=command_ledger)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (ValueError, SensitiveDataError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
