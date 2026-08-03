"""Deterministic proof-carrying bundles with SHA-256 and Merkle receipts."""
from __future__ import annotations
from pathlib import Path
import hashlib,json,os


def canonical_json(payload: object) -> str: return json.dumps(payload,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
def sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def merkle_root(hashes: list[str]) -> str:
    if not hashes: return sha(b"")
    level=sorted(hashes)
    while len(level)>1:
        if len(level)%2: level.append(level[-1])
        level=[sha((level[i]+level[i+1]).encode()) for i in range(0,len(level),2)]
    return level[0]


def write_bundle(out: str|Path, artifacts: dict[str,object], *, metadata: dict|None=None) -> dict:
    out=Path(out); out.mkdir(parents=True,exist_ok=True); receipts=[]
    for name,payload in sorted(artifacts.items()):
        data=canonical_json(payload).encode(); (out/name).write_bytes(data)
        receipts.append({"path":name,"sha256":sha(data),"size":len(data)})
    manifest={"schema_version":"2.0","engine":"OMEGA-SYNERGY-N-T-INFINITY-R2","authority":"review_only",
              "generated_epoch":int(os.environ.get("SOURCE_DATE_EPOCH","0")),"artifacts":receipts,
              "merkle_root":merkle_root([x["sha256"] for x in receipts]),
              "human_review_required":True,"automatic_merge_allowed":False,"automatic_publication_allowed":False,
              "limitations":["Integrity is not truth.","Finite fixtures are not causal or external validation."],**(metadata or {})}
    (out/"manifest.json").write_text(canonical_json(manifest),encoding="utf-8")
    return manifest


def audit_bundle(out: str|Path) -> dict:
    out=Path(out); manifest=json.loads((out/"manifest.json").read_text()); errors=[]; hashes=[]
    for receipt in manifest["artifacts"]:
        path=out/receipt["path"]
        if not path.exists(): errors.append(f"missing:{receipt['path']}"); continue
        data=path.read_bytes(); digest=sha(data); hashes.append(digest)
        if digest!=receipt["sha256"]: errors.append(f"hash:{receipt['path']}")
        if len(data)!=receipt["size"]: errors.append(f"size:{receipt['path']}")
    if merkle_root(hashes)!=manifest["merkle_root"]: errors.append("merkle_root")
    for flag in ("automatic_merge_allowed","automatic_publication_allowed"):
        if manifest.get(flag) is not False: errors.append(flag)
    return {"valid":not errors,"errors":errors,"artifact_count":len(manifest["artifacts"]),"merkle_root":manifest["merkle_root"]}
