"""Deterministic artifact summaries for Omega absorb v0.7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .generated_report_artifacts import ArtifactManifest, GeneratedArtifact
from .json_exports import packet_digest, to_deterministic_json


@dataclass(frozen=True)
class ArtifactSummary:
    summary_id: str
    count: int
    paths: Tuple[str, ...]
    digests: Tuple[str, ...]
    json: str


def build_artifact_summary(manifest: ArtifactManifest | Iterable[GeneratedArtifact]) -> ArtifactSummary:
    artifacts = manifest.artifacts if isinstance(manifest, ArtifactManifest) else tuple(manifest)
    paths = tuple(item.path for item in artifacts)
    digests = tuple(item.digest for item in artifacts)
    payload = {"count": len(artifacts), "paths": paths, "digests": digests}
    json_text = to_deterministic_json(payload)
    summary_id = packet_digest(json_text)
    return ArtifactSummary(
        summary_id=summary_id,
        count=len(artifacts),
        paths=paths,
        digests=digests,
        json=json_text,
    )
