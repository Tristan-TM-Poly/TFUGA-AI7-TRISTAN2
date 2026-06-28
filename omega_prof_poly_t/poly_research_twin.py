"""PolyResearchTwin for public research metadata absorption."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from .professor_genome import ProfessorResearchGenome, build_all_professor_genomes
from .research_atom import ResearchAtom


@dataclass(frozen=True)
class PolyResearchTwin:
    atoms: Tuple[ResearchAtom, ...]
    genomes: Tuple[ProfessorResearchGenome, ...]
    course_opportunities: Tuple[str, ...]
    project_opportunities: Tuple[str, ...]
    grant_opportunities: Tuple[str, ...]
    ip_opportunities: Tuple[str, ...]
    graph_holes: Tuple[str, ...]
    next_action: str

    def answer_questions(self) -> Dict[str, Tuple[str, ...]]:
        return {
            "courses_can_absorb_research": self.course_opportunities,
            "projects_to_forge": self.project_opportunities,
            "grant_clusters": self.grant_opportunities,
            "ip_radar": self.ip_opportunities,
            "graph_holes": self.graph_holes,
        }


def build_poly_research_twin(atoms: Iterable[ResearchAtom]) -> PolyResearchTwin:
    atoms_tuple = tuple(atoms)
    genomes = build_all_professor_genomes(atoms_tuple)
    course_opportunities = tuple(
        opportunity for genome in genomes for opportunity in genome.teaching_opportunities
    )
    project_opportunities = tuple(
        opportunity for genome in genomes for opportunity in genome.project_opportunities
    )
    grant_opportunities = tuple(
        opportunity for genome in genomes for opportunity in genome.grant_opportunities
    )
    ip_opportunities = tuple(
        signal for genome in genomes for signal in genome.ip_signals
    )
    graph_holes = []
    if not atoms_tuple:
        graph_holes.append("missing_research_atoms")
    if not genomes:
        graph_holes.append("missing_professor_genomes")
    if not course_opportunities:
        graph_holes.append("missing_course_opportunities")
    if not project_opportunities:
        graph_holes.append("missing_project_opportunities")
    if not grant_opportunities:
        graph_holes.append("missing_grant_opportunities")
    if not ip_opportunities:
        graph_holes.append("missing_ip_opportunities")

    return PolyResearchTwin(
        atoms=atoms_tuple,
        genomes=genomes,
        course_opportunities=course_opportunities,
        project_opportunities=project_opportunities,
        grant_opportunities=grant_opportunities,
        ip_opportunities=ip_opportunities,
        graph_holes=tuple(graph_holes),
        next_action="generate_course_project_grant_ip_packets",
    )
