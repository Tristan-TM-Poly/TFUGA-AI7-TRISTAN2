import json
from pathlib import Path

import pytest

from omega_ai_tristan_lab.integration import DEFAULT_R07_LOCK, IntegrationLock, PipelineProfile, RepositoryPin
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


def test_v07_profile_declares_real_three_repository_pipeline():
    profile = DEFAULT_R07_LOCK.profile("pefa-cvcd-omni-oak-r01")
    assert profile.capabilities == (
        "pefa-omega-em2.cvcd-extract",
        "tristan-omni-core.evidence-to-idea",
        "tristan.idea.analyze",
    )
    assert profile.status == "CANDIDATE_PENDING_EXACT_HEAD_CI"


def test_v07_registry_tracks_candidate_adapters_without_overpromotion():
    registry = RepoRegistry()
    pefa = registry.get("pefa")
    omni = registry.get("omni-core")
    assert pefa.distribution == "pefa-fractal-energy-system"
    assert pefa.packaging_status == "adapter-candidate"
    assert pefa.adapter_commit == "32b82d5d9818bfdd514eabf9e6ffefc520cc9260"
    assert omni.packaging_status == "adapter-candidate"
    assert omni.adapter_commit == "29e77ad2e1214eb536043b31670071f5079285a5"
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


def test_v07_committed_json_lock_matches_python_contract():
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "integration" / "tristan_runtime_r07.lock.json").read_text(encoding="utf-8"))
    python_lock = DEFAULT_R07_LOCK.to_dict()
    assert payload["schema_version"] == python_lock["schema_version"]
    assert payload["runtime"] == python_lock["runtime"]
    assert [item["commit"] for item in payload["peer_pins"]] == [pin.commit for pin in DEFAULT_R07_LOCK.peer_pins]
    assert payload["profiles"][0]["capabilities"] == list(DEFAULT_R07_LOCK.profiles[0].capabilities)
