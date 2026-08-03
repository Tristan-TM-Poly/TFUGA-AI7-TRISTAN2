from __future__ import annotations
from dataclasses import asdict, dataclass
from .hashutil import sha256

@dataclass(frozen=True)
class SourceTrust:
    source_id: str
    authority: float
    directness: float
    freshness: float
    reproducibility: float
    independence: float
    licence_clarity: float
    composite_score: float
    caveats: tuple[str,...]
    evidence_hash: str
    def to_dict(self): return asdict(self)

def score_source(source_id: str, *, authority: float, directness: float, freshness: float, reproducibility: float, independence: float, licence_clarity: float, caveats: tuple[str,...]=()) -> SourceTrust:
    values=(authority,directness,freshness,reproducibility,independence,licence_clarity)
    if any(not 0<=x<=1 for x in values): raise ValueError('scores must be in [0,1]')
    weights=(0.24,0.20,0.14,0.18,0.14,0.10)
    score=sum(v*w for v,w in zip(values,weights))
    core={'source_id':source_id,'authority':authority,'directness':directness,'freshness':freshness,'reproducibility':reproducibility,'independence':independence,'licence_clarity':licence_clarity,'composite_score':score,'caveats':caveats}
    return SourceTrust(**core,evidence_hash=sha256(core))

def claim_confidence(source_scores: list[float], contradiction_penalty: float=0.0, model_uncertainty: float=0.0) -> float:
    if not source_scores: return 0.0
    if any(not 0<=x<=1 for x in source_scores): raise ValueError('scores must be in [0,1]')
    corroboration=1.0
    for score in source_scores: corroboration*=1.0-score
    return max(0.0,min(1.0,1.0-corroboration-contradiction_penalty-model_uncertainty))
