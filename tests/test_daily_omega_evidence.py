from datetime import date
import json

from sage_tristan.daily_omega_briefing import BriefingItem, OakCheck, Source
from sage_tristan.daily_omega_evidence import (
    build_evidence_from_directory,
    build_evidence_graph,
    build_evidence_result,
    find_claim_gaps,
    find_counter_hypothesis_gaps,
    infer_support_level,
    render_evidence_markdown,
)
from sage_tristan.daily_omega_intelligence_os import compile_signal_genome


def make_item(source_quality: int, identifier: str, *, title: str = "Evidence signal") -> BriefingItem:
    return BriefingItem(
        title=title,
        topic_anchor="ai_automation_agents",
        signal_type=("opportunity", "agent"),
        why_it_matters="This agent signal needs evidence before strategic promotion.",
        actionable_opportunity="Build an EvidenceGraph and compare it against OAK blockers.",
        oak_check=OakCheck(
            claim_status="prototype_opportunity",
            risk="The claim may be weak without source support, observability, and counter-hypotheses.",
            falsification_route="Reject if the EvidenceGraph lacks source support or a counter-hypothesis.",
            m_minus_warning="Do not promote claims without source support and falsification.",
        ),
        sources=(
            Source(
                title="Evidence source",
                source_type="technical_report",
                url_or_identifier=identifier,
                source_quality=source_quality,
            ),
        ),
        next_action="Create a local EvidenceGraph export.",
        scores={"freshness": 4, "credibility": source_quality, "tristan_fit": 5, "actionability": 4, "oak_clarity": 5},
        business_funding_signal="Audit service possible after source and OAK verification.",
        ip_signal="private_research",
    )


def signal_dict(title: str, source_quality: int, identifier: str):
    return {
        "title": title,
        "topic_anchor": "ai_automation_agents",
        "signal_type": ["opportunity", "agent"],
        "why_it_matters": "This agent signal needs evidence before strategic promotion.",
        "actionable_opportunity": "Build an EvidenceGraph and compare it against OAK blockers.",
        "oak_check": {
            "claim_status": "prototype_opportunity",
            "risk": "The claim may be weak without source support, observability, and counter-hypotheses.",
            "falsification_route": "Reject if the EvidenceGraph lacks source support or a counter-hypothesis.",
            "m_minus_warning": "Do not promote claims without source support and falsification.",
        },
        "sources": [
            {
                "title": "Evidence source",
                "source_type": "technical_report",
                "url_or_identifier": identifier,
                "source_quality": source_quality,
            }
        ],
        "next_action": "Create a local EvidenceGraph export.",
        "scores": {"freshness": 4, "credibility": source_quality, "tristan_fit": 5, "actionability": 4, "oak_clarity": 5},
        "business_funding_signal": "Audit service possible after source and OAK verification.",
        "ip_signal": "private_research",
    }


def test_evidence_graph_blocks_placeholder_sources():
    genome = compile_signal_genome(make_item(1, "source_required:evidence"))
    graph = build_evidence_graph(genome)

    assert infer_support_level(genome) == "weak"
    assert graph.factual_claims[0].support_level == "weak"
    assert "claim_support_gap" in graph.promotion_blockers
    assert "source_upgrade_check" in graph.promotion_blockers
    assert find_claim_gaps(graph)
    assert not find_counter_hypothesis_gaps(graph)


def test_evidence_graph_strong_source_is_review_ready():
    genome = compile_signal_genome(make_item(4, "example:verified"))
    graph = build_evidence_graph(genome)

    assert infer_support_level(genome) == "strong"
    assert graph.factual_claims[0].support_level == "strong"
    assert "claim_support_gap" not in graph.promotion_blockers
    assert graph.evidence_score.source_quality == 4
    assert graph.counter_hypotheses


def test_evidence_result_json_and_markdown():
    weak = compile_signal_genome(make_item(1, "source_required:weak", title="Weak evidence signal"))
    strong = compile_signal_genome(make_item(4, "example:strong", title="Strong evidence signal"))

    result = build_evidence_result([weak, strong], briefing_date=date(2026, 6, 24))
    payload = json.loads(result.to_json())
    markdown = render_evidence_markdown(result)

    assert not result.is_clear
    assert payload["graphs"][0]["signal_title"] == "Weak evidence signal"
    assert "Daily Ω EvidenceGraph" in markdown
    assert "Counter-hypotheses" in markdown
    assert "claim_support_gap" in markdown


def test_evidence_from_directory(tmp_path):
    path = tmp_path / "signal.json"
    path.write_text(json.dumps(signal_dict("Directory evidence signal", 1, "source_required:dir-evidence")), encoding="utf-8")

    result = build_evidence_from_directory(str(tmp_path), briefing_date=date(2026, 6, 24))

    assert len(result.graphs) == 1
    assert result.graphs[0].signal_title == "Directory evidence signal"
    assert result.graphs[0].promotion_blockers
    assert not result.is_clear
