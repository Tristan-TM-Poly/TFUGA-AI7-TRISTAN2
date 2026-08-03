from __future__ import annotations
from dataclasses import dataclass, asdict
from statistics import mean
from .models import WorldOutcome

@dataclass(frozen=True)
class CVCDSummary:
    count: int
    mean_unserved_energy_mwh: float
    p95_unserved_energy_mwh: float
    worst_unserved_energy_mwh: float
    mean_restoration_hours: float
    mean_resilience_score: float
    high_risk_world_ids: tuple[str,...]
    compression_ratio: float
    reconstruction_claimed: bool=False
    def to_dict(self): return asdict(self)

def compress_outcomes(outcomes: list[WorldOutcome], *, high_risk_count: int=5) -> CVCDSummary:
    if not outcomes: raise ValueError("outcomes required")
    sorted_ue=sorted(o.unserved_energy_mwh for o in outcomes)
    index=min(len(sorted_ue)-1,max(0,int(0.95*(len(sorted_ue)-1))))
    risky=sorted(outcomes,key=lambda o:(o.unserved_energy_mwh,o.restoration_hours),reverse=True)[:high_risk_count]
    raw_scalars=len(outcomes)*8; compressed_scalars=7+len(risky)
    return CVCDSummary(len(outcomes),mean(o.unserved_energy_mwh for o in outcomes),sorted_ue[index],max(sorted_ue),mean(o.restoration_hours for o in outcomes),mean(o.resilience_score for o in outcomes),tuple(o.world_id for o in risky),raw_scalars/compressed_scalars,False)
