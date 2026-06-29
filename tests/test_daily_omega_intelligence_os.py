from sage_tristan.daily_omega_briefing import BriefingItem, OakCheck, Source
from sage_tristan.daily_omega_intelligence_os import (
    build_claim_graph,
    build_daily_dashboard,
    build_evidence_matrix,
    build_source_ledger,
    compile_many,
    compile_signal_genome,
    infer_canon_status,
    infer_prototype_horizon,
    infer_revenue_routes,
    render_intelligence_os_markdown,
)


def make_item(
    *,
    title="AgentTelemetry benchmark service",
    source_quality=4,
    source_identifier="example:test",
    business="Audit service and report for agent telemetry.",
    next_action="Build a benchmark tracker in 2 hours.",
):
    return BriefingItem(
        title=title,
        topic_anchor="ai_automation_agents",
        signal_type=("opportunity", "tooling"),
        why_it_matters="This signal can become a reusable Daily Omega strategic asset.",
        actionable_opportunity="Create a benchmark matrix and dry-run issue spec.",
        oak_check=OakCheck(
            claim_status="prototype_opportunity",
            risk="The signal may be overhyped without measurable evidence.",
            falsification_route="Reject if the benchmark cannot produce a measurable result.",
            m_minus_warning="Do not promote weak signals without OAK review.",
        ),
        sources=(
            Source(
                title="Test source",
                source_type="technical_report",
                url_or_identifier=source_identifier,
                source_quality=source_quality,
            ),
        ),
        next_action=next_action,
        scores={
            "freshness": 5,
            "credibility": 4,
            "tristan_fit": 5,
            "actionability": 5,
            "leverage": 5,
            "oak_clarity": 5,
            "ip_revenue": 4,
        },
        business_funding_signal=business,
        ip_signal="private_research",
    )


def test_infer_prototype_horizon_prioritizes_source_verification():
    item = make_item(next_action="Verify the source before promotion.")

    assert infer_prototype_horizon(item) == "15_min"


def test_infer_revenue_routes_detects_audit_report_service():
    routes = infer_revenue_routes(make_item())

    assert "audit" in routes
    assert "report" in routes
    assert "service" in routes


def test_infer_canon_status_requires_source_for_low_quality():
    item = make_item(source_quality=1)

    assert infer_canon_status(item) == "source_required"


def test_source_ledger_detects_placeholder_sources():
    item = make_item(source_quality=1, source_identifier="source_required:daily-omega")
    ledger = build_source_ledger(item)

    assert ledger[0].verification_status == "source_placeholder"
    assert "Replace placeholder" in ledger[0].residue


def test_claim_graph_separates_facts_inferences_and_guards():
    graph = build_claim_graph(make_item())
    claim_types = {claim.claim_type for claim in graph}

    assert "factual_claim" in claim_types
    assert "strategic_inference" in claim_types
    assert "oak_risk" in claim_types
    assert "falsification_route" in claim_types


def test_evidence_matrix_is_bounded_and_contains_residue():
    matrix = build_evidence_matrix(make_item())

    assert 0 <= matrix.source <= 5
    assert 0 <= matrix.prototype <= 5
    assert matrix.residue


def test_compile_signal_genome_is_json_safe():
    genome = compile_signal_genome(make_item())
    exported = genome.to_dict()

    assert exported["title"] == "AgentTelemetry benchmark service"
    assert exported["final_score"] > 0
    assert isinstance(exported["canon_branches"], list)
    assert isinstance(exported["source_ledger"], list)
    assert isinstance(exported["claim_graph"], list)
    assert "evidence_matrix" in exported
    assert "prototype_ladder" in exported
    assert "revenue_physics" in exported
    assert exported["canon_status"] in {
        "raw_signal",
        "imported_signal",
        "source_required",
        "source_verified",
        "oak_reviewed",
        "issue_candidate",
        "prototype_candidate",
        "prior_art_candidate",
        "revenue_candidate",
        "validated",
        "rejected",
        "canon_candidate",
        "canonized",
    }


def test_compile_many_dashboard_and_render_markdown():
    genomes = compile_many([make_item(), make_item(title="Second signal")])
    dashboard = build_daily_dashboard(genomes)
    markdown = render_intelligence_os_markdown(genomes)

    assert len(genomes) == 2
    assert dashboard["top_signal"] == "AgentTelemetry benchmark service"
    assert "Daily Ω Intelligence OS" in markdown
    assert "Dashboard" in markdown
    assert "Prototype horizon" in markdown
    assert "Revenue routes" in markdown
    assert "Revenue physics" in markdown
    assert "Second signal" in markdown
