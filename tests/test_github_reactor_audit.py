from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "github_reactor" / "repo_reactor_audit.py"


def load_module():
    spec = importlib.util.spec_from_file_location("repo_reactor_audit", MODULE_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["repo_reactor_audit"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_reactor_inventory_and_oak_score(tmp_path):
    module = load_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "docs").mkdir()
    (repo / "tools").mkdir()
    (repo / "core").mkdir()
    (repo / "schemas").mkdir()
    (repo / "memory").mkdir()
    (repo / ".github" / "workflows").mkdir(parents=True)
    (repo / "tools" / "github_reactor").mkdir(parents=True)
    (repo / "docs" / "README.md").write_text("# Safe scaffold\n", encoding="utf-8")
    (repo / "core" / "ok.py").write_text("x = 1\n", encoding="utf-8")

    inv = module.inventory(repo)
    comp = module.compile_python(repo)
    patterns = module.pattern_scan(repo)
    score = module.oak_score(inv, comp, patterns)

    assert inv["canonical_paths"]["docs"] is True
    assert inv["canonical_paths"]["github_workflows"] is True
    assert comp.failed == 0
    assert patterns.matches == 0
    assert score["score"] >= 80


def test_reactor_detects_compile_failure_and_writes_reports(tmp_path):
    module = load_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "core").mkdir()
    (repo / "core" / "bad.py").write_text("def broken(:\n", encoding="utf-8")

    comp = module.compile_python(repo)
    assert comp.failed == 1

    inv = module.inventory(repo)
    patterns = module.pattern_scan(repo)
    score = module.oak_score(inv, comp, patterns)
    actions = module.next_actions(score, comp, patterns, inv)
    assert any(action["action"] == "repair_python_compile_failures" for action in actions)

    payload = {
        "generated_at": module.utc_now(),
        "repository": "test/repo",
        "inventory": inv,
        "python_compile": {"checked": comp.checked, "failed": comp.failed, "failures": comp.failures},
        "claim_hygiene_scan": {"files_scanned": patterns.files_scanned, "matches": patterns.matches, "findings": patterns.findings},
        "oak_score": score,
        "next_actions": actions,
        "reactor_repositories": [],
    }
    out = repo / "reports" / "github-autonomous-reactor"
    module.write_reports(out, payload)

    matrix = json.loads((out / "reactor_oak_matrix.json").read_text(encoding="utf-8"))
    assert matrix["repository"] == "test/repo"
    assert (out / "REACTOR_OAK_MATRIX.md").exists()
