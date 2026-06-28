from omega_prof_poly_t import (
    absorb_public_records,
    build_all_professor_genomes,
    demo_combined_fixture_records,
    default_public_source_registry,
    generate_fixture_artifacts,
    recommend_collaborations,
    render_collaboration_markdown,
    score_department_bridge,
)


def main() -> None:
    records = demo_combined_fixture_records()
    absorption = absorb_public_records(records)
    genomes = build_all_professor_genomes(absorption.atoms)
    run = generate_fixture_artifacts(records)
    bridge = score_department_bridge(genomes)
    plan = recommend_collaborations(genomes)
    markdown = render_collaboration_markdown(plan)
    registry = default_public_source_registry()
    print("records", len(records))
    print("summary", run.summary.summary_id, run.summary.count)
    print("bridge", bridge.score, bridge.departments)
    print("plan_items", markdown.item_count)
    print("sources", sorted(registry.as_dict().keys()))


if __name__ == "__main__":
    main()
