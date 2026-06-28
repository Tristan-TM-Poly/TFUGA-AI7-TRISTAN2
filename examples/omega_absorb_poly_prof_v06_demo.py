from omega_prof_poly_t import (
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


def main() -> None:
    records = PolyPublieLikeAdapter().normalize(demo_public_research_records())
    absorption = absorb_public_records(records)
    ranking = rank_opportunity_bundles(compile_research_opportunities(absorption.atoms))
    portfolio = optimize_portfolio(ranking, max_items=2)
    genomes = build_all_professor_genomes(absorption.atoms)
    reports = render_all_professor_backlogs(genomes, ranking)
    manifest = build_report_artifacts(reports)
    graph = research_atoms_to_professor_graph(absorption.atoms)
    packet = render_backlog_packet(portfolio)
    print("portfolio", [(item.rank, item.atom_id) for item in portfolio.selected])
    print("artifacts", [(item.path, item.digest) for item in manifest.artifacts])
    print("graph_json_len", len(professor_graph_to_json(graph)))
    print("graphml_len", len(professor_graph_to_graphml(graph)))
    print("packet", packet.title, packet.labels)


if __name__ == "__main__":
    main()
