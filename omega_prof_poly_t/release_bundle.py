"""Release bundle builder for Omega absorb v1.0."""

from __future__ import annotations

from dataclasses import dataclass

from .e2e_pipeline_v09 import run_v09_e2e_pipeline
from .json_exports import to_deterministic_json
from .roadmap_compiler import render_roadmap_markdown
from .version_manifest import VersionManifest, build_version_manifest


@dataclass(frozen=True)
class ReleaseBundle:
    version: str
    manifest: VersionManifest
    summary_json: str
    roadmap_markdown: str
    next_action: str


def build_release_bundle() -> ReleaseBundle:
    manifest = build_version_manifest()
    result = run_v09_e2e_pipeline()
    summary_json = to_deterministic_json(
        {
            "version": manifest.release,
            "validation_clean": result.validation.is_clean,
            "artifact_count": len(result.artifact_run.manifest.artifacts),
            "roadmap_steps": len(result.roadmap.steps),
            "department_score": result.department_report.score,
            "manifest_versions": [entry.version for entry in manifest.entries],
        }
    )
    return ReleaseBundle(
        version=manifest.release,
        manifest=manifest,
        summary_json=summary_json,
        roadmap_markdown=render_roadmap_markdown(result.roadmap),
        next_action="store_release_bundle_artifacts",
    )
