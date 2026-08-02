"""Readable JSONL reference materialization for small R0.2 experiments."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
from typing import Iterable, Iterator

from .codec import MixedRadixCodec
from .registry import OrganicRegistry, default_ultra_registry
from .ultra_oak import assess_coordinate

EVIDENCE_KINDS = ("positive_bundle", "negative_control", "cross_modal_corroboration")
MODALITIES = ("ftir", "raman", "nmr", "mass_spectrometry", "uv_visible")

def _json_line(payload: dict[str, object]) -> bytes:
    return (json.dumps(payload, separators=(",", ":"), ensure_ascii=False)+"\n").encode("utf-8")

def compact_family_record(index: int, registry: OrganicRegistry, codec: MixedRadixCodec) -> dict[str, object]:
    coordinate = codec.decode(index).coordinate
    oak = assess_coordinate(coordinate)
    return {"i": index, "id": codec.compact_id(index), "r": registry.fingerprint[:16], "c": oak.compatibility_score, "x": oak.contradiction_bits, "e": 3*index, "s": oak.status}

def evidence_records(index: int) -> Iterator[dict[str, object]]:
    for variant, kind in enumerate(EVIDENCE_KINDS):
        yield {"i": 3*index+variant, "f": index, "k": kind, "m": MODALITIES[(index+variant)%len(MODALITIES)], "s": "synthetic_template_not_empirical_evidence"}

def _write_shard(path: Path, records: Iterable[dict[str, object]]) -> tuple[int, str, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6) as handle:
            for record in records:
                handle.write(_json_line(record)); count += 1
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return count, digest, path.stat().st_size

def generate_ultra_atlas(output: Path, *, family_records: int, family_shard_size: int = 65536, evidence_shard_size: int = 196608, registry: OrganicRegistry | None = None, start_index: int = 0) -> dict[str, object]:
    registry = registry or default_ultra_registry()
    if family_records < 0 or start_index < 0 or start_index+family_records > registry.family_space_size:
        raise ValueError("requested range is outside registry address space")
    codec = MixedRadixCodec(registry)
    output.mkdir(parents=True, exist_ok=True)
    registry.dump(output/"registry.json")
    family_shards=[]; evidence_shards=[]
    end = start_index+family_records
    for shard_number, lower in enumerate(range(start_index, end, family_shard_size)):
        upper=min(end, lower+family_shard_size)
        path=output/"families"/f"family_{shard_number:05d}.jsonl.gz"
        count, sha, size=_write_shard(path,(compact_family_record(i,registry,codec) for i in range(lower,upper)))
        family_shards.append({"path":str(path.relative_to(output)),"start":lower,"stop":upper,"count":count,"sha256":sha,"compressed_bytes":size})
    ev_start=3*start_index; ev_end=3*end
    for shard_number, lower in enumerate(range(ev_start,ev_end,evidence_shard_size)):
        upper=min(ev_end,lower+evidence_shard_size)
        first_family=lower//3; last_family=(upper+2)//3
        records=(record for i in range(first_family,last_family) for record in evidence_records(i) if lower <= int(record["i"]) < upper)
        path=output/"evidence"/f"evidence_{shard_number:05d}.jsonl.gz"
        count,sha,size=_write_shard(path,records)
        evidence_shards.append({"path":str(path.relative_to(output)),"start":lower,"stop":upper,"count":count,"sha256":sha,"compressed_bytes":size})
    manifest={"version":"R0.2-ultra-jsonl-reference","registry_fingerprint":registry.fingerprint,"logical_family_space":registry.family_space_size,"logical_linked_object_space":registry.linked_object_space_size,"start_index":start_index,"family_records":family_records,"evidence_records":3*family_records,"total_objects":4*family_records,"family_shards":family_shards,"evidence_shards":evidence_shards,"oak_boundary":"Generated addresses and evidence templates are research candidates, not certified molecules or experimental validation."}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return manifest

def audit_ultra_atlas(output: Path) -> dict[str, object]:
    manifest=json.loads((output/"manifest.json").read_text(encoding="utf-8")); errors=[]
    for section in ("family_shards","evidence_shards"):
        for shard in manifest[section]:
            path=output/shard["path"]
            if not path.exists(): errors.append(f"missing:{shard['path']}"); continue
            if hashlib.sha256(path.read_bytes()).hexdigest() != shard["sha256"]: errors.append(f"sha256:{shard['path']}")
            with gzip.open(path,"rt",encoding="utf-8") as handle: count=sum(1 for _ in handle)
            if count != shard["count"]: errors.append(f"count:{shard['path']}")
    if manifest["total_objects"] != manifest["family_records"]+manifest["evidence_records"]: errors.append("manifest_total")
    return {"valid":not errors,"errors":errors,"family_records":manifest["family_records"],"evidence_records":manifest["evidence_records"],"total_objects":manifest["total_objects"]}
