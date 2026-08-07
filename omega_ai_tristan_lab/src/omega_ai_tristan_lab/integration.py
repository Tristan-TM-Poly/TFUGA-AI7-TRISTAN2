"""Pinned cross-repository integration contracts for Tristan Runtime.

The lock is descriptive and validation-only: importing it never clones, installs,
or mutates a repository. Peer sources are pinned to immutable 40-hex commits.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Iterable

_SHA40 = re.compile(r"^[0-9a-f]{40}$")


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
        payload["pip_target"] = self.pip_target
        return payload


@dataclass(frozen=True, slots=True)
class PipelineProfile:
    id: str
    capabilities: tuple[str, ...]
    description: str
    status: str = "CANDIDATE_PENDING_EXACT_HEAD_CI"

    def __post_init__(self) -> None:
        if not self.id or not self.capabilities:
            raise ValueError("pipeline profile requires id and capabilities")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
        for pin in self.peer_pins:
            declared.update(pin.capabilities)
            if "@main" in pin.pip_target or "@master" in pin.pip_target:
                raise ValueError("floating default-branch refs are forbidden")
        for profile in self.profiles:
            missing = set(profile.capabilities) - declared
            if missing:
                raise ValueError(f"pipeline {profile.id} uses undeclared capabilities: {sorted(missing)}")

    def install_targets(self, *, include_private: bool = False) -> tuple[str, ...]:
        self.validate()
        return tuple(
            pin.pip_target
            for pin in self.peer_pins
            if include_private or pin.visibility == "public"
        )

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
            commit="32b82d5d9818bfdd514eabf9e6ffefc520cc9260",
            branch_provenance="feat/tristan-runtime-adapter-r01",
            capabilities=(
                "pefa-omega-em2.cvcd-extract",
                "pefa-omega-em2.cvcd-expand",
            ),
        ),
        RepositoryPin(
            key="omni-core",
            full_name="Tristan-TM-Poly/TTM-TFUGA-AI7-TRISTAN2",
            visibility="public",
            distribution="tristan-omni-core",
            commit="29e77ad2e1214eb536043b31670071f5079285a5",
            branch_provenance="feat/tristan-runtime-adapter-r01",
            capabilities=(
                "tristan-omni-core.evidence-to-idea",
                "tristan-omni-core.valuation-assess",
            ),
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
        ),
    ),
    oak_rule=(
        "Pinned integration proves reproducible software composition only after exact-head CI; "
        "it does not establish scientific truth, independent reproduction, product value, or merge readiness."
    ),
)
