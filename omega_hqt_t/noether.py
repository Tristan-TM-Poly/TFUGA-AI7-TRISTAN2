from __future__ import annotations
from dataclasses import asdict, dataclass
from .hashutil import sha256

@dataclass(frozen=True)
class NoetherReceipt:
    inputs_mwh: float
    outputs_mwh: float
    storage_delta_mwh: float
    modeled_losses_mwh: float
    residual_mwh: float
    normalized_residual: float
    status: str
    evidence_hash: str
    def to_dict(self): return asdict(self)

def energy_balance(*, inputs_mwh: float, outputs_mwh: float, storage_delta_mwh: float=0.0, modeled_losses_mwh: float=0.0, tolerance_fraction: float=1e-6) -> NoetherReceipt:
    residual=inputs_mwh-outputs_mwh-storage_delta_mwh-modeled_losses_mwh
    scale=max(abs(inputs_mwh),abs(outputs_mwh),1.0)
    normalized=abs(residual)/scale
    status='BALANCED_WITHIN_TOLERANCE' if normalized<=tolerance_fraction else 'OAK_RESIDUAL_REQUIRES_EXPLANATION'
    core={'inputs_mwh':inputs_mwh,'outputs_mwh':outputs_mwh,'storage_delta_mwh':storage_delta_mwh,'modeled_losses_mwh':modeled_losses_mwh,'residual_mwh':residual,'normalized_residual':normalized,'status':status}
    return NoetherReceipt(**core,evidence_hash=sha256(core))

def partition_residual(total_residual_mwh: float, weights: dict[str,float]) -> dict[str,float]:
    if any(v<0 for v in weights.values()): raise ValueError('weights must be non-negative')
    total=sum(weights.values())
    if total<=0: raise ValueError('at least one positive weight is required')
    return {key:total_residual_mwh*value/total for key,value in sorted(weights.items())}
