from omega_prof_poly_t import (
    compile_portfolio_roadmap,
    demo_combined_fixture_records,
    generate_fixture_artifacts,
    optimize_portfolio,
    rank_opportunity_bundles,
    render_department_bridge_report,
    render_roadmap_markdown,
    run_v09_e2e_pipeline,
    score_department_bridge,
    validate_public_records,
    absorb_public_records,
    build_all_professor_genomes,
    compile_research_opportunities,
)


def test_validate_public_records_returns_report():
    report = validate_public_records(demo_combined_fixture_records())
    assert report.valid_count + report.invalid_count == len(demo_combined_fixture_records())
    assert report.next_action == "normalize_valid_records_and_route_findings"


def test_roadmap_compiler_renders_steps():
    absorption = absorb_public_records(demo_combined_fixture_records())
    ranking = rank_opportunity_bundles(compile_research_opportunities(absorption.atoms))
    portfolio = optimize_portfolio(ranking, max_items=2)
    roadmap = compile_portfolio_roadmap(portfolio)
    text = render_roadmap_markdown(roadmap)
    assert roadmap.next_action == "render_roadmap_markdown"
    assert text.startswith("# Omega Absorb Roadmap")


def test_department_bridge_report_renders_markdown():
    absorption = absorb_public_records(demo_combined_fixture_records())
    genomes = build_all_professor_genomes(absorption.atoms)
    score = score_department_bridge(genomes)
    report = render_department_bridge_report(score)
    assert report.markdown.startswith("# Department Bridge Report")
    assert report.score == score.score


def test_fixture_artifacts_still_generate():
    run = generate_fixture_artifacts(demo_combined_fixture_records())
    assert run.summary.count == len(run.manifest.artifacts)
    assert run.next_action == "persist_fixture_artifacts"


def test_v09_e2e_pipeline_runs():
    result = run_v09_e2e_pipeline()
    assert result.artifact_run.manifest.artifacts
    assert result.department_report.markdown
    assert result.collaboration_markdown.markdown
    assert result.roadmap.steps
    assert result.next_action == "persist_e2e_artifacts"
