"""Generated changelog plus for Omega absorb v1.9."""

from __future__ import annotations

from .version_manifest import VersionManifest, build_version_manifest


def generate_changelog_plus(manifest: VersionManifest | None = None) -> str:
    manifest = manifest or build_version_manifest()
    lines = ["# Omega Absorb Changelog Plus", "", f"current release: {manifest.release}", ""]
    for entry in reversed(manifest.entries):
        lines.extend(
            [
                f"## v{entry.version}",
                f"- title: {entry.title}",
                f"- status: {entry.status}",
                f"- module_count: {len(entry.modules)}",
                f"- modules: {', '.join(entry.modules)}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"
