import json
from pathlib import Path

from omega_re_t import r05_cli


def test_each_demo_has_expected_boundary():
    assert r05_cli.probabilistic_demo()["claim"] == "finite_model_class_behavioral_inference_only"
    assert r05_cli.expansion_demo()["claim"] == "bounded_model_class_search_only"
    assert r05_cli.grammar_demo()["accepted"]["accepted"] is True
    assert r05_cli.hybrid_demo()["claim"] == "bounded_euler_simulation_only"
    assert r05_cli.receipt_demo()["valid"] is True
    assert r05_cli.calibration_demo()["report"]["scientifically_verified_cases"] == 0


def test_all_demo_is_deterministic():
    first = r05_cli.all_demos()
    second = r05_cli.all_demos()
    assert first == second
    assert first["boundaries"]["permanent_total_cap"] is None
    assert first["boundaries"]["external_execution"] is False


def test_cli_writes_json(tmp_path: Path):
    output = tmp_path / "r05.json"
    assert r05_cli.main(["all", "--output", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema"] == "omega-re-r05-demo/1"
    assert payload["re1024_calibration"]["report"]["executed_cases"] == 1024
