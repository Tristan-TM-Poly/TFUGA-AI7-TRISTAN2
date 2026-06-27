import json

from omega_learn_t.cli import main


def test_cli_inspect(tmp_path, capsys):
    spec = {
        "skill": "cli skill",
        "goal": "test cli",
        "notes": "alpha beta alpha",
        "evidence": [{"axis": "understanding", "successes": 1, "failures": 0}],
    }
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    main(["inspect", str(path)])
    out = capsys.readouterr().out
    assert "cli skill" in out
    assert "oakbench" in out
