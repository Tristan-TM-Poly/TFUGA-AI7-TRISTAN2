from __future__ import annotations

from typing import Iterable, List

from .models import GateResult, TransformationCandidate, VerificationContract


EXTERNAL_ACTIONS = {"ACT", "DEPLOY", "PURCHASE", "PUBLISH", "TRANSFER", "DELETE_EXTERNAL"}


def semantic_goal_gate(candidate: TransformationCandidate, contract: VerificationContract) -> GateResult:
    required = contract.required_semantic_effect
    ok = required is None or candidate.semantic_effect == required
    return GateResult("semantic_goal", ok, "target semantics satisfied" if ok else "candidate does not satisfy required semantic effect")


def role_separation_gate(candidate: TransformationCandidate) -> GateResult:
    ok = candidate.generator_role != candidate.judge_role
    return GateResult("generator_judge_separation", ok, "roles separated" if ok else "Generator == Judge")


def authority_gate(candidate: TransformationCandidate) -> GateResult:
    needs_authority = candidate.operation.upper() in EXTERNAL_ACTIONS
    ok = (not needs_authority) or candidate.authority_granted
    return GateResult("authority", ok, "authority sufficient" if ok else "external action lacks explicit authority")


def evidence_gate(candidate: TransformationCandidate, contract: VerificationContract) -> GateResult:
    scoped = [e for e in candidate.evidence if e.scope == contract.required_scope]
    enough = len(scoped) >= contract.min_evidence_count
    independent = (not contract.require_independent_verification) or any(e.independent for e in scoped)
    ok = enough and independent
    if not enough:
        reason = "insufficient evidence in required scope"
    elif not independent:
        reason = "independent verification missing"
    else:
        reason = "evidence contract satisfied"
    return GateResult("evidence", ok, reason)


def risk_gate(candidate: TransformationCandidate, contract: VerificationContract) -> GateResult:
    ok = candidate.resources.risk <= contract.max_risk
    return GateResult("risk", ok, "risk within envelope" if ok else "risk exceeds envelope")


def irreversibility_gate(candidate: TransformationCandidate, contract: VerificationContract) -> GateResult:
    ok = candidate.resources.irreversibility <= contract.max_irreversibility
    return GateResult("irreversibility", ok, "irreversibility within envelope" if ok else "irreversibility exceeds envelope")


def rollback_gate(candidate: TransformationCandidate, contract: VerificationContract) -> GateResult:
    required = contract.require_rollback_if_reversible and candidate.resources.irreversibility < 1.0 and candidate.operation.upper() not in {"NO_ACTION", "WAIT", "OBSERVE"}
    ok = (not required) or bool(candidate.rollback)
    return GateResult("rollback", ok, "rollback contract satisfied" if ok else "rollback missing")


def no_epistemic_inflation_gate(candidate: TransformationCandidate) -> GateResult:
    bad = candidate.operation.upper() == "PROMOTE_SIMULATION_TO_REALITY"
    return GateResult("epistemic_boundary", not bad, "Simulation != Reality" if not bad else "forbidden epistemic promotion")


def evaluate_hard_gates(candidate: TransformationCandidate, contract: VerificationContract) -> List[GateResult]:
    return [semantic_goal_gate(candidate, contract), role_separation_gate(candidate), authority_gate(candidate), evidence_gate(candidate, contract), risk_gate(candidate, contract), irreversibility_gate(candidate, contract), rollback_gate(candidate, contract), no_epistemic_inflation_gate(candidate)]


def meta_stop_gate(expected_savings: float, optimization_cost: float, complexity_debt: float = 0.0, risk_debt: float = 0.0, margin: float = 0.0) -> GateResult:
    benefit = max(0.0, expected_savings)
    burden = max(0.0, optimization_cost) + max(0.0, complexity_debt) + max(0.0, risk_debt) + max(0.0, margin)
    ok = benefit > burden
    return GateResult("meta_stop", ok, "optimizer earns its complexity rent" if ok else "expected savings do not exceed optimization burden")


def all_pass(gates: Iterable[GateResult]) -> bool:
    return all(g.passed for g in gates)
