from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping

from .compiler import DocumentCompiler
from .models import DocumentIR
from .projection import project_depth


class UniverseManifestError(ValueError):
    pass


def _safe_id(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_.:-]+", "-", value.strip()).strip("-")
    if not text: raise UniverseManifestError("entry id cannot be empty")
    return text


def _manifest_hash(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(raw).hexdigest()


def normalize_universe_manifest(payload: Mapping[str, Any]) -> dict[str, Any]:
    entries = []; seen: set[str] = set()
    for index, raw in enumerate(payload.get("entries", ())):
        if not isinstance(raw, Mapping): raise UniverseManifestError(f"entries[{index}] must be an object")
        entry_id = _safe_id(str(raw.get("id", f"entry-{index+1}")))
        if entry_id in seen: raise UniverseManifestError(f"duplicate universe entry id {entry_id!r}")
        seen.add(entry_id); kind = str(raw.get("kind", "docir"))
        if kind not in {"docir", "markdown", "summary", "github_snapshot"}: raise UniverseManifestError(f"unsupported source kind {kind!r}")
        path = str(raw.get("path", "")).strip()
        if not path: raise UniverseManifestError(f"entry {entry_id!r} has no path")
        entries.append({"id": entry_id, "kind": kind, "path": path, "title": str(raw.get("title", "")), "author": str(raw.get("author", "")), "language": str(raw.get("language", "en"))})
    depths = sorted({int(x) for x in payload.get("depths", [0,1,2,3,4,5])})
    if not depths or any(x < 0 for x in depths): raise UniverseManifestError("depths must contain at least one non-negative integer")
    shard_size = int(payload.get("shard_size", 128))
    if shard_size < 1: raise UniverseManifestError("shard_size must be >= 1")
    normalized = {"schema_version":"1.0.0","entries":entries,"depths":depths,"shard_size":shard_size,"boundary":"finite manifest over local/authorized inputs; no network access, remote mutation, publication or infinite-resource claim"}
    normalized["manifest_sha256"] = _manifest_hash(normalized); return normalized


def universe_plan(payload: Mapping[str, Any]) -> dict[str, Any]:
    manifest = normalize_universe_manifest(payload); jobs=[]
    for entry in manifest["entries"]:
        for depth in manifest["depths"]: jobs.append({"job_id":f"{entry['id']}:D{depth}","entry_id":entry["id"],"source_kind":entry["kind"],"source_path":entry["path"],"depth":depth,"output_relpath":f"{entry['id']}/D{depth}"})
    shards=[]; size=manifest["shard_size"]
    for start in range(0,len(jobs),size):
        subset=jobs[start:start+size]; shards.append({"shard_id":f"universe-{start//size+1:05d}","job_ids":[job["job_id"] for job in subset]})
    return {"schema_version":"1.0.0","manifest":manifest,"job_count":len(jobs),"jobs":jobs,"shards":shards,"checkpoint":{"completed_job_ids":[],"next_job_id":jobs[0]["job_id"] if jobs else None,"complete":not jobs},"boundary":"job count is derived from the finite manifest rather than a permanent system ceiling; runtime remains bounded by physical resources, quality gates and explicit input scope"}


def _load_entry(entry: Mapping[str, Any], base_dir: Path) -> DocumentIR:
    path=(base_dir/str(entry["path"])).resolve()
    if not path.exists(): raise UniverseManifestError(f"source path does not exist: {path}")
    kind=str(entry["kind"])
    if kind=="docir": return DocumentIR.from_mapping(json.loads(path.read_text(encoding="utf-8")))
    if kind=="markdown":
        from .adapters import markdown_to_document
        return markdown_to_document(path.read_text(encoding="utf-8"),title=str(entry.get("title") or path.stem),author=str(entry.get("author","")),language=str(entry.get("language","en")))
    payload=json.loads(path.read_text(encoding="utf-8"))
    if kind=="summary":
        from .adapters import summary_bundle_to_document
        return summary_bundle_to_document(payload)
    if kind=="github_snapshot":
        from .adapters import github_snapshot_to_document
        return github_snapshot_to_document(payload)
    raise UniverseManifestError(f"unsupported source kind {kind!r}")


def build_universe(manifest_path: str|Path, output_dir: str|Path, cache_dir: str|Path, *, resume: bool=True) -> dict[str, Any]:
    manifest_path=Path(manifest_path); plan=universe_plan(json.loads(manifest_path.read_text(encoding="utf-8"))); manifest=plan["manifest"]; output=Path(output_dir); cache=Path(cache_dir); output.mkdir(parents=True,exist_ok=True); cache.mkdir(parents=True,exist_ok=True)
    checkpoint_path=output/"checkpoint.json"; completed:set[str]=set()
    if resume and checkpoint_path.exists():
        checkpoint=json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint.get("manifest_sha256")==manifest["manifest_sha256"]: completed.update(str(x) for x in checkpoint.get("completed_job_ids",()))
    entries={entry["id"]:entry for entry in manifest["entries"]}; loaded:dict[str,DocumentIR]={}; receipts=[]; compiler=DocumentCompiler()
    for job in plan["jobs"]:
        job_id=job["job_id"]
        if job_id in completed: receipts.append({"job_id":job_id,"status":"resumed-skip"}); continue
        entry_id=job["entry_id"]
        if entry_id not in loaded: loaded[entry_id]=_load_entry(entries[entry_id],manifest_path.parent)
        projection=project_depth(loaded[entry_id],int(job["depth"])); target=output/job["output_relpath"]
        artifact=compiler.build_incremental_to(projection,target,cache/entry_id/f"D{job['depth']}")
        receipts.append({"job_id":job_id,"status":"built","semantic_hash":artifact.semantic_hash,"latex_sha256":artifact.latex_hash,"oak_passed":artifact.audit.passed,"cache":dict(artifact.cache_receipt or {})}); completed.add(job_id)
        remaining=[candidate["job_id"] for candidate in plan["jobs"] if candidate["job_id"] not in completed]
        checkpoint_path.write_text(json.dumps({"manifest_sha256":manifest["manifest_sha256"],"completed_job_ids":sorted(completed),"next_job_id":remaining[0] if remaining else None,"complete":not remaining},ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    report={"schema_version":"1.0.0","manifest_sha256":manifest["manifest_sha256"],"job_count":plan["job_count"],"completed_job_count":len(completed),"receipts":receipts,"checkpoint":json.loads(checkpoint_path.read_text(encoding="utf-8")) if checkpoint_path.exists() else plan["checkpoint"],"boundary":"local deterministic document campaign; success proves build/audit contracts only, not scientific truth or publication readiness"}
    (output/"universe-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return report
