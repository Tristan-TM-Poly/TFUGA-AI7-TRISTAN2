from omega_prof_poly_t import (
    GenericPublicMetadataAdapter,
    absorb_public_records,
    build_all_professor_genomes,
    compile_research_opportunities,
    demo_public_research_records,
    rank_opportunity_bundles,
    render_all_professor_backlogs,
    research_atoms_to_professor_graph,
)


def test_generic_public_metadata_adapter_normalizes_records():
    records = GenericPublicMetadataAdapter().normalize([{"id": "x", "name": "Demo", "creators": ["A"], "url": "u"}])
    assert records[0]["atom_id"] == "x"
    assert records[0]["title"] == "Demo"
    assert records[0]["authors"] == ["A"]
    assert records[0]["link"] == "u"


def test_rank_opportunity_bundles_orders_results():
    absorption = absorb_public_records(demo_public_research_records())
    compilation = compile_research_opportunities(absorption.atoms)
    ranking = rank_opportunity_bundles(compilation)
    assert len(ranking.ranked) == absorption.total
    assert ranking.ranked[0].rank == 1
    assert ranking.top_next_action
    assert ranking.ranked[0].score >= ranking.ranked[-1].score


def test_professor_backlog_reports_render_markdown():
    absorption = absorb_public_records(demo_public_research_records())
    ranking = rank_opportunity_bundles(compile_research_opportunities(absorption.atoms))
    genomes = build_all_professor_genomes(absorption.atoms)
    reports = render_all_professor_backlogs(genomes, ranking)
    assert reports
    assert reports[0].markdown.startswith("# Professor Backlog")
    assert "## Course opportunities" in reports[0].markdown


def test_research_atoms_to_professor_graph_integrates_nodes_and_edges():
    absorption = absorb_public_records(demo_public_research_records())
    graph = research_atoms_to_professor_graph(absorption.atoms)
    assert graph.nodes
    assert graph.edges
    assert any(node.kind == "research_atom" for node in graph.nodes.values())
    assert any(edge.relation == "uses_method" for edge in graph.edges.values())
