from typing import List, Sequence
import hashlib, json, uuid

from .models import Claim, Evidence, Receipt, SystemGenome
from .gates import claim_scope_gate, role_separation_gate, meta_stop_gate, hard_gate_all

def compile_receipt(input_refs: List[str], transformation: str, output_refs: List[str], evidence_refs: List[str], uncertainty: float, authority: str, provenance: str, rollback: str) -> Receipt:
    payload = {"input_refs": input_refs, "transformation": transformation, "output_refs": output_refs, "evidence_refs": evidence_refs, "authority": authority, "provenance": provenance}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
    return Receipt(id=f"receipt-{digest}", input_refs=input_refs, transformation=transformation, output_refs=output_refs, evidence_refs=evidence_refs, uncertainty=uncertainty, authority=authority, provenance=provenance, rollback=rollback)

class MetaCompiler:
    """Reference kernel: propose candidates; independent hard gates decide promotion eligibility."""

    def evaluate_claim(self, claim: Claim, evidence: Sequence[Evidence]):
        return claim_scope_gate(claim, evidence)

    def evaluate_meta_layer(self, verified_gain: float, complexity_debt: float, risk_debt: float = 0.0, compute_debt: float = 0.0):
        return meta_stop_gate(verified_gain, complexity_debt, risk_debt, compute_debt)

    def promotion_gate(self, claim: Claim, evidence: Sequence[Evidence], generator_role: str, judge_role: str, verified_gain: float, complexity_debt: float, risk_debt: float = 0.0):
        return hard_gate_all([
            claim_scope_gate(claim, evidence),
            role_separation_gate(generator_role, judge_role),
            meta_stop_gate(verified_gain, complexity_debt, risk_debt),
        ])

    def compile_system_genome(self, goal: str, capabilities: List[str], evidence_ids: List[str], permissions: List[str]) -> SystemGenome:
        return SystemGenome(
            id=f"system-{uuid.uuid4().hex[:12]}",
            goal=goal,
            rules=["Generated != Verified", "Simulation != Reality", "Capability != Authority", "NO_ACTION is valid"],
            capabilities=list(capabilities), evidence=list(evidence_ids), permissions=list(permissions),
        )
