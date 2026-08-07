"""Constitution, kernels and context-dependent weights for Ω-VALUE-OS-T∞."""
from __future__ import annotations

from .models import ContextProfile, ValueDimension


CONSTITUTION = (
    {
        "article": "I — Integrity",
        "rule": "claim_strength_must_not_exceed_evidence_strength",
        "non_compensable": True,
    },
    {
        "article": "II — Traceability",
        "rule": "important_claims_require_critical_provenance",
        "non_compensable": True,
    },
    {
        "article": "III — Falsifiability",
        "rule": "research_claims_should_expose_falsifiers_and_assumptions",
        "non_compensable": False,
    },
    {
        "article": "IV — Safety",
        "rule": "safety_legality_consent_are_hard_gates",
        "non_compensable": True,
    },
    {
        "article": "V — Sovereignty",
        "rule": "automation_capability_never_implies_automation_authority",
        "non_compensable": True,
    },
    {
        "article": "VI — Crystallization",
        "rule": "expansion_should_converge_toward_a_closed_testable_artifact",
        "non_compensable": False,
    },
    {
        "article": "VII — Reality",
        "rule": "stronger_external_claims_require_stronger_external_evidence",
        "non_compensable": False,
    },
)


KERNELS = {
    "truth": ("truth", "evidence", "falsifiability", "uncertainty", "claim_ceiling"),
    "memory": ("provenance", "replay", "m_plus", "m_minus", "version_time"),
    "representation": ("rpu", "hgfm", "cvcd", "multiscale", "invariants"),
    "creation": ("generativity", "diversity", "synergy", "compounding"),
    "crystallization": ("closure", "wip", "simplicity", "maintainability"),
    "action": ("safety", "sovereignty", "least_privilege", "reversibility"),
    "reality": ("utility", "external_proof", "distribution", "venture", "value"),
}


D = ValueDimension

CONTEXT_PROFILES = {
    "research": ContextProfile(
        name="research",
        weights={
            D.TRUTH.value: 2.0,
            D.EVIDENCE.value: 2.0,
            D.FERTILITY.value: 1.0,
            D.LEARNING.value: 1.2,
            D.CRYSTALLIZATION.value: 1.0,
            D.SOVEREIGNTY.value: 0.8,
            D.UTILITY.value: 0.7,
            D.PROTECTION.value: 0.6,
            D.GENERATIVITY.value: 0.8,
            D.EXTERNAL_VALUE.value: 0.5,
            D.SIMPLICITY.value: 0.8,
            D.TESTABILITY.value: 1.8,
            D.MAINTAINABILITY.value: 0.6,
            D.REUSE.value: 0.7,
        },
        evidence_floor=0.40,
        human_review_external_evidence_floor=2,
        human_review_closure_floor=0.70,
    ),
    "software": ContextProfile(
        name="software",
        weights={
            D.TRUTH.value: 1.2,
            D.EVIDENCE.value: 1.5,
            D.FERTILITY.value: 0.6,
            D.LEARNING.value: 0.8,
            D.CRYSTALLIZATION.value: 1.8,
            D.SOVEREIGNTY.value: 1.1,
            D.UTILITY.value: 1.4,
            D.PROTECTION.value: 0.8,
            D.GENERATIVITY.value: 0.7,
            D.EXTERNAL_VALUE.value: 0.8,
            D.SIMPLICITY.value: 1.3,
            D.TESTABILITY.value: 1.6,
            D.MAINTAINABILITY.value: 1.7,
            D.REUSE.value: 1.4,
        },
        evidence_floor=0.35,
        human_review_external_evidence_floor=2,
        human_review_closure_floor=0.80,
    ),
    "venture": ContextProfile(
        name="venture",
        weights={
            D.TRUTH.value: 1.0,
            D.EVIDENCE.value: 1.3,
            D.FERTILITY.value: 0.7,
            D.LEARNING.value: 1.0,
            D.CRYSTALLIZATION.value: 1.5,
            D.SOVEREIGNTY.value: 0.9,
            D.UTILITY.value: 1.8,
            D.PROTECTION.value: 1.3,
            D.GENERATIVITY.value: 0.8,
            D.EXTERNAL_VALUE.value: 2.0,
            D.SIMPLICITY.value: 1.1,
            D.TESTABILITY.value: 1.4,
            D.MAINTAINABILITY.value: 0.9,
            D.REUSE.value: 1.2,
        },
        evidence_floor=0.30,
        human_review_external_evidence_floor=3,
        human_review_closure_floor=0.70,
    ),
    "high_consequence": ContextProfile(
        name="high_consequence",
        weights={
            D.TRUTH.value: 2.0,
            D.EVIDENCE.value: 2.0,
            D.FERTILITY.value: 0.3,
            D.LEARNING.value: 0.5,
            D.CRYSTALLIZATION.value: 1.0,
            D.SOVEREIGNTY.value: 2.0,
            D.UTILITY.value: 0.8,
            D.PROTECTION.value: 1.5,
            D.GENERATIVITY.value: 0.3,
            D.EXTERNAL_VALUE.value: 0.4,
            D.SIMPLICITY.value: 1.0,
            D.TESTABILITY.value: 1.8,
            D.MAINTAINABILITY.value: 1.3,
            D.REUSE.value: 0.5,
        },
        evidence_floor=0.65,
        human_review_external_evidence_floor=4,
        human_review_closure_floor=0.90,
    ),
}


def constitution_payload() -> dict:
    return {
        "system": "Ω-VALUE-OS-T∞",
        "version": "R0.1",
        "articles": list(CONSTITUTION),
        "kernels": {key: list(value) for key, value in KERNELS.items()},
        "profiles": {
            key: {
                "weights": dict(sorted(profile.weights.items())),
                "evidence_floor": profile.evidence_floor,
                "human_review_external_evidence_floor": profile.human_review_external_evidence_floor,
                "human_review_closure_floor": profile.human_review_closure_floor,
            }
            for key, profile in sorted(CONTEXT_PROFILES.items())
        },
        "authority": "review_only",
        "automatic_merge_allowed": False,
        "automatic_publication_allowed": False,
        "external_action_performed": False,
        "scores_are_probabilities": False,
    }
