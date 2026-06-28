"""Interdisciplinary ProjectForge for Omega-PROF-POLY-T."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .zero_touch_oak import OAKCompileResult, compile_oak


@dataclass(frozen=True)
class ProjectInput:
    need: str
    disciplines: Tuple[str, ...]
    prototype: str
    term_weeks: int = 12
    equipment: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ProjectPacket:
    title: str
    disciplines: Tuple[str, ...]
    deliverables: Tuple[str, ...]
    success_tests: Tuple[str, ...]
    risks: Tuple[str, ...]
    publication_potential: float
    ip_potential: float
    startup_potential: float
    oak: OAKCompileResult
    next_action: str


def forge_project(project: ProjectInput, evidence_count: int = 1) -> ProjectPacket:
    title = f"{project.prototype} for {project.need}"
    deliverables = (
        "problem_statement",
        "prototype_design",
        "test_plan",
        "data_or_simulation_output",
        "oak_report",
        "final_demo_packet",
    )
    success_tests = (
        "feasibility_within_term",
        "measurable_performance_metric",
        "reproducible_build_or_simulation",
        "risk_and_limit_statement",
    )
    risks = (
        "scope_too_large" if project.term_weeks < 14 else "scope_moderate",
        "equipment_dependency" if project.equipment else "equipment_to_define",
        "overclaim_if_no_test_data",
    )
    discipline_factor = min(1.0, len(project.disciplines) / 4.0)
    equipment_factor = 0.75 if project.equipment else 0.45
    publication_potential = round(0.35 + 0.25 * discipline_factor, 3)
    ip_potential = round(0.25 + 0.25 * equipment_factor, 3)
    startup_potential = round(0.20 + 0.20 * discipline_factor + 0.15 * equipment_factor, 3)
    benefits: Dict[str, float] = {
        "teaching": 0.82,
        "research": publication_potential,
        "industry": startup_potential,
        "ip": ip_potential,
        "automation": 0.76,
        "feasibility": 0.70 if project.term_weeks >= 12 else 0.45,
    }
    risk_values: Dict[str, float] = {
        "complexity": min(0.85, 0.18 * len(project.disciplines)),
        "overclaim": 0.34,
        "confidentiality": 0.18,
        "safety": 0.22,
    }
    oak = compile_oak(title, benefits, risk_values, evidence_count=evidence_count)
    return ProjectPacket(
        title=title,
        disciplines=project.disciplines,
        deliverables=deliverables,
        success_tests=success_tests,
        risks=risks,
        publication_potential=publication_potential,
        ip_potential=ip_potential,
        startup_potential=startup_potential,
        oak=oak,
        next_action="generate_project_charter_and_oakbench",
    )
