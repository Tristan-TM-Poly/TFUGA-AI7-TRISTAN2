from __future__ import annotations

import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from .model import (
    CYCLE_STATES,
    REPORT_SCHEMA,
    CompetitionCycle,
    LedgerBundle,
    LocalPlan,
    SourceReceipt,
    SubmissionReceipt,
    convert_datetime,
    load_bundle,
    parse_datetime,
    stable_digest,
    write_json,
    write_jsonl,
)


def _deadline(cycle: CompetitionCycle, key: str) -> datetime | None:
    value = cycle.deadlines.get(key)
    return None if value is None else parse_datetime(value, f"{cycle.cycle_id}.{key}")


def _validate_deadline_order(cycle: CompetitionCycle) -> list[str]:
    blockers: list[str] = []
    pairs = (
        ("announced_at", "registration_open"),
        ("registration_open", "registration_close"),
        ("announced_at", "task_release"),
        ("task_release", "submission_open"),
        ("registration_close", "submission_close"),
        ("submission_open", "submission_close"),
        ("submission_close", "judging_end"),
        ("judging_end", "archive_at"),
    )
    for left_key, right_key in pairs:
        left = _deadline(cycle, left_key)
        right = _deadline(cycle, right_key)
        if left is not None and right is not None and left > right:
            blockers.append(f"deadline_order_invalid:{left_key}>{right_key}")
    return blockers


def derive_cycle_state(cycle: CompetitionCycle, as_of: datetime) -> str:
    archive_at = _deadline(cycle, "archive_at")
    judging_end = _deadline(cycle, "judging_end")
    submission_close = _deadline(cycle, "submission_close")
    active_candidates = [
        _deadline(cycle, "registration_open"),
        _deadline(cycle, "task_release"),
        _deadline(cycle, "submission_open"),
    ]
    announced_at = _deadline(cycle, "announced_at")
    active_start = min(
        (item for item in active_candidates if item is not None),
        default=announced_at,
    )
    if archive_at is not None and as_of >= archive_at:
        return "archived"
    if judging_end is not None and as_of >= judging_end:
        return "closed"
    if submission_close is not None and as_of >= submission_close:
        return "judging" if judging_end is not None else "closed"
    if active_start is not None and as_of >= active_start:
        return "active"
    return "announced"


def _deadline_views(cycle: CompetitionCycle, recommendation_timezone: str) -> dict[str, Any]:
    return {
        key: (
            None
            if value is None
            else convert_datetime(value, recommendation_timezone)
        )
        for key, value in cycle.deadlines.items()
    }


def _official_rule_receipt(
    cycle: CompetitionCycle,
    sources: Mapping[str, SourceReceipt],
    as_of: datetime,
    freshness_seconds: int,
) -> tuple[dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    candidates: list[SourceReceipt] = []
    parsed_rule = urlparse(cycle.official_rule_url)
    expected_domain = parsed_rule.netloc.lower()
    for source_id in cycle.source_reference_ids:
        source = sources.get(source_id)
        if source is None:
            blockers.append(f"source_reference_missing:{source_id}")
            continue
        if source.source_kind != "official_rules":
            continue
        if source.official_url != cycle.official_rule_url:
            continue
        if source.organizer_domain.lower() != cycle.organizer_domain.lower():
            continue
        if urlparse(source.official_url).netloc.lower() != expected_domain:
            continue
        observed = parse_datetime(source.observed_at, "source observed_at")
        if observed > as_of:
            blockers.append(f"official_source_after_as_of:{source.source_id}")
            continue
        candidates.append(source)
    if not candidates:
        blockers.append("official_rule_source_missing")
        return None, blockers
    latest = max(candidates, key=lambda item: parse_datetime(item.observed_at, "observed_at"))
    observed = parse_datetime(latest.observed_at, "observed_at")
    age_seconds = (as_of - observed).total_seconds()
    fresh = age_seconds <= freshness_seconds
    if not fresh:
        blockers.append(f"official_rule_source_stale:{int(age_seconds)}>{freshness_seconds}")
    receipt = {
        "source_id": latest.source_id,
        "official_url": latest.official_url,
        "source_digest": latest.source_digest,
        "observed_at": latest.observed_at,
        "age_seconds": age_seconds,
        "freshness_seconds": freshness_seconds,
        "fresh": fresh,
        "rule_digest": cycle.rule_digest,
    }
    receipt["verification_digest"] = stable_digest(receipt)
    return receipt, blockers


def _referenced_source_blockers(
    cycle: CompetitionCycle,
    sources: Mapping[str, SourceReceipt],
) -> list[str]:
    blockers: list[str] = []
    required = set(cycle.source_reference_ids)
    required.update(cycle.eligibility.terms_reference_ids)
    required.update(cycle.licenses.license_reference_ids)
    required.update(cycle.prize.prize_reference_ids)
    required.update(cycle.judging.judging_reference_ids)
    for task in cycle.tasks:
        required.update(task.task_reference_ids)
    for source_id in sorted(required):
        if source_id not in sources:
            blockers.append(f"source_reference_missing:{source_id}")
    return blockers


def _cycle_history_blockers(
    cycles: tuple[CompetitionCycle, ...],
) -> dict[tuple[str, str], list[str]]:
    blockers: dict[tuple[str, str], list[str]] = defaultdict(list)
    by_key = {(item.competition_id, item.cycle_id): item for item in cycles}
    for cycle in cycles:
        key = (cycle.competition_id, cycle.cycle_id)
        predecessor = cycle.predecessor_cycle_id
        if predecessor is None:
            continue
        if predecessor == cycle.cycle_id:
            blockers[key].append("predecessor_cycle_self_reference")
            continue
        previous = by_key.get((cycle.competition_id, predecessor))
        if previous is None:
            blockers[key].append(f"predecessor_cycle_missing:{predecessor}")
            continue
        previous_announcement = _deadline(previous, "announced_at")
        current_announcement = _deadline(cycle, "announced_at")
        if (
            previous_announcement is not None
            and current_announcement is not None
            and current_announcement <= previous_announcement
        ):
            blockers[key].append("predecessor_not_older")
    return blockers


def _eligibility_plan(
    plan: LocalPlan,
    cycle: CompetitionCycle,
    as_of: datetime,
) -> dict[str, Any]:
    blockers: list[str] = []
    if plan.rule_digest != cycle.rule_digest:
        blockers.append("stale_rule_digest")
    if parse_datetime(plan.created_at, "plan created_at") > as_of:
        blockers.append("plan_created_after_as_of")
    rules = cycle.eligibility
    age = plan.participant_age
    if rules.minimum_age is not None and (age is None or age < rules.minimum_age):
        blockers.append("minimum_age_not_satisfied")
    if rules.maximum_age is not None and (age is None or age > rules.maximum_age):
        blockers.append("maximum_age_not_satisfied")
    residency = plan.participant_residency
    if rules.allowed_residencies and residency not in rules.allowed_residencies:
        blockers.append("residency_not_allowed")
    if residency in rules.excluded_residencies:
        blockers.append("residency_excluded")
    team_size = plan.team_size
    if team_size is None:
        blockers.append("team_size_unknown")
    elif not (rules.team_min_size <= team_size <= rules.team_max_size):
        blockers.append("team_size_out_of_range")
    if plan.status == "authorized" and not plan.authorization_reference:
        blockers.append("authorization_reference_missing")
    if plan.status in {"draft", "withdrawn"}:
        blockers.append(f"plan_status_not_actionable:{plan.status}")
    assessment = {
        "plan_id": plan.plan_id,
        "competition_id": plan.competition_id,
        "cycle_id": plan.cycle_id,
        "plan_type": plan.plan_type,
        "status": plan.status,
        "current_rule_digest": cycle.rule_digest,
        "plan_rule_digest": plan.rule_digest,
        "valid": not blockers,
        "blockers": sorted(set(blockers)),
        "registration_performed": False,
        "submission_performed": False,
    }
    assessment["assessment_digest"] = stable_digest(assessment)
    return assessment


def _submission_receipt_assessment(
    receipt: SubmissionReceipt,
    cycle: CompetitionCycle,
    sources: Mapping[str, SourceReceipt],
) -> dict[str, Any]:
    blockers: list[str] = []
    if receipt.rule_digest != cycle.rule_digest:
        blockers.append("submission_rule_digest_stale")
    submitted = parse_datetime(receipt.submitted_at, "submitted_at")
    submission_open = _deadline(cycle, "submission_open")
    submission_close = _deadline(cycle, "submission_close")
    if submission_open is not None and submitted < submission_open:
        blockers.append("submitted_before_window")
    if submission_close is not None and submitted > submission_close:
        blockers.append("submitted_after_deadline")
    missing_sources = sorted(set(receipt.result_reference_ids) - set(sources))
    if missing_sources:
        blockers.append(f"result_source_missing:{','.join(missing_sources)}")
    if receipt.result_status in {"accepted", "rejected", "scored", "winner", "not_selected"}:
        if not receipt.result_reference_ids:
            blockers.append("official_result_reference_missing")
        elif not any(
            sources[source_id].source_kind == "official_results"
            for source_id in receipt.result_reference_ids
            if source_id in sources
        ):
            blockers.append("official_result_source_missing")
    result = {
        "receipt_id": receipt.receipt_id,
        "competition_id": receipt.competition_id,
        "cycle_id": receipt.cycle_id,
        "result_status": receipt.result_status,
        "valid": not blockers,
        "blockers": sorted(set(blockers)),
        "recorded_external_receipt": True,
        "submission_performed_by_ledger": False,
        "prize_payment_guaranteed": False,
    }
    result["assessment_digest"] = stable_digest(result)
    return result


def _archive_records(cycle: CompetitionCycle, state: str) -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    rows: list[dict[str, Any]] = []
    if state != "archived":
        return rows, blockers
    for task in cycle.tasks:
        if task.artifact_digest is None:
            blockers.append(f"archive_artifact_digest_missing:{task.task_id}")
            continue
        if task.archive_license.lower() in {"unknown", "none", "prohibited"}:
            blockers.append(f"archive_license_not_usable:{task.task_id}")
            continue
        row = {
            "competition_id": cycle.competition_id,
            "cycle_id": cycle.cycle_id,
            "task_id": task.task_id,
            "title": task.title,
            "task_type": task.task_type,
            "artifact_digest": task.artifact_digest,
            "archive_license": task.archive_license,
            "task_reference_ids": list(task.task_reference_ids),
            "training_benchmark_only_under_license": True,
            "open_problem_status_inherited": False,
        }
        row["archive_digest"] = stable_digest(row)
        rows.append(row)
    return rows, blockers


def evaluate_bundle(bundle: LedgerBundle) -> dict[str, Any]:
    as_of = parse_datetime(bundle.as_of, "as_of")
    sources = {item.source_id: item for item in bundle.sources}
    cycles = {(item.competition_id, item.cycle_id): item for item in bundle.cycles}
    history_blockers = _cycle_history_blockers(bundle.cycles)

    cycle_rows: list[dict[str, Any]] = []
    recommendation_rows: list[dict[str, Any]] = []
    archive_rows: list[dict[str, Any]] = []
    plan_rows: list[dict[str, Any]] = []
    submission_rows: list[dict[str, Any]] = []
    plans_by_cycle: dict[tuple[str, str], list[LocalPlan]] = defaultdict(list)
    receipts_by_cycle: dict[tuple[str, str], list[SubmissionReceipt]] = defaultdict(list)
    global_blockers: list[str] = []

    for plan in bundle.plans:
        plans_by_cycle[(plan.competition_id, plan.cycle_id)].append(plan)
        if (plan.competition_id, plan.cycle_id) not in cycles:
            global_blockers.append(f"plan_cycle_missing:{plan.plan_id}")
    for receipt in bundle.submission_receipts:
        receipts_by_cycle[(receipt.competition_id, receipt.cycle_id)].append(receipt)
        if (receipt.competition_id, receipt.cycle_id) not in cycles:
            global_blockers.append(f"submission_cycle_missing:{receipt.receipt_id}")

    for key in sorted(cycles):
        cycle = cycles[key]
        blockers = []
        blockers.extend(_validate_deadline_order(cycle))
        blockers.extend(_referenced_source_blockers(cycle, sources))
        blockers.extend(history_blockers.get(key, []))
        state = derive_cycle_state(cycle, as_of)
        if state not in CYCLE_STATES:
            blockers.append(f"invalid_derived_state:{state}")
        verification, verification_blockers = _official_rule_receipt(
            cycle,
            sources,
            as_of,
            bundle.freshness_seconds,
        )
        blockers.extend(verification_blockers)

        cycle_plan_rows: list[dict[str, Any]] = []
        for plan in sorted(plans_by_cycle.get(key, []), key=lambda item: item.plan_id):
            assessment = _eligibility_plan(plan, cycle, as_of)
            cycle_plan_rows.append(assessment)
            plan_rows.append(assessment)

        cycle_submission_rows: list[dict[str, Any]] = []
        for receipt in sorted(receipts_by_cycle.get(key, []), key=lambda item: item.receipt_id):
            assessment = _submission_receipt_assessment(receipt, cycle, sources)
            cycle_submission_rows.append(assessment)
            submission_rows.append(assessment)

        eligibility_plans = [
            row for row in cycle_plan_rows if row["plan_type"] == "eligibility"
        ]
        valid_eligibility = [row for row in eligibility_plans if row["valid"]]
        recommendation_blockers = list(blockers)
        if state != "active":
            recommendation_blockers.append(f"cycle_not_active:{state}")
        if verification is None or verification.get("fresh") is not True:
            recommendation_blockers.append("fresh_official_verification_required")
        if not valid_eligibility:
            recommendation_blockers.append("valid_eligibility_plan_missing")
        recommendation_blockers = sorted(set(recommendation_blockers))
        recommended = not recommendation_blockers

        archive_for_cycle, archive_blockers = _archive_records(cycle, state)
        blockers.extend(archive_blockers)
        archive_rows.extend(archive_for_cycle)

        cycle_row = {
            **cycle.to_dict(),
            "state": state,
            "as_of": bundle.as_of,
            "deadline_views": _deadline_views(cycle, bundle.recommendation_timezone),
            "official_verification": verification,
            "blockers": sorted(set(blockers)),
            "recommendation_ready": recommended,
            "recommendation_blockers": recommendation_blockers,
            "plan_assessment_ids": [row["plan_id"] for row in cycle_plan_rows],
            "submission_assessment_ids": [row["receipt_id"] for row in cycle_submission_rows],
            "open_problem_status_inherited": False,
            "registration_performed": False,
            "submission_performed": False,
            "prize_payment_guaranteed": False,
        }
        cycle_row["cycle_record_digest"] = stable_digest(cycle_row)
        cycle_rows.append(cycle_row)
        if recommended:
            recommendation = {
                "competition_id": cycle.competition_id,
                "cycle_id": cycle.cycle_id,
                "title": cycle.title,
                "organizer": cycle.organizer,
                "state": state,
                "rule_digest": cycle.rule_digest,
                "official_verification_digest": verification["verification_digest"],
                "submission_close": cycle.deadlines["submission_close"],
                "submission_close_views": cycle_row["deadline_views"]["submission_close"],
                "prize": cycle.prize.to_dict(),
                "valid_eligibility_plan_ids": [row["plan_id"] for row in valid_eligibility],
                "recommendation_is_not_registration_or_submission": True,
                "registration_performed": False,
                "submission_performed": False,
            }
            recommendation["recommendation_digest"] = stable_digest(recommendation)
            recommendation_rows.append(recommendation)

    evaluation = {
        "cycle_rows": cycle_rows,
        "plan_rows": sorted(plan_rows, key=lambda item: item["plan_id"]),
        "submission_rows": sorted(submission_rows, key=lambda item: item["receipt_id"]),
        "recommendations": sorted(
            recommendation_rows,
            key=lambda item: (item["submission_close"], item["competition_id"], item["cycle_id"]),
        ),
        "archive_rows": sorted(
            archive_rows,
            key=lambda item: (item["competition_id"], item["cycle_id"], item["task_id"]),
        ),
        "global_blockers": sorted(set(global_blockers)),
    }
    return evaluation


def _manifest(bundle: LedgerBundle, evaluation: Mapping[str, Any]) -> dict[str, Any]:
    artifacts = {
        "sources.jsonl": stable_digest([item.to_dict() for item in bundle.sources]),
        "cycles.jsonl": stable_digest(evaluation["cycle_rows"]),
        "plans.jsonl": stable_digest(evaluation["plan_rows"]),
        "submission_receipts.jsonl": stable_digest(evaluation["submission_rows"]),
        "recommendations.json": stable_digest(evaluation["recommendations"]),
        "archive_benchmarks.jsonl": stable_digest(evaluation["archive_rows"]),
    }
    manifest = {
        "schema": "omega-competition-ledger-manifest/11",
        "as_of": bundle.as_of,
        "freshness_seconds": bundle.freshness_seconds,
        "recommendation_timezone": bundle.recommendation_timezone,
        "source_count": len(bundle.sources),
        "cycle_count": len(bundle.cycles),
        "plan_count": len(bundle.plans),
        "submission_receipt_count": len(bundle.submission_receipts),
        "recommendation_count": len(evaluation["recommendations"]),
        "archive_benchmark_count": len(evaluation["archive_rows"]),
        "artifacts": artifacts,
        "registration_performed": False,
        "submission_performed": False,
        "open_problem_status_inherited": False,
    }
    manifest["manifest_digest"] = stable_digest(manifest)
    return manifest


def compile_competition_ledger(
    bundle_path: str | Path,
    output_dir: str | Path,
    *,
    clean: bool = True,
) -> dict[str, Any]:
    bundle = load_bundle(bundle_path)
    output = Path(output_dir)
    if output.exists() and clean:
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    evaluation = evaluate_bundle(bundle)

    write_json(output / "request.json", bundle.to_dict())
    write_jsonl(output / "sources.jsonl", [item.to_dict() for item in bundle.sources])
    write_jsonl(output / "cycles.jsonl", evaluation["cycle_rows"])
    write_jsonl(output / "plans.jsonl", evaluation["plan_rows"])
    write_jsonl(output / "submission_receipts.jsonl", evaluation["submission_rows"])
    write_json(output / "recommendations.json", evaluation["recommendations"])
    write_jsonl(output / "archive_benchmarks.jsonl", evaluation["archive_rows"])
    manifest = _manifest(bundle, evaluation)
    write_json(output / "manifest.json", manifest)

    report = {
        "schema": REPORT_SCHEMA,
        "as_of": bundle.as_of,
        "cycle_count": len(bundle.cycles),
        "active_cycle_count": sum(1 for row in evaluation["cycle_rows"] if row["state"] == "active"),
        "recommended_cycle_count": len(evaluation["recommendations"]),
        "archived_cycle_count": sum(1 for row in evaluation["cycle_rows"] if row["state"] == "archived"),
        "archive_benchmark_count": len(evaluation["archive_rows"]),
        "invalid_plan_count": sum(1 for row in evaluation["plan_rows"] if not row["valid"]),
        "invalid_submission_receipt_count": sum(
            1 for row in evaluation["submission_rows"] if not row["valid"]
        ),
        "global_blockers": evaluation["global_blockers"],
        "manifest_digest": manifest["manifest_digest"],
        "registration_performed": False,
        "submission_performed": False,
        "payment_performed": False,
        "winner_or_prize_guaranteed": False,
        "open_problem_status_inherited": False,
        "proof_claimed": False,
        "solution_claimed": False,
    }
    report["report_digest"] = stable_digest(report)
    write_json(output / "report.json", report)
    return report
