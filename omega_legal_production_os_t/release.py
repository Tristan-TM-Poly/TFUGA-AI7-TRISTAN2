"""Release-candidate planning and dry-run provenance for R0.2.

This module never creates tags, GitHub releases, package publications, or
production deployments. It produces deterministic manifests for later gates.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Mapping, Sequence

from .models import ActionType, ExternalActionEnvelope, RiskLevel, hash_payload, iso_utc


_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")


@dataclass(frozen=True, slots=True)
class ReleaseArtifact:
    name: str
    sha256: str
    media_type: str
    size_bytes: int

    def __post_init__(self) -> None:
        if not self.name.strip() or "/" in self.name or "\\" in self.name:
            raise ValueError("artifact name must be a basename")
        if not _DIGEST.fullmatch(self.sha256):
            raise ValueError("artifact digest must be canonical sha256")
        if self.size_bytes < 0:
            raise ValueError("artifact size cannot be negative")

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ReleaseArtifact":
        return cls(
            name=str(data["name"]),
            sha256=str(data["sha256"]),
            media_type=str(data.get("media_type", "application/octet-stream")),
            size_bytes=int(data.get("size_bytes", 0)),
        )


@dataclass(frozen=True, slots=True)
class ReleaseCandidate:
    release_id: str
    repository: str
    commit_sha: str
    version: str
    tag: str
    artifacts: tuple[ReleaseArtifact, ...]
    validations: Mapping[str, str]
    changelog_hash: str
    sbom_hash: str
    created_at: str
    source_issue: int | None = None

    def __post_init__(self) -> None:
        if self.repository.count("/") != 1:
            raise ValueError("repository must use owner/name form")
        if not _COMMIT.fullmatch(self.commit_sha):
            raise ValueError("commit_sha must contain 40 lowercase hexadecimal characters")
        if not _VERSION.fullmatch(self.version):
            raise ValueError("version must be semantic")
        if self.tag != f"v{self.version}":
            raise ValueError("tag must equal v<version>")
        if not self.artifacts:
            raise ValueError("at least one release artifact is required")
        if len({artifact.name for artifact in self.artifacts}) != len(self.artifacts):
            raise ValueError("artifact names must be unique")
        if not _DIGEST.fullmatch(self.changelog_hash) or not _DIGEST.fullmatch(self.sbom_hash):
            raise ValueError("changelog and SBOM must be content-addressed")

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ReleaseCandidate":
        return cls(
            release_id=str(data["release_id"]),
            repository=str(data["repository"]),
            commit_sha=str(data["commit_sha"]),
            version=str(data["version"]),
            tag=str(data["tag"]),
            artifacts=tuple(ReleaseArtifact.from_mapping(item) for item in data.get("artifacts", ())),
            validations=dict(data.get("validations", {})),
            changelog_hash=str(data["changelog_hash"]),
            sbom_hash=str(data["sbom_hash"]),
            created_at=str(data.get("created_at", iso_utc())),
            source_issue=int(data["source_issue"]) if data.get("source_issue") is not None else None,
        )

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "release_id": self.release_id,
            "repository": self.repository,
            "commit_sha": self.commit_sha,
            "version": self.version,
            "tag": self.tag,
            "artifacts": [asdict(item) for item in sorted(self.artifacts, key=lambda item: item.name)],
            "validations": dict(sorted(self.validations.items())),
            "changelog_hash": self.changelog_hash,
            "sbom_hash": self.sbom_hash,
            "created_at": self.created_at,
            "source_issue": self.source_issue,
        }

    @property
    def release_hash(self) -> str:
        return hash_payload(self.canonical_payload())

    def validate(self) -> tuple[str, ...]:
        reasons: list[str] = []
        required = ("tests", "licenses", "sbom", "install")
        for gate in required:
            if self.validations.get(gate) != "PASS":
                reasons.append(f"validation_not_passed:{gate}")
        if self.validations.get("security") not in {"PASS", "NOT_APPLICABLE"}:
            reasons.append("validation_not_passed:security")
        return tuple(reasons)

    def attestation_statement(self, *, workflow_ref: str) -> dict[str, Any]:
        """Return a deterministic SLSA-inspired statement without signing it."""
        subjects = [
            {"name": artifact.name, "digest": {"sha256": artifact.sha256.removeprefix("sha256:")}}
            for artifact in sorted(self.artifacts, key=lambda item: item.name)
        ]
        return {
            "_type": "https://in-toto.io/Statement/v1",
            "subject": subjects,
            "predicateType": "https://slsa.dev/provenance/v1",
            "predicate": {
                "buildDefinition": {
                    "buildType": "https://github.com/Attestations/GitHubActionsWorkflow@v1",
                    "externalParameters": {
                        "repository": self.repository,
                        "commit_sha": self.commit_sha,
                        "workflow_ref": workflow_ref,
                    },
                    "resolvedDependencies": [],
                },
                "runDetails": {
                    "builder": {"id": "https://github.com/actions/runner"},
                    "metadata": {"invocationId": self.release_id},
                },
            },
        }

    def to_action(
        self,
        *,
        company_id: str,
        requested_by: str,
        policy_id: str = "RELEASE-R02",
    ) -> ExternalActionEnvelope:
        payload = self.canonical_payload()
        payload["release_hash"] = self.release_hash
        return ExternalActionEnvelope(
            action_id=self.release_id,
            action_type=ActionType.RELEASE,
            company_id=company_id,
            requested_by=requested_by,
            requested_at=iso_utc(),
            purpose=f"Publish validated release {self.tag} for {self.repository}",
            payload=payload,
            required_approvals=1,
            professional_review_required=False,
            risk_level=RiskLevel.HIGH,
            source_issue=self.source_issue,
            source_commit=self.commit_sha,
            policy_id=policy_id,
            evidence_ids=(self.release_hash, self.changelog_hash, self.sbom_hash),
        )


@dataclass(frozen=True, slots=True)
class ReleaseDryRunReceipt:
    release_id: str
    release_hash: str
    status: str
    planned_tag: str
    artifact_count: int
    attestation_hash: str
    detail: str

    def to_mapping(self) -> dict[str, Any]:
        return asdict(self)


class DryRunReleaseProvider:
    name = "github-release-dry-run"

    def prepare(self, candidate: ReleaseCandidate, *, workflow_ref: str) -> ReleaseDryRunReceipt:
        blockers = candidate.validate()
        if blockers:
            raise RuntimeError("release candidate blocked: " + ",".join(blockers))
        attestation = candidate.attestation_statement(workflow_ref=workflow_ref)
        return ReleaseDryRunReceipt(
            release_id=candidate.release_id,
            release_hash=candidate.release_hash,
            status="DRY_RUN_PREPARED",
            planned_tag=candidate.tag,
            artifact_count=len(candidate.artifacts),
            attestation_hash=hash_payload(attestation),
            detail="No tag, release, package or deployment was created.",
        )


def summarize_artifacts(artifacts: Sequence[ReleaseArtifact]) -> dict[str, Any]:
    return {
        "count": len(artifacts),
        "total_size_bytes": sum(item.size_bytes for item in artifacts),
        "artifact_hash": hash_payload(
            {"artifacts": [asdict(item) for item in sorted(artifacts, key=lambda item: item.name)]}
        ),
    }
