"""Massive deterministic synthetic OAKBench for the R0.3 evidence engine.

The benchmark probes missing signals, counter-signatures, source quality, noise,
and abstention. It is engineering test data, not chemical measurement.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import struct
from typing import Iterable

FAMILIES = 16
MODALITIES = 5
NOISE_LEVELS = 16
MISSING_LEVELS = 8
COUNTER_LEVELS = 8
RECORD = struct.Struct("<BBBB")


def scenario(index: int) -> tuple[int, int, int, int]:
    expected = index % FAMILIES
    q = index // FAMILIES
    modality = q % MODALITIES
    q //= MODALITIES
    noise = q % NOISE_LEVELS
    q //= NOISE_LEVELS
    missing = q % MISSING_LEVELS
    q //= MISSING_LEVELS
    counter = q % COUNTER_LEVELS
    replicate = q // COUNTER_LEVELS
    jitter = ((index * 1103515245 + 12345) >> 16) & 31
    signal = 245 - 7 * noise - 14 * missing - 16 * counter + (jitter - 15)
    signal += (4 - modality) * 2
    if signal < 40:
        predicted = 255
        confidence = max(0, min(255, signal + 32))
    elif signal < 90:
        predicted = (expected + 1 + ((replicate + noise + counter) % (FAMILIES - 1))) % FAMILIES
        confidence = max(0, min(255, 190 - signal // 2))
    else:
        predicted = expected
        confidence = max(0, min(255, signal))
    flags = (1 if missing >= 5 else 0) | (2 if counter >= 4 else 0) | (4 if noise >= 10 else 0)
    return expected, predicted, confidence, flags


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _merkle(leaves: Iterable[str]) -> str:
    nodes = [bytes.fromhex(item) for item in leaves]
    if not nodes:
        return hashlib.sha256(b"").hexdigest()
    while len(nodes) > 1:
        if len(nodes) % 2:
            nodes.append(nodes[-1])
        nodes = [hashlib.sha256(nodes[i] + nodes[i + 1]).digest() for i in range(0, len(nodes), 2)]
    return nodes[0].hex()


def generate_benchmark(root: Path, *, cases: int, shard_cases: int = 1_048_576, clean: bool = False) -> dict[str, object]:
    if cases < 0 or shard_cases <= 0:
        raise ValueError("invalid benchmark size")
    output = root / "generated" / "omega_org_fam_t_r03_evidence_benchmark"
    shards = output / "shards"
    if clean and output.exists():
        import shutil
        shutil.rmtree(output)
    shards.mkdir(parents=True, exist_ok=True)
    confusion = [[0 for _ in range(FAMILIES + 1)] for _ in range(FAMILIES)]
    confidence_bins = [{"count": 0, "correct": 0} for _ in range(10)]
    strata = {"clean": [0, 0], "missing": [0, 0], "counter": [0, 0], "high_noise": [0, 0]}
    metadata: list[dict[str, object]] = []
    correct = wrong = abstained = 0
    for shard_index, start in enumerate(range(0, cases, shard_cases)):
        count = min(shard_cases, cases - start)
        path = shards / f"cases_{shard_index:05d}.bin.gz"
        with path.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6) as handle:
                buffer = bytearray()
                for offset in range(count):
                    expected, predicted, confidence, flags = scenario(start + offset)
                    buffer.extend(RECORD.pack(expected, predicted, confidence, flags))
                    column = FAMILIES if predicted == 255 else predicted
                    confusion[expected][column] += 1
                    is_correct = predicted == expected
                    if predicted == 255:
                        abstained += 1
                    elif is_correct:
                        correct += 1
                    else:
                        wrong += 1
                    bucket = min(9, confidence * 10 // 256)
                    confidence_bins[bucket]["count"] += 1
                    confidence_bins[bucket]["correct"] += int(is_correct)
                    key = "clean"
                    if flags & 1:
                        key = "missing"
                    if flags & 2:
                        key = "counter"
                    if flags & 4:
                        key = "high_noise"
                    strata[key][0] += 1
                    strata[key][1] += int(is_correct)
                    if len(buffer) >= 4 * 262_144:
                        handle.write(buffer)
                        buffer.clear()
                if buffer:
                    handle.write(buffer)
        metadata.append({"path": str(path.relative_to(output)), "start": start, "count": count, "raw_bytes": count * RECORD.size, "compressed_bytes": path.stat().st_size, "sha256": _sha(path)})
    for item in confidence_bins:
        item["empirical_accuracy"] = round(item["correct"] / item["count"], 6) if item["count"] else None
    strata_report = {key: {"count": value[0], "correct": value[1], "accuracy": round(value[1] / value[0], 6) if value[0] else None} for key, value in strata.items()}
    manifest = {
        "version": "R0.3-evidence-benchmark",
        "status": "synthetic_engineering_benchmark_not_chemical_evidence",
        "cases": cases,
        "record_bytes": RECORD.size,
        "correct": correct,
        "wrong": wrong,
        "abstained": abstained,
        "accuracy_non_abstained": round(correct / (correct + wrong), 6) if correct + wrong else None,
        "coverage": round((correct + wrong) / cases, 6) if cases else None,
        "shards": metadata,
        "merkle_root": _merkle(item["sha256"] for item in metadata),
        "confidence_bins": confidence_bins,
        "strata": strata_report,
        "confusion_matrix": confusion,
        "generator": {"permanent_total_ceiling": None, "finite_run_cases": cases, "axes": {"families": FAMILIES, "modalities": MODALITIES, "noise": NOISE_LEVELS, "missing": MISSING_LEVELS, "counter": COUNTER_LEVELS}},
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (output / "README.md").write_text(
        "# Ω-ORG-FAM-T R0.3 Evidence OAKBench\n\n"
        "Deterministic synthetic cases for missing bands, counter-signatures, noise, source quality and abstention. "
        "This corpus is engineering evidence for the software only; it is not experimental chemistry.\n",
        encoding="utf-8",
    )
    return manifest


def audit_benchmark(output: Path) -> dict[str, object]:
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    count = 0
    hashes: list[str] = []
    for item in manifest["shards"]:
        path = output / item["path"]
        if not path.exists():
            errors.append(f"missing:{item['path']}")
            continue
        digest = _sha(path)
        hashes.append(digest)
        if digest != item["sha256"]:
            errors.append(f"sha256:{item['path']}")
        with gzip.open(path, "rb") as handle:
            raw = handle.read()
        if len(raw) != int(item["raw_bytes"]):
            errors.append(f"raw_bytes:{item['path']}")
        if len(raw) % RECORD.size:
            errors.append(f"record_alignment:{item['path']}")
        count += len(raw) // RECORD.size
    if count != manifest["cases"]:
        errors.append(f"case_count:{count}!={manifest['cases']}")
    if _merkle(hashes) != manifest["merkle_root"]:
        errors.append("merkle_root")
    return {"valid": not errors, "errors": errors, "cases": count, "merkle_root": _merkle(hashes)}
