import json

from omega_info2.chatgpt_oak_cli import PRESET_CONTEXTS, context_from_mapping, context_from_preset, main


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


def test_context_from_preset_green_not_merged_requires_merge():
    context = context_from_preset("green-not-merged")
    assert context.requested_go_github is True
    assert context.ci_green is True
    assert context.mergeable is True
    assert context.merged is False


def test_preset_catalog_contains_core_states():
    assert set(PRESET_CONTEXTS) >= {"green-not-merged", "post-merge-success", "stale-summary", "real-blocker"}


def test_cli_lists_presets(capsys):
    code = main(["--list-presets"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert "green-not-merged" in payload
    assert "post-merge-success" in payload


def test_cli_preset_green_not_merged_fails_gate(capsys):
    code = main(["--preset", "green-not-merged"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["passed"] is False
    assert "MCHATGPT001" in payload["failed_rules"]


def test_cli_preset_post_merge_success_passes_gate(capsys):
    code = main(["--preset", "post-merge-success"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["passed"] is True
    assert payload["action"] == "POST_MERGE_SUMMARY"


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
