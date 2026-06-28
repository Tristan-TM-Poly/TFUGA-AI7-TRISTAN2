"""Generated report artifacts for Omega absorb v0.6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .json_exports import packet_digest, to_deterministic_json
from .professor_backlog_report import ProfessorBacklogReport


@dataclass(frozen=True)
class GeneratedArtifact:
    path: str
    content: str
    digest: str
    kind: str


@dataclass(frozen=True)
class ArtifactManifest:
    artifacts: Tuple[GeneratedArtifact, ...]
    next_action: str


def build_report_artifacts(
    reports: Iterable[ProfessorBacklogReport],
    base_dir: str = "generated/omega_absorb_poly_prof_v06",
) -> ArtifactManifest:
    artifacts = []
    for report in reports:
        safe_name = "".join(char.lower() if char.isalnum() else "_" for char in report.professor).strip("_") or "professor"
        content = report.markdown
        artifacts.append(
            GeneratedArtifact(
                path=f"{base_dir}/{safe_name}.md",
                content=content,
                digest=packet_digest({"professor": report.professor, "content": content}),
                kind="professor_backlog_markdown",
            )
        )
    manifest_content = to_deterministic_json(
        {
            "artifact_count": len(artifacts),
            "artifacts": [
                {"path": item.path, "digest": item.digest, "kind": item.kind}
                for item in artifacts
            ],
        }
    )
    artifacts.append(
        GeneratedArtifact(
            path=f"{base_dir}/manifest.json",
            content=manifest_content,
            digest=packet_digest(manifest_content),
            kind="manifest",
        )
    )
    return ArtifactManifest(
        artifacts=tuple(artifacts),
        next_action="persist_artifacts_if_requested_by_runtime",
    )
