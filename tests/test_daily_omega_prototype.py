from datetime import date
import json

from sage_tristan.daily_omega_briefing import BriefingItem, OakCheck, Source
from sage_tristan.daily_omega_intelligence_os import compile_signal_genome
from sage_tristan.daily_omega_prototype import (
    build_prototype_from_directory,
    build_prototype_plan,
    build_prototype_result,
    collect_prototype_blockers,
    render_prototype_markdown,
)


def make_item(source_quality: int, identifier: str, *, ip_signal: str = "private_research") -> BriefingItem:
    return BriefingItem(
        title="Prototype signal",
        topic_anchor="ai_automation_agents",
        signal_type=("opportunity", "agent"),
        why_it_matters="This agent prototype needs source support, dry-run safety, and observable results.",
        actionable_opportunity="Build a prototype benchmark tracker and export local JSON evidence.",
        oak_check=OakCheck(
            claim_status="prototype_opportunity",
            risk="Unsafe prototype claims can overstate progress without source support or baselines.",
            falsification_route="Reject if the prototype cannot produce reproducible local evidence.",
            m_minus_warning="Do not claim prototype victory without source support, dry-run, and baseline.",
        ),
        sources=(
            Source(
                title="Prototype source",
                source_type="technical_report",
                url_or_identifier=identifier,
                source_quality=source_quality,
            ),
        ),
        next_action="Create the P0 source note and P1 dry-run stub.",
        scores={"freshness": 4, "credibility": source_quality, "tristan_fit": 5, "actionability": 5, "oak_clarity": 5},
        business_funding_signal="Audit service and benchmark report possible after OAK review.",
        ip_signal=ip_signal,
    )


def signal_dict(title: str, source_quality: int, identifier: str):
    return {
        "title": title,
        "topic_anchor": "ai_automation_agents",
        "signal_type": ["opportunity", "agent"],
        "why_it_matters": "This agent prototype needs source support, dry-run safety, and observable results.",
        "actionable_opportunity": "Build a prototype benchmark tracker and export local JSON evidence.",
        "oak_check": {
            "claim_status": "prototype_opportunity",
            "risk": "Unsafe prototype claims can overstate progress without source support or baselines.",
            "falsification_route": "Reject if the prototype cannot produce reproducible local evidence.",
            "m_minus_warning": "Do not claim prototype victory without source support, dry-run, and baseline.",
        },
        "sources": [
            {
                "title": "Prototype source",
                "source_type": "technical_report",
                "url_or_identifier": identifier,
                "source_quality": source_quality,
            }
        ],
        "next_action": "Create the P0 source note and P1 dry-run stub.",
        "scores": {"freshness": 4, "credibility": source_quality, "tristan_fit": 5, "actionability": 5, "oak_clarity": 5},
        "business_funding_signal": "Audit service and benchmark report possible after OAK review.",
        "ip_signal": "private_research",
    }


def test_prototype_plan_starts_at_p0_when_source_is_blocking():
    genome = compile_signal_genome(make_item(1, "source_required:prototype"))
    plan = build_prototype_plan(genome)

    assert plan.recommended_start == "P0"
    assert "claim_support_gap" in plan.blockers
    assert "source_upgrade_check" in plan.blockers
    assert len(plan.steps) == 5
    assert plan.steps[0].level == "P0"
    assert plan.steps[0].artifact == "source_note.md"


def test_prototype_plan_marks_private_artifacts_for_confidential_ip():
    genome = compile_signal_genome(make_item(4, "example:strong", ip_signal="confidential invention and patentable trade secret"))
    blockers = collect_prototype_blockers(genome, __import__("sage_tristan.daily_omega_evidence", fromlist=["build_evidence_graph"]).build_evidence_graph(genome))
    plan = build_prototype_plan(genome)

    assert "private_only_ip_review" in blockers
    assert plan.steps[0].artifact.startswith("private_")
    assert not plan.steps[-1].allowed_public


def test_prototype_result_json_and_markdown():
    genome = compile_signal_genome(make_item(4, "example:verified"))
    result = build_prototype_result([genome], briefing_date=date(2026, 6, 24))
    payload = json.loads(result.to_json())
    markdown = render_prototype_markdown(result)

    assert payload["plans"][0]["signal_title"] == "Prototype signal"
    assert payload["plans"][0]["steps"][0]["level"] == "P0"
    assert "Daily Ω PrototypeCompiler" in markdown
    assert "P0 / 15_min" in markdown
    assert "benchmark_result.json" in markdown


def test_prototype_from_directory(tmp_path):
    path = tmp_path / "signal.json"
    path.write_text(json.dumps(signal_dict("Directory prototype signal", 4, "example:dir-prototype")), encoding="utf-8")

    result = build_prototype_from_directory(str(tmp_path), briefing_date=date(2026, 6, 24))

    assert len(result.plans) == 1
    assert result.plans[0].signal_title == "Directory prototype signal"
    assert result.plans[0].steps[1].level == "P1"
