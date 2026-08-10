from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import FrozenSet, Mapping, Tuple


class EpistemicStatus(str, Enum):
    """Required status for claims and modeled mechanisms."""

    ESTABLISHED = "established"
    MODEL = "model"
    HYPOTHESIS_T = "hypothesis_t"
    PREDICTION = "prediction"
    EVIDENCE_NEEDED = "evidence_needed"


def _unit_interval(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and in [0, 1], got {value!r}")


def _positive(name: str, value: float, *, allow_zero: bool = False) -> None:
    valid = value >= 0.0 if allow_zero else value > 0.0
    if not isfinite(value) or not valid:
        op = ">=" if allow_zero else ">"
        raise ValueError(f"{name} must be finite and {op} 0, got {value!r}")


@dataclass(frozen=True)
class NeuroCellState:
    """Compact state vector; fields are model variables, not a cell-type ontology."""

    cell_id: str
    membrane_potential_mv: float = -65.0
    calcium_relative: float = 0.0
    excitability: float = 1.0
    metabolic_support: float = 1.0
    neuromodulatory_gain: float = 1.0
    uncertainty: float = 0.0
    status: EpistemicStatus = EpistemicStatus.MODEL

    def __post_init__(self) -> None:
        if not self.cell_id:
            raise ValueError("cell_id must be non-empty")
        _positive("excitability", self.excitability)
        _positive("metabolic_support", self.metabolic_support, allow_zero=True)
        _positive("neuromodulatory_gain", self.neuromodulatory_gain, allow_zero=True)
        _unit_interval("uncertainty", self.uncertainty)
        if not isfinite(self.membrane_potential_mv) or not isfinite(self.calcium_relative):
            raise ValueError("cell state values must be finite")


@dataclass(frozen=True)
class DendriticBranchState:
    branch_id: str
    threshold: float = 0.0
    gain: float = 1.0
    saturation: float = 1.0
    local_calcium: float = 0.0
    uncertainty: float = 0.0
    status: EpistemicStatus = EpistemicStatus.MODEL

    def __post_init__(self) -> None:
        if not self.branch_id:
            raise ValueError("branch_id must be non-empty")
        _positive("gain", self.gain)
        _positive("saturation", self.saturation)
        _unit_interval("uncertainty", self.uncertainty)
        if not isfinite(self.threshold) or not isfinite(self.local_calcium):
            raise ValueError("branch values must be finite")


@dataclass(frozen=True)
class SynapseState:
    """A synapse state tensor projected into a small executable reference model."""

    synapse_id: str
    pre_cell: str
    post_cell: str
    release_probability: float = 1.0
    quantal_scale: float = 1.0
    delay_ms: float = 1.0
    short_term_gain: float = 1.0
    long_term_gain: float = 1.0
    dendritic_address: str = "soma"
    astrocytic_context: float = 1.0
    neuromodulatory_context: float = 1.0
    metabolic_context: float = 1.0
    uncertainty: float = 0.0
    status: EpistemicStatus = EpistemicStatus.MODEL

    def __post_init__(self) -> None:
        if not self.synapse_id or not self.pre_cell or not self.post_cell:
            raise ValueError("synapse_id, pre_cell and post_cell must be non-empty")
        _unit_interval("release_probability", self.release_probability)
        _positive("quantal_scale", self.quantal_scale, allow_zero=True)
        _positive("delay_ms", self.delay_ms, allow_zero=True)
        _positive("short_term_gain", self.short_term_gain, allow_zero=True)
        _positive("long_term_gain", self.long_term_gain, allow_zero=True)
        _positive("astrocytic_context", self.astrocytic_context, allow_zero=True)
        _positive("neuromodulatory_context", self.neuromodulatory_context, allow_zero=True)
        _positive("metabolic_context", self.metabolic_context, allow_zero=True)
        _unit_interval("uncertainty", self.uncertainty)


@dataclass(frozen=True)
class NetworkFingerprint:
    excitation_inhibition_ratio: float
    recurrence: float
    modularity: float
    delay_dispersion: float
    plasticity: float
    hierarchy: float
    multiscale_coherence: float

    def __post_init__(self) -> None:
        _positive("excitation_inhibition_ratio", self.excitation_inhibition_ratio, allow_zero=True)
        for name in ("recurrence", "modularity", "plasticity", "hierarchy", "multiscale_coherence"):
            _unit_interval(name, getattr(self, name))
        _positive("delay_dispersion", self.delay_dispersion, allow_zero=True)


@dataclass(frozen=True)
class HyperEdge:
    """Higher-order relation among >=2 biological/model entities."""

    edge_id: str
    members: FrozenSet[str]
    layer: str = "effective"
    scale: str = "microcircuit"
    modality: str = "electrical"
    weight: float = 1.0
    metadata: Mapping[str, str] = field(default_factory=dict)
    status: EpistemicStatus = EpistemicStatus.MODEL

    def __post_init__(self) -> None:
        if not self.edge_id:
            raise ValueError("edge_id must be non-empty")
        if len(self.members) < 2:
            raise ValueError("a hyperedge requires at least two members")
        if self.layer not in {"structural", "effective", "plastic", "modulatory", "metabolic"}:
            raise ValueError(f"unsupported layer: {self.layer}")
        if not isfinite(self.weight):
            raise ValueError("weight must be finite")

    @property
    def order(self) -> int:
        return len(self.members)

    def signature(self) -> Tuple[str, str, str, Tuple[str, ...]]:
        return self.layer, self.scale, self.modality, tuple(sorted(self.members))
