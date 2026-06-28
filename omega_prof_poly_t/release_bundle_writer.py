"""Local release bundle writer for Omega absorb v1.1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from .release_bundle import build_release_bundle
from .version_manifest import build_version_manifest


@dataclass(frozen=True)
class WrittenBundleFile:
    path: str
    bytes_written: int


@dataclass(frozen=True)
class ReleaseBundleWriteResult:
    files: Tuple[WrittenBundleFile, ...]
    next_action: str


def write_release_bundle(base_dir: str | Path = "generated/omega_absorb_poly_prof_v11") -> ReleaseBundleWriteResult:
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    bundle = build_release_bundle()
    manifest = build_version_manifest()
    files = {
        "release_summary.json": bundle.summary_json,
        "release_roadmap.md": bundle.roadmap_markdown,
        "version_manifest.md": "\n".join(
            ["# Omega Absorb Version Manifest", ""]
            + [f"- {entry.version}: {entry.title} [{entry.status}]" for entry in manifest.entries]
        )
        + "\n",
    }
    written = []
    for name, content in files.items():
        path = base / name
        path.write_text(content, encoding="utf-8")
        written.append(WrittenBundleFile(path=str(path), bytes_written=len(content.encode("utf-8"))))
    return ReleaseBundleWriteResult(files=tuple(written), next_action="bundle_files_written")
