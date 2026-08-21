from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

from .core import EnvironmentalTransformationGenome, EvidenceStatus


@dataclass(frozen=True)
class OAKFinding:
    gate: str
    passed: bool
    message: str


@dataclass(frozen=True)
class OAKReport:
    transformation_id: str
    passed: bool
    findings: Sequence[OAKFinding]
    genome_digest: str
    report_digest: str


HIGH_CONFIDENCE_EVIDENCE = {
    EvidenceStatus.OBSERVED,
    EvidenceStatus.MEASURED,
    EvidenceStatus.PROVEN,
}


def _finding(gate: str, passed: bool, ok: str, fail: str) -> OAKFinding:
    return OAKFinding(gate=gate, passed=passed, message=ok if passed else fail)


def audit(genome: EnvironmentalTransformationGenome) -> OAKReport:
    findings: list[OAKFinding] = []

    evidence_complete = bool(genome.evidence) and all(e.complete() for e in genome.evidence)
    findings.append(_finding(
        "G0_EVIDENCE_CONTRACT",
        evidence_complete,
        "Every claim has boundary, baseline and falsifier.",
        "At least one claim lacks boundary, baseline/falsifier, or no evidence contract exists.",
    ))

    residuals_accounted = all(
        bool(r.origin.strip())
        and bool(r.transformation.strip())
        and bool(r.destination.strip())
        and bool(r.spatial_boundary.strip())
        and bool(r.temporal_boundary.strip())
        for r in genome.residuals
    )
    findings.append(_finding(
        "G1_RESIDUAL_ACCOUNTING",
        residuals_accounted,
        "Residual passports retain origin, transformation, destination, space and time.",
        "At least one residual disappears from the accounting boundary.",
    ))

    epistemic_boundary = not genome.simulation_claimed_as_reality
    findings.append(_finding(
        "G2_SIMULATION_NE_REALITY",
        epistemic_boundary,
        "Simulation is kept distinct from observed reality.",
        "A simulated result is being presented as observed reality.",
    ))

    semantic_boundary = not genome.compensation_claimed_as_restoration
    findings.append(_finding(
        "G3_COMPENSATION_NE_RESTORATION",
        semantic_boundary,
        "Compensation is not silently promoted to restoration.",
        "Compensation is being treated as restoration without an equivalence proof.",
    ))

    has_high_confidence = any(
        e.status in HIGH_CONFIDENCE_EVIDENCE and bool(e.sources)
        for e in genome.evidence
    )
    irreversible_gate = (
        genome.reversibility >= 0.25
        or (genome.authority_confirmed and has_high_confidence)
    )
    findings.append(_finding(
        "G4_IRREVERSIBILITY_AUTHORITY_EVIDENCE",
        irreversible_gate,
        "High-irreversibility action has the required authority/evidence gate or is sufficiently reversible.",
        "High-irreversibility action lacks confirmed authority and high-confidence evidence.",
    ))

    scale_boundary = (
        bool(genome.local_scope.strip())
        and bool(genome.global_scope.strip())
        and genome.local_scope.strip() != genome.global_scope.strip()
    )
    findings.append(_finding(
        "G5_LOCAL_NE_GLOBAL",
        scale_boundary,
        "Local and broader accounting boundaries are explicit and distinct.",
        "Local success could be mistaken for global success because scope boundaries are collapsed.",
    ))

    needs_monitoring = bool(genome.residuals) or genome.reversibility < 1.0
    monitoring_gate = (not needs_monitoring) or genome.monitoring_required
    findings.append(_finding(
        "G6_MONITORING",
        monitoring_gate,
        "Monitoring is required for residual-bearing or non-perfectly-reversible change.",
        "Residual-bearing/non-perfectly-reversible intervention has no monitoring requirement.",
    ))

    affected_gate = bool(genome.affected_entities)
    findings.append(_finding(
        "G7_AFFECTED_ENTITIES",
        affected_gate,
        "Affected entities are explicitly represented.",
        "No affected entities are represented.",
    ))

    passed = all(f.passed for f in findings)
    payload = {
        "transformation_id": genome.transformation_id,
        "passed": passed,
        "genome_digest": genome.digest(),
        "findings": [f.__dict__ for f in findings],
    }
    report_digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return OAKReport(
        transformation_id=genome.transformation_id,
        passed=passed,
        findings=tuple(findings),
        genome_digest=genome.digest(),
        report_digest=report_digest,
    )
