"""PolyResearchTwin v3 answer model for Omega absorb v1.7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .poly_research_twin_v2 import PolyResearchTwinV2, build_poly_research_twin_v2
from .professor_tensor_weights import ProfessorTensorWeights, weight_professor_tensors


@dataclass(frozen=True)
class PolyResearchTwinV3:
    twin_v2: PolyResearchTwinV2
    weights: Tuple[ProfessorTensorWeights, ...]
    next_action: str

    def best_course_modules(self) -> Tuple[str, ...]:
        return tuple(self.twin_v2.best_course_modules[:10])

    def best_lab_projects(self) -> Tuple[str, ...]:
        return tuple(self.twin_v2.best_lab_projects[:10])

    def best_ip_candidates(self) -> Tuple[str, ...]:
        return tuple(self.twin_v2.best_ip_candidates[:10])

    def missing_evidence(self) -> Tuple[str, ...]:
        return tuple(self.twin_v2.missing_evidence[:10])

    def next_10_actions(self) -> Tuple[str, ...]:
        return self.twin_v2.next_10_actions()

    def best_weighted_routes(self) -> Tuple[str, ...]:
        ordered = sorted(self.weights, key=lambda item: (item.bridge + item.teaching + item.prototype - item.risk), reverse=True)
        return tuple(f"{item.professor}:bridge={item.bridge:.4f}:teaching={item.teaching:.4f}:prototype={item.prototype:.4f}" for item in ordered[:10])


def build_poly_research_twin_v3(records: Tuple[dict, ...] | None = None) -> PolyResearchTwinV3:
    twin_v2 = build_poly_research_twin_v2(records)
    weights = weight_professor_tensors(twin_v2.tensors)
    return PolyResearchTwinV3(twin_v2=twin_v2, weights=weights, next_action="answer_local_strategy_question")
