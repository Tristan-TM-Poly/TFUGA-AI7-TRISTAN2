#!/usr/bin/env python3
"""Generate deterministic public provenance for Tristan Web OS.

The manifest records repository-relative source references, existence, SHA-256, size,
and which public theories/claims depend on each source. A hash proves byte identity
for a repository snapshot; it does not prove truth, authorship, legality, safety,
or scientific validity.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "apps" / "tristan-8fire-site" / "data"
OUTPUT_JSON = SITE_DATA / "provenance.json"
OUTPUT_MD = ROOT / "content" / "generated" / "PROVENANCE_INDEX.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized_path(raw: str) -> str:
    value = str(raw or "").strip().replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def classify(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".md", ".rst", ".txt"}:
        return "document"
    if suffix in {".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".cpp", ".c", ".h"}:
        return "code"
    if suffix in {".json", ".jsonl", ".yaml", ".yml", ".toml"}:
        return "structured-data"
    if suffix in {".csv", ".tsv", ".parquet"}:
        return "dataset"
    if suffix in {".pdf"}:
        return "publication"
    return "other"


def build_manifest() -> dict[str, Any]:
    theory_payload = read_json(SITE_DATA / "theories.json")
    claim_payload = read_json(SITE_DATA / "claims.json")
    theories = theory_payload["theories"]
    claims = claim_payload["claims"]

    theory_refs: dict[str, set[str]] = defaultdict(set)
    claim_refs: dict[str, set[str]] = defaultdict(set)
    reference_notes: dict[str, list[dict[str, str]]] = defaultdict(list)

    for theory in theories:
        path = normalized_path(theory.get("source_path", ""))
        if path:
            theory_refs[path].add(theory["id"])
            reference_notes[path].append({
                "object_type": "theory",
                "object_id": theory["id"],
                "locator": theory.get("version", ""),
                "note": "Source canonique déclarée par la fiche publique.",
            })

    for claim in claims:
        for support in claim.get("support", []):
            path = normalized_path(support.get("path", ""))
            if not path:
                continue
            claim_refs[path].add(claim["id"])
            theory_refs[path].add(claim["theory_id"])
            reference_notes[path].append({
                "object_type": "claim",
                "object_id": claim["id"],
                "locator": str(support.get("locator", "")),
                "note": str(support.get("note", "")),
            })

    sources = []
    all_paths = sorted(set(theory_refs) | set(claim_refs))
    for index, relative in enumerate(all_paths, start=1):
        resolved = (ROOT / relative).resolve()
        within_root = resolved == ROOT or ROOT in resolved.parents
        exists = within_root and resolved.exists()
        is_file = exists and resolved.is_file()
        is_directory = exists and resolved.is_dir()
        if is_file:
            digest = sha256_file(resolved)
            size = resolved.stat().st_size
            status = "resolved-file"
        elif is_directory:
            digest = None
            size = None
            status = "resolved-directory"
        elif not within_root:
            digest = None
            size = None
            status = "blocked-outside-repository"
        else:
            digest = None
            size = None
            status = "unresolved"
        sources.append({
            "id": f"source-{index:04d}",
            "path": relative,
            "kind": classify(relative),
            "status": status,
            "sha256": digest,
            "size_bytes": size,
            "theory_ids": sorted(theory_refs[relative]),
            "claim_ids": sorted(claim_refs[relative]),
            "references": sorted(reference_notes[relative], key=lambda item: (item["object_type"], item["object_id"], item["locator"])),
            "epistemic_boundary": "Byte identity and repository presence do not certify the referenced claim.",
        })

    source_by_path = {item["path"]: item for item in sources}
    theory_provenance = []
    for theory in theories:
        path = normalized_path(theory.get("source_path", ""))
        source = source_by_path.get(path)
        theory_provenance.append({
            "theory_id": theory["id"],
            "source_ids": [source["id"]] if source else [],
            "resolved_sources": int(bool(source and source["status"].startswith("resolved"))),
            "claim_count": sum(1 for claim in claims if claim["theory_id"] == theory["id"]),
        })

    claim_provenance = []
    for claim in claims:
        paths = [normalized_path(item.get("path", "")) for item in claim.get("support", [])]
        linked = [source_by_path[path] for path in paths if path in source_by_path]
        claim_provenance.append({
            "claim_id": claim["id"],
            "theory_id": claim["theory_id"],
            "source_ids": sorted({item["id"] for item in linked}),
            "resolved_sources": sum(1 for item in linked if item["status"].startswith("resolved")),
            "unresolved_sources": sum(1 for item in linked if item["status"] == "unresolved"),
            "support_count": len(claim.get("support", [])),
            "automatic_promotion": False,
        })

    status_counts: dict[str, int] = defaultdict(int)
    for source in sources:
        status_counts[source["status"]] += 1

    return {
        "schema_version": "0.3.0",
        "generated_from": theory_payload.get("generated_at"),
        "repository_scope": "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",
        "hash_algorithm": "sha256",
        "disclaimer": "Provenance records repository references and byte identity. It does not certify truth, authorship, safety, legal status, IP ownership, or scientific validity.",
        "metrics": {
            "sources": len(sources),
            "resolved_files": status_counts.get("resolved-file", 0),
            "resolved_directories": status_counts.get("resolved-directory", 0),
            "unresolved": status_counts.get("unresolved", 0),
            "blocked_outside_repository": status_counts.get("blocked-outside-repository", 0),
            "theories": len(theories),
            "claims": len(claims),
        },
        "sources": sources,
        "theory_provenance": theory_provenance,
        "claim_provenance": claim_provenance,
    }


def render_markdown(manifest: dict[str, Any]) -> str:
    metrics = manifest["metrics"]
    lines = [
        "# Tristan Web OS — Provenance Index",
        "",
        "> A repository path or SHA-256 proves neither truth nor scientific validation.",
        "",
        "## Metrics",
        "",
        f"- Sources: **{metrics['sources']}**",
        f"- Resolved files: **{metrics['resolved_files']}**",
        f"- Resolved directories: **{metrics['resolved_directories']}**",
        f"- Unresolved references: **{metrics['unresolved']}**",
        f"- Claims mapped: **{metrics['claims']}**",
        f"- Theories mapped: **{metrics['theories']}**",
        "",
        "## Sources",
        "",
        "| ID | Status | Kind | Path | SHA-256 | Theories | Claims |",
        "|---|---|---|---|---|---:|---:|",
    ]
    for source in manifest["sources"]:
        digest = source["sha256"][:16] + "…" if source["sha256"] else "—"
        path = source["path"].replace("|", "\\|")
        lines.append(
            f"| `{source['id']}` | {source['status']} | {source['kind']} | `{path}` | `{digest}` | "
            f"{len(source['theory_ids'])} | {len(source['claim_ids'])} |"
        )
    lines.extend([
        "",
        "## OAK boundary",
        "",
        "- `resolved-file` means that the referenced path existed when this manifest was generated.",
        "- SHA-256 detects byte changes; it does not establish interpretation or validity.",
        "- `unresolved` references must remain visible and cannot silently become evidence.",
        "- The manifest contains no authorization to publish private or IP-vault material.",
        "- Every claim keeps `automatic_promotion=false`.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    manifest = build_manifest()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(render_markdown(manifest), encoding="utf-8")
    print(json.dumps(manifest["metrics"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
