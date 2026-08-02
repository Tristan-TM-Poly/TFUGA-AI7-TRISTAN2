from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .dashboard import build_dashboard
from .inbound import PrivateMailMetadata, build_public_event
from .models import (
    CompanyUnit,
    ConsentBasis,
    MailEventType,
    OutreachCase,
    OutreachKind,
    OutreachStatus,
    PublicMailEvent,
    ReplyClass,
    RiskTier,
    StrategicSignals,
)
from .policy import (
    audit_cases,
    company_signature,
    disclosure_line,
    next_action_for_event,
    validate_policy,
    validate_portfolio,
)
from .scoring import score_case


def case_from_mapping(payload: dict[str, Any]) -> OutreachCase:
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
        consent_basis=ConsentBasis(payload.get("consent_basis", "not_commercial")),
        commercial_message=bool(payload.get("commercial_message", False)),
        unsubscribe_required=bool(payload.get("unsubscribe_required", False)),
        unsubscribe_mechanism_verified=bool(payload.get("unsubscribe_mechanism_verified", False)),
        sender_identity_verified=bool(payload.get("sender_identity_verified", True)),
        thread_hash=payload.get("thread_hash"),
        latest_event_at=payload.get("latest_event_at"),
        reply_class=ReplyClass(payload["reply_class"]) if payload.get("reply_class") else None,
        risk_tier=RiskTier(payload.get("risk_tier", "low")),
    )


def event_from_mapping(payload: dict[str, Any]) -> PublicMailEvent:
    return PublicMailEvent(
        event_id=str(payload["event_id"]),
        case_id=str(payload["case_id"]),
        event_type=MailEventType(payload["event_type"]),
        message_hash=str(payload["message_hash"]),
        thread_hash=str(payload["thread_hash"]),
        counterparty_hash=str(payload["counterparty_hash"]),
        occurred_at=str(payload["occurred_at"]),
        provider=str(payload.get("provider", "gmail")),
        reply_class=ReplyClass(payload["reply_class"]) if payload.get("reply_class") else None,
        source_issue=payload.get("source_issue"),
        raw_content_retained=bool(payload.get("raw_content_retained", False)),
    )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return payload


def _load_case(path: Path) -> OutreachCase:
    return case_from_mapping(_load_json(path))


def _load_event(path: Path) -> PublicMailEvent:
    return event_from_mapping(_load_json(path))


def _load_cases(directory: Path) -> list[OutreachCase]:
    return [_load_case(path) for path in sorted(directory.glob("*.json"))]


def _load_events(directory: Path | None) -> list[PublicMailEvent]:
    if directory is None or not directory.exists():
        return []
    return [_load_event(path) for path in sorted(directory.glob("*.json"))]


def _entry_hash(entry: dict[str, Any]) -> str:
    canonical = json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _read_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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
            cases.append(case_from_mapping(case_payload))
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


def _write_json(path: Path | None, payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


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

    signature = sub.add_parser("signature")
    signature.add_argument("unit", choices=[unit.value for unit in CompanyUnit])
    signature.add_argument("--sender-name", default="Tristan Tardif-Morency")

    score = sub.add_parser("score-case")
    score.add_argument("case", type=Path)
    score.add_argument("signals", type=Path)
    score.add_argument("--out", type=Path)

    ingest = sub.add_parser("ingest-reply")
    ingest.add_argument("private_metadata", type=Path)
    ingest.add_argument("--event-id", required=True)
    ingest.add_argument("--secret-env", default="OMEGA_OUTREACH_HASH_SALT")
    ingest.add_argument("--out", type=Path, required=True)

    action = sub.add_parser("next-action")
    action.add_argument("event", type=Path)

    portfolio = sub.add_parser("portfolio-check")
    portfolio.add_argument("cases_dir", type=Path)

    dashboard = sub.add_parser("dashboard")
    dashboard.add_argument("cases_dir", type=Path)
    dashboard.add_argument("--events-dir", type=Path)
    dashboard.add_argument("--format", choices=["json", "markdown"], default="json")
    dashboard.add_argument("--out", type=Path)
    dashboard.add_argument("--generated-at")

    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "validate-case":
        case = _load_case(args.case)
        errors = validate_policy(case)
        _write_json(None, {"valid": not errors, "errors": errors, "case_hash": case.case_hash})
        return 0 if not errors else 2
    if args.command == "append-case":
        case = _load_case(args.case)
        entry = append_case(case, args.ledger)
        _write_json(None, entry)
        return 0
    if args.command == "audit-ledger":
        errors = audit_ledger(args.ledger)
        _write_json(None, {"valid": not errors, "errors": errors})
        return 0 if not errors else 2
    if args.command == "disclosure":
        print(disclosure_line(CompanyUnit(args.unit)))
        return 0
    if args.command == "signature":
        print(company_signature(CompanyUnit(args.unit), args.sender_name))
        return 0
    if args.command == "score-case":
        case = _load_case(args.case)
        signal_payload = _load_json(args.signals)
        signals = StrategicSignals(**{key: int(value) for key, value in signal_payload.items()})
        result = score_case(case, signals)
        _write_json(args.out, result.public_mapping())
        return 0
    if args.command == "ingest-reply":
        payload = _load_json(args.private_metadata)
        secret = os.environ.get(args.secret_env, "")
        if not secret:
            raise SystemExit(f"missing required environment variable: {args.secret_env}")
        metadata = PrivateMailMetadata(
            case_id=str(payload["case_id"]),
            provider_message_id=str(payload["provider_message_id"]),
            provider_thread_id=str(payload["provider_thread_id"]),
            counterparty=str(payload["counterparty"]),
            occurred_at=str(payload["occurred_at"]),
            subject=str(payload.get("subject", "")),
            snippet=str(payload.get("snippet", "")),
            headers=payload.get("headers"),
            source_issue=payload.get("source_issue"),
        )
        event = build_public_event(metadata, secret=secret, event_id=args.event_id)
        _write_json(args.out, {**event.public_mapping(), "event_hash": event.event_hash})
        return 0
    if args.command == "next-action":
        event = _load_event(args.event)
        errors = event.validate()
        if errors:
            _write_json(None, {"valid": False, "errors": errors})
            return 2
        _write_json(None, {"valid": True, "next_action": next_action_for_event(event).value})
        return 0
    if args.command == "portfolio-check":
        cases = _load_cases(args.cases_dir)
        errors = audit_cases(cases) + validate_portfolio(cases)
        _write_json(None, {"valid": not errors, "errors": errors, "case_count": len(cases)})
        return 0 if not errors else 2
    if args.command == "dashboard":
        cases = _load_cases(args.cases_dir)
        events = _load_events(args.events_dir)
        report = build_dashboard(cases, events, generated_at=args.generated_at)
        if args.format == "markdown":
            text = report.as_markdown()
            if args.out:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(text, encoding="utf-8")
            else:
                print(text, end="")
        else:
            _write_json(args.out, report.as_dict())
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
