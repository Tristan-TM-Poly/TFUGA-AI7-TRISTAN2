"""OAK ledger CLI helpers for Omega absorb v1.8."""

from __future__ import annotations

from dataclasses import dataclass

from .absorb_public_research import absorb_public_records
from .claim_graph import build_claim_graph
from .claim_oak_plus import build_claim_oak_plus
from .evidence_risk_counter import EvidenceRiskCount, count_evidence_risk, render_evidence_risk_count
from .method_graph import build_method_graph
from .method_reproduction_packet import build_method_reproduction_set
from .next_actions_engine import compile_top_next_actions
from .oak_lineage_ledger import build_oak_lineage_ledger, render_oak_lineage_ledger
from .oak_packet_manifest_plus import OAKPacketManifestPlus, build_oak_packet_manifest_plus
from .poly_research_twin_v2 import build_poly_research_twin_v2
from .source_selection import select_demo_records


@dataclass(frozen=True)
class OAKLedgerBundle:
    counts: EvidenceRiskCount
    manifest_plus: OAKPacketManifestPlus
    lineage_markdown: str
    next_action: str


def build_oak_ledger_bundle(source: str = "combined") -> OAKLedgerBundle:
    records = select_demo_records(source)
    atoms = absorb_public_records(records).atoms
    claims = build_claim_oak_plus(build_claim_graph(atoms))
    methods = build_method_reproduction_set(build_method_graph(atoms))
    counts = count_evidence_risk(claims, methods)
    twin = build_poly_research_twin_v2(records)
    actions = compile_top_next_actions(twin)
    manifest = build_oak_packet_manifest_plus(actions.actions, counts, source_id=source, adapter="demo_route", policy_status="allow_with_warnings")
    ledger = build_oak_lineage_ledger(manifest)
    return OAKLedgerBundle(counts, manifest, render_oak_lineage_ledger(ledger), "write_oak_ledger_bundle")


def render_oak_ledger_bundle(bundle: OAKLedgerBundle) -> str:
    return render_evidence_risk_count(bundle.counts) + "\n" + bundle.lineage_markdown
