"""Pinned cross-repository integration contracts for Tristan Runtime.

Importing this module is side-effect free: it never clones, installs, authenticates,
or mutates a repository. Verified profiles carry immutable source pins plus an
explicit CI evidence receipt.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any

_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class RepositoryPin:
    key: str
    full_name: str
    visibility: str
    distribution: str
    commit: str
    branch_provenance: str
    capabilities: tuple[str, ...]
    subdirectory: str | None = None

    def __post_init__(self) -> None:
        if not self.key or not self.full_name or not self.distribution:
            raise ValueError("repository pin identity fields must be non-empty")
        if self.visibility not in {"public", "private"}:
            raise ValueError("visibility must be public or private")
        if not _SHA40.fullmatch(self.commit):
            raise ValueError(f"repository pin must use an immutable 40-hex commit: {self.key}")
        if not self.capabilities:
            raise ValueError(f"repository pin must declare capabilities: {self.key}")

    @property
    def pip_target(self) -> str:
        target = f"git+https://github.com/{self.full_name}.git@{self.commit}"
        if self.subdirectory:
            target += f"#subdirectory={self.subdirectory}"
        return target

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["capabilities"] = list(self.capabilities)
        payload["pip_target"] = self.pip_target
        return payload


@dataclass(frozen=True, slots=True)
class IntegrationEvidence:
    repository: str
    run_id: int
    workflow: str
    verified_runtime_commit: str
    verified_driver_commit: str
    artifact_id: int
    artifact_sha256: str
    marker: str

    def __post_init__(self) -> None:
        if self.run_id <= 0 or self.artifact_id <= 0:
            raise ValueError("CI evidence IDs must be positive")
        if not _SHA40.fullmatch(self.verified_runtime_commit):
            raise ValueError("verified runtime commit must be a 40-hex SHA")
        if not _SHA40.fullmatch(self.verified_driver_commit):
            raise ValueError("verified driver commit must be a 40-hex SHA")
        if not _SHA256.fullmatch(self.artifact_sha256):
            raise ValueError("artifact_sha256 must be a 64-hex SHA-256")
        if not self.marker:
            raise ValueError("CI evidence marker is required")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PipelineProfile:
    id: str
    capabilities: tuple[str, ...]
    description: str
    status: str = "CANDIDATE_PENDING_EXACT_HEAD_CI"
    evidence: IntegrationEvidence | None = None

    def __post_init__(self) -> None:
        if not self.id or not self.capabilities:
            raise ValueError("pipeline profile requires id and capabilities")
        if self.status.startswith("CI_VERIFIED") and self.evidence is None:
            raise ValueError("CI_VERIFIED profile requires an evidence receipt")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "capabilities": list(self.capabilities),
            "description": self.description,
            "status": self.status,
            "evidence": self.evidence.to_dict() if self.evidence else None,
        }


@dataclass(frozen=True, slots=True)
class IntegrationLock:
    schema_version: str
    runtime_distribution: str
    runtime_version: str
    runtime_repository: str
    peer_pins: tuple[RepositoryPin, ...]
    host_capabilities: tuple[str, ...]
    profiles: tuple[PipelineProfile, ...]
    oak_rule: str

    def validate(self) -> None:
        if self.schema_version != "tristan-integration-lock-0.1":
            raise ValueError("unsupported integration lock schema")
        keys = [pin.key for pin in self.peer_pins]
        if len(keys) != len(set(keys)):
            raise ValueError("peer keys must be unique")
        declared = set(self.host_capabilities)
        pinned_commits = {pin.commit for pin in self.peer_pins}
        for pin in self.peer_pins:
            declared.update(pin.capabilities)
            if "@main" in pin.pip_target or "@master" in pin.pip_target:
                raise ValueError("floating default-branch refs are forbidden")
        for profile in self.profiles:
            missing = set(profile.capabilities) - declared
            if missing:
                raise ValueError(f"pipeline {profile.id} uses undeclared capabilities: {sorted(missing)}")
            if profile.evidence and profile.evidence.verified_driver_commit not in pinned_commits:
                raise ValueError("verified driver commit must be one of the immutable peer pins")

    def install_targets(self, *, include_private: bool = False) -> tuple[str, ...]:
        self.validate()
        return tuple(pin.pip_target for pin in self.peer_pins if include_private or pin.visibility == "public")

    def profile(self, profile_id: str) -> PipelineProfile:
        for profile in self.profiles:
            if profile.id == profile_id:
                return profile
        raise KeyError(profile_id)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "runtime": {
                "distribution": self.runtime_distribution,
                "version": self.runtime_version,
                "repository": self.runtime_repository,
                "capabilities": list(self.host_capabilities),
            },
            "peer_pins": [pin.to_dict() for pin in self.peer_pins],
            "profiles": [profile.to_dict() for profile in self.profiles],
            "oak_rule": self.oak_rule,
        }


DEFAULT_R07_LOCK = IntegrationLock(
    schema_version="tristan-integration-lock-0.1",
    runtime_distribution="omega-ai-tristan-lab",
    runtime_version="0.7.0",
    runtime_repository="Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",
    peer_pins=(
        RepositoryPin(
            key="pefa",
            full_name="Tristan-TM-Poly/PEFA-FractalEnergySystem",
            visibility="private",
            distribution="pefa-fractal-energy-system",
            commit="04914785353d3db59af36e57f5c19b3a75b74f1f",
            branch_provenance="feat/tristan-runtime-adapter-r01",
            capabilities=("pefa-omega-em2.cvcd-extract", "pefa-omega-em2.cvcd-expand"),
        ),
        RepositoryPin(
            key="omni-core",
            full_name="Tristan-TM-Poly/TTM-TFUGA-AI7-TRISTAN2",
            visibility="public",
            distribution="tristan-omni-core",
            commit="29e77ad2e1214eb536043b31670071f5079285a5",
            branch_provenance="feat/tristan-runtime-adapter-r01",
            capabilities=("tristan-omni-core.evidence-to-idea", "tristan-omni-core.valuation-assess"),
        ),
    ),
    host_capabilities=("tristan.idea.analyze",),
    profiles=(
        PipelineProfile(
            id="pefa-cvcd-omni-oak-r01",
            capabilities=(
                "pefa-omega-em2.cvcd-extract",
                "tristan-omni-core.evidence-to-idea",
                "tristan.idea.analyze",
            ),
            description="PEFA CVCD extraction -> Omni evidence bridge -> TristanLab OAK analysis.",
            status="CI_VERIFIED_CROSS_REPO_R01",
            evidence=IntegrationEvidence(
                repository="Tristan-TM-Poly/PEFA-FractalEnergySystem",
                run_id=31192063344,
                workflow="Tristan Runtime Adapter R0.1",
                verified_runtime_commit="6f0c46401be32823e4370ed6bdae699955d81ca3",
                verified_driver_commit="04914785353d3db59af36e57f5c19b3a75b74f1f",
                artifact_id=8999236642,
                artifact_sha256="83f07f9293b908d1f628c10ef9139f9f65c9ecb02a5a4b4c1220294416856341",
                marker="CROSS_REPO_PIPELINE_PINNED_PASS",
            ),
        ),
    ),
    oak_rule=(
        "CI_VERIFIED means exact-pinned software composition was executed successfully. "
        "It does not establish scientific truth, independent reproduction, product value, "
        "patentability, security certification, or permission to merge peer branches."
    ),
)
