"""GOArtifact and deterministic ReproCapsule contracts."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from .model import stable_digest


class GateState(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    NOT_APPLICABLE = "N/A"


@dataclass(frozen=True, slots=True)
class ValidationVector:
    integrity: GateState = GateState.HOLD
    reproducibility: GateState = GateState.HOLD
    empirical_support: GateState = GateState.NOT_APPLICABLE
    formal_validity: GateState = GateState.NOT_APPLICABLE
    calibration: GateState = GateState.NOT_APPLICABLE


@dataclass(frozen=True, slots=True)
class ReproCapsule:
    environment_fingerprint: str
    input_hashes: tuple[str, ...]
    dependency_hashes: tuple[str, ...]
    replay_steps: tuple[str, ...]
    expected_output_hashes: tuple[str, ...]

    @property
    def fingerprint(self) -> str:
        return stable_digest(asdict(self))


@dataclass(frozen=True, slots=True)
class GOArtifact:
    artifact_id: str
    artifact_kind: str
    content_hash: str
    claim_ids: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    uncertainty: float = 1.0
    validation: ValidationVector = ValidationVector()
    repro_capsule: ReproCapsule | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("uncertainty must be in [0,1]")

    @property
    def fingerprint(self) -> str:
        return stable_digest(asdict(self))


@dataclass(frozen=True, slots=True)
class ArtifactValidationReport:
    artifact_id: str
    status: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    artifact_fingerprint: str
    capsule_fingerprint: str | None
    boundary: str = "integrity and reproducibility gates do not certify external truth"


def validate_go_artifact(artifact: GOArtifact) -> ArtifactValidationReport:
    blockers: list[str] = []
    warnings: list[str] = []
    if not artifact.artifact_id.strip():
        blockers.append("missing_artifact_id")
    if not artifact.artifact_kind.strip():
        blockers.append("missing_artifact_kind")
    if not artifact.content_hash.strip():
        blockers.append("missing_content_hash")
    if not artifact.provenance:
        blockers.append("missing_provenance")
    if not artifact.tests:
        blockers.append("missing_tests")
    if artifact.validation.integrity != GateState.PASS:
        blockers.append("integrity_not_pass")
    if artifact.validation.reproducibility == GateState.PASS and artifact.repro_capsule is None:
        blockers.append("reproducibility_pass_requires_capsule")
    if artifact.validation.reproducibility != GateState.PASS:
        warnings.append("reproducibility_not_pass")
    if artifact.claim_ids and not artifact.evidence_refs:
        warnings.append("claims_without_evidence_refs")
    return ArtifactValidationReport(
        artifact_id=artifact.artifact_id,
        status="PASS" if not blockers else "HOLD",
        blockers=tuple(sorted(set(blockers))),
        warnings=tuple(sorted(set(warnings))),
        artifact_fingerprint=artifact.fingerprint,
        capsule_fingerprint=artifact.repro_capsule.fingerprint if artifact.repro_capsule else None,
    )
