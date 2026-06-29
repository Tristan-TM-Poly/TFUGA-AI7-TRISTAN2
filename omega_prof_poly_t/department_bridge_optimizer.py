"""Department bridge optimizer for Omega absorb v1.5."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .collaboration_recommender import CollaborationRecommendation
from .department_bridge_scoring import score_recommendation_bridge


@dataclass(frozen=True)
class OptimizedBridge:
    rank: int
    professor_a: str
    professor_b: str
    score: float
    departments: Tuple[str, ...]
    next_action: str


@dataclass(frozen=True)
class DepartmentBridgeOptimization:
    bridges: Tuple[OptimizedBridge, ...]
    next_action: str


def optimize_department_bridges(recommendations: Iterable[CollaborationRecommendation], limit: int = 10) -> DepartmentBridgeOptimization:
    ranked = []
    for item in recommendations:
        ranked.append(
            OptimizedBridge(
                rank=0,
                professor_a=item.professor_a,
                professor_b=item.professor_b,
                score=score_recommendation_bridge(item),
                departments=tuple(item.complementary_departments),
                next_action="compile_bridge_project_seed",
            )
        )
    ranked = sorted(ranked, key=lambda bridge: bridge.score, reverse=True)[:limit]
    bridges = tuple(
        OptimizedBridge(
            rank=index,
            professor_a=item.professor_a,
            professor_b=item.professor_b,
            score=item.score,
            departments=item.departments,
            next_action=item.next_action,
        )
        for index, item in enumerate(ranked, start=1)
    )
    return DepartmentBridgeOptimization(bridges=bridges, next_action="route_top_bridges_to_action_engine")
