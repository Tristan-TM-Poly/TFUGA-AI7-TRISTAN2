from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, asdict
from pathlib import Path

from .canon_export import document_card, markdown_cards, opportunity_card
from .entity_resolution import cluster_people, entity_warnings
from .fixtures import load_synthetic_documents
from .models import DigestDocument, Opportunity
from .oak_gates import assess_opportunity
from .reuse_blueprints import build_blueprints


@dataclass
class PipelineConfig:
    mode: str = "plus-ultra"
    source_policy: str = "synthetic-fixtures-only"
    oak_ip_required: bool = True


@dataclass
class PipelineResult:
    documents: int
    opportunities: int
    bridges: int
    output_dir: str


def build_opportunities(documents: list[DigestDocument]) -> list[Opportunity]:
    science = [doc for doc in documents if doc.kind == "science"]
    patents = [doc for doc in documents if doc.kind == "patent"]
    opportunities: list[Opportunity] = []
    counter = 1
    for sci in science:
        for pat in patents:
            bridge_topics = sorted(set(sci.topics).intersection(pat.topics))
            if not bridge_topics:
                continue
            opportunities.append(
                Opportunity(
                    opportunity_id=f"opp-{counter:03d}",
                    title=f"Bridge: {sci.title} ↔ {pat.title}",
                    science_doc=sci.doc_id,
                    ip_doc=pat.doc_id,
                    bridge_topics=bridge_topics,
                    oak_status="review_required",
                    release_class="internal_review",
                    cautions=["synthetic fixture", "verify sources before use"],
                )
            )
            counter += 1
    return opportunities


class DigestPipeline:
    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()

    def run(self, out_dir: str | Path) -> PipelineResult:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        documents = load_synthetic_documents()
        opportunities = build_opportunities(documents)
        people = [person for doc in documents for person in doc.people]
        clusters = cluster_people(people)
        warnings = entity_warnings(clusters)
        gates = {opp.opportunity_id: [gate.to_dict() for gate in assess_opportunity(opp)] for opp in opportunities}
        doc_cards = [document_card(doc) for doc in documents]
        opp_cards = [opportunity_card(opp) for opp in opportunities]
        cards = doc_cards + opp_cards
        blueprints = build_blueprints()

        (out / "pipeline_config.json").write_text(json.dumps(asdict(self.config), indent=2) + "\n", encoding="utf-8")
        (out / "documents.json").write_text(json.dumps([doc.to_dict() for doc in documents], indent=2) + "\n", encoding="utf-8")
        (out / "opportunities.json").write_text(json.dumps([opp.to_dict() for opp in opportunities], indent=2) + "\n", encoding="utf-8")
        (out / "entity_clusters.json").write_text(json.dumps(clusters, indent=2) + "\n", encoding="utf-8")
        (out / "entity_resolution_warnings.md").write_text("# Entity Resolution Warnings\n\n" + "\n".join(f"- {item}" for item in warnings) + "\n", encoding="utf-8")
        (out / "release_assessment.json").write_text(json.dumps(gates, indent=2) + "\n", encoding="utf-8")
        (out / "release_assessment.md").write_text(self._release_markdown(gates), encoding="utf-8")
        (out / "reuse_blueprints.json").write_text(json.dumps(blueprints, indent=2) + "\n", encoding="utf-8")
        (out / "reuse_blueprints.md").write_text(self._blueprints_markdown(blueprints), encoding="utf-8")
        canon = out / "canon_pack"
        canon.mkdir(exist_ok=True)
        (canon / "dct_cards.json").write_text(json.dumps(cards, indent=2) + "\n", encoding="utf-8")
        (canon / "dct_cards.md").write_text(markdown_cards(cards), encoding="utf-8")
        self._write_sqlite(out / "digest.sqlite", documents, opportunities)
        bridges = sum(len(opp.bridge_topics) for opp in opportunities)
        summary = PipelineResult(len(documents), len(opportunities), bridges, str(out))
        (out / "pipeline_summary.json").write_text(json.dumps(asdict(summary), indent=2) + "\n", encoding="utf-8")
        return summary

    def _release_markdown(self, gates: dict) -> str:
        lines = ["# OAK Release Assessment", "", "All outputs are internal review only.", ""]
        for opp_id, gate_rows in gates.items():
            lines.append(f"## {opp_id}")
            for gate in gate_rows:
                lines.append(f"- {gate['name']}: {gate['status']} — {', '.join(gate['reasons'])}")
            lines.append("")
        return "\n".join(lines)

    def _blueprints_markdown(self, blueprints: list[dict]) -> str:
        lines = ["# Reuse Blueprints", ""]
        for item in blueprints:
            lines.append(f"## {item['name']}")
            lines.append(f"- purpose: {item['purpose']}")
            lines.append(f"- inputs: {', '.join(item['inputs'])}")
            lines.append(f"- outputs: {', '.join(item['outputs'])}")
            lines.append(f"- OAK locks: {', '.join(item['oak_locks'])}")
            lines.append("")
        return "\n".join(lines)

    def _write_sqlite(self, path: Path, documents: list[DigestDocument], opportunities: list[Opportunity]) -> None:
        conn = sqlite3.connect(path)
        try:
            conn.execute("create table if not exists documents (doc_id text primary key, kind text, title text, institution text, year integer)")
            conn.execute("create table if not exists opportunities (opportunity_id text primary key, title text, science_doc text, ip_doc text, release_class text)")
            conn.executemany("insert or replace into documents values (?, ?, ?, ?, ?)", [(d.doc_id, d.kind, d.title, d.institution, d.year) for d in documents])
            conn.executemany("insert or replace into opportunities values (?, ?, ?, ?, ?)", [(o.opportunity_id, o.title, o.science_doc, o.ip_doc, o.release_class) for o in opportunities])
            conn.commit()
        finally:
            conn.close()
