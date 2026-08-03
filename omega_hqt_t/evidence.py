from __future__ import annotations
from dataclasses import dataclass, asdict, field
from .hashutil import sha256
from .models import Evidence

@dataclass
class EvidenceLedger:
    records: list[Evidence]=field(default_factory=list)
    def append(self, evidence: Evidence) -> None:
        if any(x.evidence_id==evidence.evidence_id for x in self.records): raise ValueError("duplicate evidence id")
        self.records.append(evidence)
    def audit(self) -> dict:
        invalid=[e.evidence_id for e in self.records if not 0<=e.uncertainty<=1 or not e.source_ref or not e.observed_at]
        payload={"count":len(self.records),"invalid":invalid,"oak_statuses":sorted({e.oak_status for e in self.records}),"sensitivity_levels":sorted({e.sensitivity for e in self.records})}
        payload["ledger_hash"]=sha256([e.to_dict() for e in self.records]); payload["passed"]=not invalid
        return payload
