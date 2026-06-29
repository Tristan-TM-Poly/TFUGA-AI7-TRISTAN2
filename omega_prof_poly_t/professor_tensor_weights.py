"""Weighted ProfessorTensor routes for Omega absorb v1.7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .professor_tensor import ProfessorTensor


@dataclass(frozen=True)
class ProfessorTensorWeights:
    professor: str
    teaching: float
    prototype: float
    bridge: float
    ip: float
    risk: float
    next_action: str

    def as_dict(self) -> dict[str, float | str]:
        return {
            "professor": self.professor,
            "teaching": self.teaching,
            "prototype": self.prototype,
            "bridge": self.bridge,
            "ip": self.ip,
            "risk": self.risk,
        }


def weight_professor_tensor(tensor: ProfessorTensor) -> ProfessorTensorWeights:
    teaching = min(1.0, 0.35 + 0.08 * len(tensor.teaching) + 0.03 * len(tensor.keywords))
    prototype = min(1.0, 0.30 + 0.08 * len(tensor.projects) + 0.05 * len(tensor.methods))
    bridge = min(1.0, 0.25 + 0.07 * len(tensor.departments) + 0.03 * len(tensor.collaboration_vector))
    ip = min(1.0, 0.20 + 0.08 * len(tensor.ip_signals))
    risk = min(1.0, 0.10 + 0.07 * len(tensor.risks))
    return ProfessorTensorWeights(
        professor=tensor.professor,
        teaching=round(teaching, 4),
        prototype=round(prototype, 4),
        bridge=round(bridge, 4),
        ip=round(ip, 4),
        risk=round(risk, 4),
        next_action="route_weighted_tensor_to_twin_v3",
    )


def weight_professor_tensors(tensors: Iterable[ProfessorTensor]) -> Tuple[ProfessorTensorWeights, ...]:
    return tuple(weight_professor_tensor(tensor) for tensor in tensors)


def render_tensor_weights_table(weights: Iterable[ProfessorTensorWeights]) -> str:
    lines = ["professor | teaching | prototype | bridge | ip | risk", "--- | --- | --- | --- | --- | ---"]
    for item in weights:
        lines.append(f"{item.professor} | {item.teaching:.4f} | {item.prototype:.4f} | {item.bridge:.4f} | {item.ip:.4f} | {item.risk:.4f}")
    return "\n".join(lines) + "\n"
