from sage_tristan.daily_omega_briefing import BriefingItem, OakCheck, Source
from sage_tristan.daily_omega_intelligence_os import (
    build_agent_security_ledger,
    build_critical_material_dependency,
    build_daily_dashboard,
    build_funding_signal,
    build_infrastructure_dependency,
    build_oak_validation_route,
    build_observability_signal,
    compile_signal_genome,
)


def make_v3_item():
    return BriefingItem(
        title="Agent security and critical minerals compute signal",
        topic_anchor="world_tech_geopolitics",
        signal_type=("opportunity", "agent", "funding"),
        why_it_matters="AI agents need secure cloud GPU infrastructure, HBM memory, energy, and indium supply chains.",
        actionable_opportunity="Build an audit service and benchmark tracker for agent security, compute risk, and critical minerals.",
        oak_check=OakCheck(
            claim_status="prototype_opportunity",
            risk="Agent actions can fail through permission misuse, weak observability, IP leakage, and supply-chain overconfidence.",
            falsification_route="Reject if source traceability, safety checks, and infrastructure assumptions cannot be verified.",
            m_minus_warning="Do not promote agent automation without permission logs, rollback, and source verification.",
        ),
        sources=(
            Source(
                title="Placeholder source",
                source_type="news",
                url_or_identifier="source_required:agent-security-compute",
                source_quality=1,
            ),
        ),
        next_action="Verify source, define permission scope, and create a 2-hour benchmark matrix.",
        scores={
            "freshness": 5,
            "credibility": 2,
            "tristan_fit": 5,
            "actionability": 5,
            "leverage": 5,
            "oak_clarity": 5,
            "ip_revenue": 5,
            "source_penalty": 3,
        },
        business_funding_signal="Grant, government program, enterprise customer, strategic partner, and audit service potential.",
        ip_signal="Prior-art and confidential IP review required before public disclosure.",
    )


def test_v3_ledgers_detect_agent_funding_infrastructure_and_materials():
    item = make_v3_item()

    security = build_agent_security_ledger(item)
    observability = build_observability_signal(item)
    funding = build_funding_signal(item)
    infrastructure = build_infrastructure_dependency(item)
    materials = build_critical_material_dependency(item)

    assert security.permission_scope == "read_only"
    assert security.human_approval_required
    assert "tool_misuse" in security.abuse_cases
    assert "task_success_rate" in observability.metrics
    assert "grant_possible" in funding.routes
    assert "customer_budget_possible" in funding.routes
    assert infrastructure.risk_level == "high"
    assert "gpu" in infrastructure.dependencies
    assert "hbm" in infrastructure.dependencies
    assert "indium" in materials.materials


def test_v3_oak_route_blocks_weak_source_and_ip_risk():
    item = make_v3_item()
    genome = compile_signal_genome(item)
    route = build_oak_validation_route(item, genome.ip_risk_level)

    assert genome.ip_risk_level in {"medium_prior_art_needed", "high_confidential_invention"}
    assert route.blocking_check == "source_upgrade_check"
    assert not route.promotion_allowed


def test_v3_genome_export_and_dashboard_include_new_fields():
    genome = compile_signal_genome(make_v3_item())
    exported = genome.to_dict()
    dashboard = build_daily_dashboard([genome])

    for field in (
        "agent_security_ledger",
        "observability_signal",
        "funding_signal",
        "ip_risk_level",
        "infrastructure_dependency",
        "critical_material_dependency",
        "oak_validation_route",
    ):
        assert field in exported

    assert exported["oak_validation_route"]["blocking_check"] == "source_upgrade_check"
    assert dashboard["top_infrastructure_risk"] == genome.title
    assert dashboard["top_agent_security_risk"] == genome.title
