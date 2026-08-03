from __future__ import annotations
from dataclasses import dataclass, asdict
from .hashutil import sha256
from .models import Scenario

@dataclass(frozen=True)
class CausalHypothesis:
    hypothesis_id: str
    causes: tuple[str,...]
    outcome: str
    support: tuple[str,...]
    alternatives: tuple[str,...]
    tests: tuple[str,...]
    status: str="hypothesis_not_proof"
    def to_dict(self): return asdict(self)

def build_outage_hypotheses(s: Scenario) -> tuple[CausalHypothesis,...]:
    candidates=[]
    if s.ice_severity>0.3: candidates.append("ice loading")
    if s.wind_severity>0.3: candidates.append("wind exposure")
    if s.logistics_delay>0.3: candidates.append("repair logistics delay")
    candidates.extend(("synthetic corridor exposure","demand stress"))
    return (
        CausalHypothesis("cause-compound-hazard",tuple(candidates),"unserved energy",("scenario parameters","simulation receipts"),("generation adequacy dominates","topological fragmentation dominates"),("ablation by hazard","compare matched random seeds")),
        CausalHypothesis("cause-restoration",("failed corridor count","repair-hour fixture","workforce availability","logistics delay"),"restoration duration",("deterministic restoration model",),("communications or spare-parts effects omitted",),("sensitivity sweep","external authorized validation")),
    )
