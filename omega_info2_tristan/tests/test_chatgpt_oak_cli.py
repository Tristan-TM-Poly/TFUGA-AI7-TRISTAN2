import json

from omega_info2.chatgpt_oak_cli import context_from_mapping, main


def test_context_from_mapping_coerces_booleans_and_ignores_unknowns():
    context = context_from_mapping(
        {
            "requested_go_github": "true",
            "pr_open": "1",
            "ci_green": "yes",
            "mergeable": True,
            "merged": "false",
            "checks_per_head_sha": "2",
            "unknown": "ignored",
        }
    )
    assert context.requested_go_github is True
    assert context.pr_open is True
    assert context.ci_green is True
    assert context.mergeable is True
    assert context.merged is False
    assert context.checks_per_head_sha == 2


def test_cli_rules_prints_markdown(capsys):
    code = main(["--rules"])
    captured = capsys.readouterr()
    assert code == 0
    assert "MCHATGPT001" in captured.out


def test_cli_outputs_merge_failure_decision(tmp_path, capsys):
    path = tmp_path / "context.json"
    path.write_text(
        json.dumps(
            {
                "requested_go_github": True,
                "pr_open": True,
                "ci_green": True,
                "mergeable": True,
                "merged": False,
                "used_fresh_head_sha": True,
            }
        ),
        encoding="utf-8",
    )
    code = main(["--context", str(path)])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["passed"] is False
    assert "MCHATGPT001" in payload["failed_rules"]


def test_cli_can_fail_nonzero_on_gate_fail(tmp_path, capsys):
    path = tmp_path / "context.json"
    path.write_text(
        json.dumps(
            {
                "requested_go_github": True,
                "pr_open": True,
                "ci_green": True,
                "mergeable": True,
                "merged": False,
                "used_fresh_head_sha": True,
            }
        ),
        encoding="utf-8",
    )
    code = main(["--context", str(path), "--exit-nonzero-on-fail"])
    assert code == 2
