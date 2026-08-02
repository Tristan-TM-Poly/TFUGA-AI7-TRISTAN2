#!/usr/bin/env python3
"""Generate a deterministic byte-level manifest for the Tristan Web OS public app.

The manifest detects changed, missing or extra application files. It is not a code
signature, a security certification, or proof that the browser executed the files.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "apps" / "tristan-8fire-site"
OUTPUT = SITE / "data" / "build-manifest.json"
OUTPUT_MD = ROOT / "content" / "generated" / "BUILD_MANIFEST.md"
EXCLUDED = {
    "data/build-manifest.json",
    ".DS_Store",
}
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", "node_modules", ".git"}


def digest_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def role(path: str) -> str:
    if path == "index.html":
        return "document-shell"
    if path.endswith(".css"):
        return "stylesheet"
    if path.endswith(".js"):
        return "javascript-module"
    if path.endswith(".json"):
        return "public-data"
    if path.endswith(".webmanifest"):
        return "web-manifest"
    if path.endswith(".md"):
        return "documentation"
    if path == "package.json":
        return "module-contract"
    return "asset"


def iter_files() -> list[Path]:
    files = []
    for path in SITE.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(SITE).as_posix()
        if relative in EXCLUDED or any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(SITE).as_posix())


def build_manifest() -> dict[str, Any]:
    theory_payload = json.loads((SITE / "data" / "theories.json").read_text(encoding="utf-8"))
    records = []
    role_counts: Counter[str] = Counter()
    extension_counts: Counter[str] = Counter()
    total_bytes = 0
    root_digest = hashlib.sha256()

    for path in iter_files():
        relative = path.relative_to(SITE).as_posix()
        content = path.read_bytes()
        file_digest = digest_bytes(content)
        file_role = role(relative)
        size = len(content)
        total_bytes += size
        role_counts[file_role] += 1
        extension_counts[path.suffix.lower() or "<none>"] += 1
        root_digest.update(relative.encode("utf-8"))
        root_digest.update(b"\0")
        root_digest.update(file_digest.encode("ascii"))
        root_digest.update(b"\0")
        root_digest.update(str(size).encode("ascii"))
        root_digest.update(b"\n")
        records.append({
            "path": relative,
            "role": file_role,
            "size_bytes": size,
            "sha256": file_digest,
            "cache_candidate": relative not in {"README.md", "package.json"},
        })

    return {
        "schema_version": "0.3.0",
        "generated_from": theory_payload.get("generated_at"),
        "algorithm": "sha256(path\\0sha256\\0size\\n)",
        "root_sha256": root_digest.hexdigest(),
        "metrics": {
            "files": len(records),
            "bytes": total_bytes,
            "roles": dict(sorted(role_counts.items())),
            "extensions": dict(sorted(extension_counts.items())),
        },
        "files": records,
        "excluded": sorted(EXCLUDED),
        "epistemic_boundary": (
            "The root hash identifies this generated application snapshot. It does not "
            "certify security, accessibility, scientific validity, deployment identity, "
            "authorship, legal status, or absence of runtime compromise."
        ),
    }


def render_markdown(manifest: dict[str, Any]) -> str:
    metrics = manifest["metrics"]
    lines = [
        "# Tristan Web OS — Build Manifest",
        "",
        f"- Schema: `{manifest['schema_version']}`",
        f"- Files: **{metrics['files']}**",
        f"- Bytes: **{metrics['bytes']}**",
        f"- Root SHA-256: `{manifest['root_sha256']}`",
        "",
        "> The root hash identifies bytes in this repository snapshot; it is not a security or scientific certification.",
        "",
        "## Role counts",
        "",
    ]
    for key, value in metrics["roles"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend([
        "",
        "## Files",
        "",
        "| Path | Role | Bytes | SHA-256 |",
        "|---|---|---:|---|",
    ])
    for item in manifest["files"]:
        lines.append(f"| `{item['path']}` | {item['role']} | {item['size_bytes']} | `{item['sha256']}` |")
    lines.extend([
        "",
        "## Verification",
        "",
        "```bash",
        "python scripts/generate_tristan_web_build_manifest.py",
        "git diff --exit-code -- apps/tristan-8fire-site/data/build-manifest.json content/generated/BUILD_MANIFEST.md",
        "```",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    manifest = build_manifest()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(render_markdown(manifest), encoding="utf-8")
    print(json.dumps({"files": manifest["metrics"]["files"], "bytes": manifest["metrics"]["bytes"], "root_sha256": manifest["root_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
