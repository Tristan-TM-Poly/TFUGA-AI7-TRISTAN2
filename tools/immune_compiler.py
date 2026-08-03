"""Immune compiler for Tristan AIT actions.

Compiles an intended action into an Action Immune Packet (AIP): goal, risk
signals, canaries, M- matches, risk debt, privacy status, rollback status, and a
safe next action. This is a governance helper, not a substitute for qualified
medical/legal/financial/security review.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from tools.ait_action_autonomy_gate import AutonomyDecision, RiskDomain, decide_action_autonomy
from tools.risk_debt_ledger import RiskDebtReport, assess_risk_debt


class OakStatus(StrEnum):
    PASS = "pass"
    SLOW_MAX = "slow_max"
    DRY_RUN = "dry_run"
    ONE_TOUCH = "one_touch"
    NO_TOUCH = "no_touch"


@dataclass(frozen=True)
class RollbackProof:
    exists: bool
    tested: bool
    summary: str = ""

    @property
    def sufficient_for_zero_touch(self) -> bool:
        return self.exists and self.tested


@dataclass(frozen=True)
class ActionImmunePacket:
    goal: str
    expected_benefit: str
    risk_domains: tuple[str, ...]
    oak_status: OakStatus
    m_minus_matches: tuple[str, ...]
    canaries: tuple[str, ...]
    tests_required: tuple[str, ...]
    rollback_proof: RollbackProof
    privacy_status: str
    risk_debt: RiskDebtReport
    autonomy_decision: AutonomyDecision
    safe_next_action: str


CANARY_TERMS = {
    "guaranteed": "overconfidence_guarantee",
    "zero risk": "overconfidence_zero_risk",
    "delete": "destructive_action",
    "publish": "public_side_effect",
    "secret": "possible_secret_leak",
    "medical": "medical_domain",
    "dose": "medical_or_pharma_domain",
    "urgent": "time_pressure",
    "no tests": "missing_tests",
    "unlimited": "runaway_language",
    "autonomous": "autonomy_pressure",
}

M_MINUS_PATTERNS = {
    "no tests": "vitesse sans vérification = illusion",
    "guaranteed": "claim trop fort sans OAK",
    "zero risk": "zéro risque = surconfiance",
    "dose": "pas d’optimisation de substance",
    "medical": "IA ≠ médecin",
    "delete": "irréversible = pas de zéro-touch",
    "publish": "public ≠ privé",
    "secret": "SecretsGate requis",
}


def detect_canaries(text: str) -> tuple[str, ...]:
    normalized = text.lower()
    return tuple(label for term, label in CANARY_TERMS.items() if term in normalized)


def detect_m_minus(text: str) -> tuple[str, ...]:
    normalized = text.lower()
    return tuple(rule for term, rule in M_MINUS_PATTERNS.items() if term in normalized)


def compile_action_immune_packet(
    *,
    goal: str,
    expected_benefit: str,
    risk_domains: tuple[RiskDomain | str, ...],
    action_text: str,
    rollback: RollbackProof | None = None,
    missing_tests: bool = False,
    weak_sources: bool = False,
    sensitive_data_unclear: bool = False,
    irreversible_or_public_side_effect: bool = False,
    claim_too_strong: bool = False,
    uncertainty_unquantified: bool = False,
) -> ActionImmunePacket:
    """Compile an intended action into a conservative Action Immune Packet."""

    rollback = rollback or RollbackProof(exists=False, tested=False, summary="No rollback proof provided.")
    canaries = detect_canaries(action_text)
    m_minus = detect_m_minus(action_text)

    risk_debt = assess_risk_debt(
        missing_tests=missing_tests or ("missing_tests" in canaries),
        weak_sources=weak_sources,
        no_rollback=not rollback.sufficient_for_zero_touch,
        sensitive_data_unclear=sensitive_data_unclear,
        irreversible_or_public_side_effect=irreversible_or_public_side_effect,
        claim_too_strong=claim_too_strong or ("overconfidence_guarantee" in canaries or "overconfidence_zero_risk" in canaries),
        uncertainty_unquantified=uncertainty_unquantified,
    )

    autonomy = decide_action_autonomy(
        risk_domains,
        irreversible=irreversible_or_public_side_effect,
        public_side_effect=irreversible_or_public_side_effect,
    )

    if autonomy.mode == "NO-TOUCH":
        oak_status = OakStatus.NO_TOUCH
        safe_next = "Block execution; explain safely; route to qualified human review or emergency help if relevant."
    elif autonomy.mode == "ONE-TOUCH":
        oak_status = OakStatus.ONE_TOUCH
        safe_next = "Prepare draft/simulation and request explicit validation before action."
    elif risk_debt.blocks_zero_touch or canaries:
        oak_status = OakStatus.SLOW_MAX
        safe_next = "Continue only with added tests, sources, rollback proof, privacy check, and review."
    else:
        oak_status = OakStatus.PASS
        safe_next = "Proceed with reversible low-risk artifact, branch, or draft PR."

    tests_required = []
    if missing_tests or risk_debt.blocks_zero_touch:
        tests_required.append("add_minimal_regression_or_safety_tests")
    if weak_sources:
        tests_required.append("add_source_trust_evidence")
    if not rollback.sufficient_for_zero_touch:
        tests_required.append("add_and_test_rollback_proof")
    if sensitive_data_unclear:
        tests_required.append("run_privacy_gate")

    privacy_status = "needs_review" if sensitive_data_unclear else "generic_or_scrubbed"

    return ActionImmunePacket(
        goal=goal,
        expected_benefit=expected_benefit,
        risk_domains=tuple(str(domain) for domain in risk_domains),
        oak_status=oak_status,
        m_minus_matches=m_minus,
        canaries=canaries,
        tests_required=tuple(tests_required),
        rollback_proof=rollback,
        privacy_status=privacy_status,
        risk_debt=risk_debt,
        autonomy_decision=autonomy,
        safe_next_action=safe_next,
    )
