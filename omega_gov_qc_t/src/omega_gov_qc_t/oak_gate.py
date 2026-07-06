"""OAKGate for public-sector use cases.

The evaluator is intentionally conservative. It blocks deployment when a use
case touches sensitive decisions without explicit human authority, unauthorized
sources, or unmanaged privacy/security risks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    reason: str

    def to_dict(self) -> Dict[str, object]:
        return {"name": self.name, "passed": self.passed, "reason": self.reason}


@dataclass(frozen=True)
class OAKReport:
    use_case: str
    deployable: bool
    gates: List[GateResult] = field(default_factory=list)
    classification: str = "signal_or_analysis_only"
    warning: str = "Signal ≠ preuve ≠ verdict ≠ décision publique finale."

    def failures(self) -> List[GateResult]:
        return [gate for gate in self.gates if not gate.passed]

    def to_dict(self) -> Dict[str, object]:
        return {
            "use_case": self.use_case,
            "deployable": self.deployable,
            "classification": self.classification,
            "warning": self.warning,
            "gates": [gate.to_dict() for gate in self.gates],
            "failures": [gate.to_dict() for gate in self.failures()],
        }


class OAKGate:
    """Conservative public-sector gate evaluator."""

    SENSITIVE_DOMAINS = {
        "health",
        "justice",
        "police",
        "tax",
        "benefits",
        "education_decision",
        "employment",
        "child_protection",
        "housing_eligibility",
        "immigration",
    }

    def evaluate_context(
        self,
        *,
        use_case: str,
        contains_personal_data: bool,
        makes_sensitive_decision: bool,
        source_is_authorized: bool,
        human_review_required: bool,
        domain: str = "open_government",
        security_controls_present: bool = True,
        explains_sources: bool = True,
        fairness_review_done: bool = False,
        utility_metric_defined: bool = True,
    ) -> OAKReport:
        domain_is_sensitive = domain in self.SENSITIVE_DOMAINS

        gates = [
            GateResult(
                "LegalGate",
                source_is_authorized,
                "Sources are authorized" if source_is_authorized else "Unauthorized or unclear source",
            ),
            GateResult(
                "PrivacyGate",
                not contains_personal_data or human_review_required,
                "No personal data or human-reviewed privacy path"
                if (not contains_personal_data or human_review_required)
                else "Personal data requires explicit privacy review and authority",
            ),
            GateResult(
                "SecurityGate",
                security_controls_present,
                "Security controls present" if security_controls_present else "Missing security controls",
            ),
            GateResult(
                "FairnessGate",
                (not domain_is_sensitive) or fairness_review_done,
                "Fairness review not required for low-risk open analysis"
                if not domain_is_sensitive
                else (
                    "Fairness review done" if fairness_review_done else "Sensitive domain requires fairness review"
                ),
            ),
            GateResult(
                "ExplainabilityGate",
                explains_sources,
                "Sources and reasoning are explainable" if explains_sources else "Sources are not explainable",
            ),
            GateResult(
                "HumanAuthorityGate",
                (not makes_sensitive_decision) and (not domain_is_sensitive or human_review_required),
                "No autonomous sensitive decision"
                if ((not makes_sensitive_decision) and (not domain_is_sensitive or human_review_required))
                else "Sensitive public decisions require human authority",
            ),
            GateResult(
                "EvidenceGate",
                source_is_authorized and explains_sources,
                "Evidence path is traceable" if (source_is_authorized and explains_sources) else "Evidence path incomplete",
            ),
            GateResult(
                "RobustnessGate",
                True,
                "Prototype gate: requires tests before production promotion",
            ),
            GateResult(
                "UtilityGate",
                utility_metric_defined,
                "Utility metric defined" if utility_metric_defined else "No measurable public utility metric",
            ),
        ]

        deployable = all(gate.passed for gate in gates)
        classification = "analysis_deployable" if deployable else "blocked_or_requires_review"
        return OAKReport(
            use_case=use_case,
            deployable=deployable,
            gates=gates,
            classification=classification,
        )
