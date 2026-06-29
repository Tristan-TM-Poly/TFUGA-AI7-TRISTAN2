from omega_prof_poly_t import (
    VERSION,
    build_claim_graph,
    build_claim_oak_plus,
    build_method_graph,
    build_method_reproduction_set,
    default_mminus_registry,
    generate_github_work_packet,
    render_github_packet_markdown,
    render_mminus_markdown,
    run_cli,
    select_demo_records,
    validate_records_against_schema,
)
from omega_prof_poly_t.absorb_public_research import absorb_public_records


def test_v14_cli_commands():
    assert VERSION
    assert run_cli(["version"]).startswith("omega-absorb ")
    assert run_cli(["schema-check", "--source", "combined"]).startswith("accepted=")
    assert run_cli(["mminus"]).startswith("# Omega Absorb M-minus Registry")


def test_source_schema_reports_missing_required_field():
    report = validate_records_against_schema(({"id": "x"},), "generic")
    assert report.rejected_count == 1
    assert any(finding.level == "error" for finding in report.findings)


def test_claim_oak_plus_expands_claims():
    atoms = absorb_public_records(select_demo_records("combined")).atoms
    graph = build_claim_graph(atoms)
    plus = build_claim_oak_plus(graph)
    assert plus.claims
    assert plus.claims[0].counterclaims
    assert "compare_against_counterexample" in plus.claims[0].falsification_tests


def test_method_reproduction_packets():
    atoms = absorb_public_records(select_demo_records("combined")).atoms
    graph = build_method_graph(atoms)
    packets = build_method_reproduction_set(graph)
    assert packets.packets
    assert packets.packets[0].failure_modes
    assert packets.next_action == "rank_methods_by_reproducibility_and_value"


def test_mminus_and_github_packet_renderers():
    registry = default_mminus_registry()
    assert registry.entries
    assert "M-minus" in render_mminus_markdown(registry)
    packet = generate_github_work_packet("claim_oak_plus")
    text = render_github_packet_markdown(packet)
    assert packet.files
    assert text.startswith("# Add claim_oak_plus")
