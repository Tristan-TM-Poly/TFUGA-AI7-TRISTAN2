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


def main() -> None:
    records = GenericPublicMetadataAdapter().normalize(demo_public_research_records())
    absorption = absorb_public_records(records)
    ranking = rank_opportunity_bundles(compile_research_opportunities(absorption.atoms))
    genomes = build_all_professor_genomes(absorption.atoms)
    reports = render_all_professor_backlogs(genomes, ranking)
    graph = research_atoms_to_professor_graph(absorption.atoms)
    print([(item.rank, item.atom_id, item.score) for item in ranking.ranked])
    print([report.professor for report in reports])
    print(len(graph.nodes), len(graph.edges))


if __name__ == "__main__":
    main()
