from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "github_reactor" / "issue_draft_generator.py"


def load_module():
    spec = importlib.util.spec_from_file_location("issue_draft_generator", MODULE_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["issue_draft_generator"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_generate_drafts_from_ranked_actions():
    module = load_module()
    scores = {
        "ranked_actions": [
            {
                "rank": 1,
                "repository": "Tristan-TM-Poly/root",
                "priority": "P0",
                "packet_type": "root_reactor_harden",
                "action": "review root reactor",
                "reason": "root priority",
                "score": 42,
            }
        ]
    }
    drafts = module.generate_drafts(scores, limit=5)
    assert len(drafts) == 1
    assert drafts[0].title.startswith("[P0]")
    assert "root-reactor" in drafts[0].labels
    assert drafts[0].allowed_mode == "draft_only"


def test_write_issue_draft_reports(tmp_path):
    module = load_module()
    drafts = module.generate_drafts(
        {
            "ranked_actions": [
                {
                    "rank": 1,
                    "repository": "Tristan-TM-Poly/root",
                    "priority": "P0",
                    "packet_type": "root_reactor_harden",
                    "action": "review root reactor",
                    "reason": "root priority",
                    "score": 42,
                }
            ]
        },
        limit=1,
    )
    out = tmp_path / "reports"
    module.write_reports(out, drafts)
    payload = json.loads((out / "issue_drafts.json").read_text(encoding="utf-8"))
    assert payload["draft_count"] == 1
    assert (out / "ISSUE_DRAFTS.md").exists()
