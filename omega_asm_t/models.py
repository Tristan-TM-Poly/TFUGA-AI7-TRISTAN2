from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class Instruction:
    """One SSA-like operation in the architecture-neutral ASM-IR."""

    op: str
    output: str | None = None
    inputs: tuple[str, ...] = ()
    latency: float = 1.0
    size_bytes: int = 4
    memory_bytes: int = 0
    branch_probability: float | None = None
    vector_width: int = 1
    metadata: dict[str, Any] = field(default_factory=dict, compare=False)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["inputs"] = list(self.inputs)
        return data


@dataclass(frozen=True)
class Program:
    name: str
    inputs: tuple[str, ...]
    instructions: tuple[Instruction, ...]
    outputs: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "inputs": list(self.inputs),
            "instructions": [instruction.to_dict() for instruction in self.instructions],
            "outputs": list(self.outputs),
        }


@dataclass(frozen=True)
class AnalysisMetrics:
    instruction_count: int
    critical_path: float
    ilp_upper_bound: float
    register_time_volume: int
    peak_live_values: int
    memory_bytes: int
    branch_entropy_bits: float
    mean_vector_width: float
    useful_ops_per_memory_byte: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Candidate:
    name: str
    architecture: str
    variant: str
    estimated_cycles: float
    code_size_score: float
    memory_score: float
    correctness_level: str = "E0/E1 intended; native CI required"

    def objective_vector(self) -> tuple[float, float, float]:
        return (self.estimated_cycles, self.code_size_score, self.memory_score)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OAKReport:
    valid: bool
    authority: str
    human_review_required: bool
    automatic_merge_allowed: bool
    claims: tuple[str, ...]
    limitations: tuple[str, ...]
    metrics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["claims"] = list(self.claims)
        data["limitations"] = list(self.limitations)
        return data
