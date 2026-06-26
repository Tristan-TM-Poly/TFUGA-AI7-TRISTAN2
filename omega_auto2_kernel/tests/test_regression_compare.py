import json

from omega_auto2 import compare_scores, current_canonical_suite, regression_check
from omega_auto2.cli import main


def test_compare_scores_preserves_baseline():
    result = compare_scores({"total": 4, "pass_rate": 0.0}, {"total": 4, "pass_rate": 0.0})
    assert result["passed"] is True


def test_regression_check_default_passes():
    result = regression_check()
    assert result["passed"] is True


def test_current_canonical_suite_shape():
    suite = current_canonical_suite()
    assert suite["total"] >= 4
    assert "results" in suite


def test_cli_compare_default(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["auto2", "compare", "canonical"])
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is True
