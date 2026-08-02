from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .models import CompanyUnit, OutreachCase, OutreachKind, OutreachStatus
from .policy import audit_cases, disclosure_line, validate_policy


def _case_from_payload(payload: Mapping[str, Any]) -> OutreachCase:
    return OutreachCase(
        case_id=str(payload["case_id"]),
        company_unit=CompanyUnit(payload["company_unit"]),
        kind=OutreachKind(payload["kind"]),
        target_organization=str(payload["target_organization"]),
        recipient_hash=str(payload["recipient_hash"]),
        subject=str(payload["subject"]),
        purpose=str(payload["purpose"]),
        status=OutreachStatus(payload["status"]),
        sent_at=payload.get("sent_at"),
        provider_receipt_hash=payload.get("provider_receipt_hash"),
        source_issue=payload.get("source_issue"),
        follow_up_after=payload.get("follow_up_after"),
        legal_entity_claimed=bool(payload.get("legal_entity_claimed", False)),
        corporate_domain_verified=bool(payload.get("corporate_domain_verified", False)),
    )


def _load_case(path: Path) -> OutreachCase:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("outreach case must be a JSON object")
    return _case_from_payload(payload)


def _entry_hash(entry: dict[str, Any]) -> str:
    canonical = json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _read_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"ledger line {line_number} must be a JSON object")
        entries.append(payload)
    return entries


def audit_ledger(path: Path) -> list[str]:
    entries = _read_ledger(path)
    errors: list[str] = []
    previous = None
    cases: list[OutreachCase] = []
    for index, entry in enumerate(entries, start=1):
        stored = entry.get("entry_hash")
        unsigned = {key: value for key, value in entry.items() if key != "entry_hash"}
        expected = _entry_hash(unsigned)
        if stored != expected:
            errors.append(f"entry {index}: hash mismatch")
        if entry.get("previous_hash") != previous:
            errors.append(f"entry {index}: previous_hash mismatch")
        previous = stored
        case_payload = entry.get("case")
        if isinstance(case_payload, dict):
            cases.append(_case_from_payload(case_payload))
        else:
            errors.append(f"entry {index}: missing case object")
    errors.extend(audit_cases(cases))
    return errors


def append_case(case: OutreachCase, ledger: Path) -> dict[str, Any]:
    errors = validate_policy(case)
    if errors:
        raise ValueError("; ".join(errors))
    existing = _read_ledger(ledger)
    if any(entry.get("case", {}).get("case_id") == case.case_id for entry in existing):
        raise ValueError(f"case already exists: {case.case_id}")
    previous = existing[-1]["entry_hash"] if existing else None
    unsigned = {
        "sequence": len(existing) + 1,
        "previous_hash": previous,
        "case_hash": case.case_hash,
        "case": case.public_mapping(),
    }
    entry = {**unsigned, "entry_hash": _entry_hash(unsigned)}
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    return entry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Company-routed strategic outreach control plane")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate-case")
    validate.add_argument("case", type=Path)

    append = sub.add_parser("append-case")
    append.add_argument("case", type=Path)
    append.add_argument("--ledger", type=Path, required=True)

    audit = sub.add_parser("audit-ledger")
    audit.add_argument("ledger", type=Path)

    disclose = sub.add_parser("disclosure")
    disclose.add_argument("unit", choices=[unit.value for unit in CompanyUnit])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "validate-case":
        case = _load_case(args.case)
        errors = validate_policy(case)
        print(json.dumps({"valid": not errors, "errors": errors, "case_hash": case.case_hash}, indent=2))
        return 0 if not errors else 2
    if args.command == "append-case":
        case = _load_case(args.case)
        entry = append_case(case, args.ledger)
        print(json.dumps(entry, indent=2, ensure_ascii=False))
        return 0
    if args.command == "audit-ledger":
        errors = audit_ledger(args.ledger)
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        return 0 if not errors else 2
    if args.command == "disclosure":
        print(disclosure_line(CompanyUnit(args.unit)))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
