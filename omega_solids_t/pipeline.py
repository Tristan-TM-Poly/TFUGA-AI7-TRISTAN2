from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .defects import DefectInteractionGraph
from .genome import SolidGenome, save_genome
from .hypergraph import SolidHyperGraph
from .invariants import CVCDSolidSignature, build_signature
from .oak import OAKReport, run_oak_gate
from .ontology import OntologyTag, classify


@dataclass(frozen=True, slots=True)
class SolidReport:
    genome: SolidGenome
    signature: CVCDSolidSignature
    ontology: tuple[OntologyTag, ...]
    hypergraph: SolidHyperGraph
    defect_tensor: dict[str, Any]
    oak: OAKReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest": {
                "system": "Ω-SOLID-T∞",
                "version": "0.1.0",
                "genome_id": self.genome.identifier,
                "fingerprint": self.genome.fingerprint(),
                "epistemic_boundary": (
                    "Generated analyses are structured research artifacts, not material "
                    "certification, synthesis proof, safety approval or experimental validation."
                ),
            },
            "genome": self.genome.to_dict(),
            "cvcd_signature": self.signature.to_dict(),
            "ontology": [
                {
                    "namespace": tag.namespace,
                    "value": tag.value,
                    "confidence": tag.confidence,
                    "rationale": tag.rationale,
                }
                for tag in self.ontology
            ],
            "hypergraph_summary": self.hypergraph.to_dict()["summary"],
            "defect_tensor": dict(self.defect_tensor),
            "oak": self.oak.to_dict(),
        }


class SolidPipeline:
    def analyze(self, genome: SolidGenome) -> SolidReport:
        graph = SolidHyperGraph.from_genome(genome)
        defect_tensor = DefectInteractionGraph.infer(genome).tensor().to_dict()
        return SolidReport(
            genome,
            build_signature(genome),
            classify(genome),
            graph,
            defect_tensor,
            run_oak_gate(genome),
        )

    def materialize(self, report: SolidReport, output_dir: str | Path) -> Path:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        save_genome(report.genome, output / "solid-genome.json")
        report.hypergraph.write_json(output / "solid-hypergraph.json")
        (output / "solid-hypergraph.graphml").write_text(
            report.hypergraph.to_graphml(), encoding="utf-8"
        )
        (output / "cvcd-signature.json").write_text(
            json.dumps(
                report.signature.to_dict(),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (output / "oak-report.json").write_text(
            json.dumps(report.oak.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        (output / "report.json").write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        (output / "report.md").write_text(self.render_markdown(report), encoding="utf-8")
        return output

    @staticmethod
    def render_markdown(report: SolidReport) -> str:
        genome = report.genome
        lines = [
            f"# Ω-SOLID-T∞ — {genome.name}",
            "",
            f"- **Identifier:** `{genome.identifier}`",
            f"- **Family:** {genome.family}",
            f"- **Formula/projection:** `{genome.formula}`",
            f"- **Order:** `{genome.order.value}`",
            f"- **Dimensionality:** `{genome.dimensionality.value}`",
            f"- **Epistemic status:** `{genome.status.value}`",
            f"- **Fingerprint:** `{genome.fingerprint()}`",
            "",
            "## OAK",
            "",
            f"- **Status:** `{report.oak.status.value}`",
            f"- **Score:** {report.oak.score:.3f}",
            "",
            "| Gate | Status | Score |",
            "|---|---:|---:|",
        ]
        for gate in report.oak.gates:
            lines.append(f"| {gate.gate} | {gate.status.value} | {gate.score:.3f} |")
        lines.extend(
            [
                "",
                "## CVCD signature",
                "",
                "```json",
                json.dumps(report.signature.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
                "```",
                "",
                "## Hypergraph",
                "",
                f"- Nodes: {len(report.hypergraph.nodes)}",
                f"- Hyperedges: {len(report.hypergraph.edges)}",
                f"- Connected components: {len(report.hypergraph.connected_components())}",
                "",
                "## Risks",
                "",
            ]
        )
        lines.extend(f"- {risk}" for risk in genome.risks)
        if not genome.risks:
            lines.append("- No risk has been encoded; this is an OAK warning, not evidence of safety.")
        lines.extend(["", "## Next experiments", ""])
        lines.extend(f"- {experiment}" for experiment in genome.next_experiments)
        if not genome.next_experiments:
            lines.append("- Define a discriminating experiment before promotion.")
        lines.extend(
            [
                "",
                "## Boundary",
                "",
                "This artifact is a structured research model. It is not a certificate of material "
                "identity, manufacturability, safety, performance, or regulatory compliance.",
                "",
            ]
        )
        return "\n".join(lines)
