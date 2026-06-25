from datetime import date

from sage_tristan.daily_omega_batch import (
    build_batch_result,
    discover_signal_files,
    is_signal_json_file,
    load_items_from_directory,
    summarize_batch,
    write_batch_outputs,
)
from sage_tristan.daily_omega_io import item_from_dict


def make_signal(title: str, score: int):
    return {
        "title": title,
        "topic_anchor": "ai_automation_agents",
        "signal_type": ["opportunity"],
        "why_it_matters": "This batch signal can be ranked and exported into a reusable report.",
        "actionable_opportunity": "Generate a batch report and inspect the supervised decisions.",
        "oak_check": {
            "claim_status": "prototype_opportunity",
            "risk": "The batch item may be too vague without a concrete source.",
            "falsification_route": "Reject the item if the generated decision lacks a next action.",
        },
        "sources": [
            {
                "title": "Batch source",
                "source_type": "technical_report",
                "url_or_identifier": "example:batch",
                "source_quality": 4,
            }
        ],
        "next_action": "Create a supervised issue spec in dry-run mode.",
        "scores": {
            "freshness": score,
            "credibility": score,
            "tristan_fit": score,
            "actionability": score,
            "oak_clarity": score,
        },
    }


def test_build_batch_result_ranks_and_exports_decisions_and_genomes():
    low = item_from_dict(make_signal("Low batch signal", 2))
    high = item_from_dict(make_signal("High batch signal", 5))

    result = build_batch_result([low, high], briefing_date=date(2026, 6, 24))

    assert result.items[0].title == "High batch signal"
    assert "Daily Ω Briefing" in result.markdown_report
    assert "Daily Ω War Room" in result.markdown_report
    assert "Daily Ω Intelligence OS" in result.markdown_report
    assert len(result.decisions) == 2
    assert len(result.genomes) == 2
    assert "High batch signal" in result.decisions_json()
    assert "source_ledger" in result.genomes_json()


def test_discover_and_load_directory(tmp_path):
    path = tmp_path / "signal.json"
    path.write_text(__import__("json").dumps(make_signal("File signal", 4)), encoding="utf-8")

    files = discover_signal_files(tmp_path)
    items = load_items_from_directory(tmp_path)

    assert files == [path]
    assert items[0].title == "File signal"


def test_batch_loader_skips_manifest_and_non_signal_json(tmp_path):
    signal_path = tmp_path / "signal.json"
    manifest_path = tmp_path / "manifest.json"
    notes_path = tmp_path / "notes.json"
    signal_path.write_text(__import__("json").dumps(make_signal("Real signal", 4)), encoding="utf-8")
    manifest_path.write_text(__import__("json").dumps({"date": "2026-06-24", "items": 1}), encoding="utf-8")
    notes_path.write_text(__import__("json").dumps({"title": "Not enough keys"}), encoding="utf-8")

    assert is_signal_json_file(signal_path)
    assert not is_signal_json_file(manifest_path)
    assert not is_signal_json_file(notes_path)
    assert discover_signal_files(tmp_path) == [signal_path]
    assert load_items_from_directory(tmp_path)[0].title == "Real signal"


def test_write_batch_outputs(tmp_path):
    item = item_from_dict(make_signal("Writable signal", 4))
    result = build_batch_result([item], briefing_date=date(2026, 6, 24))

    markdown_path, json_path = write_batch_outputs(result, tmp_path, stem="2026-06-24")
    genomes_path = tmp_path / "2026-06-24.genomes.json"

    assert markdown_path.exists()
    assert json_path.exists()
    assert genomes_path.exists()
    assert "Writable signal" in markdown_path.read_text(encoding="utf-8")
    assert "Writable signal" in json_path.read_text(encoding="utf-8")
    assert "source_ledger" in genomes_path.read_text(encoding="utf-8")


def test_summarize_batch():
    item = item_from_dict(make_signal("Summary signal", 4))
    result = build_batch_result([item], briefing_date=date(2026, 6, 24))

    summary = summarize_batch(result)

    assert "Daily Omega batch" in summary
    assert "Summary signal" in summary
