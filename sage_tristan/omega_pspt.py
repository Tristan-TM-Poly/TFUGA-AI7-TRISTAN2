"""Omega-PSPT++ helpers.

This module provides a tiny executable layer for Tristan solid-phase cards:
claim discipline, OAK promotion checks, Bayes-Tristan posterior containers,
and simple hyperloop/cycle-rank utilities.

The scientific rule is intentionally conservative:
strong names do not imply strong evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, Iterable, List, Mapping, Sequence


class OAKLevel(IntEnum):
    """Ordered OAK certification levels."""

    OAK_0 = 0  # intuition / image / name
    OAK_1 = 1  # formal definition
    OAK_2 = 2  # simulation
    OAK_3 = 3  # falsifiable prediction
    OAK_4 = 4  # internal measurement
    OAK_5 = 5  # controlled measurement and artifact rejection
    OAK_6 = 6  # independent replication
    OAK_7 = 7  # canonized robust phase

    @classmethod
    def parse(cls, value: str | int | "OAKLevel") -> "OAKLevel":
        if isinstance(value, cls):
            return value
        if isinstance(value, int):
            return cls(value)
        normalized = value.strip().replace("-", "_")
        return cls[normalized]


CLAIM_LEVEL_TO_MIN_OAK: Mapping[str, OAKLevel] = {
    "vision": OAKLevel.OAK_0,
    "candidate": OAKLevel.OAK_1,
    "simulated_candidate": OAKLevel.OAK_2,
    "predicted_candidate": OAKLevel.OAK_3,
    "measured_candidate": OAKLevel.OAK_4,
    "controlled_candidate": OAKLevel.OAK_5,
    "replicated_phase": OAKLevel.OAK_6,
    "canonized_phase": OAKLevel.OAK_7,
}


@dataclass(frozen=True)
class BayesTristanPosterior:
    """Posterior dimensions for a phase candidate.

    Each value must live in [0, 1]. The dimensions are deliberately separated:
    truth, usefulness, fertility, and testability are not the same quantity.
    """

    truth_probability: float
    utility: float
    fertility: float
    testability: float
    safety: float
    profitability: float
    compressibility: float
    replicability: float

    def __post_init__(self) -> None:
        for key, value in self.as_dict().items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{key} must be in [0, 1], got {value!r}")

    def as_dict(self) -> Dict[str, float]:
        return {
            "truth_probability": self.truth_probability,
            "utility": self.utility,
            "fertility": self.fertility,
            "testability": self.testability,
            "safety": self.safety,
            "profitability": self.profitability,
            "compressibility": self.compressibility,
            "replicability": self.replicability,
        }

    def action_score(self) -> float:
        """Score for prioritizing next work.

        High fertility/testability/compressibility can make a low-truth candidate
        worth simulating, while low safety or replicability penalizes promotion.
        """

        return (
            0.20 * self.truth_probability
            + 0.15 * self.utility
            + 0.20 * self.fertility
            + 0.20 * self.testability
            + 0.10 * self.compressibility
            + 0.10 * self.replicability
            + 0.05 * self.safety
        )


@dataclass
class PhaseCard:
    """Minimal executable representation of an Omega-PSPT phase card."""

    phase_id: str
    name: str
    oak_level: OAKLevel
    claim_level: str
    invariants: List[str] = field(default_factory=list)
    required_signatures: List[str] = field(default_factory=list)
    falsifiers: List[str] = field(default_factory=list)
    next_tests: List[str] = field(default_factory=list)
    posterior: BayesTristanPosterior | None = None

    def __post_init__(self) -> None:
        if self.claim_level not in CLAIM_LEVEL_TO_MIN_OAK:
            raise ValueError(f"Unknown claim level: {self.claim_level}")

    @property
    def minimum_oak_for_claim(self) -> OAKLevel:
        return CLAIM_LEVEL_TO_MIN_OAK[self.claim_level]

    def is_claim_allowed(self) -> bool:
        """Return True when evidence level supports the declared claim level."""

        return self.oak_level >= self.minimum_oak_for_claim

    def missing_for_promotion(self, target: OAKLevel | str | int) -> List[str]:
        """Return generic missing requirements for promotion to target OAK."""

        target_level = OAKLevel.parse(target)
        if self.oak_level >= target_level:
            return []
        requirements = {
            OAKLevel.OAK_1: "formal definition",
            OAKLevel.OAK_2: "simulation evidence",
            OAKLevel.OAK_3: "falsifiable prediction",
            OAKLevel.OAK_4: "internal measurement",
            OAKLevel.OAK_5: "artifact-controlled measurement",
            OAKLevel.OAK_6: "independent replication",
            OAKLevel.OAK_7: "canonization criteria",
        }
        return [
            requirement
            for level, requirement in requirements.items()
            if self.oak_level < level <= target_level
        ]


def cycle_rank(num_vertices: int, num_edges: int, components: int = 1) -> int:
    """Return the graph cycle rank beta_1 = |E| - |V| + c.

    This is the simplest hyperloop invariant. It counts independent cycles in
    an undirected graph under ordinary graph-theoretic assumptions.
    """

    if num_vertices < 0 or num_edges < 0 or components < 0:
        raise ValueError("num_vertices, num_edges, and components must be non-negative")
    return max(0, num_edges - num_vertices + components)


def hyperloop_score(loop_counts_by_scale: Sequence[int], weights: Sequence[float] | None = None) -> float:
    """Compute a log-stable hyperloop hierarchy score.

    L_T(n) = sum_k w_k log(1 + |Gamma_k|)
    """

    import math

    if weights is None:
        weights = [1.0] * len(loop_counts_by_scale)
    if len(weights) != len(loop_counts_by_scale):
        raise ValueError("weights must match loop_counts_by_scale length")
    if any(count < 0 for count in loop_counts_by_scale):
        raise ValueError("loop counts must be non-negative")
    return sum(float(w) * math.log1p(int(count)) for w, count in zip(weights, loop_counts_by_scale))


def artifact_penalty(observed_tags: Iterable[str], negative_memory_tags: Iterable[str]) -> float:
    """Simple Jaccard-style penalty for similarity to known false positives."""

    observed = {tag.strip().lower() for tag in observed_tags if tag.strip()}
    negative = {tag.strip().lower() for tag in negative_memory_tags if tag.strip()}
    if not observed or not negative:
        return 0.0
    return len(observed & negative) / len(observed | negative)


def should_promote_phase(
    card: PhaseCard,
    target: OAKLevel | str | int,
    observed_falsifiers: Iterable[str] = (),
    negative_memory_tags: Iterable[str] = (),
    max_artifact_penalty: float = 0.25,
) -> bool:
    """Conservative promotion gate.

    Promotion is blocked by: insufficient OAK evidence, direct falsifier hits,
    or high similarity to negative memory.
    """

    target_level = OAKLevel.parse(target)
    if card.oak_level < target_level:
        return False

    observed = {tag.strip().lower() for tag in observed_falsifiers if tag.strip()}
    known_falsifiers = {tag.strip().lower() for tag in card.falsifiers}
    if observed & known_falsifiers:
        return False

    penalty = artifact_penalty(observed, negative_memory_tags)
    return penalty <= max_artifact_penalty


OMEGA_TFTS = PhaseCard(
    phase_id="Omega-TFTS",
    name="Tristan fractal topological superconducting candidate",
    oak_level=OAKLevel.OAK_1,
    claim_level="candidate",
    invariants=[
        "fractal_dimension",
        "cycle_rank",
        "bdg_gap_candidate",
        "real_space_topological_marker",
        "edge_or_corner_mode_robustness",
        "ffwt_hac_cvcd_coherence",
    ],
    required_signatures=[
        "zero_resistance_or_strong_transport_evidence",
        "meissner_effect_or_magnetic_screening",
        "spectroscopic_gap",
        "critical_current",
        "critical_field",
        "artifact_controls",
        "replication",
    ],
    falsifiers=[
        "contact_short",
        "contamination",
        "ordinary_percolation_only",
        "no_meissner_signal",
        "no_gap",
        "non_replicated_signal",
    ],
    next_tests=[
        "simulate_fractal_lattice_cycle_rank",
        "simulate_bdg_gap_and_edge_modes",
        "compute_real_space_topological_marker",
        "simulate_impedance_tree",
        "design_transport_magnetic_controls",
    ],
    posterior=BayesTristanPosterior(
        truth_probability=0.05,
        utility=0.85,
        fertility=0.95,
        testability=0.75,
        safety=0.80,
        profitability=0.55,
        compressibility=0.90,
        replicability=0.30,
    ),
)
