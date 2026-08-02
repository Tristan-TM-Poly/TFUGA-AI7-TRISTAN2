#!/usr/bin/env python3
"""Generate Ω-GENERATOR-DISCOVERY-STACK R0.2 Massive.

The output is a machine-readable candidate atlas, not empirical evidence.
It creates 8,192 generator templates and 16,384 linked benchmark templates.
No permanent total-addition ceiling is encoded; shard sizes are runtime choices.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable, Iterator

DOMAINS = (
    "spectral", "crystal", "elastic", "thermal", "electromagnetic", "chemical",
    "quantum", "stochastic", "fluid", "battery", "optical", "photonic",
    "acoustic", "biological", "ecological", "climate", "materials", "calibration",
    "control", "robotics", "computing", "neural", "epistemic", "software",
    "economic", "energy", "transport", "geological", "astronomical", "linguistic",
    "social", "game",
)
FAMILIES = (
    "translation", "dilation", "rotation", "shear", "diffusion", "advection",
    "reaction", "relaxation", "oscillation", "coupling", "projection", "lift",
    "convolution", "deconvolution", "phase_shift", "amplitude", "broadening",
    "splitting", "merging", "branching", "threshold", "saturation", "hysteresis",
    "memory", "symmetry_break", "topology_change", "rank_change", "noise",
    "measurement", "control", "correction", "compression",
)
SCALES = ("atomic", "molecular", "micro", "meso", "macro", "system", "network", "multiscale")
REPRESENTATIONS = ("state", "operator", "observable", "hypergraph")
STATUSES = ("established_tool", "computational_model", "prototype", "fertile_hypothesis")
INVARIANTS = ("mass", "energy", "charge", "probability", "norm", "symmetry", "positivity", "causality", "trace", "rank", "entropy_budget", "none")
RISKS = ("branch_ambiguity", "non_identifiability", "hidden_state", "numerical_instability", "unit_mismatch", "causal_overclaim", "none")
NON_INVERTIBLE = {"projection", "merging", "rank_change", "measurement", "compression"}


def generator_records() -> Iterator[dict[str, object]]:
    index = 0
    for domain in DOMAINS:
        for family in FAMILIES:
            for scale in SCALES:
                yield {
                    "id": f"GEN-{index:05d}",
                    "domain": domain,
                    "family": family,
                    "scale": scale,
                    "representation": REPRESENTATIONS[(index * 7 + len(domain) + len(family)) % len(REPRESENTATIONS)],
                    "status": STATUSES[(index + len(domain)) % len(STATUSES)],
                    "invariant": INVARIANTS[(index * 3 + len(family)) % len(INVARIANTS)],
                    "risk": RISKS[(index * 5 + len(scale)) % len(RISKS)],
                    "parameter_count": 1 + index % 7,
                    "supports_inverse": family not in NON_INVERTIBLE,
                    "oak_gate": "reconstruct+baseline+uncertainty+domain+negative_control",
                    "benchmark_ids": [f"BEN-{2 * index:05d}", f"BEN-{2 * index + 1:05d}"],
                }
                index += 1


def benchmark_records(specs: list[dict[str, object]]) -> Iterator[dict[str, object]]:
    for index, spec in enumerate(specs):
        for variant in range(2):
            benchmark_index = 2 * index + variant
            yield {
                "id": f"BEN-{benchmark_index:05d}",
                "generator_id": spec["id"],
                "variant": variant,
                "input_seed": (index * 2654435761 + variant) % 2147483647,
                "parameters": {
                    "amplitude": round(1.0 + ((index * 13 + variant) % 17) / 10, 3),
                    "shift": round((((index * 7 + variant) % 21) - 10) / 10, 3),
                    "scale": round(0.5 + ((index * 11 + variant) % 19) / 10, 3),
                },
                "expected": {
                    "finite": True,
                    "reconstruction_error_max": round(1e-6 * (1 + index % 9), 9),
                    "preserve": spec["invariant"],
                },
                "negative_control": "wrong_family",
                "oak_status": "synthetic_template_not_empirical_evidence",
            }


def write_jsonl_shards(records: Iterable[dict[str, object]], directory: Path, prefix: str, shard_size: int) -> tuple[int, list[Path]]:
    if shard_size <= 0:
        raise ValueError("shard_size must be positive")
    directory.mkdir(parents=True, exist_ok=True)
    for stale in directory.glob(f"{prefix}_*.jsonl"):
        stale.unlink()
    count = 0
    paths: list[Path] = []
    handle = None
    try:
        for record in records:
            if count % shard_size == 0:
                if handle is not None:
                    handle.close()
                path = directory / f"{prefix}_{count // shard_size:02d}.jsonl"
                paths.append(path)
                handle = path.open("w", encoding="utf-8")
            assert handle is not None
            handle.write(json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n")
            count += 1
    finally:
        if handle is not None:
            handle.close()
    return count, paths


def fingerprint(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def verify(catalog_paths: list[Path], benchmark_paths: list[Path]) -> dict[str, object]:
    generator_ids: set[str] = set()
    benchmark_links: dict[str, int] = {}
    generator_count = 0
    benchmark_count = 0
    for path in catalog_paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            record_id = record["id"]
            if record_id in generator_ids:
                raise ValueError(f"duplicate generator id: {record_id}")
            generator_ids.add(record_id)
            generator_count += 1
    for path in benchmark_paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            generator_id = record["generator_id"]
            benchmark_links[generator_id] = benchmark_links.get(generator_id, 0) + 1
            benchmark_count += 1
    missing = sorted(generator_ids - benchmark_links.keys())
    wrong_coverage = sorted(key for key, value in benchmark_links.items() if value != 2)
    if generator_count != 8192 or benchmark_count != 16384 or missing or wrong_coverage:
        raise ValueError({
            "generator_count": generator_count,
            "benchmark_count": benchmark_count,
            "missing": missing[:10],
            "wrong_coverage": wrong_coverage[:10],
        })
    return {
        "valid": True,
        "generator_count": generator_count,
        "benchmark_count": benchmark_count,
        "linked_generators": len(benchmark_links),
        "coverage_per_generator": 2,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--catalog-shard-size", type=int, default=1024)
    parser.add_argument("--benchmark-shard-size", type=int, default=1024)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    output = root / "generated" / "omega_generator_discovery_r02"
    catalog_dir = output / "catalogs"
    benchmark_dir = output / "benchmarks"
    specs = list(generator_records())
    generator_count, catalog_paths = write_jsonl_shards(specs, catalog_dir, "generator_catalog", args.catalog_shard_size)
    benchmark_count, benchmark_paths = write_jsonl_shards(benchmark_records(specs), benchmark_dir, "benchmark_matrix", args.benchmark_shard_size)
    validation = verify(catalog_paths, benchmark_paths)
    manifest = {
        "version": "R0.2-massive",
        "generator_records": generator_count,
        "benchmark_records": benchmark_count,
        "domains": DOMAINS,
        "families": FAMILIES,
        "scales": SCALES,
        "catalog_fingerprint": fingerprint(catalog_paths),
        "benchmark_fingerprint": fingerprint(benchmark_paths),
        "record_status": "machine_generated_candidate_templates",
        "oak_boundary": "Volume is not evidence density; promotion requires units, baseline, uncertainty, domain, data and falsification.",
        "validation": validation,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "README.md").write_text(
        "# Ω-GENERATOR-DISCOVERY R0.2 Massive\n\n"
        "8,192 generator candidates and 16,384 linked synthetic benchmark templates.\n\n"
        "These records are machine-generated research candidates, not empirical evidence or certified physical laws.\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
