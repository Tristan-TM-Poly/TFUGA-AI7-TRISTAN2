"""End-to-end Ω-INFO²-T pipeline.

Text/source → InfoObject → Bayes-Tristan → CVCD → OAK → Router → M⁻ → Info2Graph.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .bayes_tristan import BayesTristanReport, BayesTristanUpdater, EvidenceVector
from .claim_extractor import extract_candidate_claims
from .cvcd_compressor import CVCDCompressor, CVCDReport
from .graph import Info2Graph
from .half_life import freshness_score
from .m_minus_registry import MMinusEntry, MMinusRegistry
from .models import InfoObject, InfoScores, MetaInformation, Provenance, ProvenanceStep, RawObject
from .oak_gate import OAKInfoGate
from .router import route_information
from .source_trust import SourceTrustInput, score_source


@dataclass(slots=True)
class Info2PipelineResult:
    info_object: InfoObject
    bayes_report: BayesTristanReport | None
    cvcd_report: CVCDReport
    m_minus_entries: list[MMinusEntry]
    graph: Info2Graph

    def to_dict(self) -> dict[str, Any]:
        return {
            "info_object": self.info_object.to_dict(),
            "bayes_report": self.bayes_report.to_dict() if self.bayes_report else None,
            "cvcd_report": self.cvcd_report.to_dict(),
            "m_minus_entries": [entry.to_dict() for entry in self.m_minus_entries],
            "graph": self.graph.to_dict(),
        }


class Info2Pipeline:
    """Composable end-to-end pipeline with OAK-safe defaults."""

    def __init__(
        self,
        oak_gate: OAKInfoGate | None = None,
        bayes_updater: BayesTristanUpdater | None = None,
        cvcd: CVCDCompressor | None = None,
        m_minus: MMinusRegistry | None = None,
    ) -> None:
        self.oak_gate = oak_gate or OAKInfoGate()
        self.bayes_updater = bayes_updater or BayesTristanUpdater()
        self.cvcd = cvcd or CVCDCompressor()
        self.m_minus = m_minus or MMinusRegistry()

    def run_text(
        self,
        text: str,
        *,
        source: str | None = None,
        domain: str = "general",
        evidence: list[EvidenceVector] | None = None,
        age_days: float = 0.0,
    ) -> Info2PipelineResult:
        source_trust = score_source(
            SourceTrustInput(
                reputation=0.5,
                traceability=0.7 if source else 0.2,
                reproducibility=0.4,
                freshness=freshness_score(age_days, domain=domain),
                independence=0.5,
                opacity=0.2 if source else 0.7,
            )
        )
        obj = InfoObject(
            id="info2_pipeline_object",
            raw_object=RawObject(type="text", location=source, content_preview=text[:280]),
            claims=extract_candidate_claims(text, domain=domain),
            meta=MetaInformation(source=source, domain=domain),
            provenance=Provenance(
                extraction_tool="Info2Pipeline",
                extraction_version="0.1.0",
                transformations=[ProvenanceStep(operation="run_text", tool="Info2Pipeline", confidence=0.80)],
            ),
            scores=InfoScores(
                truth=0.45,
                utility=0.55,
                fertility=0.55,
                testability=0.65,
                risk=0.30,
                freshness=freshness_score(age_days, domain=domain),
                source_trust=source_trust,
            ),
        )
        bayes_report = self.bayes_updater.update_info_object(obj, evidence or []) if evidence else None
        cvcd_report = self.cvcd.compress_info_object(obj)
        oak_report = self.oak_gate.evaluate(obj)
        route_information(obj)
        m_entries = MMinusRegistry.entries_from_oak_report(obj, oak_report)
        self.m_minus.extend(m_entries)
        graph = Info2Graph.from_info_object(obj)
        return Info2PipelineResult(
            info_object=obj,
            bayes_report=bayes_report,
            cvcd_report=cvcd_report,
            m_minus_entries=m_entries,
            graph=graph,
        )
