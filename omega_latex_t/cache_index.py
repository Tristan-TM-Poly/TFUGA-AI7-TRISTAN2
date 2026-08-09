from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping


class CacheIndexError(ValueError):
    pass


def _valid_hash(value: str) -> bool:
    return len(value)==64 and all(ch in "0123456789abcdef" for ch in value.lower())


def cache_shard(content_sha256: str, *, prefix_len: int=2) -> str:
    digest=str(content_sha256).lower()
    if not _valid_hash(digest): raise CacheIndexError("content_sha256 must be a SHA-256 hex digest")
    if prefix_len < 1 or prefix_len > 8: raise CacheIndexError("prefix_len must be in [1,8]")
    return digest[:prefix_len]


def build_cache_index(entries: list[Mapping[str, Any]], *, prefix_len: int=2) -> dict[str, Any]:
    normalized=[]; seen={}
    for raw in entries:
        key=str(raw.get("key","")).strip(); digest=str(raw.get("content_sha256","")).lower(); path=str(raw.get("path","")).strip()
        if not key or not path: raise CacheIndexError("cache entry requires key and path")
        shard=cache_shard(digest,prefix_len=prefix_len)
        previous=seen.get(key)
        if previous and previous != digest: raise CacheIndexError(f"cache key collision with different content: {key}")
        seen[key]=digest; normalized.append({"key":key,"content_sha256":digest,"path":path,"shard":shard,"size":int(raw.get("size",0))})
    normalized.sort(key=lambda x:(x["shard"],x["key"],x["content_sha256"]))
    shards={}
    for item in normalized: shards.setdefault(item["shard"],[]).append(item["key"])
    body={"schema_version":"1.0.0","prefix_len":prefix_len,"entries":normalized,"shards":shards,"boundary":"content-addressed index is an immutable routing aid; cache identity is not current truth and callers must include semantic/environment inputs in keys"}
    body["index_sha256"]=sha256(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()
    return body


def write_sharded_index(index: Mapping[str, Any], root: str|Path) -> list[str]:
    root_path=Path(root); root_path.mkdir(parents=True,exist_ok=True); paths=[]
    by_shard={}
    for entry in index.get("entries",()): by_shard.setdefault(str(entry["shard"]),[]).append(entry)
    for shard in sorted(by_shard):
        path=root_path/f"{shard}.json"; path.write_text(json.dumps({"entries":by_shard[shard]},ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); paths.append(str(path))
    manifest=root_path/"index.json"; manifest.write_text(json.dumps(dict(index),ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); paths.append(str(manifest)); return paths
