from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Iterator, Mapping

from .compiler import DocumentCompiler
from .models import DocumentIR
from .projection import project_depth


class UniverseManifestError(ValueError):
    pass


def _safe_id(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_.:-]+", "-", value.strip()).strip("-")
    if not text:
        raise UniverseManifestError("entry id cannot be empty")
    return text


def _manifest_hash(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(raw).hexdigest()


def normalize_universe_manifest(payload: Mapping[str, Any]) -> dict[str, Any]:
    entries = []
    seen: set[str] = set()
    raw_entries = payload.get("entries", ())
    if not isinstance(raw_entries, (list, tuple)):
        raise UniverseManifestError("entries must be an array")
    for index, raw in enumerate(raw_entries):
        if not isinstance(raw, Mapping):
            raise UniverseManifestError(f"entries[{index}] must be an object")
        entry_id = _safe_id(str(raw.get("id", f"entry-{index+1}")))
        if entry_id in seen:
            raise UniverseManifestError(f"duplicate universe entry id {entry_id!r}")
        seen.add(entry_id)
        kind = str(raw.get("kind", "docir"))
        if kind not in {"docir", "markdown", "summary", "github_snapshot"}:
            raise UniverseManifestError(f"unsupported source kind {kind!r}")
        path = str(raw.get("path", "")).strip()
        if not path:
            raise UniverseManifestError(f"entry {entry_id!r} has no path")
        entries.append({"id": entry_id, "kind": kind, "path": path, "title": str(raw.get("title", "")), "author": str(raw.get("author", "")), "language": str(raw.get("language", "en"))})

    try:
        depths = sorted({int(x) for x in payload.get("depths", [0, 1, 2, 3, 4, 5])})
    except (TypeError, ValueError) as exc:
        raise UniverseManifestError("depths must contain integers") from exc
    if not depths or any(x < 0 for x in depths):
        raise UniverseManifestError("depths must contain at least one non-negative integer")

    try:
        shard_size = int(payload.get("shard_size", 128))
    except (TypeError, ValueError) as exc:
        raise UniverseManifestError("shard_size must be an integer") from exc
    if shard_size < 1:
        raise UniverseManifestError("shard_size must be >= 1")

    raw_roots = payload.get("allowed_roots", ["."])
    if not isinstance(raw_roots, (list, tuple)) or not raw_roots:
        raise UniverseManifestError("allowed_roots must be a non-empty array")
    allowed_roots = [str(x).strip() for x in raw_roots]
    if any(not root for root in allowed_roots):
        raise UniverseManifestError("allowed_roots cannot contain empty paths")

    normalized = {
        "schema_version": "1.0.1",
        "entries": entries,
        "depths": depths,
        "shard_size": shard_size,
        "allowed_roots": allowed_roots,
        "boundary": "finite manifest over local/authorized inputs; filesystem access is confined to explicit allowed_roots; no network access, remote mutation, publication or infinite-resource claim",
    }
    normalized["manifest_sha256"] = _manifest_hash(normalized)
    return normalized


def _iter_jobs(manifest: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
    for entry in manifest["entries"]:
        for depth in manifest["depths"]:
            yield {"job_id": f"{entry['id']}:D{depth}", "entry_id": entry["id"], "source_kind": entry["kind"], "source_path": entry["path"], "depth": depth, "output_relpath": f"{entry['id']}/D{depth}"}


def universe_plan(payload: Mapping[str, Any]) -> dict[str, Any]:
    manifest = normalize_universe_manifest(payload)
    jobs = list(_iter_jobs(manifest))
    shards = []
    size = manifest["shard_size"]
    for start in range(0, len(jobs), size):
        subset = jobs[start:start + size]
        shards.append({"shard_id": f"universe-{start//size+1:05d}", "job_ids": [job["job_id"] for job in subset]})
    return {
        "schema_version": "1.0.1",
        "manifest": manifest,
        "job_count": len(jobs),
        "jobs": jobs,
        "shards": shards,
        "checkpoint": {"next_job_index": 0, "completed_job_count": 0, "next_job_id": jobs[0]["job_id"] if jobs else None, "complete": not jobs},
        "boundary": "universe-plan materializes a finite review plan; build-universe itself streams jobs and is not limited by a permanent total-document ceiling",
    }


def _resolve_allowed_roots(base_dir: Path, roots: list[str]) -> tuple[Path, ...]:
    resolved = []
    for raw in roots:
        root = Path(raw)
        if not root.is_absolute():
            root = base_dir / root
        resolved.append(root.resolve())
    return tuple(resolved)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _authorized_path(path_value: str, base_dir: Path, allowed_roots: tuple[Path, ...]) -> Path:
    candidate = Path(path_value)
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    resolved = candidate.resolve()
    if not any(_is_within(resolved, root) for root in allowed_roots):
        raise UniverseManifestError(f"source path escapes allowed_roots: {path_value!r}")
    if not resolved.exists():
        raise UniverseManifestError(f"source path does not exist: {resolved}")
    if not resolved.is_file():
        raise UniverseManifestError(f"source path is not a regular file: {resolved}")
    return resolved


def _load_entry(entry: Mapping[str, Any], base_dir: Path, allowed_roots: tuple[Path, ...]) -> DocumentIR:
    path = _authorized_path(str(entry["path"]), base_dir, allowed_roots)
    kind = str(entry["kind"])
    if kind == "docir":
        return DocumentIR.from_mapping(json.loads(path.read_text(encoding="utf-8")))
    if kind == "markdown":
        from .adapters import markdown_to_document
        return markdown_to_document(path.read_text(encoding="utf-8"), title=str(entry.get("title") or path.stem), author=str(entry.get("author", "")), language=str(entry.get("language", "en")))
    payload = json.loads(path.read_text(encoding="utf-8"))
    if kind == "summary":
        from .adapters import summary_bundle_to_document
        return summary_bundle_to_document(payload)
    if kind == "github_snapshot":
        from .adapters import github_snapshot_to_document
        return github_snapshot_to_document(payload)
    raise UniverseManifestError(f"unsupported source kind {kind!r}")


def _legacy_resume_index(manifest: Mapping[str, Any], checkpoint: Mapping[str, Any]) -> int:
    completed = {str(x) for x in checkpoint.get("completed_job_ids", ())}
    if not completed:
        return 0
    index = 0
    for job in _iter_jobs(manifest):
        if job["job_id"] not in completed:
            return index
        index += 1
    return index


def build_universe(manifest_path: str | Path, output_dir: str | Path, cache_dir: str | Path, *, resume: bool = True) -> dict[str, Any]:
    manifest_path = Path(manifest_path)
    manifest = normalize_universe_manifest(json.loads(manifest_path.read_text(encoding="utf-8")))
    output = Path(output_dir)
    cache = Path(cache_dir)
    output.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)

    base_dir = manifest_path.parent.resolve()
    allowed_roots = _resolve_allowed_roots(base_dir, list(manifest["allowed_roots"]))
    checkpoint_path = output / "checkpoint.json"
    total_jobs = len(manifest["entries"]) * len(manifest["depths"])
    start_index = 0
    if resume and checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint.get("manifest_sha256") == manifest["manifest_sha256"]:
            if "next_job_index" in checkpoint:
                start_index = max(0, min(int(checkpoint.get("next_job_index", 0)), total_jobs))
            else:
                start_index = _legacy_resume_index(manifest, checkpoint)

    receipts = []
    compiler = DocumentCompiler()
    depth_count = len(manifest["depths"])
    current_entry_index = -1
    current_doc: DocumentIR | None = None

    for flat_index in range(start_index, total_jobs):
        entry_index, depth_index = divmod(flat_index, depth_count)
        entry = manifest["entries"][entry_index]
        depth = manifest["depths"][depth_index]
        job_id = f"{entry['id']}:D{depth}"

        if entry_index != current_entry_index:
            current_doc = _load_entry(entry, base_dir, allowed_roots)
            current_entry_index = entry_index
        assert current_doc is not None

        projection = project_depth(current_doc, int(depth))
        target = output / entry["id"] / f"D{depth}"
        artifact = compiler.build_incremental_to(projection, target, cache / entry["id"] / f"D{depth}")
        receipts.append({"job_id": job_id, "status": "built", "semantic_hash": artifact.semantic_hash, "latex_sha256": artifact.latex_hash, "oak_passed": artifact.audit.passed, "cache": dict(artifact.cache_receipt or {})})

        next_index = flat_index + 1
        next_job_id = None
        if next_index < total_jobs:
            next_entry_index, next_depth_index = divmod(next_index, depth_count)
            next_entry = manifest["entries"][next_entry_index]
            next_depth = manifest["depths"][next_depth_index]
            next_job_id = f"{next_entry['id']}:D{next_depth}"

        checkpoint_path.write_text(json.dumps({
            "schema_version": "1.0.1",
            "manifest_sha256": manifest["manifest_sha256"],
            "next_job_index": next_index,
            "completed_job_count": next_index,
            "next_job_id": next_job_id,
            "complete": next_index >= total_jobs,
            "boundary": "cursor checkpoint is O(1) in campaign size; it records deterministic progress, not scientific validity",
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if total_jobs == 0 or start_index >= total_jobs:
        checkpoint_payload = {
            "schema_version": "1.0.1",
            "manifest_sha256": manifest["manifest_sha256"],
            "next_job_index": total_jobs,
            "completed_job_count": total_jobs,
            "next_job_id": None,
            "complete": True,
            "boundary": "cursor checkpoint is O(1) in campaign size; it records deterministic progress, not scientific validity",
        }
        checkpoint_path.write_text(json.dumps(checkpoint_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    report = {
        "schema_version": "1.0.1",
        "manifest_sha256": manifest["manifest_sha256"],
        "job_count": total_jobs,
        "completed_job_count": int(checkpoint["completed_job_count"]),
        "executed_job_count": len(receipts),
        "receipts": receipts,
        "checkpoint": checkpoint,
        "allowed_roots": [str(x) for x in allowed_roots],
        "streaming": {"materialized_job_list": False, "resident_document_count_max": 1, "checkpoint_state_growth": "O(1)"},
        "boundary": "local deterministic streaming document campaign; success proves build/audit contracts only, not scientific truth or publication readiness",
    }
    (output / "universe-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
