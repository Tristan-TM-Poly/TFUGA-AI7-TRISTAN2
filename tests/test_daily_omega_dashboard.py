from datetime import date
import json

from sage_tristan.daily_omega_batch import DEFAULT_TIMEZONE
from sage_tristan.daily_omega_dashboard import (
    build_dashboard_from_directory,
    build_dashboard_result,
    render_dashboard_markdown,
)
from sage_tristan.daily_omega_intelligence_os import compile_signal_genome
from sage_tristan.daily_omega_io import item_from_dict


def make_signal(title: str, score: int):
    return {
        "title": title,
        "topic_anchor": "ai_automation_agents",
        "signal_type": ["opportunity", "agent"],
        "why_it_matters": "This signal needs agent observability, source traceability, and OAK review.",
        "actionable_opportunity": "Build an audit service and benchmark tracker for agent reliability.",
        "oak_check": {
            "claim_status": "prototype_opportunity",
            "risk": "The agentic claim may be overhyped without logs, rollback, or measurable task completion.",
            "falsification_route": "Reject if task success rate and source traceability cannot be measured.",
        },
        "sources": [
            {
                "title": "Dashboard source",
                "source_type": "technical_report",
                "url_or_identifier": "example:dashboard",
                "source_quality": 4,
            }
        ],
        "next_action": "Create a dashboard and inspect the top OAK warning.",
        "scores": {
            "freshness": score,
            "credibility": score,
            "tristan_fit": score,
            "actionability": score,
            "oak_clarity": score,
            "ip_revenue": score,
        },
        "business_funding_signal": "Audit service and customer budget possible.",
        "ip_signal": "private_research",
    }


def test_build_dashboard_result_from_genomes():
    item = item_from_dict(make_signal("Dashboard signal", 5))
    genome = compile_signal_genome(item)

    result = build_dashboard_result([genome], briefing_date=date(2026, 6, 24), timezone=DEFAULT_TIMEZONE)

    assert result.dashboard["top_signal"] == "Dashboard signal"
    assert result.dashboard["top_agent_security_risk"] == "Dashboard signal"
    assert result.timezone == "Europe/Paris"
    assert "Dashboard signal" in result.dashboard_json()


def test_build_dashboard_from_directory_and_render_markdown(tmp_path):
    signal_path = tmp_path / "signal.json"
    signal_path.write_text(json.dumps(make_signal("File dashboard signal", 4)), encoding="utf-8")

    result = build_dashboard_from_directory(
        str(tmp_path),
        briefing_date=date(2026, 6, 24),
        timezone=DEFAULT_TIMEZONE,
    )
    markdown = render_dashboard_markdown(result)

    assert result.dashboard["top_signal"] == "File dashboard signal"
    assert "Daily Ω Dashboard" in markdown
    assert "Timezone: `Europe/Paris`" in markdown
    assert "top_next_action" in markdown
    assert "1 compiled SignalGenome++" in markdown


def test_dashboard_json_is_parseable(tmp_path):
    signal_path = tmp_path / "signal.json"
    signal_path.write_text(json.dumps(make_signal("Parseable dashboard signal", 4)), encoding="utf-8")

    result = build_dashboard_from_directory(
        str(tmp_path),
        briefing_date=date(2026, 6, 24),
        timezone=DEFAULT_TIMEZONE,
    )
    payload = json.loads(result.dashboard_json())

    assert payload["top_signal"] == "Parseable dashboard signal"
    assert "top_oak_warning" in payload
    assert "top_infrastructure_risk" in payload
