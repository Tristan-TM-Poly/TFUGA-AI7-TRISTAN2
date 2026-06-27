import json

from omega_auto2 import build_issue_draft, render_issue_draft, write_issue_draft


def test_build_issue_draft_is_local_dry_run():
    draft = build_issue_draft("prepare a local review packet")

    payload = draft.to_dict()
    assert payload["dry_run"] is True
    assert payload["external_action"] == "none"
    assert "auto2" in payload["labels"]
    assert payload["workflow"]["id"].startswith("auto2_")
    assert payload["oak_report"]["status"] in {
        "blocked",
        "draft_only",
        "dry_run_allowed",
        "controlled_deployment",
        "trusted_limited",
    }
    assert any("Dry-run only" in item for item in payload["m_minus"])


def test_render_issue_draft_markdown_contains_oak_and_boundary():
    text = render_issue_draft("prepare a local review packet", output_format="markdown")

    assert "AUTO² dry-run issue draft" in text
    assert "OAK status" in text
    assert "M⁻" in text
    assert "It did not create an issue" in text
    assert "spend money" in text


def test_render_issue_draft_json_is_parseable():
    text = render_issue_draft("prepare a local review packet", output_format="json")
    payload = json.loads(text)

    assert payload["dry_run"] is True
    assert payload["external_action"] == "none"
    assert payload["title"].startswith("AUTO²:")
    assert "workflow" in payload
    assert "oak_report" in payload


def test_write_issue_draft_uses_explicit_output_path(tmp_path):
    output_path = tmp_path / "drafts" / "task.md"
    path = write_issue_draft("prepare a local review packet", output_path)

    assert path == output_path
    assert output_path.exists()
    assert "AUTO² dry-run issue draft" in output_path.read_text(encoding="utf-8")
