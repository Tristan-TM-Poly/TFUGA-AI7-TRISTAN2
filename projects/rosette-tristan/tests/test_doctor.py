from pathlib import Path

from rosette_tristan.doctor import check_commands, check_optional_modules, run_doctor


def test_check_commands_with_known_python():
    checks = check_commands(["python"])
    assert checks[0].name == "python"
    assert isinstance(checks[0].available, bool)


def test_check_optional_modules_detects_json():
    checks = check_optional_modules({"json": "stdlib json"})
    assert checks[0].module == "json"
    assert checks[0].available is True


def test_run_doctor_shape():
    report = run_doctor()
    payload = report.to_dict()
    assert "python_version" in payload
    assert "commands" in payload
    assert "optional_modules" in payload
    assert payload["oak_status"].startswith("doctor_")


def test_doctor_report_can_write_json(tmp_path: Path):
    report = run_doctor()
    out = tmp_path / "doctor.json"
    out.write_text(__import__("json").dumps(report.to_dict()), encoding="utf-8")
    assert out.exists()
    assert "oak_status" in out.read_text(encoding="utf-8")
