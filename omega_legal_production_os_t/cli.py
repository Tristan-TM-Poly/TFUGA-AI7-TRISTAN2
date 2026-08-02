"""No-network CLI for Ω-LEGAL-PRODUCTION-OS-T∞ R0.1/R0.2."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .ledger import ActionLedger
from .models import ApprovalRecord, AuthorityGrant, ExternalActionEnvelope, iso_utc
from .policy import LegalProductionPolicyGate
from .release import DryRunReleaseProvider, ReleaseCandidate


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(payload: Mapping[str, Any], output: Path | None = None) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-legal-production",
        description="Prepare and audit immutable external actions without external execution.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init_action = sub.add_parser("init-action")
    init_action.add_argument("--out", type=Path, required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("action", type=Path)

    hash_action = sub.add_parser("hash-action")
    hash_action.add_argument("action", type=Path)

    approve = sub.add_parser("approve")
    approve.add_argument("action", type=Path)
    approve.add_argument("--approver", required=True)
    approve.add_argument("--role", required=True)
    approve.add_argument("--note", default="")
    approve.add_argument("--out", type=Path, required=True)

    gate = sub.add_parser("gate")
    gate.add_argument("action", type=Path)
    gate.add_argument("--grants", type=Path)
    gate.add_argument("--execute", action="store_true")
    gate.add_argument("--report", type=Path)

    audit_ledger = sub.add_parser("audit-ledger")
    audit_ledger.add_argument("ledger", type=Path)

    release = sub.add_parser("release-dry-run")
    release.add_argument("candidate", type=Path)
    release.add_argument("--workflow-ref", required=True)
    release.add_argument("--receipt", type=Path)
    return parser


def _grants(path: Path | None) -> tuple[AuthorityGrant, ...]:
    if path is None:
        return ()
    payload = _load(path)
    if not isinstance(payload, list):
        raise ValueError("grants file must contain a JSON array")
    return tuple(
        AuthorityGrant(
            grant_id=str(item["grant_id"]),
            person_id=str(item["person_id"]),
            company_id=str(item["company_id"]),
            role=str(item["role"]),
            permissions=tuple(str(value) for value in item.get("permissions", ())),
            amount_limit_cad=(float(item["amount_limit_cad"]) if item.get("amount_limit_cad") is not None else None),
            jurisdictions=tuple(str(value) for value in item.get("jurisdictions", ())),
            valid_from=str(item["valid_from"]) if item.get("valid_from") else None,
            valid_until=str(item["valid_until"]) if item.get("valid_until") else None,
            revoked=bool(item.get("revoked", False)),
            evidence_hash=str(item["evidence_hash"]) if item.get("evidence_hash") else None,
        )
        for item in payload
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "init-action":
        _write(
            {
                "action_id": "ACT-2026-000001",
                "action_type": "RELEASE",
                "company_id": "tristan_parent_opco",
                "requested_by": "tristan",
                "requested_at": iso_utc(),
                "purpose": "Prepare one bounded external action",
                "payload": {},
                "required_approvals": 1,
                "professional_review_required": False,
                "risk_level": "MEDIUM",
                "state": "DRAFT",
                "approvals": [],
                "source_issue": None,
                "source_commit": None,
                "policy_id": "DEFAULT-DENY",
                "evidence_ids": [],
                "metadata": {},
            },
            args.out,
        )
        return 0

    if args.command == "audit-ledger":
        result = ActionLedger(args.ledger).audit()
        _write(result)
        return 0 if result["valid"] else 1

    if args.command == "release-dry-run":
        candidate = ReleaseCandidate.from_mapping(_load(args.candidate))
        receipt = DryRunReleaseProvider().prepare(candidate, workflow_ref=args.workflow_ref)
        _write(receipt.to_mapping(), args.receipt)
        return 0

    action = ExternalActionEnvelope.from_mapping(_load(args.action))

    if args.command == "validate":
        reasons = action.validate()
        _write({"valid": not reasons, "reasons": list(reasons), "action_hash": action.action_hash})
        return 0 if not reasons else 1

    if args.command == "hash-action":
        _write({"action_id": action.action_id, "action_hash": action.action_hash})
        return 0

    if args.command == "approve":
        approval = ApprovalRecord.create(
            action,
            approver=args.approver,
            role=args.role,
            note=args.note,
        )
        _write(asdict(approval), args.out)
        return 0

    if args.command == "gate":
        report = LegalProductionPolicyGate().evaluate(
            action,
            grants=_grants(args.grants),
            execute=args.execute,
        )
        _write(report.to_mapping(), args.report)
        return 0 if report.allowed else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
