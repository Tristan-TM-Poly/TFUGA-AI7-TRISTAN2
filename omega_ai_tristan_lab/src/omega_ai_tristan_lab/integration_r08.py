"""Ω-TRISTAN-RUNTIME v0.8 immutable four-repository environment lock.

This module records the exact environment that passed the four-repository matrix.
It is declarative only: no clone, install, authentication, network call, or GitHub
mutation occurs when the module is imported or validated.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any

from .integration import RepositoryPin

_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class RuntimePin:
    distribution: str
    version: str
    repository: str
    commit: str
    subdirectory: str
    capabilities: tuple[str, ...]

    def __post_init__(self) -> None:
        if not _SHA40.fullmatch(self.commit):
            raise ValueError("runtime commit must be an immutable 40-hex SHA")
        if not self.distribution or not self.version or not self.repository:
            raise ValueError("runtime identity fields are required")
        if not self.capabilities:
            raise ValueError("runtime must declare at least one capability")

    @property
    def pip_target(self) -> str:
        return (
            f"git+https://github.com/{self.repository}.git@{self.commit}"
            f"#subdirectory={self.subdirectory}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "distribution": self.distribution,
            "version": self.version,
            "repository": self.repository,
            "commit": self.commit,
            "subdirectory": self.subdirectory,
            "capabilities": list(self.capabilities),
            "pip_target": self.pip_target,
        }


@dataclass(frozen=True, slots=True)
class ExecutionProbe:
    id: str
    mode: str
    capabilities: tuple[str, ...]
    description: str
    interpretation_boundary: str

    def __post_init__(self) -> None:
        if self.mode not in {"pipeline", "independent-probe"}:
            raise ValueError("probe mode must be pipeline or independent-probe")
        if not self.id or not self.capabilities:
            raise ValueError("probe id and capabilities are required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "mode": self.mode,
            "capabilities": list(self.capabilities),
            "description": self.description,
            "interpretation_boundary": self.interpretation_boundary,
        }


@dataclass(frozen=True, slots=True)
class MatrixEvidence:
    repository: str
    run_id: int
    workflow: str
    driver_commit: str
    artifact_id: int
    artifact_sha256: str
    marker: str

    def __post_init__(self) -> None:
        if self.run_id <= 0 or self.artifact_id <= 0:
            raise ValueError("evidence IDs must be positive")
        if not _SHA40.fullmatch(self.driver_commit):
            raise ValueError("driver commit must be an immutable 40-hex SHA")
        if not _SHA256.fullmatch(self.artifact_sha256):
            raise ValueError("artifact digest must be a 64-hex SHA-256")
        if not self.marker:
            raise ValueError("matrix marker is required")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class R08IntegrationLock:
    schema_version: str
    environment_id: str
    runtime: RuntimePin
    peers: tuple[RepositoryPin, ...]
    probes: tuple[ExecutionProbe, ...]
    evidence: MatrixEvidence
    status: str
    oak_rule: str

    def validate(self) -> None:
        if self.schema_version != "tristan-integration-lock-0.2":
            raise ValueError("unsupported R0.8 integration schema")
        if self.status != "CI_VERIFIED_FOUR_REPO_R02":
            raise ValueError("R0.8 lock must represent the verified four-repo matrix")
        if len(self.peers) != 3:
            raise ValueError("R0.8 verified environment requires exactly three peer repositories")
        peer_keys = [peer.key for peer in self.peers]
        if len(peer_keys) != len(set(peer_keys)):
            raise ValueError("peer keys must be unique")
        if self.evidence.driver_commit != self.peer("pefa").commit:
            raise ValueError("matrix driver must equal the immutable PEFA peer pin")

        declared = set(self.runtime.capabilities)
        for peer in self.peers:
            declared.update(peer.capabilities)
            if "@main" in peer.pip_target or "@master" in peer.pip_target:
                raise ValueError("floating peer refs are forbidden")
        if "@main" in self.runtime.pip_target or "@master" in self.runtime.pip_target:
            raise ValueError("floating runtime refs are forbidden")
        for probe in self.probes:
            missing = set(probe.capabilities) - declared
            if missing:
                raise ValueError(f"probe {probe.id} uses undeclared capabilities: {sorted(missing)}")

        # OAK invariant: Protein was an independent probe in the verified run,
        # not a fourth semantic stage in the PEFA→Omni→OAK pipeline.
        pipelines = [probe for probe in self.probes if probe.mode == "pipeline"]
        if any("protein-fold-tristan.sequence-validate" in probe.capabilities for probe in pipelines):
            raise ValueError("protein validation must not be represented as part of the PEFA/OAK semantic pipeline")

    def peer(self, key: str) -> RepositoryPin:
        for peer in self.peers:
            if peer.key == key:
                return peer
        raise KeyError(key)

    def public_install_targets(self) -> tuple[str, ...]:
        self.validate()
        return (self.runtime.pip_target,) + tuple(
            peer.pip_target for peer in self.peers if peer.visibility == "public"
        )

    def private_extension_targets(self) -> tuple[str, ...]:
        self.validate()
        return tuple(peer.pip_target for peer in self.peers if peer.visibility == "private")

    def all_install_targets(self) -> tuple[str, ...]:
        return self.public_install_targets() + self.private_extension_targets()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "environment_id": self.environment_id,
            "runtime": self.runtime.to_dict(),
            "peers": [peer.to_dict() for peer in self.peers],
            "probes": [probe.to_dict() for probe in self.probes],
            "evidence": self.evidence.to_dict(),
            "status": self.status,
            "oak_rule": self.oak_rule,
        }


DEFAULT_R08_LOCK = R08IntegrationLock(
    schema_version="tristan-integration-lock-0.2",
    environment_id="tristan-runtime-four-repo-r02",
    runtime=RuntimePin(
        distribution="omega-ai-tristan-lab",
        version="0.7.0",
        repository="Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",
        commit="f4f1968b6fd63ec4c2167f79d29701d92e65afa7",
        subdirectory="omega_ai_tristan_lab",
        capabilities=("tristan.idea.analyze",),
    ),
    peers=(
        RepositoryPin(
            key="pefa",
            full_name="Tristan-TM-Poly/PEFA-FractalEnergySystem",
            visibility="private",
            distribution="pefa-fractal-energy-system",
            commit="1e72e4619c3fb2b2c175f23ae8053d752a709621",
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
        RepositoryPin(
            key="protein-fold",
            full_name="Tristan-TM-Poly/Tristan_Tardif-Morency_TFUG",
            visibility="public",
            distribution="protein-fold-tristan",
            commit="42c3467b2675c7d83beae6b274586dc2cdf77d42",
            branch_provenance="feat/tristan-runtime-adapter-r01",
            capabilities=(
                "protein-fold-tristan.sequence-validate",
                "protein-fold-tristan.contact-map",
                "protein-fold-tristan.oak-level",
            ),
        ),
    ),
    probes=(
        ExecutionProbe(
            id="pefa-cvcd-omni-oak-r02",
            mode="pipeline",
            capabilities=(
                "pefa-omega-em2.cvcd-extract",
                "tristan-omni-core.evidence-to-idea",
                "tristan.idea.analyze",
            ),
            description="Exact-pinned PEFA CVCD extraction -> Omni evidence bridge -> TristanLab OAK analysis.",
            interpretation_boundary="SOFTWARE_COMPOSITION_AND_OAK_REPORT_NOT_SCIENTIFIC_PROOF",
        ),
        ExecutionProbe(
            id="protein-sequence-runtime-r01",
            mode="independent-probe",
            capabilities=("protein-fold-tristan.sequence-validate",),
            description="Independent Protein sequence-validation probe in the same four-repository runtime environment.",
            interpretation_boundary="COMPUTATIONAL_VALIDATION_ONLY_NONCLINICAL",
        ),
    ),
    evidence=MatrixEvidence(
        repository="Tristan-TM-Poly/PEFA-FractalEnergySystem",
        run_id=31193546089,
        workflow="Tristan Runtime Adapter R0.2 Four-Repo Matrix",
        driver_commit="1e72e4619c3fb2b2c175f23ae8053d752a709621",
        artifact_id=8999841064,
        artifact_sha256="ddff439b450870965fc7a4b103ced0c3955890dda55bc08ceeaffd18f8961b41",
        marker="FOUR_REPO_RUNTIME_PINNED_PASS",
    ),
    status="CI_VERIFIED_FOUR_REPO_R02",
    oak_rule=(
        "The four-repository matrix proves exact-pinned software co-installation and bounded capability execution only. "
        "It does not establish physical validity, biological function, clinical meaning, independent scientific reproduction, "
        "economic value, patentability, security certification, or permission to merge peer branches."
    ),
)
