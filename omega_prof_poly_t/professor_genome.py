"""ProfessorResearchGenome builder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from .research_atom import ResearchAtom


@dataclass(frozen=True)
class ProfessorResearchGenome:
    professor: str
    departments: Tuple[str, ...]
    expertise_keywords: Tuple[str, ...]
    publication_atoms: Tuple[str, ...]
    methods: Tuple[str, ...]
    claims: Tuple[str, ...]
    datasets: Tuple[str, ...]
    code_links: Tuple[str, ...]
    teaching_opportunities: Tuple[str, ...]
    project_opportunities: Tuple[str, ...]
    grant_opportunities: Tuple[str, ...]
    ip_signals: Tuple[str, ...]
    oak_risks: Tuple[str, ...]
    next_actions: Tuple[str, ...]


def _unique(items: Iterable[str]) -> Tuple[str, ...]:
    seen: Dict[str, None] = {}
    for item in items:
        clean = str(item).strip()
        if clean:
            seen.setdefault(clean, None)
    return tuple(seen.keys())


def build_professor_genome(professor: str, atoms: Iterable[ResearchAtom]) -> ProfessorResearchGenome:
    selected = tuple(atom for atom in atoms if professor in atom.professors or professor in atom.authors)
    departments = _unique(dept for atom in selected for dept in atom.departments)
    keywords = _unique(keyword for atom in selected for keyword in atom.keywords)
    methods = _unique(method for atom in selected for method in atom.methods)
    claims = _unique(claim for atom in selected for claim in atom.claims)
    datasets = _unique(dataset for atom in selected for dataset in atom.datasets)
    code_links = _unique(link for atom in selected for link in atom.code_links)
    publication_atoms = tuple(atom.atom_id for atom in selected)

    teaching_opportunities = tuple(
        f"Course module from {atom.title}" for atom in selected if atom.keywords or atom.methods
    )
    project_opportunities = tuple(
        f"Project seed from {method}" for method in methods[:8]
    )
    grant_opportunities = tuple(
        f"Grant cluster around {keyword}" for keyword in keywords[:8]
    )
    ip_signals = tuple(
        f"IP triage candidate: {atom.title}" for atom in selected if atom.oak and atom.oak.benefits.get("prototype", 0.0) >= 0.55
    )
    oak_risks = _unique(
        warning for atom in selected if atom.oak for warning in atom.oak.warnings
    )
    next_actions = (
        "generate_course_modules",
        "generate_project_backlog",
        "run_ip_oak_gate_on_high_prototype_atoms",
        "build_grant_clusters",
    ) if selected else ("collect_public_metadata_for_professor",)

    return ProfessorResearchGenome(
        professor=professor,
        departments=departments,
        expertise_keywords=keywords,
        publication_atoms=publication_atoms,
        methods=methods,
        claims=claims,
        datasets=datasets,
        code_links=code_links,
        teaching_opportunities=teaching_opportunities,
        project_opportunities=project_opportunities,
        grant_opportunities=grant_opportunities,
        ip_signals=ip_signals,
        oak_risks=oak_risks,
        next_actions=next_actions,
    )


def build_all_professor_genomes(atoms: Iterable[ResearchAtom]) -> Tuple[ProfessorResearchGenome, ...]:
    atoms_tuple = tuple(atoms)
    professors = _unique(
        person for atom in atoms_tuple for person in (atom.professors or atom.authors)
    )
    return tuple(build_professor_genome(professor, atoms_tuple) for professor in professors)
