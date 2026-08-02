from __future__ import annotations

from datetime import datetime, timezone
import hashlib

from .models import BranchDNA, MergePlan, MergeReceipt, Severity


def build_merge_receipt(
    *,
    branch_dna: BranchDNA,
    plan: MergePlan,
    result_sha: str | None = None,
    completed_tests: tuple[str, ...] = (),
    artifacts: tuple[str, ...] = (),
    known_residues: tuple[str, ...] = (),
    timestamp: str | None = None,
) -> MergeReceipt:
    stamp = timestamp or datetime.now(timezone.utc).isoformat(timespec="seconds")
    seed = "\0".join(
        (
            stamp,
            branch_dna.base_sha,
            branch_dna.head_sha,
            result_sha or "dry-run",
            branch_dna.digest(),
            plan.verdict,
        )
    )
    receipt_id = "convergence-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
    high_or_critical = sum(
        conflict.severity in {Severity.HIGH, Severity.CRITICAL}
        for conflict in plan.conflicts
    )

    if result_sha is None:
        oak_verdict = "DRY_RUN_ONLY"
    elif high_or_critical:
        oak_verdict = "MERGED_WITH_EXPLICIT_RESIDUES"
    elif set(plan.required_tests).issubset(completed_tests):
        oak_verdict = "MERGED_SOFTWARE_GATES_PASSED"
    else:
        oak_verdict = "MERGED_TEST_EVIDENCE_INCOMPLETE"

    residues = tuple(known_residues)
    if result_sha is not None and not set(plan.required_tests).issubset(completed_tests):
        missing = sorted(set(plan.required_tests) - set(completed_tests))
        residues += ("missing-tests:" + ",".join(missing),)

    return MergeReceipt(
        receipt_id=receipt_id,
        base_sha=branch_dna.base_sha,
        head_sha=branch_dna.head_sha,
        result_sha=result_sha,
        branch_dna_sha256=branch_dna.digest(),
        conflict_count=len(plan.conflicts),
        high_or_critical_conflicts=high_or_critical,
        tests=tuple(sorted(completed_tests)),
        artifacts=tuple(sorted(artifacts)),
        known_residues=tuple(sorted(residues)),
        oak_verdict=oak_verdict,
        automatic_scientific_promotion=False,
        automatic_merge=False,
    )
