"""CourseCVCD engine.

Transforms a course description into a compact concept graph, exercise seeds,
project seeds, and an automated OAK packet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

from .zero_touch_oak import OAKCompileResult, compile_oak


@dataclass(frozen=True)
class CourseInput:
    title: str
    disciplines: Tuple[str, ...]
    objectives: Tuple[str, ...]
    prerequisites: Tuple[str, ...] = ()
    constraints: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ConceptNode:
    concept: str
    depends_on: Tuple[str, ...] = ()
    common_error: str = "not_yet_mapped"
    minimal_example: str = "to_generate"


@dataclass(frozen=True)
class CourseCVCDPacket:
    course_title: str
    concept_graph: Tuple[ConceptNode, ...]
    exercise_seeds: Tuple[str, ...]
    project_seeds: Tuple[str, ...]
    rubric_axes: Tuple[str, ...]
    oak: OAKCompileResult
    next_action: str


def _concepts_from_objectives(objectives: Sequence[str]) -> List[ConceptNode]:
    nodes: List[ConceptNode] = []
    previous: Tuple[str, ...] = ()
    for index, objective in enumerate(objectives, start=1):
        concept = objective.strip() or f"objective_{index}"
        nodes.append(
            ConceptNode(
                concept=concept,
                depends_on=previous[-2:],
                common_error="overclaim_or_formula_without_context",
                minimal_example=f"minimal_example_for_{index}",
            )
        )
        previous = previous + (concept,)
    return nodes


def generate_coursecvcd(course: CourseInput, evidence_count: int = 1) -> CourseCVCDPacket:
    concepts = tuple(_concepts_from_objectives(course.objectives))
    exercise_seeds = tuple(f"Exercise: apply {node.concept}" for node in concepts)
    project_seeds = tuple(
        f"Project seed: connect {course.title} to {discipline} prototype"
        for discipline in course.disciplines
    )
    rubric_axes = (
        "conceptual_correctness",
        "method_transparency",
        "reproducibility",
        "uncertainty_awareness",
        "oak_boundary_respect",
    )
    benefits: Dict[str, float] = {
        "teaching": 0.90 if concepts else 0.35,
        "student_support": 0.82,
        "reproducibility": 0.70,
        "automation": 0.85,
        "feasibility": 0.80,
    }
    risks: Dict[str, float] = {
        "overclaim": 0.20,
        "integrity": 0.30,
        "privacy": 0.10,
        "complexity": min(0.70, 0.08 * len(concepts)),
    }
    oak = compile_oak(course.title, benefits, risks, evidence_count=evidence_count)
    return CourseCVCDPacket(
        course_title=course.title,
        concept_graph=concepts,
        exercise_seeds=exercise_seeds,
        project_seeds=project_seeds,
        rubric_axes=rubric_axes,
        oak=oak,
        next_action="generate_exercise_bank_and_lab_seed_report",
    )
