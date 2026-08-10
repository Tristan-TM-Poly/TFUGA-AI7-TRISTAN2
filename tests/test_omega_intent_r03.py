from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_intent_t.r03 import (
    ImpactRouter,
    ProofArtifactBuilder,
    RepoTwinScanner,
    ValidationReceipt,
    run_oakbench,
)


def build_repo(root: Path) -> Path:
    (root / "alpha").mkdir()
    (root / "beta").mkdir()
    (root / "tests").mkdir()
    (root / ".github/workflows").mkdir(parents=True)
    (root / "alpha/__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "beta/core.py").write_text("import alpha\nVALUE = alpha.VALUE\n", encoding="utf-8")
    (root / "tests/test_beta.py").write_text("import beta\ndef test_beta(): assert beta is not None\n", encoding="utf-8")
    (root / ".github/workflows/beta.yml").write_text(
        "name: Beta CI\non:\n  pull_request:\n    paths:\n      - 'beta/**'\n      - 'tests/test_beta.py'\nconcurrency:\n  cancel-in-progress: true\n",
        encoding="utf-8",
    )
    return root


def test_manifest_is_deterministic(tmp_path: Path) -> None:
    root = build_repo(tmp_path)
    scanner = RepoTwinScanner()
    first = scanner.scan(root)
    second = scanner.scan(root)
    assert first.root_digest == second.root_digest
    assert first.to_dict() == second.to_dict()


def test_reverse_dependency_closure_and_test_mapping(tmp_path: Path) -> None:
    manifest = RepoTwinScanner().scan(build_repo(tmp_path))
    plan = ImpactRouter().route(manifest, ["alpha/__init__.py"])
    assert {"alpha", "beta"}.issubset(plan.affected_packages)
    assert "tests/test_beta.py" in plan.affected_tests
    assert plan.full_suite_required is False


def test_workflow_path_routing(tmp_path: Path) -> None:
    manifest = RepoTwinScanner().scan(build_repo(tmp_path))
    plan = ImpactRouter().route(manifest, ["beta/core.py"])
    assert ".github/workflows/beta.yml" in plan.selected_workflows
    assert "integration" in plan.tiers


def test_workflow_definition_change_escalates_to_integration(tmp_path: Path) -> None:
    manifest = RepoTwinScanner().scan(build_repo(tmp_path))
    plan = ImpactRouter().route(manifest, [".github/workflows/beta.yml"])
    assert "integration" in plan.tiers
    assert any(reason.startswith("workflow_definition_changed") for reason in plan.reasons)


def test_global_file_requires_full_suite(tmp_path: Path) -> None:
    manifest = RepoTwinScanner().scan(build_repo(tmp_path))
    plan = ImpactRouter().route(manifest, ["pyproject.toml"])
    assert plan.full_suite_required is True
    assert "nightly_or_manual_full" in plan.tiers


def test_unknown_package_path_requires_full_suite(tmp_path: Path) -> None:
    manifest = RepoTwinScanner().scan(build_repo(tmp_path))
    plan = ImpactRouter().route(manifest, ["brand_new_package/core.py"])
    assert plan.full_suite_required is True
    assert "brand_new_package/core.py" in plan.unknown_paths


def test_empty_changed_paths_rejected(tmp_path: Path) -> None:
    manifest = RepoTwinScanner().scan(build_repo(tmp_path))
    with pytest.raises(ValueError):
        ImpactRouter().route(manifest, [])


def test_proof_artifact_detects_tamper(tmp_path: Path) -> None:
    root = build_repo(tmp_path)
    target = root / "beta/core.py"
    builder = ProofArtifactBuilder()
    artifact = builder.build(
        target,
        root=root,
        provenance=("INTENT-1",),
        derived_from=("REQ-1",),
        validations=(ValidationReceipt("pytest", "passed", "pytest -q"),),
    )
    assert builder.verify(artifact, target)["passed"] is True
    target.write_text("VALUE = 999\n", encoding="utf-8")
    assert builder.verify(artifact, target)["passed"] is False


def test_proof_requires_provenance(tmp_path: Path) -> None:
    root = build_repo(tmp_path)
    with pytest.raises(ValueError):
        ProofArtifactBuilder().build(root / "alpha/__init__.py", provenance=())


def test_impact_plan_is_deterministic(tmp_path: Path) -> None:
    manifest = RepoTwinScanner().scan(build_repo(tmp_path))
    router = ImpactRouter()
    first = router.route(manifest, ["beta/core.py", "alpha/__init__.py"])
    second = router.route(manifest, ["alpha/__init__.py", "beta/core.py"])
    assert first.plan_id == second.plan_id
    assert first.to_dict() == second.to_dict()


def test_manifest_json_roundtrip(tmp_path: Path) -> None:
    manifest = RepoTwinScanner().scan(build_repo(tmp_path))
    encoded = json.dumps(manifest.to_dict())
    decoded = json.loads(encoded)
    assert decoded["root_digest"] == manifest.root_digest
    assert decoded["remote_mutations"] == 0


def test_cost_is_explicitly_relative(tmp_path: Path) -> None:
    manifest = RepoTwinScanner().scan(build_repo(tmp_path))
    plan = ImpactRouter().route(manifest, ["beta/core.py"])
    assert plan.cost.relative_cost_score > 0
    assert "not billed cost" in plan.cost.interpretation


def test_generated_files_marked(tmp_path: Path) -> None:
    root = build_repo(tmp_path)
    (root / "generated").mkdir()
    (root / "generated/output.json").write_text("{}\n", encoding="utf-8")
    manifest = RepoTwinScanner().scan(root)
    record = next(item for item in manifest.files if item.path == "generated/output.json")
    assert record.generated is True


def test_oakbench_passes() -> None:
    result = run_oakbench()
    assert result.passed is True
    assert result.remote_mutations == 0
    assert result.automatic_merge is False
    assert result.theorem_claimed is False
