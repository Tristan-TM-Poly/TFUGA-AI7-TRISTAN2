"""Stable CLI for Omega Absorb OS v2.0."""

from __future__ import annotations

import argparse

from .absorb_public_research import absorb_public_records
from .action_packet_writer import write_action_packets
from .adapter_router import route_records
from .changelog_generator import generate_changelog
from .claim_graph import build_claim_graph
from .claim_oak_plus import build_claim_oak_plus
from .cli_command_groups import render_cli_command_groups
from .collaboration_recommender import recommend_collaborations
from .compact_table_report import render_compact_table, render_validation_table
from .department_bridge_optimizer import optimize_department_bridges
from .department_strategy_matrix import build_department_strategy_matrix, render_department_strategy_matrix
from .documentation_index import render_documentation_index
from .e2e_pipeline_v09 import run_v09_e2e_pipeline
from .evidence_risk_counter import count_evidence_risk, render_evidence_risk_count
from .export_bundle import build_export_bundle
from .export_commands import build_export_payloads
from .generated_changelog_plus import generate_changelog_plus
from .github_packet_generator import generate_github_work_packet, render_github_packet_markdown
from .github_work_bundle import build_github_work_bundle, write_github_work_bundle
from .ingest_json_pipeline_v2 import run_ingest_json_pipeline_v2
from .local_json_loader import load_and_normalize_local_json, load_local_json_records
from .method_graph import build_method_graph
from .method_reproduction_packet import build_method_reproduction_set
from .mminus_registry import render_mminus_markdown
from .mminus_rules_engine import apply_mminus_rules, render_mminus_decision
from .next_actions_engine import compile_top_next_actions, render_next_actions_markdown
from .oak_ledger_cli import build_oak_ledger_bundle, render_oak_ledger_bundle
from .oak_lineage_ledger import build_oak_lineage_ledger, render_oak_lineage_ledger
from .oak_packet_manifest import build_oak_packet_manifest
from .oak_packet_manifest_plus import build_oak_packet_manifest_plus
from .omega_absorb_os_v2 import render_omega_absorb_os_v2
from .opportunity_ranker import rank_opportunity_bundles
from .package_ci_plan import render_package_ci_plan
from .package_health import build_package_health_report
from .package_layout_v2 import render_package_layout_v2
from .package_status import build_package_status_report
from .poly_research_twin_v2 import build_poly_research_twin_v2
from .poly_research_twin_v3 import build_poly_research_twin_v3
from .professor_genome import build_all_professor_genomes
from .professor_tensor import build_professor_tensors
from .professor_tensor_weights import render_tensor_weights_table, weight_professor_tensors
from .release_bundle_writer import write_release_bundle
from .release_intelligence import render_release_intelligence
from .report_atlas import render_report_atlas
from .report_bundle_contract import render_report_bundle_contract
from .report_writer import write_reports
from .research_opportunity_compiler import compile_research_opportunities
from .roadmap_compiler import render_roadmap_markdown
from .route_confidence_dashboard import build_route_confidence_dashboard, render_route_confidence_dashboard
from .source_oak_policy import apply_source_oak_policy
from .source_record_validation import validate_public_records
from .source_registry_schema import validate_records_against_schema
from .source_selection import available_demo_sources, select_demo_records
from .twin_answer_engine import answer_twin_question, render_twin_answer
from .workflow_seed import render_workflow_seed


VERSION = "2.0.0"


def _atoms_and_genomes(source: str):
    atoms = absorb_public_records(select_demo_records(source)).atoms
    genomes = build_all_professor_genomes(atoms)
    return atoms, genomes


def _bridge_plan(source: str):
    _, genomes = _atoms_and_genomes(source)
    return optimize_department_bridges(recommend_collaborations(genomes).recommendations)


def _top_actions(source: str):
    twin = build_poly_research_twin_v2(select_demo_records(source))
    return compile_top_next_actions(twin, _bridge_plan(source).bridges)


def _claims_methods_counts(source: str):
    atoms = absorb_public_records(select_demo_records(source)).atoms
    claims = build_claim_oak_plus(build_claim_graph(atoms))
    methods = build_method_reproduction_set(build_method_graph(atoms))
    counts = count_evidence_risk(claims, methods)
    return claims, methods, counts


def _load_or_demo_records(path: str, source: str):
    return load_local_json_records(path) if path else select_demo_records(source)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-absorb", description="Omega absorb public research pipeline")
    parser.add_argument(
        "command",
        choices=(
            "version", "demo", "roadmap", "summary-json", "validation-json", "graph-json", "graphml", "docs-index", "status", "sources", "write-bundle", "ingest-json", "table", "export-bundle", "health", "changelog", "schema-check", "claim-oak", "method-packets", "mminus", "github-packet", "tensor", "twin-v2", "bridge-opt", "next-actions", "oak-manifest", "route-source", "policy-check", "ingest-json-v2", "write-actions", "github-bundle", "tensor-weights", "twin-answer", "department-matrix", "route-dashboard", "evidence-risk", "oak-manifest-plus", "oak-lineage", "mminus-apply", "oak-ledger", "reports", "write-reports", "release-intel", "changelog-plus", "ci-plan", "layout-v2", "report-contract", "workflow-seed", "command-groups", "absorb-os",
        ),
        help="Command to run",
    )
    parser.add_argument("--source", default="combined", choices=available_demo_sources(), help="Demo source family")
    parser.add_argument("--input", default="", help="Local JSON input path")
    parser.add_argument("--input-source", default="generic", help="Adapter for local JSON input")
    parser.add_argument("--question", default="next-10", help="Twin v3 local question")
    parser.add_argument("--feature", default="omega_absorb_next", help="Feature name for packet generation")
    parser.add_argument("--mminus-context", default="", help="M-minus context key")
    parser.add_argument("--output-dir", default="generated/omega_absorb_poly_prof_v20", help="Output directory")
    return parser


def run_cli(argv: list[str] | None = None) -> str:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "version":
        return f"omega-absorb {VERSION}\n"
    if args.command == "layout-v2":
        return render_package_layout_v2()
    if args.command == "report-contract":
        return render_report_bundle_contract()
    if args.command == "workflow-seed":
        return render_workflow_seed()
    if args.command == "command-groups":
        return render_cli_command_groups()
    if args.command == "absorb-os":
        return render_omega_absorb_os_v2()
    if args.command == "reports":
        return render_report_atlas()
    if args.command == "write-reports":
        result = write_reports(args.output_dir)
        return f"report_files={len(result.files)}\n"
    if args.command == "release-intel":
        return render_release_intelligence()
    if args.command == "changelog-plus":
        return generate_changelog_plus()
    if args.command == "ci-plan":
        return render_package_ci_plan()
    if args.command == "sources":
        return "\n".join(available_demo_sources()) + "\n"
    if args.command == "docs-index":
        return render_documentation_index()
    if args.command == "status":
        return build_package_status_report().markdown
    if args.command == "health":
        return build_package_health_report().markdown
    if args.command == "changelog":
        return generate_changelog()
    if args.command == "mminus":
        return render_mminus_markdown()
    if args.command == "mminus-apply":
        key = args.mminus_context or "unknown_source"
        return render_mminus_decision(apply_mminus_rules({key: True}))
    if args.command == "evidence-risk":
        _, _, counts = _claims_methods_counts(args.source)
        return render_evidence_risk_count(counts)
    if args.command == "oak-manifest-plus":
        _, _, counts = _claims_methods_counts(args.source)
        return build_oak_packet_manifest_plus(_top_actions(args.source).actions, counts, source_id=args.source).manifest_json
    if args.command == "oak-lineage":
        _, _, counts = _claims_methods_counts(args.source)
        manifest = build_oak_packet_manifest_plus(_top_actions(args.source).actions, counts, source_id=args.source)
        return render_oak_lineage_ledger(build_oak_lineage_ledger(manifest))
    if args.command == "oak-ledger":
        return render_oak_ledger_bundle(build_oak_ledger_bundle(args.source))
    if args.command == "github-packet":
        return render_github_packet_markdown(generate_github_work_packet(args.feature))
    if args.command == "tensor-weights":
        _, genomes = _atoms_and_genomes(args.source)
        return render_tensor_weights_table(weight_professor_tensors(build_professor_tensors(genomes)))
    if args.command == "twin-answer":
        twin = build_poly_research_twin_v3(select_demo_records(args.source))
        return render_twin_answer(answer_twin_question(twin, args.question))
    if args.command == "department-matrix":
        _, genomes = _atoms_and_genomes(args.source)
        matrix = build_department_strategy_matrix(build_professor_tensors(genomes))
        return render_department_strategy_matrix(matrix)
    if args.command == "route-dashboard":
        dashboard = build_route_confidence_dashboard(_load_or_demo_records(args.input, args.source))
        return render_route_confidence_dashboard(dashboard)
    if args.command == "route-source":
        routed = route_records(_load_or_demo_records(args.input, args.source), args.input_source if args.input else None)
        return f"source_id={routed.route.source_id} adapter={routed.route.adapter_name} confidence={routed.route.confidence:.2f}\n"
    if args.command == "policy-check":
        routed = route_records(_load_or_demo_records(args.input, args.source), args.input_source if args.input else None)
        report = apply_source_oak_policy(routed.records, routed.route.source_id)
        return f"status={report.status} warnings={len(report.warnings)} blocked={len(report.blocked_fields)}\n"
    if args.command == "ingest-json-v2":
        if not args.input:
            raise ValueError("--input is required for ingest-json-v2")
        result = run_ingest_json_pipeline_v2(args.input, args.input_source)
        return f"route={result.source_route.source_id} atoms={result.atom_count} actions={result.action_count}\n"
    if args.command == "write-actions":
        result = write_action_packets(_top_actions(args.source).actions, args.output_dir)
        return f"action_files={len(result.files)} manifest={result.manifest_path}\n"
    if args.command == "github-bundle":
        bundle = build_github_work_bundle(_top_actions(args.source).actions)
        files = write_github_work_bundle(bundle, args.output_dir)
        return f"github_bundle_files={len(files)}\n"
    if args.command == "tensor":
        _, genomes = _atoms_and_genomes(args.source)
        return f"professor_tensors={len(build_professor_tensors(genomes))}\n"
    if args.command == "twin-v2":
        twin = build_poly_research_twin_v2(select_demo_records(args.source))
        return f"twin_tensors={len(twin.tensors)} bridge_score={twin.bridge_score:.4f} actions={len(twin.next_10_actions())}\n"
    if args.command == "bridge-opt":
        plan = _bridge_plan(args.source)
        return f"optimized_bridges={len(plan.bridges)}\n"
    if args.command == "next-actions":
        return render_next_actions_markdown(_top_actions(args.source))
    if args.command == "oak-manifest":
        return build_oak_packet_manifest(_top_actions(args.source).actions).manifest_json
    if args.command in {"summary-json", "validation-json", "graph-json", "graphml"}:
        payloads = build_export_payloads(args.source)
        if args.command == "summary-json":
            return payloads.summary_json
        if args.command == "validation-json":
            return payloads.validation_json
        if args.command == "graphml":
            return payloads.graphml
        return payloads.graph_json
    if args.command == "write-bundle":
        result = write_release_bundle(args.output_dir)
        return "".join(f"{item.path} {item.bytes_written}\n" for item in result.files)
    if args.command == "export-bundle":
        result = build_export_bundle(args.source, args.output_dir)
        return result.manifest_json
    if args.command == "ingest-json":
        if not args.input:
            raise ValueError("--input is required for ingest-json")
        loaded = load_and_normalize_local_json(args.input, args.input_source)
        report = validate_public_records(loaded.normalized_records)
        return render_validation_table(report)
    if args.command == "schema-check":
        records = select_demo_records(args.source)
        report = validate_records_against_schema(records, "generic")
        return f"accepted={report.accepted_count} rejected={report.rejected_count} findings={len(report.findings)}\n"
    if args.command == "claim-oak":
        atoms = absorb_public_records(select_demo_records(args.source)).atoms
        graph = build_claim_graph(atoms)
        return f"claim_oak_plus={len(build_claim_oak_plus(graph).claims)}\n"
    if args.command == "method-packets":
        atoms = absorb_public_records(select_demo_records(args.source)).atoms
        graph = build_method_graph(atoms)
        return f"method_packets={len(build_method_reproduction_set(graph).packets)}\n"
    if args.command == "table":
        absorption = absorb_public_records(select_demo_records(args.source))
        ranking = rank_opportunity_bundles(compile_research_opportunities(absorption.atoms))
        return render_compact_table(ranking)
    result = run_v09_e2e_pipeline()
    if args.command == "roadmap":
        return render_roadmap_markdown(result.roadmap)
    return (
        "Omega absorb demo\n"
        f"validation_clean={result.validation.is_clean}\n"
        f"artifact_count={len(result.artifact_run.manifest.artifacts)}\n"
        f"roadmap_steps={len(result.roadmap.steps)}\n"
    )


def main() -> None:
    print(run_cli().rstrip())


if __name__ == "__main__":
    main()
