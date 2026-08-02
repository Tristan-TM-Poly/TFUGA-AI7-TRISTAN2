#!/usr/bin/env python3
"""Generate Ω-GENERATOR-DISCOVERY R0.3 Ultra.

The compiler expands a configurable Cartesian research space into linked JSONL
shards plus a SQLite index. It intentionally encodes no permanent total-record
ceiling: the configuration controls the current finite experiment.

Generated candidates are not scientific discoveries. Generated benchmark and
validation records are specifications that still require real data, calibrated
units, baselines, uncertainty and falsification before promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Sequence

INVARIANTS = (
    "mass", "energy", "charge", "probability", "norm", "symmetry",
    "positivity", "causality", "trace", "rank", "entropy_budget", "none",
)
RISKS = (
    "branch_ambiguity", "non_identifiability", "hidden_state",
    "numerical_instability", "unit_mismatch", "causal_overclaim", "none",
)
STATUSES = (
    "established_tool", "computational_model", "prototype", "fertile_hypothesis",
)
NON_INVERTIBLE = {
    "projection", "merging", "rank_change", "measurement", "compression",
}
FAMILY_DSL = {
    "translation": "exp(theta_0 * partial_axis)",
    "dilation": "exp(theta_0 * x_axis * partial_axis)",
    "rotation": "exp(theta_0 * J_axis)",
    "shear": "exp(theta_0 * x_j * partial_i)",
    "diffusion": "exp(theta_0 * laplacian)",
    "advection": "exp(-theta_0 * velocity_dot_grad)",
    "reaction": "exp(theta_0 * reaction_jacobian)",
    "relaxation": "exp(-theta_0 * relaxation_rate)",
    "oscillation": "exp(theta_0 * skew_generator)",
    "coupling": "exp(theta_0 * coupled_block_operator)",
    "projection": "lift_then_project(projector_rank_r)",
    "lift": "exp(nilpotent_lift(T))",
    "convolution": "exp(theta_0 * convolution_generator)",
    "deconvolution": "regularized_inverse(exp(theta_0 * convolution_generator))",
    "phase_shift": "exp(i * theta_0 * phase_operator)",
    "amplitude": "exp(theta_0 * identity)",
    "broadening": "exp(theta_0 * width_generator)",
    "splitting": "discrete_split + exp(theta_0 * branch_generator)",
    "merging": "singular_merge + active_support_exp(theta_0)",
    "branching": "conditional_product_exp(branch_generators)",
    "threshold": "event_gate(threshold) o exp(theta_0 * local_generator)",
    "saturation": "nonlinear_flow(saturation_field)",
    "hysteresis": "path_ordered_exp(memory_connection)",
    "memory": "augmented_state_exp(delay_generator)",
    "symmetry_break": "sector_change(symmetry_label) + exp(theta_0 * mode)",
    "topology_change": "topological_sector + lifted_continuous_flow",
    "rank_change": "active_factorization(kernel,image,cokernel)",
    "noise": "stochastic_semigroup(noise_generator)",
    "measurement": "instrument_lift + exp(acquisition_generator) + projection",
    "control": "closed_loop_exp(A + B*K)",
    "correction": "exp(theta_0 * correction_operator)",
    "compression": "encoder + active_exp(latent_generator) + decoder",
}


def load_config(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = (
        "domains", "families", "scales", "representations", "regimes",
        "benchmark_variants", "shard_size", "validation_sample_modulus",
        "high_risk_families", "oak_boundary",
    )
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"missing configuration keys: {missing}")
    for key in ("domains", "families", "scales", "representations", "regimes"):
        values = data[key]
        if not isinstance(values, list) or not values or len(values) != len(set(values)):
            raise ValueError(f"{key} must be a non-empty unique list")
    if int(data["shard_size"]) <= 0:
        raise ValueError("shard_size must be positive")
    return data


def _generator_id(index: int) -> str:
    return f"GEN3-{index:06d}"


def _benchmark_id(index: int) -> str:
    return f"BEN3-{index:07d}"


def _edge_id(index: int) -> str:
    return f"EDGE3-{index:06d}"


def _negative_id(index: int) -> str:
    return f"NEG3-{index:06d}"


def _validation_id(index: int) -> str:
    return f"VAL3-{index:06d}"


def expected_generator_count(config: Mapping[str, object]) -> int:
    total = 1
    for key in ("domains", "families", "scales", "representations", "regimes"):
        total *= len(config[key])  # type: ignore[arg-type]
    return total


def generator_records(config: Mapping[str, object]) -> Iterator[dict[str, object]]:
    domains: Sequence[str] = config["domains"]  # type: ignore[assignment]
    families: Sequence[str] = config["families"]  # type: ignore[assignment]
    scales: Sequence[str] = config["scales"]  # type: ignore[assignment]
    representations: Sequence[str] = config["representations"]  # type: ignore[assignment]
    regimes: Sequence[str] = config["regimes"]  # type: ignore[assignment]
    high_risk = set(config["high_risk_families"])  # type: ignore[arg-type]
    benchmark_variants: Sequence[str] = config["benchmark_variants"]  # type: ignore[assignment]

    for index, (domain, family, scale, representation, regime) in enumerate(
        itertools.product(domains, families, scales, representations, regimes)
    ):
        family_index = families.index(family)
        status = STATUSES[(index + len(domain) + family_index) % len(STATUSES)]
        risk = RISKS[(index * 5 + len(family) + len(regime)) % len(RISKS)]
        risk_tier = "high" if family in high_risk else ("medium" if risk != "none" else "low")
        benchmark_start = index * len(benchmark_variants)
        yield {
            "id": _generator_id(index),
            "ordinal": index,
            "coordinates": {
                "domain": domain,
                "family": family,
                "scale": scale,
                "representation": representation,
                "regime": regime,
            },
            "operator_dsl": FAMILY_DSL[family],
            "parameter_schema": {
                "theta_0": {"type": "number", "unit": "domain_required"},
                "time_or_path": {"type": "number", "minimum": 0},
            },
            "status": status,
            "invariant": INVARIANTS[(index * 3 + len(domain)) % len(INVARIANTS)],
            "risk": risk,
            "risk_tier": risk_tier,
            "supports_inverse": family not in NON_INVERTIBLE,
            "requires_discrete_sector": family in {
                "splitting", "branching", "threshold", "symmetry_break", "topology_change",
            },
            "requires_singular_sector": family in NON_INVERTIBLE,
            "oak_gate": [
                "units", "provenance", "reconstruction", "baseline", "uncertainty",
                "domain_of_validity", "negative_control", "falsification",
            ],
            "benchmark_ids": [
                _benchmark_id(benchmark_start + offset)
                for offset in range(len(benchmark_variants))
            ],
            "hyperedge_id": _edge_id(index),
            "negative_control_id": _negative_id(index),
            "validation_id": _validation_id(index),
            "epistemic_status": "machine_generated_candidate_not_evidence",
        }


def benchmark_records(
    specs: Sequence[dict[str, object]], config: Mapping[str, object]
) -> Iterator[dict[str, object]]:
    variants: Sequence[str] = config["benchmark_variants"]  # type: ignore[assignment]
    for index, spec in enumerate(specs):
        coordinates = spec["coordinates"]
        assert isinstance(coordinates, dict)
        for variant_index, variant in enumerate(variants):
            benchmark_index = index * len(variants) + variant_index
            seed = (index * 2654435761 + variant_index * 40503) % 2147483647
            yield {
                "id": _benchmark_id(benchmark_index),
                "generator_id": spec["id"],
                "variant": variant,
                "input_seed": seed,
                "domain": coordinates["domain"],
                "family": coordinates["family"],
                "scale": coordinates["scale"],
                "representation": coordinates["representation"],
                "regime": coordinates["regime"],
                "parameters": {
                    "theta_0": round((((index * 17 + variant_index) % 41) - 20) / 20, 6),
                    "duration": round(0.05 + ((index * 11 + variant_index) % 40) / 20, 6),
                    "noise_fraction": round(variant_index * (1 + index % 7) / 1000, 6),
                },
                "expected": {
                    "finite": True,
                    "reconstruction_error_max": round(1e-7 * (1 + index % 17), 12),
                    "preserve": spec["invariant"],
                    "reject_wrong_family": True,
                },
                "baseline": "identity_or_domain_standard",
                "epistemic_status": "synthetic_benchmark_specification_not_experiment",
            }


def _partner_index(index: int, config: Mapping[str, object]) -> int:
    families: Sequence[str] = config["families"]  # type: ignore[assignment]
    scales: Sequence[str] = config["scales"]  # type: ignore[assignment]
    representations: Sequence[str] = config["representations"]  # type: ignore[assignment]
    regimes: Sequence[str] = config["regimes"]  # type: ignore[assignment]
    family_stride = len(scales) * len(representations) * len(regimes)
    domain_stride = len(families) * family_stride
    domain_offset = (index // domain_stride) * domain_stride
    within_domain = index % domain_stride
    family_index = within_domain // family_stride
    remainder = within_domain % family_stride
    partner_family = (family_index + 1) % len(families)
    return domain_offset + partner_family * family_stride + remainder


def hyperedge_records(
    specs: Sequence[dict[str, object]], config: Mapping[str, object]
) -> Iterator[dict[str, object]]:
    for index, left in enumerate(specs):
        partner_index = _partner_index(index, config)
        right = specs[partner_index]
        left_coords = left["coordinates"]
        right_coords = right["coordinates"]
        assert isinstance(left_coords, dict) and isinstance(right_coords, dict)
        pair = (left_coords["family"], right_coords["family"])
        expected = "nonzero" if pair in {
            ("translation", "dilation"), ("rotation", "shear"),
            ("advection", "diffusion"), ("reaction", "diffusion"),
            ("measurement", "correction"), ("control", "correction"),
        } else "unknown_requires_test"
        yield {
            "id": _edge_id(index),
            "left_generator_id": left["id"],
            "right_generator_id": right["id"],
            "relation": "ordered_composition_and_commutator_candidate",
            "same_domain": True,
            "expected_commutator": expected,
            "experiment": {
                "path_a": [left["id"], right["id"]],
                "path_b": [right["id"], left["id"]],
                "compare": "normalized_final_state_residual",
            },
            "epistemic_status": "generated_hyperedge_requires_domain_validation",
        }


def negative_control_records(
    specs: Sequence[dict[str, object]], config: Mapping[str, object]
) -> Iterator[dict[str, object]]:
    families: Sequence[str] = config["families"]  # type: ignore[assignment]
    for index, spec in enumerate(specs):
        coordinates = spec["coordinates"]
        assert isinstance(coordinates, dict)
        family = str(coordinates["family"])
        wrong_family = families[(families.index(family) + 7) % len(families)]
        yield {
            "id": _negative_id(index),
            "generator_id": spec["id"],
            "negative_family": wrong_family,
            "perturbation": "replace_family_keep_domain_scale_representation_regime",
            "expected_outcome": "worse_reconstruction_or_invariant_violation",
            "failure_if_not_rejected": "non_identifiability_or_overflexible_basis",
            "epistemic_status": "mandatory_negative_control_specification",
        }


def validation_records(
    specs: Sequence[dict[str, object]], config: Mapping[str, object]
) -> Iterator[dict[str, object]]:
    modulus = int(config["validation_sample_modulus"])
    for index, spec in enumerate(specs):
        risk_tier = str(spec["risk_tier"])
        if risk_tier == "high":
            mode = "exhaustive_required"
        elif index % modulus == 0:
            mode = "deterministic_stratified_sample"
        else:
            mode = "deferred_low_or_medium_risk"
        yield {
            "id": _validation_id(index),
            "generator_id": spec["id"],
            "risk_tier": risk_tier,
            "validation_mode": mode,
            "checks": [
                "schema", "finite_output", "cross_links", "negative_control",
                "invariant", "reconstruction", "uncertainty_placeholder",
            ],
            "promotion_allowed": False,
            "promotion_blocker": "real_data_and_domain_expert_review_required",
        }


def write_jsonl_shards(
    records: Iterable[dict[str, object]], directory: Path, prefix: str, shard_size: int
) -> tuple[int, list[Path]]:
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
                path = directory / f"{prefix}_{count // shard_size:03d}.jsonl"
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
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def _iter_jsonl(paths: Iterable[Path]) -> Iterator[dict[str, object]]:
    for path in sorted(paths):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def build_sqlite(
    database: Path,
    catalog_paths: list[Path],
    benchmark_paths: list[Path],
    edge_paths: list[Path],
    negative_paths: list[Path],
    validation_paths: list[Path],
) -> None:
    if database.exists():
        database.unlink()
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    try:
        connection.executescript(
            """
            PRAGMA journal_mode=OFF;
            PRAGMA synchronous=OFF;
            CREATE TABLE generators (
                id TEXT PRIMARY KEY, ordinal INTEGER UNIQUE, domain TEXT, family TEXT,
                scale TEXT, representation TEXT, regime TEXT, status TEXT,
                invariant_name TEXT, risk TEXT, risk_tier TEXT,
                supports_inverse INTEGER, payload TEXT
            );
            CREATE TABLE benchmarks (
                id TEXT PRIMARY KEY, generator_id TEXT, variant TEXT, payload TEXT
            );
            CREATE TABLE hyperedges (
                id TEXT PRIMARY KEY, left_id TEXT, right_id TEXT, payload TEXT
            );
            CREATE TABLE negative_controls (
                id TEXT PRIMARY KEY, generator_id TEXT UNIQUE, payload TEXT
            );
            CREATE TABLE validations (
                id TEXT PRIMARY KEY, generator_id TEXT UNIQUE, validation_mode TEXT,
                risk_tier TEXT, payload TEXT
            );
            CREATE INDEX idx_generators_coordinates
                ON generators(domain, family, scale, representation, regime);
            CREATE INDEX idx_generators_risk ON generators(risk_tier, risk);
            CREATE INDEX idx_benchmarks_generator ON benchmarks(generator_id);
            CREATE INDEX idx_edges_left ON hyperedges(left_id);
            CREATE INDEX idx_edges_right ON hyperedges(right_id);
            """
        )
        for record in _iter_jsonl(catalog_paths):
            coordinates = record["coordinates"]
            assert isinstance(coordinates, dict)
            connection.execute(
                "INSERT INTO generators VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    record["id"], record["ordinal"], coordinates["domain"],
                    coordinates["family"], coordinates["scale"],
                    coordinates["representation"], coordinates["regime"],
                    record["status"], record["invariant"], record["risk"],
                    record["risk_tier"], int(bool(record["supports_inverse"])),
                    json.dumps(record, separators=(",", ":"), ensure_ascii=False),
                ),
            )
        for record in _iter_jsonl(benchmark_paths):
            connection.execute(
                "INSERT INTO benchmarks VALUES (?,?,?,?)",
                (record["id"], record["generator_id"], record["variant"], json.dumps(record, separators=(",", ":"), ensure_ascii=False)),
            )
        for record in _iter_jsonl(edge_paths):
            connection.execute(
                "INSERT INTO hyperedges VALUES (?,?,?,?)",
                (record["id"], record["left_generator_id"], record["right_generator_id"], json.dumps(record, separators=(",", ":"), ensure_ascii=False)),
            )
        for record in _iter_jsonl(negative_paths):
            connection.execute(
                "INSERT INTO negative_controls VALUES (?,?,?)",
                (record["id"], record["generator_id"], json.dumps(record, separators=(",", ":"), ensure_ascii=False)),
            )
        for record in _iter_jsonl(validation_paths):
            connection.execute(
                "INSERT INTO validations VALUES (?,?,?,?,?)",
                (record["id"], record["generator_id"], record["validation_mode"], record["risk_tier"], json.dumps(record, separators=(",", ":"), ensure_ascii=False)),
            )
        connection.commit()
        connection.execute("VACUUM")
    finally:
        connection.close()


def audit_database(database: Path, config: Mapping[str, object]) -> dict[str, object]:
    expected_generators = expected_generator_count(config)
    expected_benchmarks = expected_generators * len(config["benchmark_variants"])  # type: ignore[arg-type]
    connection = sqlite3.connect(database)
    try:
        counts = {
            name: connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            for name in ("generators", "benchmarks", "hyperedges", "negative_controls", "validations")
        }
        orphan_benchmarks = connection.execute(
            "SELECT COUNT(*) FROM benchmarks b LEFT JOIN generators g ON g.id=b.generator_id WHERE g.id IS NULL"
        ).fetchone()[0]
        orphan_edges = connection.execute(
            "SELECT COUNT(*) FROM hyperedges e LEFT JOIN generators l ON l.id=e.left_id LEFT JOIN generators r ON r.id=e.right_id WHERE l.id IS NULL OR r.id IS NULL"
        ).fetchone()[0]
        wrong_benchmark_coverage = connection.execute(
            "SELECT COUNT(*) FROM (SELECT generator_id,COUNT(*) c FROM benchmarks GROUP BY generator_id HAVING c != ?)",
            (len(config["benchmark_variants"]),),  # type: ignore[arg-type]
        ).fetchone()[0]
        high_risk_not_exhaustive = connection.execute(
            "SELECT COUNT(*) FROM validations WHERE risk_tier='high' AND validation_mode!='exhaustive_required'"
        ).fetchone()[0]
        coordinate_groups = connection.execute(
            "SELECT COUNT(*) FROM (SELECT domain,family,scale,representation,regime FROM generators GROUP BY domain,family,scale,representation,regime)"
        ).fetchone()[0]
        valid = (
            counts["generators"] == expected_generators
            and counts["benchmarks"] == expected_benchmarks
            and counts["hyperedges"] == expected_generators
            and counts["negative_controls"] == expected_generators
            and counts["validations"] == expected_generators
            and orphan_benchmarks == 0
            and orphan_edges == 0
            and wrong_benchmark_coverage == 0
            and high_risk_not_exhaustive == 0
            and coordinate_groups == expected_generators
        )
        return {
            "valid": valid,
            "counts": counts,
            "expected": {
                "generators": expected_generators,
                "benchmarks": expected_benchmarks,
                "hyperedges": expected_generators,
                "negative_controls": expected_generators,
                "validations": expected_generators,
            },
            "orphan_benchmarks": orphan_benchmarks,
            "orphan_hyperedges": orphan_edges,
            "wrong_benchmark_coverage": wrong_benchmark_coverage,
            "high_risk_not_exhaustive": high_risk_not_exhaustive,
            "unique_coordinate_groups": coordinate_groups,
        }
    finally:
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--config", default="configs/omega_generator_r03_ultra.json")
    parser.add_argument("--output", default="generated/omega_generator_discovery_r03_ultra")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config_path = root / args.config
    output = root / args.output
    config = load_config(config_path)
    shard_size = int(config["shard_size"])
    specs = list(generator_records(config))

    generator_count, catalog_paths = write_jsonl_shards(specs, output / "catalogs", "generator_catalog", shard_size)
    benchmark_count, benchmark_paths = write_jsonl_shards(benchmark_records(specs, config), output / "benchmarks", "benchmark_matrix", shard_size)
    edge_count, edge_paths = write_jsonl_shards(hyperedge_records(specs, config), output / "hyperedges", "composition_hyperedges", shard_size)
    negative_count, negative_paths = write_jsonl_shards(negative_control_records(specs, config), output / "negative_controls", "negative_controls", shard_size)
    validation_count, validation_paths = write_jsonl_shards(validation_records(specs, config), output / "validation", "validation_ledger", shard_size)

    database = output / "index" / "omega_generator_r03_ultra.sqlite3"
    build_sqlite(database, catalog_paths, benchmark_paths, edge_paths, negative_paths, validation_paths)
    audit = audit_database(database, config)
    if not audit["valid"]:
        raise SystemExit(json.dumps(audit, indent=2))

    all_jsonl = catalog_paths + benchmark_paths + edge_paths + negative_paths + validation_paths
    risk_distribution = Counter(str(spec["risk_tier"]) for spec in specs)
    manifest = {
        "version": config.get("version", "R0.3-ultra"),
        "profile": "finite_default_profile_without_permanent_total_ceiling",
        "counts": {
            "generators": generator_count,
            "benchmarks": benchmark_count,
            "hyperedges": edge_count,
            "negative_controls": negative_count,
            "validations": validation_count,
            "total_jsonl_records": generator_count + benchmark_count + edge_count + negative_count + validation_count,
        },
        "axes": {
            key: config[key]
            for key in ("domains", "families", "scales", "representations", "regimes")
        },
        "shard_size": shard_size,
        "jsonl_files": len(all_jsonl),
        "combined_fingerprint": fingerprint(all_jsonl),
        "risk_distribution": dict(sorted(risk_distribution.items())),
        "database": str(database.relative_to(root)),
        "audit": audit,
        "oak_boundary": config["oak_boundary"],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "README.md").write_text(
        "# Ω-GENERATOR-DISCOVERY R0.3 Ultra\n\n"
        f"- {generator_count:,} generator candidates\n"
        f"- {benchmark_count:,} synthetic benchmark specifications\n"
        f"- {edge_count:,} ordered-composition hyperedges\n"
        f"- {negative_count:,} negative-control specifications\n"
        f"- {validation_count:,} validation-ledger entries\n"
        f"- {manifest['counts']['total_jsonl_records']:,} total JSONL records\n\n"
        "The atlas is generated research infrastructure, not empirical evidence.\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
