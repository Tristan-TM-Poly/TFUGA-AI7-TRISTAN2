"""PolyResearchTwin v2 for Omega absorb v1.5."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .department_bridge_scoring import score_department_bridge
from .fixture_loader_v08 import demo_combined_fixture_records
from .professor_genome import build_all_professor_genomes
from .professor_tensor import ProfessorTensor, build_professor_tensors
from .absorb_public_research import absorb_public_records


@dataclass(frozen=True)
class PolyResearchTwinV2:
    tensors: Tuple[ProfessorTensor, ...]
    best_course_modules: Tuple[str, ...]
    best_lab_projects: Tuple[str, ...]
    best_ip_candidates: Tuple[str, ...]
    missing_evidence: Tuple[str, ...]
    bridge_score: float
    next_action: str

    def next_10_actions(self) -> Tuple[str, ...]:
        actions = []
        actions.extend(f"course:{item}" for item in self.best_course_modules[:3])
        actions.extend(f"project:{item}" for item in self.best_lab_projects[:3])
        actions.extend(f"ip:{item}" for item in self.best_ip_candidates[:2])
        actions.extend(f"evidence:{item}" for item in self.missing_evidence[:2])
        return tuple(actions[:10])


def build_poly_research_twin_v2(records: Tuple[dict, ...] | None = None) -> PolyResearchTwinV2:
    records = records or demo_combined_fixture_records()
    absorption = absorb_public_records(records)
    genomes = build_all_professor_genomes(absorption.atoms)
    tensors = build_professor_tensors(genomes)
    bridge = score_department_bridge(genomes)
    courses = tuple(item for tensor in tensors for item in tensor.teaching)
    projects = tuple(item for tensor in tensors for item in tensor.projects)
    ips = tuple(item for tensor in tensors for item in tensor.ip_signals)
    missing = tuple(risk for tensor in tensors for risk in tensor.risks) or ("no_missing_evidence_detected",)
    return PolyResearchTwinV2(
        tensors=tensors,
        best_course_modules=courses,
        best_lab_projects=projects,
        best_ip_candidates=ips,
        missing_evidence=missing,
        bridge_score=bridge.score,
        next_action="compile_top_10_next_actions",
    )
