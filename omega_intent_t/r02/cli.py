from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from .budget import AdaptiveBudgetController
from .campaign import CampaignRunner, deterministic_executor, synthetic_records
from .completion import evaluate_completion
from .diff import compare_reports
from .ledger import IntentLedger
from .models import BudgetPolicy, CompletionContract, WorkRecord
from .oak import run_oakbench
from .stack import StackPlanner


def _write(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-intent-r02",
        description="Ω-INTENT-TO-EVERYTHING-T∞ R0.2 persistent orchestration and recovery kernel.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    manifest = commands.add_parser("manifest")
    manifest.add_argument("--output")

    oak = commands.add_parser("oak")
    oak.add_argument("--campaign-items", type=int, default=4096)
    oak.add_argument("--output")

    campaign = commands.add_parser("campaign")
    campaign.add_argument("--intent-id", default="INTENT-R02-CAMPAIGN")
    campaign.add_argument("--ledger", default="generated/omega_intent_r02/ledger.sqlite3")
    campaign.add_argument("--count", type=int, default=100_000)
    campaign.add_argument("--start-offset", type=int, default=0)
    campaign.add_argument("--initial-items", type=int, default=256)
    campaign.add_argument("--initial-bytes", type=int, default=4 * 1024 * 1024)
    campaign.add_argument("--max-records", type=int)
    campaign.add_argument("--output")

    inspect = commands.add_parser("inspect")
    inspect.add_argument("ledger")
    inspect.add_argument("intent_id")
    inspect.add_argument("--output")

    stack = commands.add_parser("stack-plan")
    stack.add_argument("input", help="JSONL work records")
    stack.add_argument("--max-items", type=int, default=128)
    stack.add_argument("--max-bytes", type=int, default=2 * 1024 * 1024)
    stack.add_argument("--branch-prefix", default="feat/omega-intent-r02")
    stack.add_argument("--output")

    completion = commands.add_parser("completion")
    completion.add_argument("contract", help="JSON completion contract")
    completion.add_argument("--output")

    diff = commands.add_parser("diff")
    diff.add_argument("before")
    diff.add_argument("after")
    diff.add_argument("--output")
    return parser


def _manifest() -> dict[str, Any]:
    controller = AdaptiveBudgetController()
    return {
        "schema": "omega-intent-r02-manifest/v2",
        "capabilities": [
            "sqlite_wal_intent_ledger",
            "idempotent_work_ingestion",
            "strict_state_machine",
            "exact_checkpoint_resume",
            "content_addressed_artifacts",
            "m_minus_residual_registry",
            "cooperative_work_leases",
            "adaptive_batch_and_byte_budgets",
            "evidence_based_completion_contract",
            "failure_to_repair_intent_compilation",
            "dependency_aware_stacked_pr_planning",
            "differential_progress_reports",
            "finite_streaming_campaigns",
        ],
        "budget": controller.manifest(),
        "permanent_total_cap": None,
        "remote_mutations": 0,
        "automatic_merge": False,
    }


def _campaign(args: argparse.Namespace) -> dict[str, Any]:
    if args.count < 0 or args.start_offset < 0:
        raise ValueError("count and start offset cannot be negative")
    policy = BudgetPolicy(initial_items=args.initial_items, initial_bytes=args.initial_bytes)
    controller = AdaptiveBudgetController(policy)
    with IntentLedger(args.ledger) as ledger:
        ledger.ingest_intent({"id": args.intent_id, "objective": "R0.2 finite synthetic campaign"})
        report = CampaignRunner(ledger, controller=controller).run(
            args.intent_id,
            synthetic_records(args.intent_id, args.count, start_offset=args.start_offset),
            deterministic_executor,
            max_records=args.max_records,
        )
        return {
            "report": report.to_dict(),
            "ledger": ledger.summary(args.intent_id),
            "budget": controller.manifest(),
        }


def _stack(args: argparse.Namespace) -> dict[str, Any]:
    records: list[WorkRecord] = []
    with Path(args.input).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            raw = json.loads(line)
            if not isinstance(raw, dict):
                raise TypeError(f"line {line_number} must contain an object")
            records.append(WorkRecord.from_mapping(raw))
    return StackPlanner(
        max_items_per_shard=args.max_items,
        max_bytes_per_shard=args.max_bytes,
        branch_prefix=args.branch_prefix,
    ).manifest(records)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "manifest":
        payload = _manifest()
    elif args.command == "oak":
        payload = run_oakbench(campaign_items=args.campaign_items)
    elif args.command == "campaign":
        payload = _campaign(args)
    elif args.command == "inspect":
        with IntentLedger(args.ledger) as ledger:
            payload = ledger.summary(args.intent_id)
    elif args.command == "stack-plan":
        payload = _stack(args)
    elif args.command == "completion":
        raw = json.loads(Path(args.contract).read_text(encoding="utf-8"))
        payload = evaluate_completion(CompletionContract(**raw)).to_dict()
    elif args.command == "diff":
        before = json.loads(Path(args.before).read_text(encoding="utf-8"))
        after = json.loads(Path(args.after).read_text(encoding="utf-8"))
        payload = compare_reports(before, after)
    else:
        raise AssertionError("unreachable")
    _write(payload, getattr(args, "output", None))
    return 0 if payload.get("passed", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
