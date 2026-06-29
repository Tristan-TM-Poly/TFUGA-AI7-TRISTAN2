"""Local JSON ingestion pipeline v2 for Omega absorb v1.6."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .adapter_router import AdapterRoute, route_records
from .absorb_public_research import absorb_public_records
from .claim_graph import build_claim_graph
from .claim_oak_plus import build_claim_oak_plus
from .local_json_loader import load_local_json_records
from .method_graph import build_method_graph
from .method_reproduction_packet import build_method_reproduction_set
from .next_actions_engine import compile_top_next_actions
from .oak_packet_manifest import build_oak_packet_manifest
from .poly_research_twin_v2 import build_poly_research_twin_v2
from .professor_genome import build_all_professor_genomes
from .professor_tensor import build_professor_tensors
from .source_oak_policy import SourceOAKPolicyReport, apply_source_oak_policy


@dataclass(frozen=True)
class IngestJSONPipelineResult:
    source_route: AdapterRoute
    policy_report: SourceOAKPolicyReport
    atom_count: int
    claim_oak_count: int
    method_packet_count: int
    tensor_count: int
    action_count: int
    manifest_json: str
    next_action: str


def run_ingest_json_pipeline_v2(path: str | Path, preferred_source: str | None = None) -> IngestJSONPipelineResult:
    records = load_local_json_records(path)
    routed = route_records(records, preferred_source)
    policy = apply_source_oak_policy(routed.records, routed.route.source_id)
    absorption = absorb_public_records(routed.normalized_records if policy.status != "blocked" else ())
    atoms = absorption.atoms
    claim_oak = build_claim_oak_plus(build_claim_graph(atoms))
    methods = build_method_reproduction_set(build_method_graph(atoms))
    genomes = build_all_professor_genomes(atoms)
    tensors = build_professor_tensors(genomes)
    twin = build_poly_research_twin_v2(routed.normalized_records if atoms else ())
    actions = compile_top_next_actions(twin)
    manifest = build_oak_packet_manifest(actions.actions, version="1.6.0")
    return IngestJSONPipelineResult(
        source_route=routed.route,
        policy_report=policy,
        atom_count=len(atoms),
        claim_oak_count=len(claim_oak.claims),
        method_packet_count=len(methods.packets),
        tensor_count=len(tensors),
        action_count=len(actions.actions),
        manifest_json=manifest.manifest_json,
        next_action="write_ingest_v2_bundle",
    )
