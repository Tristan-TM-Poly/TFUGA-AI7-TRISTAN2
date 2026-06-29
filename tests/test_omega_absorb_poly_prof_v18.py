from omega_prof_poly_t import (
    VERSION,
    apply_mminus_rules,
    build_claim_graph,
    build_claim_oak_plus,
    build_method_graph,
    build_method_reproduction_set,
    build_oak_ledger_bundle,
    build_oak_lineage_ledger,
    build_oak_packet_manifest_plus,
    count_evidence_risk,
    render_evidence_risk_count,
    render_mminus_decision,
    render_oak_ledger_bundle,
    render_oak_lineage_ledger,
    run_cli,
    select_demo_records,
)
from omega_prof_poly_t.absorb_public_research import absorb_public_records
from omega_prof_poly_t.next_actions_engine import compile_top_next_actions
from omega_prof_poly_t.poly_research_twin_v2 import build_poly_research_twin_v2


def _claims_methods_counts():
    atoms = absorb_public_records(select_demo_records("combined")).atoms
    claims = build_claim_oak_plus(build_claim_graph(atoms))
    methods = build_method_reproduction_set(build_method_graph(atoms))
    counts = count_evidence_risk(claims, methods)
    return claims, methods, counts


def test_v18_cli_commands():
    assert VERSION == "1.8.0"
    assert run_cli(["version"]) == "omega-absorb 1.8.0\n"
    assert run_cli(["evidence-risk", "--source", "combined"]).startswith("# Evidence Risk Count")
    assert "packets" in run_cli(["oak-manifest-plus", "--source", "combined"])
    assert run_cli(["oak-lineage", "--source", "combined"]).startswith("packet_id | lineage")
    assert run_cli(["mminus-apply", "--mminus-context", "unknown_source"]).startswith("# M-minus Decision")
    assert run_cli(["oak-ledger", "--source", "combined"]).startswith("# Evidence Risk Count")


def test_evidence_risk_counter():
    _, _, counts = _claims_methods_counts()
    assert counts.evidence_count >= 0
    assert counts.risk_count >= 0
    assert render_evidence_risk_count(counts).startswith("# Evidence Risk Count")


def test_oak_manifest_plus_and_lineage():
    _, _, counts = _claims_methods_counts()
    twin = build_poly_research_twin_v2(select_demo_records("combined"))
    actions = compile_top_next_actions(twin)
    manifest = build_oak_packet_manifest_plus(actions.actions, counts, source_id="combined")
    assert manifest.packets
    assert "lineage" in manifest.manifest_json
    ledger = build_oak_lineage_ledger(manifest)
    assert ledger.entries
    assert render_oak_lineage_ledger(ledger).startswith("packet_id | lineage")


def test_mminus_rules_engine():
    decision = apply_mminus_rules({"strict_version_test": True})
    assert decision.decision == "relax_version_assertion"
    assert render_mminus_decision(decision).startswith("# M-minus Decision")


def test_oak_ledger_bundle():
    bundle = build_oak_ledger_bundle("combined")
    assert bundle.counts
    assert bundle.manifest_plus.packets
    assert render_oak_ledger_bundle(bundle).startswith("# Evidence Risk Count")
