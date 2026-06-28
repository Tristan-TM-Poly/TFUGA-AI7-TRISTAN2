"""Changelog generator for Omega absorb v1.3."""

from __future__ import annotations

from .version_manifest import VersionManifest, build_version_manifest


def generate_changelog(manifest: VersionManifest | None = None) -> str:
    manifest = manifest or build_version_manifest()
    lines = ["# Omega Absorb Changelog", ""]
    for entry in reversed(manifest.entries):
        lines.extend(
            [
                f"## v{entry.version}",
                "",
                f"- {entry.title}",
                f"- status: {entry.status}",
                f"- modules: {', '.join(entry.modules)}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def generate_release_notes(version: str, manifest: VersionManifest | None = None) -> str:
    manifest = manifest or build_version_manifest()
    for entry in manifest.entries:
        if entry.version == version:
            return (
                f"# Omega Absorb v{entry.version}\n\n"
                f"{entry.title}\n\n"
                f"Status: {entry.status}\n\n"
                f"Modules: {', '.join(entry.modules)}\n"
            )
    return f"# Omega Absorb v{version}\n\nNo manifest entry found.\n"
