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


def test_artifact_summary_is_deterministic():
    absorption = absorb_public_records(demo_public_research_records())
    reports = render_all_professor_backlogs(build_all_professor_genomes(absorption.atoms))
    manifest = build_report_artifacts(reports)
    summary1 = build_artifact_summary(manifest)
    summary2 = build_artifact_summary(manifest)
    assert summary1.summary_id == summary2.summary_id
    assert summary1.count == len(manifest.artifacts)
    assert summary1.json == summary2.json


def test_recommender_returns_plan_object():
    absorption = absorb_public_records(demo_public_research_records())
    genomes = build_all_professor_genomes(absorption.atoms)
    plan = recommend_collaborations(genomes)
    assert plan.next_action == "render_collaboration_backlog"
    assert isinstance(plan.recommendations, tuple)


def test_enriched_graphml_contains_keys_and_metadata():
    absorption = absorb_public_records(demo_public_research_records())
    graph = research_atoms_to_professor_graph(absorption.atoms)
    text = professor_graph_to_enriched_graphml(graph)
    assert "ProfessorGraphPoly" in text
    assert "attr.name=\"kind\"" in text
    assert "attr.name=\"relation\"" in text
    assert "research_atom" in text
