"""R0.5 Ω-SANS-PLAFOND backpressure bridge."""
from __future__ import annotations
from dataclasses import asdict, dataclass

@dataclass(frozen=True)
class BackpressureState:
    generation_rate: float
    validation_rate: float
    queued_jobs: int
    closure_ratio: float
    fanout_factor: float
    queue_waste_ratio: float

    def __post_init__(self) -> None:
        for name in ("generation_rate", "validation_rate", "fanout_factor", "queue_waste_ratio"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.queued_jobs < 0:
            raise ValueError("queued_jobs cannot be negative")
        if not 0.0 <= self.closure_ratio <= 1.0:
            raise ValueError("closure_ratio must be between 0 and 1")

def decide_backpressure(state: BackpressureState) -> dict:
    absorption_ratio = state.validation_rate / max(state.generation_rate, 1e-12) if state.generation_rate > 0 else 1.0
    pressure = 0.0
    pressure += min(1.0, max(0.0, 1.0 - absorption_ratio)) * 0.4
    pressure += min(1.0, state.queued_jobs / max(1.0, state.queued_jobs + 4.0)) * 0.2
    pressure += min(1.0, max(0.0, state.fanout_factor - 1.0) / max(1.0, state.fanout_factor)) * 0.15
    pressure += min(1.0, state.queue_waste_ratio) * 0.15
    pressure += max(0.0, 1.0 - state.closure_ratio) * 0.10

    if state.generation_rate > state.validation_rate and pressure >= 0.55:
        mode = "THROTTLE_AND_CRYSTALLIZE"
        admission_fraction = max(0.05, min(1.0, absorption_ratio))
    elif pressure >= 0.30 or state.queued_jobs > 0:
        mode = "HOLD_OR_CAUTIOUS_GROWTH"
        admission_fraction = max(0.25, min(1.0, max(absorption_ratio, 0.5)))
    else:
        mode = "GROW_AT_OBSERVED_FRONTIER"
        admission_fraction = 1.0

    return {
        "schema": "omega-workmax-frontier-bridge/v1",
        "mode": mode,
        "pressure": pressure,
        "absorption_ratio": absorption_ratio,
        "admission_fraction": admission_fraction,
        "state": asdict(state),
        "no_permanent_work_count_ceiling": True,
        "automatic_remote_mutation_authorized": False,
        "oak_limits": [
            "Backpressure controls admission rate; it does not define a permanent global work ceiling.",
            "Queue presence alone does not prove capacity saturation.",
            "Validation, safety, required-check and rollback gates cannot be bypassed to increase throughput.",
        ],
    }
