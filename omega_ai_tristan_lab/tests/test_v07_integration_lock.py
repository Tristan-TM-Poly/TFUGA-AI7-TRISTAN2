import json
from pathlib import Path

import pytest

from omega_ai_tristan_lab.integration import DEFAULT_R07_LOCK, IntegrationEvidence, PipelineProfile, RepositoryPin
from omega_ai_tristan_lab.repo_registry import RepoRegistry


def test_v07_lock_uses_exact_peer_commits_and_validates():
    DEFAULT_R07_LOCK.validate()
    assert len(DEFAULT_R07_LOCK.peer_pins) == 2
    assert all(len(pin.commit) == 40 for pin in DEFAULT_R07_LOCK.peer_pins)
    assert all("@main" not in pin.pip_target for pin in DEFAULT_R07_LOCK.peer_pins)
    assert all("@master" not in pin.pip_target for pin in DEFAULT_R07_LOCK.peer_pins)


def test_v07_private_pefa_is_not_in_public_install_targets():
    public_targets = DEFAULT_R07_LOCK.install_targets()
    all_targets = DEFAULT_R07_LOCK.install_targets(include_private=True)
    assert len(public_targets) == 1
    assert "TTM-TFUGA-AI7-TRISTAN2" in public_targets[0]
    assert not any("PEFA-FractalEnergySystem" in target for target in public_targets)
    assert any("PEFA-FractalEnergySystem" in target for target in all_targets)


def test_v07_profile_is_exact_pinned_ci_verified_with_receipt():
    profile = DEFAULT_R07_LOCK.profile("pefa-cvcd-omni-oak-r01")
    assert profile.capabilities == (
        "pefa-omega-em2.cvcd-extract",
        "tristan-omni-core.evidence-to-idea",
        "tristan.idea.analyze",
    )
    assert profile.status == "CI_VERIFIED_CROSS_REPO_R01"
    assert profile.evidence is not None
    assert profile.evidence.run_id == 31192063344
    assert profile.evidence.verified_runtime_commit == "6f0c46401be32823e4370ed6bdae699955d81ca3"
    assert profile.evidence.verified_driver_commit == "04914785353d3db59af36e57f5c19b3a75b74f1f"
    assert profile.evidence.artifact_id == 8999236642
    assert profile.evidence.marker == "CROSS_REPO_PIPELINE_PINNED_PASS"
    assert len(profile.evidence.artifact_sha256) == 64


def test_v07_registry_tracks_verified_heads_without_overpromotion():
    registry = RepoRegistry()
    pefa = registry.get("pefa")
    omni = registry.get("omni-core")
    host = registry.get("tfuga-ai7")
    assert pefa.distribution == "pefa-fractal-energy-system"
    assert pefa.packaging_status == "adapter-candidate"
    assert pefa.adapter_commit == "04914785353d3db59af36e57f5c19b3a75b74f1f"
    assert omni.packaging_status == "adapter-candidate"
    assert omni.adapter_commit == "29e77ad2e1214eb536043b31670071f5079285a5"
    assert host.adapter_commit == "6f0c46401be32823e4370ed6bdae699955d81ca3"
    summary = registry.doctor_summary()
    assert summary["adapter_candidates"] == 2
    assert summary["registered_runtime_capabilities"] >= 5


def test_v07_lock_rejects_floating_or_malformed_refs():
    with pytest.raises(ValueError):
        RepositoryPin(
            key="bad",
            full_name="owner/repo",
            visibility="public",
            distribution="bad",
            commit="main",
            branch_provenance="main",
            capabilities=("bad.cap",),
        )


def test_v07_verified_profile_requires_receipt():
    with pytest.raises(ValueError):
        PipelineProfile(id="bad", capabilities=("x",), description="bad", status="CI_VERIFIED_BUT_MISSING_RECEIPT")


def test_v07_receipt_rejects_invalid_artifact_digest():
    with pytest.raises(ValueError):
        IntegrationEvidence(
            repository="owner/repo",
            run_id=1,
            workflow="test",
            verified_runtime_commit="6f0c46401be32823e4370ed6bdae699955d81ca3",
            verified_driver_commit="04914785353d3db59af36e57f5c19b3a75b74f1f",
            artifact_id=1,
            artifact_sha256="not-a-digest",
            marker="PASS",
        )


def test_v07_committed_json_lock_matches_python_contract():
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "integration" / "tristan_runtime_r07.lock.json").read_text(encoding="utf-8"))
    python_lock = DEFAULT_R07_LOCK.to_dict()
    assert payload == python_lock
