from omega_prof_poly_t import (
    absorb_public_records,
    build_claim_graph,
    build_method_graph,
    compile_atom_opportunities,
    compile_research_opportunities,
    demo_public_research_records,
    packet_digest,
    to_deterministic_json,
)


def test_claim_graph_builds_claim_nodes():
    absorption = absorb_public_records(demo_public_research_records())
    graph = build_claim_graph(absorption.atoms)
    assert graph.claims
    assert graph.claims_by_atom()
    assert graph.next_action == "compile_claims_to_tests_and_research_opportunities"


def test_method_graph_builds_method_nodes():
    absorption = absorb_public_records(demo_public_research_records())
    graph = build_method_graph(absorption.atoms)
    assert graph.methods
    assert graph.methods_by_domain()
    assert graph.next_action == "route_reusable_methods_to_course_lab_project_compilers"


def test_deterministic_json_export_is_stable():
    data = {"b": 2, "a": [1, 2]}
    text1 = to_deterministic_json(data)
    text2 = to_deterministic_json(data)
    assert text1 == text2
    assert text1.endswith("\n")
    assert packet_digest(data) == packet_digest(data)


def test_compile_atom_opportunities_routes_to_all_packets():
    absorption = absorb_public_records(demo_public_research_records())
    bundle = compile_atom_opportunities(absorption.atoms[0])
    assert bundle.course_packet.course_title.startswith("Research module:")
    assert bundle.project_packet.deliverables
    assert bundle.grant_packet.workpackages
    assert bundle.ip_packet.next_action == "generate_ip_summary_and_prior_art_search_plan"


def test_compile_research_opportunities_creates_bundle_per_atom():
    absorption = absorb_public_records(demo_public_research_records())
    compilation = compile_research_opportunities(absorption.atoms)
    assert len(compilation.bundles) == absorption.total
    assert compilation.next_action == "rank_bundles_and_generate_professor_backlogs"
