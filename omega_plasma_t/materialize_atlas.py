"""Materialize the lazy Ω-PLASMA-T∞ atlas into reviewable JSONL shards.

This generator has no permanent total-cell ceiling. Each execution is finite and
records provenance, SHA-256 hashes, counts, and epistemic status. Generated rows
are candidate research objects, never certified physical results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

from .atlas import (
    benchmarks,
    diagnostics,
    instabilities,
    iter_benchmark_model_matrix,
    iter_model_transition_graph,
    iter_regime_lattice,
    models,
    regimes,
)


def _jsonl(rows: Iterable[dict]) -> str:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )


def _write(path: Path, text: str) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return {
        "file": path.name,
        "bytes": len(text.encode("utf-8")),
        "lines": text.count("\n"),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def materialize(output_dir: Path, shard_size: int = 400) -> dict:
    if shard_size <= 0:
        raise ValueError("shard_size must be positive")
    output_dir.mkdir(parents=True, exist_ok=True)

    cells = list(iter_regime_lattice())
    files: list[dict] = []
    for start in range(0, len(cells), shard_size):
        chunk = cells[start : start + shard_size]
        name = f"regime_cells_{start // shard_size:03d}.jsonl"
        metadata = _write(output_dir / name, _jsonl(chunk))
        metadata.update({"start": start, "count": len(chunk)})
        files.append(metadata)

    files.append(
        _write(
            output_dir / "benchmark_model_matrix.jsonl",
            _jsonl(iter_benchmark_model_matrix()),
        )
    )
    files.append(
        _write(
            output_dir / "model_transition_graph.jsonl",
            _jsonl(iter_model_transition_graph()),
        )
    )

    instability_diagnostic_rows = (
        {
            "instability_id": instability["id"],
            "diagnostic_id": diagnostic["id"],
            "status": "candidate_pair_requires_physics_review",
            "direct_text_overlap": sorted(
                set(instability.get("diagnostics", []))
                & set(diagnostic.get("measures", []))
            ),
            "required_checks": [
                "measurement_operator",
                "bandwidth",
                "spatial_resolution",
                "inversion_identifiability",
                "negative_control",
            ],
            "epistemic_status": "generated_mapping_not_validated",
        }
        for instability in instabilities()
        for diagnostic in diagnostics()
    )
    files.append(
        _write(
            output_dir / "instability_diagnostic_matrix.jsonl",
            _jsonl(instability_diagnostic_rows),
        )
    )

    regime_model_rows = (
        {
            "regime_id": regime["id"],
            "model_id": model["id"],
            "status": "candidate_requires_compiler_assessment",
            "required_evidence": [
                "dimensionless_signature",
                "scale_separation",
                "closure_validity",
                "baseline",
                "residual",
            ],
            "epistemic_status": "generated_mapping_not_certified",
        }
        for regime in regimes()
        for model in models()
    )
    files.append(
        _write(
            output_dir / "regime_model_candidate_matrix.jsonl",
            _jsonl(regime_model_rows),
        )
    )

    readme = """# Ω-PLASMA-T∞ Materialized Atlas

Generated, reviewable projections of the lazy plasma atlas. Every row is a
candidate research object, not a certified physical result.

- `regime_cells_*.jsonl`: multi-axis regime cells.
- `benchmark_model_matrix.jsonl`: benchmark/model implementation candidates.
- `model_transition_graph.jsonl`: candidate projections and lifts.
- `instability_diagnostic_matrix.jsonl`: candidate diagnostic mappings.
- `regime_model_candidate_matrix.jsonl`: candidate regime/model mappings.

The manifest records counts and SHA-256 hashes. No file is a permanent ceiling;
future generations may add axes, regimes, models, diagnostics and benchmarks.
"""
    files.append(_write(output_dir / "README.md", readme))

    manifest = {
        "theory": "Ω-PLASMA-T∞",
        "release": "R0.1-materialized-atlas",
        "generator": "omega_plasma_t.materialize_atlas",
        "epistemic_status": "generated_candidate_objects_not_certified",
        "permanent_cap": False,
        "shard_size": shard_size,
        "counts": {
            "regime_cells": len(cells),
            "addressable_regimes": len(regimes()),
            "models": len(models()),
            "benchmarks": len(benchmarks()),
            "instabilities": len(instabilities()),
            "diagnostics": len(diagnostics()),
            "benchmark_model_pairs": len(benchmarks()) * len(models()),
            "model_transitions": len(models()) * (len(models()) - 1),
            "instability_diagnostic_pairs": len(instabilities()) * len(diagnostics()),
            "regime_model_pairs": len(regimes()) * len(models()),
        },
        "files": files,
        "authority": {
            "hardware_actions": 0,
            "experiments": 0,
            "automatic_main_merge": False,
        },
    }
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _write(output_dir / "manifest.json", manifest_text)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("generated/omega_plasma_t/materialized_atlas"),
    )
    parser.add_argument("--shard-size", type=int, default=400)
    args = parser.parse_args(argv)
    manifest = materialize(args.output_dir, args.shard_size)
    print(json.dumps(manifest["counts"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
