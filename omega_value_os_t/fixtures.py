"""Deterministic demonstration fixtures for Ω-VALUE-OS-T∞."""
from __future__ import annotations

from .models import AutonomyLevel, EvidenceLevel, ValueCase


_ALL_GATES = {
    "integrity": True,
    "safety": True,
    "legality": True,
    "consent": True,
    "critical_provenance": True,
}


def _dims(**updates: float) -> dict[str, float]:
    base = {
        "truth": 0.75,
        "evidence": 0.70,
        "fertility": 0.75,
        "learning": 0.80,
        "crystallization": 0.65,
        "sovereignty": 0.90,
        "utility": 0.70,
        "protection": 0.75,
        "generativity": 0.70,
        "external_value": 0.50,
        "simplicity": 0.70,
        "testability": 0.85,
        "maintainability": 0.70,
        "reuse": 0.75,
    }
    base.update(updates)
    return base


def demo_cases() -> tuple[ValueCase, ...]:
    return (
        ValueCase(
            case_id="software.crystallized",
            title="Crystallized OAK-safe software kernel",
            profile="software",
            hard_gates=_ALL_GATES,
            dimensions=_dims(crystallization=0.92, evidence=0.86, maintainability=0.88, testability=0.93),
            debts={"crystallization": 0.03, "confidence": 0.04, "technical": 0.05, "risk": 0.02},
            evidence_level=EvidenceLevel.E2_INDEPENDENT_BENCHMARK,
            evidence_strength=0.88,
            claim_strength=0.55,
            closure=0.93,
            reuse=0.82,
            uncertainty=0.18,
            reversibility=1.0,
            autonomy_level=AutonomyLevel.A2_DRAFT,
            expected_action_value=0.70,
            expected_information_value=0.35,
            provenance_refs=("fixture://software.crystallized",),
            falsifiers=("focused tests fail", "clean-room replay diverges"),
            assumptions=("fixture scores are governance inputs, not measured universal values",),
        ),
        ValueCase(
            case_id="research.fertile",
            title="Fertile but under-evidenced research hypothesis",
            profile="research",
            hard_gates=_ALL_GATES,
            dimensions=_dims(fertility=0.96, generativity=0.94, evidence=0.28, crystallization=0.35),
            debts={"crystallization": 0.45, "confidence": 0.12, "technical": 0.05, "risk": 0.02},
            evidence_level=EvidenceLevel.E0_SELF_EVALUATION,
            evidence_strength=0.30,
            claim_strength=0.18,
            closure=0.30,
            reuse=0.65,
            uncertainty=0.72,
            expected_action_value=0.20,
            expected_information_value=0.85,
            provenance_refs=("fixture://research.fertile",),
            falsifiers=("baseline matches or exceeds predicted effect",),
            assumptions=("hypothesis is exploratory",),
        ),
        ValueCase(
            case_id="action.unsafe",
            title="High-value action with a failed safety gate",
            profile="high_consequence",
            hard_gates={**_ALL_GATES, "safety": False},
            dimensions=_dims(utility=0.95, external_value=0.95),
            debts={"risk": 0.70},
            evidence_level=EvidenceLevel.E4_EXTERNAL_REPLICATION,
            evidence_strength=0.95,
            claim_strength=0.40,
            closure=0.95,
            reuse=0.80,
            uncertainty=0.10,
            reversibility=0.20,
            autonomy_level=AutonomyLevel.A5_HIGH_CONSEQUENCE,
            human_approval=False,
            expected_action_value=0.95,
            expected_information_value=0.10,
            provenance_refs=("fixture://action.unsafe",),
            falsifiers=("safety gate remains unresolved",),
            assumptions=("utility cannot compensate for safety failure",),
        ),
        ValueCase(
            case_id="claim.overreach",
            title="Overclaim relative to evidence",
            profile="research",
            hard_gates=_ALL_GATES,
            dimensions=_dims(truth=0.85, evidence=0.45),
            debts={"confidence": 0.60},
            evidence_level=EvidenceLevel.E1_AUTOMATED_TESTS,
            evidence_strength=0.45,
            claim_strength=0.90,
            closure=0.70,
            reuse=0.60,
            uncertainty=0.40,
            expected_action_value=0.40,
            expected_information_value=0.70,
            provenance_refs=("fixture://claim.overreach",),
            falsifiers=("independent replication contradicts claim",),
            assumptions=("automated tests alone do not justify a strong external claim",),
        ),
    )
