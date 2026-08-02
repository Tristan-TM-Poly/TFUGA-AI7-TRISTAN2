"""CLI for Ω-MAIL-T corporate officialization and one-message delivery."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .hardening import OneMessageLedger
from .officialization import (
    ApprovalRecord,
    CompanyIdentity,
    ComplianceContext,
    MailAuthority,
    OfficialMessageDraft,
    OfficializationGate,
)
from .production import deliver_one


def _load(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _write(path: Path | None, payload: Mapping[str, Any]) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-mail-official",
        description="Prepare, audit, approve, and optionally send exactly one official email.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init_company = sub.add_parser("init-company", help="Write a pre-officialization company template")
    init_company.add_argument("--out", type=Path, required=True)

    hash_message = sub.add_parser("hash-message", help="Compute the canonical SHA-256 of a message")
    hash_message.add_argument("message", type=Path)

    approve = sub.add_parser("approve", help="Create a one-message approval record")
    approve.add_argument("message", type=Path)
    approve.add_argument("--approver", required=True)
    approve.add_argument("--note", default="")
    approve.add_argument("--out", type=Path, required=True)

    readiness = sub.add_parser("readiness", help="Evaluate official-send readiness")
    _add_gate_inputs(readiness)
    readiness.add_argument("--production", action="store_true")
    readiness.add_argument("--report", type=Path)

    send_one = sub.add_parser("send-one", help="Dry-run by default; --execute opens SMTP")
    _add_gate_inputs(send_one)
    send_one.add_argument("--execute", action="store_true")
    send_one.add_argument(
        "--ledger",
        type=Path,
        help="Append-only execution ledger; mandatory for --execute unless set by environment",
    )
    send_one.add_argument("--receipt", type=Path)

    audit_ledger = sub.add_parser("audit-ledger", help="Validate a hash-chained execution ledger")
    audit_ledger.add_argument("ledger", type=Path)
    audit_ledger.add_argument("--report", type=Path)
    return parser


def _add_gate_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--company", type=Path, required=True)
    parser.add_argument("--message", type=Path, required=True)
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--compliance", type=Path, required=True)
    parser.add_argument("--approval", type=Path)


def _objects(args: argparse.Namespace):
    company = CompanyIdentity.from_mapping(_load(args.company))
    draft = OfficialMessageDraft.from_mapping(_load(args.message))
    authority = MailAuthority.from_mapping(_load(args.authority))
    compliance = ComplianceContext.from_mapping(_load(args.compliance))
    approval = ApprovalRecord.from_mapping(_load(args.approval)) if args.approval else None
    return company, draft, authority, compliance, approval


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "init-company":
        template = {
            "company_id": "tristan_parent_opco",
            "conceptual_name": "Tristan Company Foundry",
            "state": "IDEA",
            "legal_name": None,
            "operating_name": None,
            "jurisdiction": "QC",
            "neq": None,
            "corporation_number": None,
            "domain": None,
            "legal_identity_verified": False,
            "domain_control_verified": False,
            "spf_verified": False,
            "dkim_verified": False,
            "dmarc_verified": False,
            "external_send_enabled": False,
            "evidence_ids": [],
        }
        _write(args.out, template)
        return 0

    if args.command == "hash-message":
        draft = OfficialMessageDraft.from_mapping(_load(args.message))
        _write(None, {"message_hash": draft.content_hash})
        return 0

    if args.command == "approve":
        draft = OfficialMessageDraft.from_mapping(_load(args.message))
        record = ApprovalRecord.create(
            draft,
            approver=args.approver,
            note=args.note,
        )
        _write(args.out, record.to_mapping())
        return 0

    if args.command == "audit-ledger":
        _write(args.report, OneMessageLedger(args.ledger).audit())
        return 0

    company, draft, authority, compliance, approval = _objects(args)
    gate = OfficializationGate()

    if args.command == "readiness":
        report = gate.evaluate(
            company=company,
            draft=draft,
            authority=authority,
            compliance=compliance,
            approval=approval,
            production=args.production,
        )
        _write(args.report, report.to_mapping())
        return 0 if report.allowed else 1

    if args.command == "send-one":
        report = gate.evaluate(
            company=company,
            draft=draft,
            authority=authority,
            compliance=compliance,
            approval=approval,
            production=args.execute,
        )
        ledger = OneMessageLedger(args.ledger) if args.ledger else None
        receipt = deliver_one(
            report=report,
            draft=draft,
            execute=args.execute,
            approval=approval,
            ledger=ledger,
        )
        payload = {"gate": report.to_mapping(), "receipt": receipt.to_mapping()}
        _write(args.receipt, payload)
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
