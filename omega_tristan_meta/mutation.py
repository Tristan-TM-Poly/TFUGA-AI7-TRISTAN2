from typing import Dict
from .models import Claim, Evidence
from .gates import claim_scope_gate, role_separation_gate

def invariant_mutation_probes() -> Dict[str, bool]:
    evidence = Evidence(id="E1", statement="bounded observation", scope=0.4, provenance="mutation-test", independent=True)
    overclaim = Claim(id="C1", statement="deliberately over-scoped claim", scope=0.9, epistemic_status="TEST", evidence_ids=["E1"], provenance="mutation-test")
    claim_detected = not claim_scope_gate(overclaim, [evidence]).passed
    role_detected = not role_separation_gate("same-agent", "same-agent").passed
    return {"claim_scope_mutation_detected": claim_detected, "generator_judge_mutation_detected": role_detected}
