from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import json

from .core import ModelRegistry
from .oak import OAKGate, OAKReport, combine_reports
from .physics import generate_qed_emu_events, invariant_residual_summary
from .transforms import residual_multiscale_score


@dataclass
class PipelineReport:
    registry_report: dict[str, Any]
    event_report: dict[str, Any]
    combined_report: dict[str, Any]
    hypergraph_digest: str
    hypergraph_nodes: int
    hypergraph_edges: int
    event_count: int
    residual_summary: dict[str, float]
    multiscale_summary: dict[str, Any]
    outputs: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OmegaPCTPipeline:
    def __init__(self, registry: ModelRegistry, *, tolerance: float = 1e-9) -> None:
        self.registry = registry
        self.gate = OAKGate(tolerance=tolerance)

    @classmethod
    def from_catalog(cls, path: str | Path, *, tolerance: float = 1e-9) -> "OmegaPCTPipeline":
        return cls(ModelRegistry.from_catalog(path), tolerance=tolerance)

    def run_qed_reference(self, output_dir: str | Path, *, count: int = 256, sqrt_s: float = 10.0, seed: int = 0) -> PipelineReport:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        registry_report = self.gate.audit_registry(self.registry)
        events = generate_qed_emu_events(count, sqrt_s, seed=seed)
        representative = events[0] if events else None
        event_report = self.gate.audit_event(representative, "qed-emu-reference") if representative else OAKReport("qed-emu-reference", "empty", assumptions=["No event requested."])
        combined = combine_reports("omega-pct-qed-reference", [registry_report, event_report])
        graph = self.registry.build_hypergraph()
        residuals = invariant_residual_summary(events)
        observed = [event.weight for event in events]
        expected = sorted(observed)
        multiscale = residual_multiscale_score(observed, expected) if observed else {"l2": 0.0, "max_abs": 0.0}
        paths = {
            "hypergraph_json": str(output / "particle-field-hypergraph.json"),
            "hypergraph_graphml": str(output / "particle-field-hypergraph.graphml"),
            "oak_json": str(output / "oak-report.json"),
            "oak_markdown": str(output / "oak-report.md"),
            "events_jsonl": str(output / "events.jsonl"),
            "manifest": str(output / "manifest.json"),
        }
        Path(paths["hypergraph_json"]).write_text(json.dumps(graph.to_dict(), indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        Path(paths["hypergraph_graphml"]).write_text(graph.to_graphml(), encoding="utf-8")
        Path(paths["oak_json"]).write_text(json.dumps(combined.to_dict(), indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        Path(paths["oak_markdown"]).write_text(combined.to_markdown(), encoding="utf-8")
        with Path(paths["events_jsonl"]).open("w", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps({
                    "incoming": [vector.as_tuple() for vector in event.incoming],
                    "outgoing": [vector.as_tuple() for vector in event.outgoing],
                    "theta": event.theta, "phi": event.phi, "weight": event.weight,
                    "mandelstam": event.mandelstam(), "metadata": event.metadata,
                }, sort_keys=True) + "\n")
        report = PipelineReport(
            registry_report=registry_report.to_dict(), event_report=event_report.to_dict(), combined_report=combined.to_dict(),
            hypergraph_digest=graph.digest(), hypergraph_nodes=len(graph.nodes), hypergraph_edges=len(graph.edges),
            event_count=len(events), residual_summary=residuals, multiscale_summary=multiscale, outputs=paths,
        )
        Path(paths["manifest"]).write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        return report
