"""CLI for Ω-OPEN-PROBLEMS-ATLAS-T∞ R0.2 MAX."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark import run_benchmark, write_report
from .formal import audit_paths
from .intake import IntakePolicy, ingest_records, jsonl, load_json_records, snapshot_file
from .obligations import compile_obligations
from .store import AtlasStore


def _write(payload: object, output: str | None) -> None:
    encoded = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output:
        Path(output).write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


def _benchmark(args: argparse.Namespace) -> int:
    report = run_benchmark(
        lead_count=args.leads,
        obligation_budget=args.obligations,
        transfer_lead_sample=args.transfer_sample,
        sqlite_path=args.sqlite,
    )
    if args.output:
        write_report(report, args.output)
    else:
        _write(report, None)
    return 0


def _intake(args: argparse.Namespace) -> int:
    policy = IntakePolicy(
        source_id=args.source_id,
        authority_class=args.authority,
        license_class=args.license_class,
        allow_statement_summary=not args.metadata_only,
        allow_full_statement=False,
        require_status_recheck=not args.status_stable_fixture,
        require_literature_check=True,
        max_summary_chars=args.max_summary_chars,
    )
    snapshot = snapshot_file(args.input, policy, args.retrieved_at)
    records = load_json_records(args.input)
    leads, report = ingest_records(records, policy, snapshot)
    if args.leads_output:
        Path(args.leads_output).write_text("\n".join(jsonl(leads)) + ("\n" if leads else ""), encoding="utf-8")
    _write({"snapshot": snapshot.__dict__, "report": report.to_dict()}, args.output)
    return 0 if report.accepted_count else 2


def _audit_formal(args: argparse.Namespace) -> int:
    reports = [report.to_dict() for report in audit_paths(args.paths)]
    _write(
        {
            "reports": reports,
            "placeholder_total": sum(item["placeholder_count"] for item in reports),
            "formal_skeleton_is_not_completed_proof": True,
        },
        args.output,
    )
    return 0


def _compile_obligations(args: argparse.Namespace) -> int:
    raw = json.loads(Path(args.lead).read_text(encoding="utf-8"))
    from .models import LeadStatus, ProblemLead

    lead = ProblemLead(
        lead_id=raw["lead_id"],
        source_id=raw["source_id"],
        source_locator=raw["source_locator"],
        title=raw["title"],
        statement_summary=raw["statement_summary"],
        domains=tuple(raw["domains"]),
        kind=raw.get("kind", "RESEARCH_PROBLEM"),
        lead_status=LeadStatus(raw.get("lead_status", "DISCOVERED")),
        methods=tuple(raw.get("methods", [])),
        independently_checked_open=bool(raw.get("independently_checked_open", False)),
        solution_claimed=False,
    )
    obligations = compile_obligations(lead, per_operator_budget=args.units)
    _write(
        {
            "problem_id": lead.lead_id,
            "obligation_count": len(obligations),
            "obligations": [item.canonical_payload() for item in obligations],
            "solution_claimed": False,
        },
        args.output,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-open-problems-r02")
    commands = parser.add_subparsers(dest="command", required=True)

    benchmark = commands.add_parser("benchmark")
    benchmark.add_argument("--leads", type=int, default=4096)
    benchmark.add_argument("--obligations", type=int, default=100000)
    benchmark.add_argument("--transfer-sample", type=int, default=256)
    benchmark.add_argument("--sqlite")
    benchmark.add_argument("--output")
    benchmark.set_defaults(handler=_benchmark)

    intake = commands.add_parser("intake")
    intake.add_argument("--input", required=True)
    intake.add_argument("--source-id", required=True)
    intake.add_argument("--authority", default="UNREVIEWED_SOURCE")
    intake.add_argument("--license-class", default="REVIEW_REQUIRED")
    intake.add_argument("--retrieved-at", required=True)
    intake.add_argument("--metadata-only", action="store_true")
    intake.add_argument("--status-stable-fixture", action="store_true")
    intake.add_argument("--max-summary-chars", type=int, default=1200)
    intake.add_argument("--leads-output")
    intake.add_argument("--output")
    intake.set_defaults(handler=_intake)

    formal = commands.add_parser("audit-formal")
    formal.add_argument("paths", nargs="+")
    formal.add_argument("--output")
    formal.set_defaults(handler=_audit_formal)

    obligations = commands.add_parser("compile-obligations")
    obligations.add_argument("--lead", required=True)
    obligations.add_argument("--units", type=int, default=1)
    obligations.add_argument("--output")
    obligations.set_defaults(handler=_compile_obligations)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
