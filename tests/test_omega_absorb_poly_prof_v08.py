from omega_prof_poly_t import (
    absorb_public_records,
    build_all_professor_genomes,
    combine_fixture_records,
    demo_combined_fixture_records,
    default_public_source_registry,
    generate_fixture_artifacts,
    recommend_collaborations,
    render_collaboration_markdown,
    score_department_bridge,
    score_recommendation_bridge,
)


def test_combined_fixture_loader_merges_record_families():
    records = combine_fixture_records(
        polypublie_like=({"identifier": "p", "dc.title": "Paper"},),
        expertise_like=({"id": "e", "name": "Prof", "expertise": ["AI"]},),
    )
    assert len(records) == 2
    assert records[0]["atom_id"] == "p"
    assert records[1]["atom_id"] == "e"


def test_fixture_artifact_generator_produces_summary():
    run = generate_fixture_artifacts(demo_combined_fixture_records())
    assert run.manifest.artifacts
    assert run.summary.count == len(run.manifest.artifacts)
    assert run.ranking_count > 0
    assert run.professor_count > 0


def test_department_bridge_scoring_uses_genomes():
    absorption = absorb_public_records(demo_combined_fixture_records())
    genomes = build_all_professor_genomes(absorption.atoms)
    bridge = score_department_bridge(genomes)
    assert bridge.score > 0
    assert bridge.professor_count == len(genomes)
    assert bridge.next_action == "use_bridge_score_to_rank_pairing_plan"


def test_collaboration_markdown_renders_plan():
    absorption = absorb_public_records(demo_combined_fixture_records())
    genomes = build_all_professor_genomes(absorption.atoms)
    plan = recommend_collaborations(genomes)
    markdown = render_collaboration_markdown(plan)
    assert markdown.markdown.startswith("# Collaboration Plan")
    assert markdown.item_count == len(plan.recommendations)
    if plan.recommendations:
        assert score_recommendation_bridge(plan.recommendations[0]) >= plan.recommendations[0].score


def test_public_source_registry_contains_defaults():
    registry = default_public_source_registry()
    data = registry.as_dict()
    assert "polypublie_like" in data
    assert "expertise_like" in data
    assert "demo_fixture" in data
