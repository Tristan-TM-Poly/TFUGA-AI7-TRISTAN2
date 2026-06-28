"""Department bridge scoring for Omega absorb v0.8."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .collaboration_recommender import CollaborationRecommendation
from .professor_genome import ProfessorResearchGenome


@dataclass(frozen=True)
class DepartmentBridgeScore:
    departments: Tuple[str, ...]
    professor_count: int
    keyword_count: int
    method_count: int
    score: float
    next_action: str


def score_department_bridge(genomes: Iterable[ProfessorResearchGenome]) -> DepartmentBridgeScore:
    genomes_tuple = tuple(genomes)
    departments = tuple(sorted({dept for genome in genomes_tuple for dept in genome.departments}))
    keywords = {kw for genome in genomes_tuple for kw in genome.expertise_keywords}
    methods = {method for genome in genomes_tuple for method in genome.methods}
    score = min(
        1.0,
        0.20
        + 0.08 * min(5, len(departments))
        + 0.04 * min(10, len(keywords))
        + 0.05 * min(6, len(methods))
        + 0.05 * min(4, len(genomes_tuple)),
    )
    return DepartmentBridgeScore(
        departments=departments,
        professor_count=len(genomes_tuple),
        keyword_count=len(keywords),
        method_count=len(methods),
        score=round(score, 4),
        next_action="use_bridge_score_to_rank_pairing_plan",
    )


def score_recommendation_bridge(item: CollaborationRecommendation) -> float:
    return round(
        min(
            1.0,
            item.score
            + 0.04 * min(5, len(item.complementary_departments))
            + 0.03 * min(5, len(item.shared_keywords))
            + 0.04 * min(4, len(item.shared_methods)),
        ),
        4,
    )
