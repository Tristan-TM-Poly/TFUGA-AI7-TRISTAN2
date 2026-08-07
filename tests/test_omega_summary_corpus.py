from __future__ import annotations

import json
from pathlib import Path

from omega_summary_fractal_t.corpus import CorpusSummaryEngine, RepositorySpec, discover_local_repositories, load_manifest
from omega_summary_fractal_t.corpus_cli import main


def make_repo(root: Path, name: str, system: str) -> Path:
    repo = root / name
    repo.mkdir()
    (repo / "README.md").write_text(f"# {name}\n\nRepository.\n", encoding="utf-8")
    pkg = repo / system
    pkg.mkdir()
    (pkg / "README.md").write_text(f"# {system}\n\nShared signal analysis engine.\n", encoding="utf-8")
    (pkg / "core.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    return repo


def test_discover_workspace_and_generate(tmp_path):
    make_repo(tmp_path, "repo_a", "omega_signal_t")
    make_repo(tmp_path, "repo_b", "omega_signal_copy_t")
    specs = discover_local_repositories(tmp_path, include_workspace=False)
    assert [s.display_name for s in specs] == ["repo_a", "repo_b"]
    bundle = CorpusSummaryEngine(specs).generate(depth=4, audience="oak")
    assert bundle.totals["repositories"] == 2
    assert bundle.totals["systems"] == 2
    assert len(bundle.fingerprint) == 64


def test_manifest_relative_paths(tmp_path):
    make_repo(tmp_path, "repo_a", "omega_alpha_t")
    manifest = tmp_path / "repos.json"
    manifest.write_text(json.dumps({"repositories": [{"root": "repo_a", "name": "A"}]}), encoding="utf-8")
    specs = load_manifest(manifest)
    assert specs[0].path == (tmp_path / "repo_a").resolve()
    assert specs[0].display_name == "A"


def test_corpus_write_and_cli(tmp_path, monkeypatch):
    make_repo(tmp_path, "repo_a", "omega_alpha_t")
    make_repo(tmp_path, "repo_b", "omega_beta_t")
    out = tmp_path / "out"
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1786111200")
    assert main(["--workspace", str(tmp_path), "--output-dir", str(out), "--depth", "4", "--audience", "oak"]) == 0
    payload = json.loads((out / "CORPUS_SUMMARY.json").read_text())
    assert payload["totals"]["repositories"] == 2
    assert (out / "CORPUS_SUMMARY.md").exists()
    assert (out / "repositories" / "repo_a" / "SUMMARY.md").exists()


def test_missing_repository_is_reported_not_invented(tmp_path):
    missing = tmp_path / "missing"
    bundle = CorpusSummaryEngine([RepositorySpec(str(missing), "missing")]).generate()
    assert bundle.repositories[0]["available"] is False
    assert bundle.repositories[0]["reason"] == "path_missing"
