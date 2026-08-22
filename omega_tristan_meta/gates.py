from dataclasses import dataclass, asdict
from typing import Iterable, Sequence
from .models import Claim, Evidence

@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    reason: str

    def to_dict(self):
        return asdict(self)

def claim_scope_gate(claim: Claim, evidence: Sequence[Evidence]) -> GateResult:
    linked = [e for e in evidence if e.id in claim.evidence_ids]
    if not linked:
        return GateResult("claim_scope", False, "claim has no linked evidence")
    supported_scope = max(e.scope for e in linked)
    passed = claim.scope <= supported_scope
    return GateResult("claim_scope", passed, f"claim_scope={claim.scope:.3f}; max_evidence_scope={supported_scope:.3f}")

def role_separation_gate(generator_role: str, judge_role: str) -> GateResult:
    passed = generator_role != judge_role
    return GateResult("generator_judge_separation", passed, "Generator and Judge are distinct" if passed else "Generator cannot be its own Judge")

def meta_stop_gate(verified_gain: float, complexity_debt: float, risk_debt: float = 0.0, compute_debt: float = 0.0) -> GateResult:
    debt = complexity_debt + risk_debt + compute_debt
    passed = verified_gain > debt
    return GateResult("meta_stop", passed, f"verified_gain={verified_gain:.3f}; debt={debt:.3f}")

def persistent_structure_gate(persistent_structure: float, verified_necessary_structure: float) -> GateResult:
    passed = persistent_structure <= verified_necessary_structure
    return GateResult("persistent_structure", passed, f"persistent={persistent_structure:.3f}; necessary={verified_necessary_structure:.3f}")

def hard_gate_all(results: Iterable[GateResult]) -> GateResult:
    results = list(results)
    failures = [r.name for r in results if not r.passed]
    return GateResult("hard_gate_all", not failures, "PASS" if not failures else "FAIL: " + ", ".join(failures))
