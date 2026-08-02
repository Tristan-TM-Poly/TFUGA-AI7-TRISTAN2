"""CLI for Ω-COMPANY-AUTOPILOT-T."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date
import json
from pathlib import Path
from typing import Sequence

from .approvals import approve_action
from .governance import GovernanceEngine
from .models import ActionKind, ActionRequest, AutonomyLevel, CompanyRecord, CompanyState, DivisionRecord, RiskLevel
from .policy import OAKCorporateGate
from .serialization import load_company, save_company
from .spinout import SpinoutEngine
from .treasury import TreasuryEngine


def _json(value) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-company-autopilot")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("path", type=Path)
    init.add_argument("--company-id", default="tristan_parent_opco")
    init.add_argument("--name", default="Tristan Parent OpCo")
    status = sub.add_parser("status")
    status.add_argument("company", type=Path)
    add_div = sub.add_parser("add-division")
    add_div.add_argument("company", type=Path)
    add_div.add_argument("division_id")
    add_div.add_argument("display_name")
    add_div.add_argument("--mission", default="")
    gate = sub.add_parser("gate")
    gate.add_argument("company", type=Path)
    gate.add_argument("action", type=Path)
    board = sub.add_parser("board-pack")
    board.add_argument("company", type=Path)
    board.add_argument("--out", type=Path)
    allocate = sub.add_parser("allocate-receipt")
    allocate.add_argument("gross", type=float)
    payment = sub.add_parser("propose-payment")
    payment.add_argument("company", type=Path)
    payment.add_argument("--action-id", required=True)
    payment.add_argument("--division")
    payment.add_argument("--amount", type=float, required=True)
    payment.add_argument("--counterparty", required=True)
    payment.add_argument("--category", required=True)
    payment.add_argument("--invoice-id")
    payment.add_argument("--known-vendor", action="store_true")
    payment.add_argument("--out", type=Path, required=True)
    spinout = sub.add_parser("spinout-assess")
    spinout.add_argument("company", type=Path)
    spinout.add_argument("division_id")
    approve = sub.add_parser("approve")
    approve.add_argument("action", type=Path)
    approve.add_argument("--approval-id", required=True)
    approve.add_argument("--approver", required=True)
    approve.add_argument("--reason", required=True)
    approve.add_argument("--out", type=Path, required=True)
    return parser


def _load_action(path: Path) -> ActionRequest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["kind"] = ActionKind(payload["kind"])
    payload["risk_level"] = RiskLevel(payload.get("risk_level", "MODERATE"))
    return ActionRequest(**payload)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "init":
        company = CompanyRecord(
            company_id=args.company_id,
            conceptual_name=args.name,
            state=CompanyState.CANDIDATE_LEGAL_ENTITY,
            autonomy_level=AutonomyLevel.L2_PREPARE,
            divisions=[
                DivisionRecord("tristan_oak_systems", "Tristan OAK Systems", "Validation and technical audit"),
                DivisionRecord("tristan_software_labs", "Tristan Software Labs", "Software and automation"),
                DivisionRecord("tristan_research_foundry", "Tristan Research Foundry", "Research and prototyping"),
            ],
        )
        for division in company.divisions: division.owner_company_id = company.company_id
        save_company(company, args.path)
        print(_json(company.to_dict()))
        return 0
    if args.command == "status":
        print(_json(load_company(args.company).to_dict()))
        return 0
    if args.command == "add-division":
        company = load_company(args.company)
        if any(item.division_id == args.division_id for item in company.divisions): raise SystemExit("duplicate division")
        company.divisions.append(DivisionRecord(args.division_id, args.display_name, args.mission, owner_company_id=company.company_id))
        save_company(company, args.company)
        print(_json(company.to_dict()))
        return 0
    if args.command == "gate":
        company = load_company(args.company)
        result = OAKCorporateGate().evaluate(company, _load_action(args.action))
        print(_json(asdict(result)))
        return 0 if result.decision.value != "BLOCK" else 2
    if args.command == "board-pack":
        pack = GovernanceEngine().build_board_pack(load_company(args.company), as_of=date.today())
        payload = _json(asdict(pack))
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(payload + "\n", encoding="utf-8")
        print(payload)
        return 0
    if args.command == "allocate-receipt":
        print(_json(asdict(TreasuryEngine().allocate_receipt(args.gross))))
        return 0
    if args.command == "propose-payment":
        company = load_company(args.company)
        action = TreasuryEngine().propose_payment(
            action_id=args.action_id, company_id=company.company_id, division_id=args.division,
            amount_cad=args.amount, counterparty=args.counterparty, category=args.category,
            invoice_id=args.invoice_id, known_vendor=args.known_vendor,
        )
        payload = asdict(action)
        payload["kind"] = action.kind.value
        payload["risk_level"] = action.risk_level.value
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(_json(payload) + "\n", encoding="utf-8")
        print(_json(payload))
        return 0
    if args.command == "spinout-assess":
        company = load_company(args.company)
        print(_json(asdict(SpinoutEngine().assess(company.division(args.division_id)))))
        return 0
    if args.command == "approve":
        approval = approve_action(_load_action(args.action), approval_id=args.approval_id, approver=args.approver, reason=args.reason)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(_json(asdict(approval)) + "\n", encoding="utf-8")
        print(_json(asdict(approval)))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
