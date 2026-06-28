"""Omega-PROF-POLY-T package."""

from .absorb_public_research import AbsorptionReport, absorb_public_records, demo_public_research_records
from .core import (
    Evidence,
    OAKDecision,
    OAKStatus,
    ProfessorSignal,
    build_project_forge_prompt,
    evaluate_signal,
    rank_signals,
)
from .course_memory_minus import CourseAntiError, CourseMemoryMinus, build_course_memory_minus
from .coursecvcd import CourseCVCDPacket, CourseInput, generate_coursecvcd
from .grant_forge import GrantInput, GrantPacket, forge_grant, grant_score
from .ip_oak_gate import IPGatePacket, IPInput, IPStatus, classify_ip
from .lab_oakbench import LabInput, LabOAKBenchPacket, generate_lab_oakbench
from .poly_research_twin import PolyResearchTwin, build_poly_research_twin
from .prior_art_packet import PriorArtPacket, generate_prior_art_packet
from .professor_genome import ProfessorResearchGenome, build_all_professor_genomes, build_professor_genome
from .professor_graph import HyperEdge, Node, ProfessorGraph, demo_professor_graph
from .project_forge import ProjectInput, ProjectPacket, forge_project
from .reports import render_packet_report
from .research_atom import ResearchAtom, atom_from_public_record
from .zero_touch_oak import BlockedActionPacket, GateStatus, OAKCompileResult, compile_oak

__all__ = [
    "AbsorptionReport",
    "absorb_public_records",
    "demo_public_research_records",
    "Evidence",
    "OAKDecision",
    "OAKStatus",
    "ProfessorSignal",
    "build_project_forge_prompt",
    "evaluate_signal",
    "rank_signals",
    "CourseAntiError",
    "CourseMemoryMinus",
    "build_course_memory_minus",
    "CourseCVCDPacket",
    "CourseInput",
    "generate_coursecvcd",
    "GrantInput",
    "GrantPacket",
    "forge_grant",
    "grant_score",
    "IPGatePacket",
    "IPInput",
    "IPStatus",
    "classify_ip",
    "LabInput",
    "LabOAKBenchPacket",
    "generate_lab_oakbench",
    "PolyResearchTwin",
    "build_poly_research_twin",
    "PriorArtPacket",
    "generate_prior_art_packet",
    "ProfessorResearchGenome",
    "build_all_professor_genomes",
    "build_professor_genome",
    "HyperEdge",
    "Node",
    "ProfessorGraph",
    "demo_professor_graph",
    "ProjectInput",
    "ProjectPacket",
    "forge_project",
    "render_packet_report",
    "ResearchAtom",
    "atom_from_public_record",
    "BlockedActionPacket",
    "GateStatus",
    "OAKCompileResult",
    "compile_oak",
]
