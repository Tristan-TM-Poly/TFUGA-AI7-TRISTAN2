"""CLI for deterministic inbox-to-outcome dry runs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .engine import InboxOutcomeEngine
from .intake import IntakeRegistry
from .models import AutonomousDeliveryContract, Channel, DataClass, Intent, ResolvedIdentity


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _identity(payload: dict) -> ResolvedIdentity:
    return ResolvedIdentity(
        person_id=payload.get("person_id"),
        organization_id=payload.get("organization_id"),
        verified_addresses=list(payload.get("verified_addresses", [])),
        relationship=str(payload.get("relationship", "unknown")),
        contract_id=payload.get("contract_id"),
        allowed_project_ids=list(payload.get("allowed_project_ids", [])),
        allowed_data_classes=[DataClass(item) for item in payload.get("allowed_data_classes", ["public"])],
        identity_confidence=float(payload.get("identity_confidence", 0.0)),
        organization_confidence=float(payload.get("organization_confidence", 0.0)),
        authority_confidence=float(payload.get("authority_confidence", 0.0)),
        may_receive_financial_documents=bool(payload.get("may_receive_financial_documents", False)),
        may_receive_source_code=bool(payload.get("may_receive_source_code", False)),
    )


def _contract(payload: dict) -> AutonomousDeliveryContract:
    return AutonomousDeliveryContract(
        contract_id=str(payload["contract_id"]),
        company_id=str(payload["company_id"]),
        division_id=str(payload["division_id"]),
        allowed_intents=[Intent(item) for item in payload["allowed_intents"]],
        allowed_response_types=list(payload.get("allowed_response_types", [])),
        allowed_deliverables=list(payload.get("allowed_deliverables", [])),
        allowed_channels=[Channel(item) for item in payload.get("allowed_channels", ["email"])],
        forbidden_actions=list(payload.get("forbidden_actions", [])),
        maximum_replies_per_case=int(payload.get("maximum_replies_per_case", 4)),
        maximum_external_deliveries_per_day=int(payload.get("maximum_external_deliveries_per_day", 20)),
        maximum_attachment_size_mb=float(payload.get("maximum_attachment_size_mb", 10.0)),
        minimum_identity_confidence=float(payload.get("minimum_identity_confidence", 0.9)),
        minimum_authority_confidence=float(payload.get("minimum_authority_confidence", 0.75)),
        maximum_data_class=DataClass(payload.get("maximum_data_class", "client_confidential")),
        expires_at=payload.get("expires_at"),
        kill_switch=bool(payload.get("kill_switch", False)),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-inbox-outcome")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("dry-run")
    run.add_argument("event", type=Path)
    run.add_argument("identity", type=Path)
    run.add_argument("contract", type=Path)
    run.add_argument("--workspace", type=Path, default=Path("private/inbox_outcome"))
    run.add_argument("--report", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    event_payload = _load(args.event)
    event = IntakeRegistry().ingest_email(event_payload, owned_addresses=set(event_payload.get("owned_addresses", [])))
    identity = _identity(_load(args.identity))
    contract = _contract(_load(args.contract))
    result = InboxOutcomeEngine(args.workspace).process(
        event,
        identity=identity,
        contract=contract,
        company_id=contract.company_id,
        division_id=contract.division_id,
    )
    payload = json.dumps(result.to_dict(), indent=2, ensure_ascii=False, sort_keys=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
