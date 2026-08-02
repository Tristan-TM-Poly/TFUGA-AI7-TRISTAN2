from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Sequence

from .models import Conflict, ConflictKind, MergePlan, Severity


_SEVERITY_WEIGHT = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 3,
    Severity.HIGH: 8,
    Severity.CRITICAL: 21,
}


def _strategy_for(path: str, path_conflicts: Sequence[Conflict]) -> str:
    kinds = {item.kind for item in path_conflicts}
    severities = {item.severity for item in path_conflicts}
    if ConflictKind.BINARY in kinds:
        return "preserve_blob_then_select_by_sha"
    if ConflictKind.POLICY in kinds or Severity.CRITICAL in severities:
        return "block_pending_human_security_review"
    if ConflictKind.API in kinds:
        return "semantic_merge_with_compatibility_adapter"
    if ConflictKind.SCHEMA in kinds:
        return "version_schema_and_add_migration"
    if ConflictKind.EPISTEMIC in kinds:
        return "separate_status_dimensions_and_require_evidence"
    if ConflictKind.FILE in kinds:
        return "semantic_three_way_merge"
    return "additive_overlay"


def build_merge_plan(
    *,
    base_sha: str,
    head_sha: str,
    changed_paths: Iterable[str],
    conflicts: Iterable[Conflict],
    declared_tests: Iterable[str] = (),
) -> MergePlan:
    conflict_tuple = tuple(conflicts)
    by_path: dict[str, list[Conflict]] = defaultdict(list)
    for conflict in conflict_tuple:
        path = conflict.key.split(":", 1)[0]
        by_path[path].append(conflict)

    strategy_by_path = {
        path: _strategy_for(path, by_path.get(path, ())) for path in sorted(set(changed_paths))
    }
    preservation_paths = tuple(
        sorted(path for path, strategy in strategy_by_path.items() if "preserve" in strategy)
    )

    required_tests = set(declared_tests)
    required_tests.add("python_compile")
    if any(item.kind is ConflictKind.API for item in conflict_tuple):
        required_tests.update({"public_api_contract", "cli_surface"})
    if any(item.kind is ConflictKind.SCHEMA for item in conflict_tuple):
        required_tests.update({"schema_validation", "migration_roundtrip"})
    if any(item.kind is ConflictKind.POLICY for item in conflict_tuple):
        required_tests.update({"workflow_permission_audit", "dry_run_no_remote_mutation"})
    if any(item.kind is ConflictKind.EPISTEMIC for item in conflict_tuple):
        required_tests.add("claim_evidence_status_gate")
    if any(item.kind is ConflictKind.BINARY for item in conflict_tuple):
        required_tests.update({"binary_sha_preservation", "artifact_manifest"})

    weighted_risk = sum(_SEVERITY_WEIGHT[item.severity] for item in conflict_tuple)
    critical = any(item.severity is Severity.CRITICAL for item in conflict_tuple)
    high = sum(item.severity is Severity.HIGH for item in conflict_tuple)
    if critical:
        verdict = "BLOCKED_SECURITY_OR_POLICY"
    elif high >= 3 or weighted_risk >= 24:
        verdict = "REQUIRES_EXPLICIT_RECONCILIATION"
    elif conflict_tuple:
        verdict = "DRY_RUN_CANDIDATE_WITH_RESIDUES"
    else:
        verdict = "ADDITIVE_DRY_RUN_CANDIDATE"

    rollback_steps = (
        f"record pre-merge base {base_sha}",
        "store branch DNA and conflict report",
        "create merge commit with both parents; never rewrite main history",
        "revert the merge commit if post-merge gates fail",
        "retain failed evidence in M-minus",
    )

    return MergePlan(
        base_sha=base_sha,
        head_sha=head_sha,
        strategy_by_path=strategy_by_path,
        conflicts=conflict_tuple,
        required_tests=tuple(sorted(required_tests)),
        preservation_paths=preservation_paths,
        rollback_steps=rollback_steps,
        verdict=verdict,
        automatic_merge_allowed=False,
    )
