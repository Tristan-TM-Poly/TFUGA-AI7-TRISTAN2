from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable

from .audit import audit_document
from .delta import node_hash, semantic_delta
from .models import DocumentIR, Node


CACHE_VERSION = "omega-latex-node-cache-v1"


def _stable_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fragment_cache_key(node: Node, doc: DocumentIR) -> str:
    result_value = doc.results.get(node.result_key) if node.result_key else None
    payload = {
        "cache_version": CACHE_VERSION,
        "node_hash": node_hash(node),
        "result_key": node.result_key,
        "result_value": result_value,
    }
    return sha256(_stable_json(payload)).hexdigest()


@dataclass(frozen=True)
class CacheReceipt:
    hits: int
    misses: int
    keys: dict[str, str]

    def to_mapping(self) -> dict[str, Any]:
        return {"hits": self.hits, "misses": self.misses, "keys": dict(sorted(self.keys.items()))}


class FragmentCache:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def path_for(self, key: str) -> Path:
        return self.root / key[:2] / f"{key}.tex"

    def get(self, key: str) -> str | None:
        path = self.path_for(key)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def put(self, key: str, content: str) -> Path:
        path = self.path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = content.encode("utf-8")
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(encoded)
        tmp.replace(path)
        return path


def shard_ids(node_ids: Iterable[str], shard_size: int = 128) -> list[list[str]]:
    size = int(shard_size)
    if size < 1:
        raise ValueError("shard_size must be >= 1")
    ordered = sorted(set(str(x) for x in node_ids))
    return [ordered[i : i + size] for i in range(0, len(ordered), size)]


def rebuild_plan(before: DocumentIR, after: DocumentIR, *, shard_size: int = 128) -> dict[str, Any]:
    delta = semantic_delta(before, after)
    affected = list(delta["affected_after"])
    shards = []
    for index, ids in enumerate(shard_ids(affected, shard_size), start=1):
        shards.append(
            {
                "shard_id": f"latex-rebuild-{index:05d}",
                "node_ids": ids,
                "node_hashes": {node.id: node_hash(node) for node in after.nodes if node.id in ids},
            }
        )
    return {
        "schema_version": "1.0.0",
        "before_semantic_hash": delta["before_semantic_hash"],
        "after_semantic_hash": delta["after_semantic_hash"],
        "rebuild_required": delta["rebuild_required"],
        "affected_after": affected,
        "shard_size": int(shard_size),
        "shards": shards,
        "delta": delta,
        "checkpoint": {
            "completed_shards": [],
            "next_shard": shards[0]["shard_id"] if shards else None,
            "complete": not shards,
        },
        "boundary": "finite sharding/checkpoint plan; no claim of unbounded physical compute or complete semantic impact detection",
    }


def write_rebuild_plan(before: DocumentIR, after: DocumentIR, path: str | Path, *, shard_size: int = 128) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(rebuild_plan(before, after, shard_size=shard_size), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def incremental_fragments(
    compiler: Any,
    doc: DocumentIR,
    cache_dir: str | Path,
    *,
    force_node_ids: Iterable[str] = (),
) -> tuple[dict[str, str], CacheReceipt]:
    report = audit_document(doc)
    if getattr(compiler, "fail_on_audit_error", True) and not report.passed:
        raise ValueError("OAK audit failed: " + ", ".join(x.code for x in report.errors))
    cache = FragmentCache(cache_dir)
    force = set(force_node_ids)
    fragments: dict[str, str] = {}
    keys: dict[str, str] = {}
    hits = 0
    misses = 0
    for node in compiler.topological_nodes(doc):
        key = fragment_cache_key(node, doc)
        keys[node.id] = key
        cached = None if node.id in force else cache.get(key)
        if cached is not None:
            hits += 1
            fragments[node.id] = cached
            continue
        misses += 1
        rendered = compiler.render_node(node, doc)
        cache.put(key, rendered)
        fragments[node.id] = rendered
    return fragments, CacheReceipt(hits=hits, misses=misses, keys=keys)
