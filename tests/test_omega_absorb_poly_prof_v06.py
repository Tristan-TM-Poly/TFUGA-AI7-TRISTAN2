from omega_prof_poly_t import (
    ExpertiseLikeAdapter,
    PolyPublieLikeAdapter,
    absorb_public_records,
    build_all_professor_genomes,
    build_report_artifacts,
    compile_research_opportunities,
    demo_public_research_records,
    optimize_portfolio,
    professor_graph_to_graphml,
    professor_graph_to_json,
    rank_opportunity_bundles,
    render_all_professor_backlogs,
    render_backlog_packet,
    research_atoms_to_professor_graph,
)


def test_specialized_adapters_normalize_public_records():
    poly = PolyPublieLikeAdapter().normalize([{"identifier": "p1", "dc.title": "Paper", "dc.creator": ["A"]}])
    expertise = ExpertiseLikeAdapter().normalize([{"name": "Prof", "expertise": ["AI"]}])
    assert poly[0]["atom_id"] == "p1"
    assert poly[0]["title"] == "Paper"
    assert expertise[0]["professors"] == ("Prof",)
    assert "AI" in expertise[0]["keywords"]


def test_portfolio_optimizer_selects_ranked_items():
    absorption = absorb_public_records(demo_public_research_records())
    ranking = rank_opportunity_bundles(compile_research_opportunities(absorption.atoms))
    portfolio = optimize_portfolio(ranking, max_items=1)
    assert len(portfolio.selected) == 1
    assert portfolio.objective == "maximize_score_with_path_diversity"
    assert portfolio.next_action == "render_portfolio_backlog"


def test_report_artifact_manifest_includes_manifest_json():
    absorption = absorb_public_records(demo_public_research_records())
    ranking = rank_opportunity_bundles(compile_research_opportunities(absorption.atoms))
    reports = render_all_professor_backlogs(build_all_professor_genomes(absorption.atoms), ranking)
    manifest = build_report_artifacts(reports)
    assert manifest.artifacts
    assert manifest.artifacts[-1].path.endswith("manifest.json")
    assert manifest.artifacts[-1].kind == "manifest"


def test_graph_exports_produce_json_and_graphml():
    absorption = absorb_public_records(demo_public_research_records())
    graph = research_atoms_to_professor_graph(absorption.atoms)
    json_text = professor_graph_to_json(graph)
    graphml_text = professor_graph_to_graphml(graph)
    assert "nodes" in json_text
    assert "<graphml" in graphml_text
    assert "research_atom" in json_text


def test_backlog_packet_template_renders_selection():
    absorption = absorb_public_records(demo_public_research_records())
    ranking = rank_opportunity_bundles(compile_research_opportunities(absorption.atoms))
    portfolio = optimize_portfolio(ranking, max_items=2)
    packet = render_backlog_packet(portfolio)
    assert packet.title == "Omega Absorb Portfolio Backlog"
    assert "Selected items" in packet.body
    assert "omega-absorb" in packet.labels
