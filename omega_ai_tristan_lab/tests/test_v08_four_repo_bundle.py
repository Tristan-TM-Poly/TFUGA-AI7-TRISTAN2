import json
from pathlib import Path

import pytest

from omega_ai_tristan_lab.bundle import BundlePlan
from omega_ai_tristan_lab.integration_r08 import DEFAULT_R08_LOCK, ExecutionProbe, RuntimePin
from omega_ai_tristan_lab.repo_registry import RepoRegistry


def test_r08_four_repo_lock_is_exact_and_verified():
    DEFAULT_R08_LOCK.validate()
    assert DEFAULT_R08_LOCK.status == "CI_VERIFIED_FOUR_REPO_R02"
    assert DEFAULT_R08_LOCK.evidence.run_id == 31193546089
    assert DEFAULT_R08_LOCK.evidence.driver_commit == "1e72e4619c3fb2b2c175f23ae8053d752a709621"
    assert DEFAULT_R08_LOCK.evidence.artifact_id == 8999841064
    assert DEFAULT_R08_LOCK.evidence.artifact_sha256 == "ddff439b450870965fc7a4b103ced0c3955890dda55bc08ceeaffd18f8961b41"
    assert DEFAULT_R08_LOCK.evidence.marker == "FOUR_REPO_RUNTIME_PINNED_PASS"


def test_r08_environment_has_host_plus_three_peers_and_no_floating_refs():
    assert len(DEFAULT_R08_LOCK.peers) == 3
    assert DEFAULT_R08_LOCK.runtime.commit == "f4f1968b6fd63ec4c2167f79d29701d92e65afa7"
    targets = DEFAULT_R08_LOCK.all_install_targets()
    assert len(targets) == 4
    assert all("@main" not in target and "@master" not in target for target in targets)


def test_r08_public_targets_exclude_private_pefa_but_include_protein_and_omni():
    public = DEFAULT_R08_LOCK.public_install_targets()
    private = DEFAULT_R08_LOCK.private_extension_targets()
    assert len(public) == 3
    assert any("TFUGA-AI7-TRISTAN2" in target for target in public)
    assert any("TTM-TFUGA-AI7-TRISTAN2" in target for target in public)
    assert any("Tristan_Tardif-Morency_TFUG" in target for target in public)
    assert not any("PEFA-FractalEnergySystem" in target for target in public)
    assert len(private) == 1 and "PEFA-FractalEnergySystem" in private[0]


def test_r08_does_not_fake_protein_as_fourth_pefa_pipeline_stage():
    pipeline = next(probe for probe in DEFAULT_R08_LOCK.probes if probe.mode == "pipeline")
    protein = next(probe for probe in DEFAULT_R08_LOCK.probes if probe.mode == "independent-probe")
    assert pipeline.capabilities == (
        "pefa-omega-em2.cvcd-extract",
        "tristan-omni-core.evidence-to-idea",
        "tristan.idea.analyze",
    )
    assert protein.capabilities == ("protein-fold-tristan.sequence-validate",)
    assert "protein-fold-tristan.sequence-validate" not in pipeline.capabilities
    assert protein.interpretation_boundary == "COMPUTATIONAL_VALIDATION_ONLY_NONCLINICAL"


def test_r08_lock_file_equals_python_contract():
    root = Path(__file__).resolve().parents[1]
    stored = json.loads((root / "integration" / "tristan_runtime_r08.lock.json").read_text(encoding="utf-8"))
    assert stored == DEFAULT_R08_LOCK.to_dict()


def test_r08_registry_tracks_three_adapter_candidates_and_eight_capabilities():
    summary = RepoRegistry().doctor_summary()
    assert summary["adapter_candidates"] == 3
    assert summary["registered_runtime_capabilities"] == 8
    assert RepoRegistry().get("tfug-corpus").adapter_commit == "42c3467b2675c7d83beae6b274586dc2cdf77d42"
    assert RepoRegistry().get("pefa").adapter_commit == "1e72e4619c3fb2b2c175f23ae8053d752a709621"


def test_bundle_plan_is_network_free_private_safe_and_manifest_redacted_by_default(tmp_path: Path):
    plan = BundlePlan()
    public_manifest = plan.manifest()
    private_manifest = plan.manifest(include_private_extension=True)
    public_manifest_text = json.dumps(public_manifest, sort_keys=True)
    private_manifest_text = json.dumps(private_manifest, sort_keys=True)

    assert public_manifest["build_policy"]["automatic_install"] is False
    assert public_manifest["build_policy"]["network_on_import"] is False
    assert public_manifest["private_extension_included"] is False
    assert public_manifest["private_extension_targets"] == []
    assert "PEFA-FractalEnergySystem" not in plan.public_requirements_text()
    assert "PEFA-FractalEnergySystem" not in public_manifest_text
    assert private_manifest["private_extension_included"] is True
    assert "PEFA-FractalEnergySystem" in private_manifest_text
    assert "PEFA-FractalEnergySystem" in plan.private_extension_requirements_text()

    files = plan.materialize(tmp_path / "bundle")
    assert files.manifest.exists()
    assert files.public_requirements.exists()
    assert files.private_extension_requirements is None
    assert "PEFA-FractalEnergySystem" not in files.manifest.read_text(encoding="utf-8")
    assert not (tmp_path / "bundle" / "requirements-private-extension.lock").exists()

    files_private = plan.materialize(tmp_path / "bundle-private", include_private_extension=True)
    assert files_private.private_extension_requirements is not None
    assert files_private.private_extension_requirements.exists()
    assert "PEFA-FractalEnergySystem" in files_private.manifest.read_text(encoding="utf-8")


def test_r08_rejects_malformed_runtime_pin():
    with pytest.raises(ValueError):
        RuntimePin(
            distribution="x",
            version="0",
            repository="owner/repo",
            commit="main",
            subdirectory="pkg",
            capabilities=("x.cap",),
        )


def test_r08_rejects_protein_inside_semantic_pefa_pipeline():
    bad = DEFAULT_R08_LOCK.__class__(
        schema_version=DEFAULT_R08_LOCK.schema_version,
        environment_id="bad",
        runtime=DEFAULT_R08_LOCK.runtime,
        peers=DEFAULT_R08_LOCK.peers,
        probes=(
            ExecutionProbe(
                id="bad",
                mode="pipeline",
                capabilities=(
                    "pefa-omega-em2.cvcd-extract",
                    "protein-fold-tristan.sequence-validate",
                ),
                description="bad",
                interpretation_boundary="bad",
            ),
        ),
        evidence=DEFAULT_R08_LOCK.evidence,
        status=DEFAULT_R08_LOCK.status,
        oak_rule=DEFAULT_R08_LOCK.oak_rule,
    )
    with pytest.raises(ValueError):
        bad.validate()
