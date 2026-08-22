from __future__ import annotations

import hashlib
import json
from typing import Dict, Iterable, List, Sequence, Tuple

from .gates import all_pass, evaluate_hard_gates
from .models import Decision, Evaluation, MactReceipt, TransformationCandidate, VerificationContract


DEFAULT_WEIGHTS: Dict[str, float] = {
    "action": 1.0,
    "compute": 1.0,
    "memory_persistent": 1.0,
    "observation": 1.0,
    "human_attention": 2.0,
    "time": 1.0,
    "persistent_complexity": 2.0,
    "risk": 4.0,
    "irreversibility": 5.0,
}


def pareto_front(candidates: Sequence[TransformationCandidate]) -> List[TransformationCandidate]:
    front: List[TransformationCandidate] = []
    for candidate in candidates:
        if any(other.resources.dominates(candidate.resources) for other in candidates if other.id != candidate.id):
            continue
        front.append(candidate)
    return sorted(front, key=lambda c: c.id)


def future_adjusted_cost(candidate: TransformationCandidate, weights: Dict[str, float]) -> float:
    immediate = candidate.resources.weighted_cost(weights)
    leverage = max(0.0, candidate.expected_future_work_avoided)
    verified_gain = max(0.0, candidate.expected_verified_gain)
    return immediate / (1.0 + leverage + verified_gain)


class MactCompiler:
    """Bounded least-transformation compiler.

    The compiler ranks only candidates that first satisfy non-compensatory gates.
    It does not execute external actions and never auto-promotes generated plans.
    """

    mandatory_candidates: Tuple[str, ...] = ("NO_ACTION", "WAIT", "REUSE")

    def __init__(self, weights: Dict[str, float] | None = None) -> None:
        self.weights = dict(DEFAULT_WEIGHTS if weights is None else weights)

    def ensure_anti_candidates(self, candidates: Iterable[TransformationCandidate]) -> None:
        ops = {c.operation.upper() for c in candidates}
        missing = [op for op in self.mandatory_candidates if op not in ops]
        if missing:
            raise ValueError(f"missing mandatory anti-candidates: {', '.join(missing)}")

    def evaluate(self, candidates: Sequence[TransformationCandidate], contract: VerificationContract) -> List[Evaluation]:
        self.ensure_anti_candidates(candidates)
        front_ids = {c.id for c in pareto_front(candidates)}
        out: List[Evaluation] = []
        for candidate in candidates:
            gates = evaluate_hard_gates(candidate, contract)
            hard_pass = all_pass(gates)
            if hard_pass:
                decision = Decision.ELIGIBLE
            elif any(g.name in {"authority", "evidence", "rollback"} and not g.passed for g in gates):
                decision = Decision.HOLD
            else:
                decision = Decision.REJECT
            out.append(Evaluation(candidate_id=candidate.id, decision=decision, gates=gates, scalar_cost=future_adjusted_cost(candidate, self.weights), pareto_dominated=candidate.id not in front_ids))
        return sorted(out, key=lambda e: (e.decision != Decision.ELIGIBLE, e.pareto_dominated, e.scalar_cost, e.candidate_id))

    def select(self, candidates: Sequence[TransformationCandidate], contract: VerificationContract) -> TransformationCandidate | None:
        evaluations = self.evaluate(candidates, contract)
        by_id = {c.id: c for c in candidates}
        eligible = [e for e in evaluations if e.decision == Decision.ELIGIBLE and not e.pareto_dominated]
        return by_id[eligible[0].candidate_id] if eligible else None

    def receipt(self, candidate: TransformationCandidate, evaluation: Evaluation, input_state_ref: str, output_state_ref: str, provenance: str) -> MactReceipt:
        payload = {"candidate": candidate.id, "operation": candidate.operation, "input": input_state_ref, "output": output_state_ref, "resources": candidate.resources.as_dict(), "evidence": [e.id for e in candidate.evidence], "decision": evaluation.decision.value, "provenance": provenance}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:20]
        return MactReceipt(id=f"mact-{digest}", candidate_id=candidate.id, operation=candidate.operation, input_state_ref=input_state_ref, output_state_ref=output_state_ref, resources=candidate.resources, evidence_ids=[e.id for e in candidate.evidence], gate_results=evaluation.gates, decision=evaluation.decision, provenance=provenance, rollback=candidate.rollback, external_action_performed=False, auto_promoted=False)
