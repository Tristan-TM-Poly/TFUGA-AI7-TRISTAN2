import json

from sage_tristan.daily_omega_io import (
    export_decision_dict,
    export_decision_json,
    export_decision_markdown,
    item_from_dict,
)


def signal_dict():
    return {
        "title": "Portable reusable signal",
        "topic_anchor": "ai_automation_agents",
        "signal_type": ["opportunity", "tooling"],
        "why_it_matters": "This portable object can produce reports, issue specs, and memory updates.",
        "actionable_opportunity": "Run the signal through the reusable supervisor in dry-run mode.",
        "oak_check": {
            "claim_status": "prototype_opportunity",
            "risk": "The object may be under-sourced or too vague.",
            "falsification_route": "Reject or revise if the generated issue lacks a concrete test.",
            "m_minus_warning": "Do not promote portable signals without OAK review.",
        },
        "sources": [
            {
                "title": "Portable source",
                "source_type": "technical_report",
                "url_or_identifier": "example:portable",
                "source_quality": 4,
            }
        ],
        "next_action": "Generate a reviewable issue spec.",
        "business_funding_signal": "Reusable workflow primitive.",
        "ip_signal": "private_research",
        "scores": {
            "freshness": 5,
            "credibility": 4,
            "tristan_fit": 5,
            "actionability": 5,
            "leverage": 4,
            "oak_clarity": 5,
        },
    }


def test_item_from_dict_builds_briefing_item():
    item = item_from_dict(signal_dict())

    assert item.title == "Portable reusable signal"
    assert item.topic_anchor == "ai_automation_agents"
    assert item.sources[0].source_quality == 4


def test_export_decision_dict_is_json_safe():
    item = item_from_dict(signal_dict())
    exported = export_decision_dict(item)

    assert exported["title"] == item.title
    assert "canon_branches" in exported
    assert "issue_spec" in exported
    json.dumps(exported)


def test_export_decision_json_contains_supervision():
    item = item_from_dict(signal_dict())
    exported = export_decision_json(item)

    assert "supervision" in exported
    assert "review_spec" in exported


def test_export_decision_markdown_contains_issue_body():
    item = item_from_dict(signal_dict())
    markdown = export_decision_markdown(item)

    assert "Daily Omega Decision" in markdown
    assert "## Signal" in markdown
    assert "## OAK check" in markdown
