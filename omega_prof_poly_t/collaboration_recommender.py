"""Cross-department collaboration recommender for Omega absorb v0.7."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Tuple

from .professor_genome import ProfessorResearchGenome


@dataclass(frozen=True)
class CollaborationRecommendation:
    professor_a: str
    professor_b: str
    shared_keywords: Tuple[str, ...]
    complementary_departments: Tuple[str, ...]
    shared_methods: Tuple[str, ...]
    score: float
    rationale: str
    next_action: str


@dataclass(frozen=True)
class CollaborationPlan:
    recommendations: Tuple[CollaborationRecommendation, ...]
    next_action: str


def recommend_collaborations(genomes: Iterable[ProfessorResearchGenome], limit: int = 10) -> CollaborationPlan:
    genomes_tuple = tuple(genomes)
    recommendations = []
    for left, right in combinations(genomes_tuple, 2):
        left_keywords = set(left.expertise_keywords)
        right_keywords = set(right.expertise_keywords)
        shared_keywords = tuple(sorted(left_keywords & right_keywords))
        shared_methods = tuple(sorted(set(left.methods) & set(right.methods)))
        departments = tuple(sorted(set(left.departments) | set(right.departments)))
        department_bonus = 0.20 if set(left.departments) != set(right.departments) else 0.05
        score = min(
            1.0,
            0.20
            + 0.10 * min(4, len(shared_keywords))
            + 0.12 * min(3, len(shared_methods))
            + department_bonus
            + 0.05 * min(4, len(departments)),
        )
        if score <= 0.25:
            continue
        recommendations.append(
            CollaborationRecommendation(
                professor_a=left.professor,
                professor_b=right.professor,
                shared_keywords=shared_keywords,
                complementary_departments=departments,
                shared_methods=shared_methods,
                score=round(score, 4),
                rationale="shared_research_surface_plus_department_bridge",
                next_action="generate_collaboration_seed_packet",
            )
        )
    recommendations.sort(key=lambda item: item.score, reverse=True)
    return CollaborationPlan(
        recommendations=tuple(recommendations[:limit]),
        next_action="render_collaboration_backlog",
    )
