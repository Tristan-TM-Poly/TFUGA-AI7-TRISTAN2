"""Fast fixed-width packed atlas for tens of millions of addressable objects.

Family records are four bytes each: compatibility percent (u8), contradiction
bitset (u16 little-endian), warning flags (u8). The family index is implicit
from shard start + record offset. Evidence records are one byte each; family
and evidence ids are implicit from position. This is lossless for the declared
schema and avoids pretending that repeated JSON keys are scientific content.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import struct

from .registry import OrganicRegistry, default_ultra_registry

FAMILY_RECORD_BYTES = 4
EVIDENCE_RECORD_BYTES = 1
FAMILY_STRUCT = struct.Struct("<BHB")


def _digits_for(index: int, radices: tuple[int, ...]) -> list[int]:
    digits = [0] * len(radices)
    for pos in range(len(radices) - 1, -1, -1):
        index, digits[pos] = divmod(index, radices[pos])
    return digits


def _increment(digits: list[int], radices: tuple[int, ...]) -> None:
    for pos in range(len(digits) - 1, -1, -1):
        value = digits[pos] + 1
        if value < radices[pos]:
            digits[pos] = value
            return
        digits[pos] = 0


def _assessment(d: list[int]) -> tuple[int, int, int]:
    skeleton, family, electronic, _, stereo, environment, _, protonation, _, solvent, temperature, _ = d
    bits = 0
    if electronic == 0 and family == 1: bits |= 1 << 0
    if electronic == 0 and skeleton == 15: bits |= 1 << 1
    if electronic == 3 and skeleton == 0: bits |= 1 << 2
    if electronic == 3 and skeleton == 1: bits |= 1 << 3
    if stereo == 2 and skeleton == 6: bits |= 1 << 4
    if environment == 0 and solvent == 4: bits |= 1 << 5
    if environment == 2 and solvent == 0: bits |= 1 << 6
    if temperature == 0 and solvent == 6: bits |= 1 << 7
    flags = 0
    if electronic == 7: flags |= 1 << 0
    if protonation in (6, 7): flags |= 1 << 1
    penalty = 20 * bits.bit_count() + 3 * flags.bit_count()
    return max(0, 100 - penalty), bits, flags


def _family_payload(start: int, count: int, radices: tuple[int, ...]) -> bytes:
    digits = _digits_for(start, radices)
    out = bytearray(count * FAMILY_RECORD_BYTES)
    offset = 0
    for _ in range(count):
        score, bits, flags = _assessment(digits)
        FAMILY_STRUCT.pack_into(out, offset, score, bits, flags)
        offset += FAMILY_RECORD_BYTES
        _increment(digits, radices)
    return bytes(out)


def _evidence_payload(family_start: int, family_count: int) -> bytes:
    out = bytearray(family_count * 3)
    offset = 0
    for family_index in range(family_start, family_start + family_count):
        for variant in range(3):
            modality = (family_index + variant) % 5
            out[offset] = (modality << 2) | variant
            offset += 1
    return bytes(out)


def _write_gzip(path: Path, payload: bytes) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6) as handle:
            handle.write(payload)
    data = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "compressed_bytes": len(data), "raw_bytes": len(payload)}


def _merkle_root(hashes: list[str]) -> str:
    nodes = [bytes.fromhex(value) for value in hashes]
    if not nodes: return hashlib.sha256(b"").hexdigest()
    while len(nodes) > 1:
        if len(nodes) % 2: nodes.append(nodes[-1])
        nodes = [hashlib.sha256(nodes[i] + nodes[i+1]).digest() for i in range(0, len(nodes), 2)]
    return nodes[0].hex()


def generate_packed_atlas(output: Path, *, family_records: int = 16_777_216, shard_families: int = 1_048_576, start_index: int = 0, registry: OrganicRegistry | None = None) -> dict[str, object]:
    registry = registry or default_ultra_registry()
    if family_records < 0 or shard_families <= 0 or start_index < 0 or start_index + family_records > registry.family_space_size:
        raise ValueError("invalid packed-atlas range")
    output.mkdir(parents=True, exist_ok=True)
    registry.dump(output / "registry.json")
    family_shards=[]; evidence_shards=[]
    for shard_no, lower in enumerate(range(start_index, start_index + family_records, shard_families)):
        count = min(shard_families, start_index + family_records - lower)
        fpath = output / "families" / f"family_{shard_no:05d}.bin.gz"
        fmeta = _write_gzip(fpath, _family_payload(lower, count, registry.radices))
        fmeta.update({"path": str(fpath.relative_to(output)), "start": lower, "count": count, "record_bytes": FAMILY_RECORD_BYTES})
        family_shards.append(fmeta)
        epath = output / "evidence" / f"evidence_{shard_no:05d}.bin.gz"
        emeta = _write_gzip(epath, _evidence_payload(lower, count))
        emeta.update({"path": str(epath.relative_to(output)), "family_start": lower, "family_count": count, "count": 3 * count, "record_bytes": EVIDENCE_RECORD_BYTES})
        evidence_shards.append(emeta)
        checkpoint={"version":"R0.2-ultra-packed","next_family_index":lower+count,"completed_family_records":lower+count-start_index,"target_family_records":family_records,"last_completed_shard":shard_no}
        (output/"checkpoint.json").write_text(json.dumps(checkpoint,indent=2)+"\n",encoding="utf-8")
    hashes=[s["sha256"] for s in family_shards+evidence_shards]
    manifest={"version":"R0.2-ultra-packed","encoding":"fixed_width_binary_gzip","registry_fingerprint":registry.fingerprint,"logical_family_space":registry.family_space_size,"logical_linked_object_space":registry.linked_object_space_size,"start_index":start_index,"family_records":family_records,"evidence_records":3*family_records,"total_objects":4*family_records,"family_record_schema":"<BHB: compatibility_percent, contradiction_bits, warning_flags; index implicit","evidence_record_schema":"u8: bits[1:0]=kind, bits[4:2]=modality; family index implicit","family_shards":family_shards,"evidence_shards":evidence_shards,"merkle_root":_merkle_root(hashes),"oak_boundary":"Packed objects are deterministic research addresses and test templates, not certified molecules, syntheses, spectra or safety claims."}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    with (output/"m_plus.jsonl").open("a",encoding="utf-8") as handle:
        handle.write(json.dumps({"event":"packed_materialization_succeeded","family_records":family_records,"total_objects":4*family_records,"merkle_root":manifest["merkle_root"]})+"\n")
    return manifest


def audit_packed_atlas(output: Path, *, sample_stride: int = 104729) -> dict[str, object]:
    manifest=json.loads((output/"manifest.json").read_text(encoding="utf-8")); errors=[]; samples=0
    for section, expected_record_bytes in (("family_shards",FAMILY_RECORD_BYTES),("evidence_shards",EVIDENCE_RECORD_BYTES)):
        for shard in manifest[section]:
            path=output/shard["path"]
            if not path.exists(): errors.append(f"missing:{shard['path']}"); continue
            if hashlib.sha256(path.read_bytes()).hexdigest()!=shard["sha256"]: errors.append(f"sha256:{shard['path']}")
            with gzip.open(path,"rb") as handle: payload=handle.read()
            if len(payload)!=int(shard["count"])*expected_record_bytes: errors.append(f"raw_size:{shard['path']}")
            if section=="family_shards" and payload:
                count=int(shard["count"])
                for pos in range(0,count,max(1,sample_stride)):
                    score,bits,flags=FAMILY_STRUCT.unpack_from(payload,pos*FAMILY_RECORD_BYTES)
                    if score>100 or bits>0xFFFF or flags>0xFF: errors.append(f"decode:{shard['path']}:{pos}")
                    samples+=1
    hashes=[s["sha256"] for s in manifest["family_shards"]+manifest["evidence_shards"]]
    if _merkle_root(hashes)!=manifest["merkle_root"]: errors.append("merkle_root")
    return {"valid":not errors,"errors":errors,"samples_checked":samples,"family_records":manifest["family_records"],"evidence_records":manifest["evidence_records"],"total_objects":manifest["total_objects"],"merkle_root":manifest["merkle_root"]}
