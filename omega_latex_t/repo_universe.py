from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping


class RepoUniverseError(ValueError):
    pass


def _digest(payload: Mapping[str, Any]) -> str:
    return sha256(json.dumps(dict(payload),ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()


def repository_inventory_to_universe(payload: Mapping[str, Any], *, depths=(0,1,2,3,4,5), shard_size: int=128) -> dict[str, Any]:
    repositories=payload.get("repositories",())
    if not isinstance(repositories,(list,tuple)): raise RepoUniverseError("repositories must be an array")
    normalized_depths=sorted({int(x) for x in depths})
    if not normalized_depths or any(x < 0 for x in normalized_depths): raise RepoUniverseError("depths must contain at least one non-negative integer")
    if int(shard_size) < 1: raise RepoUniverseError("shard_size must be >= 1")
    entries=[]; skipped=[]; seen=set(); routing={}
    for index,repo in enumerate(repositories):
        if not isinstance(repo,Mapping): skipped.append({"index":index,"reason":"not-an-object"}); continue
        full_name=str(repo.get("full_name",repo.get("name",""))).strip()
        repo_id=str(repo.get("id",full_name or f"repo-{index+1}"))
        source=repo.get("document_source",{})
        if not isinstance(source,Mapping) or not str(source.get("path","")).strip():
            skipped.append({"repository":full_name or repo_id,"reason":"no-authorized-document-source"}); continue
        kind=str(source.get("kind","summary")); path=str(source.get("path",""))
        if kind not in {"docir","markdown","summary","github_snapshot"}: skipped.append({"repository":full_name or repo_id,"reason":f"unsupported-source-kind:{kind}"}); continue
        entry_id="repo-"+sha256(repo_id.encode("utf-8")).hexdigest()[:16]
        if entry_id in seen: raise RepoUniverseError(f"duplicate repository identity {repo_id!r}")
        seen.add(entry_id)
        entries.append({"id":entry_id,"kind":kind,"path":path,"title":str(source.get("title",full_name or repo_id)),"author":str(source.get("author","")),"language":str(source.get("language","en"))}); routing[entry_id]={"repository":full_name,"repository_id":repo_id,"repository_ref":str(repo.get("ref",repo.get("default_branch","")))}
    manifest={"entries":entries,"depths":normalized_depths,"shard_size":int(shard_size)}
    return {"schema_version":"1.0.0","inventory_sha256":_digest(payload),"repository_count":len(repositories),"admitted_count":len(entries),"skipped":skipped,"routing":routing,"universe_manifest":manifest,"boundary":"repository inventory routing uses only explicit authorized document_source paths; repository presence alone is not evidence of document semantics or scientific validity"}
