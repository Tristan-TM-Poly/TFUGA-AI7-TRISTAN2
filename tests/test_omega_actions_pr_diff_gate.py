from __future__ import annotations

from pathlib import Path

from omega_actions_t.pr_diff_gate import assess_repository_measurement, assess_workflow_measurement


def _workflow(root: Path, name: str, paths: list[str]) -> Path:
    target = root / ".github" / "workflows" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    body = ["on:", "  pull_request:", "    paths:"]
    body.extend(f'      - "{item}"' for item in paths)
    body += ["jobs:", "  test:", "    runs-on: ubuntu-latest"]
    target.write_text("\n".join(body) + "\n", encoding="utf-8")
    return target


def test_self_change_from_older_pr_commit_contaminates_latest_commit_witness(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path, "dojo.yml", ["dojo/**", ".github/workflows/dojo.yml"])
    row = assess_workflow_measurement(
        workflow,
        tmp_path,
        ["pyproject.toml"],
        ["pyproject.toml", ".github/workflows/dojo.yml"],
    )
    assert row["status"] == "PR_DIFF_CARRYOVER_CONTAMINATED"
    assert row["self_changed_in_pr"] is True
    assert row["measurement_valid"] is False
    assert row["carryover_matches"] == [".github/workflows/dojo.yml"]


def test_mixed_current_and_carryover_matches_are_not_causal_proof(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path, "mixed.yml", ["pyproject.toml", ".github/workflows/mixed.yml"])
    row = assess_workflow_measurement(
        workflow,
        tmp_path,
        ["pyproject.toml"],
        ["pyproject.toml", ".github/workflows/mixed.yml"],
    )
    assert row["status"] == "MIXED_PR_DIFF_CONTAMINATION"
    assert row["commit_matches"] == ["pyproject.toml"]
    assert row["carryover_matches"] == [".github/workflows/mixed.yml"]
    assert row["measurement_valid"] is False


def test_untouched_workflow_is_clean_pre_migration_baseline(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path, "atlas.yml", ["atlas/**", "pyproject.toml", ".github/workflows/atlas.yml"])
    row = assess_workflow_measurement(
        workflow,
        tmp_path,
        ["pyproject.toml"],
        ["pyproject.toml"],
    )
    assert row["status"] == "ATTRIBUTABLE_TO_LATEST_COMMIT"
    assert row["measurement_valid"] is True
    assert row["self_changed_in_pr"] is False
    assert row["pr_matches"] == ["pyproject.toml"]


def test_repository_report_exposes_protocol_cleanliness(tmp_path: Path) -> None:
    _workflow(tmp_path, "clean.yml", ["pyproject.toml", ".github/workflows/clean.yml"])
    _workflow(tmp_path, "carry.yml", ["carry/**", ".github/workflows/carry.yml"])
    report = assess_repository_measurement(
        tmp_path,
        ["pyproject.toml"],
        ["pyproject.toml", ".github/workflows/carry.yml"],
    )
    assert report["aggregate"]["workflow_count"] == 2
    assert report["aggregate"]["attributable_count"] == 1
    assert report["aggregate"]["measurement_protocol_clean"] is False
    assert report["status_counts"] == {
        "ATTRIBUTABLE_TO_LATEST_COMMIT": 1,
        "PR_DIFF_CARRYOVER_CONTAMINATED": 1,
    }
