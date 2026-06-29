"""ProfessorTensor for Omega absorb v1.5."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .professor_genome import ProfessorResearchGenome


@dataclass(frozen=True)
class ProfessorTensor:
    professor: str
    departments: Tuple[str, ...]
    keywords: Tuple[str, ...]
    methods: Tuple[str, ...]
    claims: Tuple[str, ...]
    teaching: Tuple[str, ...]
    projects: Tuple[str, ...]
    ip_signals: Tuple[str, ...]
    risks: Tuple[str, ...]
    collaboration_vector: Tuple[str, ...]
    next_action: str


def build_professor_tensor(genome: ProfessorResearchGenome) -> ProfessorTensor:
    collaboration_vector = tuple(sorted(set(genome.departments + genome.expertise_keywords + genome.methods)))
    return ProfessorTensor(
        professor=genome.professor,
        departments=tuple(genome.departments),
        keywords=tuple(genome.expertise_keywords),
        methods=tuple(genome.methods),
        claims=tuple(genome.claims),
        teaching=tuple(genome.teaching_opportunities),
        projects=tuple(genome.project_opportunities),
        ip_signals=tuple(genome.ip_signals),
        risks=tuple(genome.oak_risks),
        collaboration_vector=collaboration_vector,
        next_action="rank_professor_routes",
    )


def build_professor_tensors(genomes: Iterable[ProfessorResearchGenome]) -> Tuple[ProfessorTensor, ...]:
    return tuple(build_professor_tensor(genome) for genome in genomes)
