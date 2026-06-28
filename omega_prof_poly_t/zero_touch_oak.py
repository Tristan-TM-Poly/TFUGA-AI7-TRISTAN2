"""Zero-touch OAK compiler for Omega-PROF-POLY-T.

OAK is treated as a compiler: it transforms an artifact into status,
evidence notes, risk notes, score, warnings, and a next machine action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Mapping, Tuple


class GateStatus(str, Enum):
    SAFE_EXECUTE = "safe_execute"
    AUTO_GENERATE_ONLY = "auto_generate_only"
    EXTERNAL_ACTION_LOCKED = "external_action_locked"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class BlockedActionPacket:
    status: str
    reason: str
    artifact_ready: bool
    next_machine_action: str


@dataclass(frozen=True)
class OAKCompileResult:
    artifact_name: str
    status: GateStatus
    score: float
    evidence_count: int
    risks: Dict[str, float]
    benefits: Dict[str, float]
    warnings: Tuple[str, ...] = field(default_factory=tuple)
    next_action: str = "generate_dct_packet"
    blocked_action: BlockedActionPacket | None = None


def clamp01(value: float) -> float:
    if value < 0:
        return 0.0
    if value > 1:
        return 1.0
    return float(value)


def mean_score(values: Mapping[str, float]) -> float:
    if not values:
        return 0.0
    return sum(clamp01(v) for v in values.values()) / len(values)


def compile_oak(
    artifact_name: str,
    benefits: Mapping[str, float],
    risks: Mapping[str, float],
    evidence_count: int = 0,
    external_action: bool = False,
) -> OAKCompileResult:
    """Compile an artifact into an automated OAK decision.

    The compiler never asks for manual checking as a normal step. It either
    continues, generates only inside the workspace, emits an external-action
    lock, or blocks high-risk action.
    """

    benefits_norm = {k: clamp01(v) for k, v in benefits.items()}
    risks_norm = {k: clamp01(v) for k, v in risks.items()}
    benefit_score = mean_score(benefits_norm)
    risk_score = mean_score(risks_norm)
    evidence_bonus = min(0.10, 0.025 * max(0, evidence_count))
    score = clamp01(benefit_score - 0.60 * risk_score + evidence_bonus)

    warnings = []
    if evidence_count == 0:
        warnings.append("no_evidence_attached")
    if risk_score >= 0.60:
        warnings.append("high_risk_requires_auto_gate")
    if risks_norm.get("overclaim", 0.0) >= 0.55:
        warnings.append("separate_claim_model_simulation_measurement")
    if risks_norm.get("confidentiality", 0.0) >= 0.55:
        warnings.append("run_ip_and_confidentiality_gate")
    if risks_norm.get("privacy", 0.0) >= 0.55:
        warnings.append("minimize_anonymize_aggregate_data")

    blocked_action = None
    if risk_score >= 0.82:
        status = GateStatus.BLOCKED
        next_action = "emit_blocked_action_packet"
        blocked_action = BlockedActionPacket(
            status="blocked_external_action",
            reason="risk_threshold_exceeded",
            artifact_ready=True,
            next_machine_action="reduce_risk_and_recompile_oak",
        )
    elif external_action:
        status = GateStatus.EXTERNAL_ACTION_LOCKED
        next_action = "emit_external_action_packet"
        blocked_action = BlockedActionPacket(
            status="blocked_external_action",
            reason="external_capability_required",
            artifact_ready=True,
            next_machine_action="execute_when_capability_available",
        )
    elif risk_score >= 0.45:
        status = GateStatus.AUTO_GENERATE_ONLY
        next_action = "generate_artifact_and_oak_report"
    else:
        status = GateStatus.SAFE_EXECUTE
        next_action = "generate_artifact_tests_and_report"

    return OAKCompileResult(
        artifact_name=artifact_name,
        status=status,
        score=round(score, 4),
        evidence_count=max(0, evidence_count),
        risks={k: round(v, 4) for k, v in risks_norm.items()},
        benefits={k: round(v, 4) for k, v in benefits_norm.items()},
        warnings=tuple(warnings),
        next_action=next_action,
        blocked_action=blocked_action,
    )
