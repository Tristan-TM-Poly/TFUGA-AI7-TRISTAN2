from omega_prof_poly_t import (
    absorb_public_records,
    build_all_professor_genomes,
    build_artifact_summary,
    build_report_artifacts,
    demo_public_research_records,
    professor_graph_to_enriched_graphml,
    recommend_collaborations,
    render_all_professor_backlogs,
    research_atoms_to_professor_graph,
)


def main() -> None:
    absorption = absorb_public_records(demo_public_research_records())
    genomes = build_all_professor_genomes(absorption.atoms)
    reports = render_all_professor_backlogs(genomes)
    manifest = build_report_artifacts(reports)
    summary = build_artifact_summary(manifest)
    graph = research_atoms_to_professor_graph(absorption.atoms)
    plan = recommend_collaborations(genomes)
    print("summary", summary.summary_id, summary.count)
    print("pair_count", len(plan.recommendations))
    print("graphml_len", len(professor_graph_to_enriched_graphml(graph)))


if __name__ == "__main__":
    main()
