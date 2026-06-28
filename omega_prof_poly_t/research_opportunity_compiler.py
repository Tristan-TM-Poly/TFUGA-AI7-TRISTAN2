"""Research opportunity compiler.

Routes ResearchAtoms into CourseCVCD, ProjectForge, GrantForge, and IP-OAK Gate
packets using public metadata only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .coursecvcd import CourseCVCDPacket, CourseInput, generate_coursecvcd
from .grant_forge import GrantInput, GrantPacket, forge_grant
from .ip_oak_gate import IPGatePacket, IPInput, classify_ip
from .project_forge import ProjectInput, ProjectPacket, forge_project
from .research_atom import ResearchAtom


@dataclass(frozen=True)
class ResearchOpportunityBundle:
    atom_id: str
    course_packet: CourseCVCDPacket
    project_packet: ProjectPacket
    grant_packet: GrantPacket
    ip_packet: IPGatePacket
    next_action: str


@dataclass(frozen=True)
class ResearchOpportunityCompilation:
    bundles: Tuple[ResearchOpportunityBundle, ...]
    next_action: str


def compile_atom_opportunities(atom: ResearchAtom) -> ResearchOpportunityBundle:
    objectives = atom.keywords or atom.methods or atom.claims or (atom.title,)
    disciplines = atom.departments or ("intergenie",)
    evidence_count = 1 + bool(atom.abstract) + len(atom.datasets) + len(atom.code_links)

    course_packet = generate_coursecvcd(
        CourseInput(
            title=f"Research module: {atom.title}",
            disciplines=disciplines,
            objectives=objectives[:6],
            prerequisites=("source literacy", "OAK boundaries"),
            constraints=("public metadata only",),
        ),
        evidence_count=int(evidence_count),
    )
    project_packet = forge_project(
        ProjectInput(
            need=f"prototype path for {atom.title}",
            disciplines=disciplines,
            prototype=(atom.methods[0] if atom.methods else "research prototype"),
            term_weeks=12,
            equipment=tuple(keyword for keyword in atom.keywords if "sensor" in keyword.lower() or "lab" in keyword.lower()),
        ),
        evidence_count=int(evidence_count),
    )
    grant_packet = forge_grant(
        GrantInput(
            title=f"Grant cluster: {atom.title}",
            problem=f"Convert public research atom {atom.atom_id} into course-lab-project impact.",
            objectives=atom.claims or ("build research-to-impact pipeline",),
            methods=atom.methods or ("public metadata analysis", "OAK scoring"),
            team_strength=0.55 + 0.05 * min(4, len(atom.professors)),
            impact=0.60 + 0.04 * min(5, len(atom.keywords)),
            novelty=0.55 + 0.05 * min(4, len(atom.methods)),
            feasibility=0.65,
            reproducibility=0.45 + 0.15 * bool(atom.datasets) + 0.20 * bool(atom.code_links),
        ),
        evidence_count=int(evidence_count),
    )
    ip_packet = classify_ip(
        IPInput(
            result_name=f"IP triage: {atom.title}",
            novelty_score=0.55 + 0.05 * min(4, len(atom.methods)),
            utility_score=0.60 + 0.04 * min(5, len(atom.keywords)),
            market_score=0.45 + 0.04 * min(5, len(atom.departments)),
            feasibility_score=0.55 + 0.10 * bool(atom.datasets) + 0.10 * bool(atom.code_links),
            disclosure_risk=0.25,
            reproducibility_score=0.45 + 0.20 * bool(atom.datasets) + 0.25 * bool(atom.code_links),
        ),
        evidence_count=int(evidence_count),
    )
    return ResearchOpportunityBundle(
        atom_id=atom.atom_id,
        course_packet=course_packet,
        project_packet=project_packet,
        grant_packet=grant_packet,
        ip_packet=ip_packet,
        next_action="render_bundle_report_and_export_json",
    )


def compile_research_opportunities(atoms: Iterable[ResearchAtom]) -> ResearchOpportunityCompilation:
    bundles = tuple(compile_atom_opportunities(atom) for atom in atoms)
    return ResearchOpportunityCompilation(
        bundles=bundles,
        next_action="rank_bundles_and_generate_professor_backlogs",
    )
