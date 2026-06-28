"""Export command helpers for Omega absorb v1.2."""

from __future__ import annotations

from dataclasses import dataclass

from .absorb_public_research import absorb_public_records
from .e2e_pipeline_v09 import run_v09_e2e_pipeline
from .enriched_graph_exports import professor_graph_to_enriched_graphml
from .graph_exports import professor_graph_to_json
from .json_exports import to_deterministic_json
from .professor_graph_integration import research_atoms_to_professor_graph
from .source_selection import select_demo_records


@dataclass(frozen=True)
class ExportPayloads:
    summary_json: str
    graph_json: str
    graphml: str
    validation_json: str
    source: str
    next_action: str


def build_export_payloads(source: str = "combined") -> ExportPayloads:
    records = select_demo_records(source)
    result = run_v09_e2e_pipeline()
    absorption = absorb_public_records(records)
    graph = research_atoms_to_professor_graph(absorption.atoms)
    validation_json = to_deterministic_json(
        {
            "source": source,
            "record_count": len(records),
            "valid_count": result.validation.valid_count,
            "invalid_count": result.validation.invalid_count,
            "is_clean": result.validation.is_clean,
        }
    )
    summary_json = to_deterministic_json(
        {
            "source": source,
            "record_count": len(records),
            "artifact_count": len(result.artifact_run.manifest.artifacts),
            "roadmap_steps": len(result.roadmap.steps),
            "department_score": result.department_report.score,
        }
    )
    return ExportPayloads(
        summary_json=summary_json,
        graph_json=professor_graph_to_json(graph),
        graphml=professor_graph_to_enriched_graphml(graph),
        validation_json=validation_json,
        source=source,
        next_action="write_selected_payload",
    )
