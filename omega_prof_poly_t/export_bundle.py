"""JSON and GraphML export bundle for Omega absorb v1.3."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from .documentation_index import render_documentation_index
from .export_commands import build_export_payloads
from .json_exports import packet_digest, to_deterministic_json
from .package_status import build_package_status_report
from .release_bundle import build_release_bundle


@dataclass(frozen=True)
class ExportBundleFile:
    path: str
    kind: str
    digest: str


@dataclass(frozen=True)
class ExportBundleResult:
    source: str
    files: Tuple[ExportBundleFile, ...]
    manifest_json: str
    next_action: str


def build_export_bundle(source: str = "combined", output_dir: str | Path = "generated/omega_absorb_poly_prof_v13") -> ExportBundleResult:
    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)
    payloads = build_export_payloads(source)
    release = build_release_bundle()
    status = build_package_status_report().markdown
    contents = {
        "summary.json": ("summary", payloads.summary_json),
        "validation.json": ("validation", payloads.validation_json),
        "graph.json": ("graph_json", payloads.graph_json),
        "graph.graphml": ("graphml", payloads.graphml),
        "roadmap.md": ("roadmap", release.roadmap_markdown),
        "status.md": ("status", status),
        "docs_index.md": ("docs_index", render_documentation_index()),
    }
    files = []
    for filename, (kind, content) in contents.items():
        path = base / filename
        path.write_text(content, encoding="utf-8")
        files.append(ExportBundleFile(path=str(path), kind=kind, digest=packet_digest(content)))
    manifest = to_deterministic_json(
        {
            "bundle_version": "1.3.0",
            "source": source,
            "files": [file.__dict__ for file in files],
            "next_action": "route_bundle_to_report_or_repo",
        }
    )
    manifest_path = base / "manifest.json"
    manifest_path.write_text(manifest, encoding="utf-8")
    files.append(ExportBundleFile(path=str(manifest_path), kind="manifest", digest=packet_digest(manifest)))
    return ExportBundleResult(source=source, files=tuple(files), manifest_json=manifest, next_action="bundle_written")
