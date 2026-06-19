from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "github_reactor" / "propagation_planner.py"


def load_module():
    spec = importlib.util.spec_from_file_location("propagation_planner", MODULE_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["propagation_planner"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_parse_repo_blocks_and_make_actions():
    module = load_module()
    text = """
repositories:
  - name: Tristan-TM-Poly/TFUGA-AI7-TRISTAN2
    role: root_reactor
    priority: P0
  - name: Tristan-TM-Poly/PEFA-FractalEnergySystem
    role: pefa_energy_scaffold
    priority: P1
"""
    repos = module.parse_repo_blocks(text)
    assert len(repos) == 2
    actions = module.make_actions(repos)
    assert [action.packet_type for action in actions] == ["root_reactor_harden", "physics_oak_contract"]
    assert all(action.allowed_mode == "additive_draft_pr_only" for action in actions)


def test_write_propagation_reports(tmp_path):
    module = load_module()
    actions = [
        module.PropagationAction(
            priority="P1",
            repository="Tristan-TM-Poly/example",
            packet_type="repo_contract",
            action="add docs",
            reason="test reason",
        )
    ]
    out = tmp_path / "reports"
    module.write_reports(out, actions, {"repositories": "atlas/repositories.yml"})
    payload = json.loads((out / "propagation_queue.json").read_text(encoding="utf-8"))
    assert payload["actions"][0]["repository"] == "Tristan-TM-Poly/example"
    assert (out / "PROPAGATION_QUEUE.md").exists()
