from datetime import date
import json

from sage_tristan.daily_omega_briefing import BriefingItem, OakCheck, Source
from sage_tristan.daily_omega_intelligence_os import compile_signal_genome
from sage_tristan.daily_omega_io import item_from_dict
from sage_tristan.daily_omega_verify import (
    build_verification_from_directory,
    build_verification_result,
    find_source_gaps,
    render_verification_markdown,
)


def make_item(source_quality: int, identifier: str) -> BriefingItem:
    return BriefingItem(
        title="Verification signal",
        topic_anchor="ai_automation_agents",
        signal_type=("opportunity",),
        why_it_matters="This signal needs source verification before promotion.",
        actionable_opportunity="Build a source verification checklist.",
        oak_check=OakCheck(
            claim_status="prototype_opportunity",
            risk="Weak sources can promote false signals.",
            falsification_route="Reject if the source cannot be upgraded or corroborated.",
        ),
        sources=(
            Source(
                title="Candidate source",
                source_type="news",
                url_or_identifier=identifier,
                source_quality=source_quality,
            ),
        ),
        next_action="Upgrade the source before promotion.",
        scores={"freshness": 4, "credibility": source_quality, "tristan_fit": 4, "actionability": 4},
    )


def make_signal_dict(title: str, source_quality: int, identifier: str):
    return {
        "title": title,
        "topic_anchor": "ai_automation_agents",
        "signal_type": ["opportunity"],
        "why_it_matters": "This signal needs source verification before promotion.",
        "actionable_opportunity": "Build a source verification checklist.",
        "oak_check": {
            "claim_status": "prototype_opportunity",
            "risk": "Weak sources can promote false signals.",
            "falsification_route": "Reject if the source cannot be upgraded or corroborated.",
        },
        "sources": [
            {
                "title": "Candidate source",
                "source_type": "news",
                "url_or_identifier": identifier,
                "source_quality": source_quality,
            }
        ],
        "next_action": "Upgrade the source before promotion.",
        "scores": {"freshness": 4, "credibility": source_quality, "tristan_fit": 4, "actionability": 4},
    }


def test_placeholder_source_is_blocking_gap():
    genome = compile_signal_genome(make_item(1, "source_required:daily-omega"))

    gaps = find_source_gaps(genome)

    assert len(gaps) == 1
    assert gaps[0].verification_status == "source_placeholder"
    assert gaps[0].blocking
    assert "Replace placeholder" in gaps[0].next_check


def test_source_found_gap_requires_corroboration_but_is_not_blocking():
    genome = compile_signal_genome(make_item(2, "example:weak-source"))

    gaps = find_source_gaps(genome)

    assert len(gaps) == 1
    assert gaps[0].verification_status == "source_found"
    assert not gaps[0].blocking
    assert "Corroborate" in gaps[0].next_check


def test_verified_source_has_clear_result():
    genome = compile_signal_genome(make_item(4, "example:strong-source"))

    result = build_verification_result([genome], briefing_date=date(2026, 6, 24))

    assert result.checked_signals == 1
    assert result.is_clear
    assert result.gaps == ()
    assert "\"is_clear\": true" in result.to_json()


def test_verification_from_directory_outputs_markdown_and_json(tmp_path):
    path = tmp_path / "signal.json"
    path.write_text(json.dumps(make_signal_dict("Directory verification signal", 1, "source_required:dir")), encoding="utf-8")

    result = build_verification_from_directory(str(tmp_path), briefing_date=date(2026, 6, 24))
    markdown = render_verification_markdown(result)
    payload = json.loads(result.to_json())

    assert not result.is_clear
    assert payload["gaps"][0]["signal_title"] == "Directory verification signal"
    assert "Daily Ω Source Verification" in markdown
    assert "source_required:dir" in markdown
    assert "Clear for promotion: `false`" in markdown


def test_item_from_dict_still_compiles_for_verification():
    item = item_from_dict(make_signal_dict("Portable verification signal", 4, "example:portable"))
    genome = compile_signal_genome(item)
    result = build_verification_result([genome], briefing_date=date(2026, 6, 24))

    assert result.is_clear
