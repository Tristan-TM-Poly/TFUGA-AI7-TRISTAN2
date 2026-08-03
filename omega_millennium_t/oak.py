"""OAK proof gate: evidence-aware, fail-closed claim promotion."""
from __future__ import annotations

from collections import Counter
from typing import Iterable, Mapping

from .models import Claim, ClaimKind, Evidence, EvidenceKind, OAKDecision, OAKLevel


_LEVEL_REQUIREMENTS: dict[OAKLevel, tuple[EvidenceKind, ...]] = {
    OAKLevel.INTUITION: (),
    OAKLevel.WELL_TYPED: (),
    OAKLevel.KNOWN_CASES: (EvidenceKind.SOURCE,),
    OAKLevel.NUMERICALLY_TESTED: (EvidenceKind.NUMERICAL,),
    OAKLevel.RESTRICTED_PROOF: (EvidenceKind.RESTRICTED_PROOF,),
    OAKLevel.GENERAL_MANUSCRIPT: (EvidenceKind.MANUSCRIPT_PROOF,),
    OAKLevel.FORMALIZED: (EvidenceKind.FORMAL_PROOF,),
    OAKLevel.INDEPENDENTLY_REVIEWED: (EvidenceKind.INDEPENDENT_REVIEW,),
}


def maximum_evidence_level(evidence: Iterable[Evidence]) -> OAKLevel:
    kinds = {item.kind for item in evidence}
    if EvidenceKind.INDEPENDENT_REVIEW in kinds and EvidenceKind.FORMAL_PROOF in kinds:
        return OAKLevel.INDEPENDENTLY_REVIEWED
    if EvidenceKind.FORMAL_PROOF in kinds:
        return OAKLevel.FORMALIZED
    if EvidenceKind.MANUSCRIPT_PROOF in kinds:
        return OAKLevel.GENERAL_MANUSCRIPT
    if EvidenceKind.RESTRICTED_PROOF in kinds:
        return OAKLevel.RESTRICTED_PROOF
    if EvidenceKind.NUMERICAL in kinds:
        return OAKLevel.NUMERICALLY_TESTED
    if EvidenceKind.SOURCE in kinds or EvidenceKind.SYMBOLIC in kinds:
        return OAKLevel.KNOWN_CASES
    return OAKLevel.WELL_TYPED


def evaluate_claim(
    claim: Claim,
    evidence_by_id: Mapping[str, Evidence],
    *,
    requested_level: OAKLevel | None = None,
    dependency_levels: Mapping[str, OAKLevel] | None = None,
) -> OAKDecision:
    blockers: list[str] = []
    warnings: list[str] = []
    dependency_levels = dependency_levels or {}

    claim_errors = claim.validate()
    blockers.extend(claim_errors)

    evidence: list[Evidence] = []
    for evidence_id in claim.evidence_ids:
        item = evidence_by_id.get(evidence_id)
        if item is None:
            blockers.append(f"missing evidence: {evidence_id}")
            continue
        errors = item.validate()
        blockers.extend(f"evidence {evidence_id}: {error}" for error in errors)
        evidence.append(item)

    missing_dependencies = [dep for dep in claim.dependencies if dep not in dependency_levels]
    blockers.extend(f"missing dependency status: {dep}" for dep in missing_dependencies)

    weakest_dependency = min(
        (dependency_levels[dep] for dep in claim.dependencies if dep in dependency_levels),
        default=OAKLevel.INDEPENDENTLY_REVIEWED,
    )
    evidence_limit = maximum_evidence_level(evidence)
    maximum = min(evidence_limit, weakest_dependency)
    if not claim.dependencies:
        maximum = evidence_limit

    if claim.kind == ClaimKind.SOLUTION_CLAIM:
        if EvidenceKind.FORMAL_PROOF not in {item.kind for item in evidence}:
            blockers.append("solution claim requires a formal proof certificate before OAK-6")
            maximum = min(maximum, OAKLevel.GENERAL_MANUSCRIPT)
        if EvidenceKind.INDEPENDENT_REVIEW not in {item.kind for item in evidence}:
            warnings.append("solution claim has no independent-review evidence")

    if claim.kind == ClaimKind.COMPUTATION and maximum > OAKLevel.NUMERICALLY_TESTED:
        maximum = OAKLevel.NUMERICALLY_TESTED
        warnings.append("a computation cannot self-promote into a proof")

    requested = requested_level if requested_level is not None else claim.oak_level
    if requested > maximum:
        blockers.append(f"requested OAK-{int(requested)} exceeds evidence/dependency limit OAK-{int(maximum)}")

    counts = Counter(item.kind.value for item in evidence)
    return OAKDecision(
        claim_id=claim.claim_id,
        current_level=claim.oak_level,
        maximum_allowed_level=maximum,
        accepted=not blockers and requested <= maximum,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        evidence_summary=dict(sorted(counts.items())),
    )


def required_evidence_for(level: OAKLevel) -> tuple[EvidenceKind, ...]:
    return _LEVEL_REQUIREMENTS[level]
