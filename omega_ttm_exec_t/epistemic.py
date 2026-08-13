from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

class EpistemicStatus(str, Enum):
    CANDIDATE="candidate"; FERTILE="fertile"; TESTED="tested"; COMPARED="compared"
    REPLICATED="replicated"; CERTIFIED="certified"; REJECTED="rejected"

class EvidenceClass(str, Enum):
    NONE="none"; ASSERTION="assertion"; SIMULATION="simulation"; SOFTWARE_TEST="software_test"
    BENCHMARK="benchmark"; EMPIRICAL_MEASUREMENT="empirical_measurement"
    FORMAL_PROOF="formal_proof"; EXTERNAL_REPLICATION="external_replication"

@dataclass(frozen=True)
class Claim:
    statement: str
    domain: str
    status: EpistemicStatus=EpistemicStatus.CANDIDATE
    evidence_class: EvidenceClass=EvidenceClass.NONE
    uncertainty: float=1.0
    validity_region: str="unspecified"
    baseline_id: str|None=None
    source: str|None=None
    external_world: bool=False
    def to_dict(self)->dict[str,Any]:
        d=asdict(self); d["status"]=self.status.value; d["evidence_class"]=self.evidence_class.value; return d

@dataclass(frozen=True)
class OAKDecision:
    accepted: bool
    promoted_status: EpistemicStatus
    reason: str
    def to_dict(self)->dict[str,Any]:
        return {"accepted":self.accepted,"promoted_status":self.promoted_status.value,"reason":self.reason}

def evaluate_claim(c: Claim)->OAKDecision:
    if not 0 <= c.uncertainty <= 1:
        return OAKDecision(False,EpistemicStatus.REJECTED,"uncertainty_out_of_range")
    if c.evidence_class is EvidenceClass.NONE and c.status not in {EpistemicStatus.CANDIDATE,EpistemicStatus.FERTILE}:
        return OAKDecision(False,EpistemicStatus.CANDIDATE,"status_exceeds_evidence")
    if c.status is EpistemicStatus.COMPARED:
        if c.evidence_class is not EvidenceClass.BENCHMARK:
            return OAKDecision(False,EpistemicStatus.TESTED,"compared_requires_benchmark_evidence")
        if not c.baseline_id:
            return OAKDecision(False,EpistemicStatus.TESTED,"comparison_without_declared_baseline")
    if c.status is EpistemicStatus.REPLICATED and c.evidence_class is not EvidenceClass.EXTERNAL_REPLICATION:
        return OAKDecision(False,EpistemicStatus.COMPARED,"replicated_requires_external_replication")
    if c.external_world and c.status in {EpistemicStatus.REPLICATED,EpistemicStatus.CERTIFIED}:
        if c.evidence_class is EvidenceClass.SIMULATION:
            return OAKDecision(False,EpistemicStatus.TESTED,"simulation_cannot_certify_external_world_claim")
        if c.evidence_class is EvidenceClass.FORMAL_PROOF and c.validity_region != "formal_model":
            return OAKDecision(False,EpistemicStatus.TESTED,"formal_proof_does_not_certify_external_world_claim")
    return OAKDecision(True,c.status,"oak_type_pass")
