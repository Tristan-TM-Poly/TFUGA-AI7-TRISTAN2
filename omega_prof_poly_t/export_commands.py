"""Export command helpers for Omega absorb v1.1."""

from __future__ import annotations

from dataclasses import dataclass

from .e2e_pipeline_v09 import run_v09_e2e_pipeline
from .graph_exports import professor_graph_to_json
from .professor_graph_integration import research_atoms_to_professor_graph
from .fixture_loader_v08 import demo_combined_fixture_records
from .absorb_public_research import absorb_public_records
from .json_exports import to_deterministic_json


@dataclass(frozen=True)
class ExportPayloads:
    summary_json: str
    graph_json: str
    validation_json: str
    next_action: str


def build_export_payloads() -> ExportPayloads:
    records = demo_combined_fixture_records()
    result = run_v09_e2e_pipeline()
    absorption = absorb_public_records(records)
    graph = research_atoms_to_professor_graph(absorption.atoms)
    validation_json = to_deterministic_json(
        {
            "valid_count": result.validation.valid_count,
            "invalid_count": result.validation.invalid_count,
            "is_clean": result.validation.is_clean,
            "findings": [finding.__dict__ for finding in result.validation.findings],
        }
    )
    summary_json = to_deterministic_json(
        {
            "artifact_count": len(result.artifact_run.manifest.artifacts),
            "roadmap_steps": len(result.roadmap.steps),
            "department_score": result.department_report.score,
            "validation_clean": result.validation.is_clean,
        }
    )
    return ExportPayloads(
        summary_json=summary_json,
        graph_json=professor_graph_to_json(graph),
        validation_json=validation_json,
        next_action="write_selected_payload",
    )
