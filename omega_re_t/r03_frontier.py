"""Ω-RE-T∞ R0.3 synthetic RE-64 / RE-1024 frontier generator.

All generated objects are research fixtures. Materialization is not execution,
scientific verification, authorization for external action, or evidence about a
real third-party system.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass, asdict
from hashlib import sha256
from itertools import product
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

SCHEMA = "omega-re-frontier/0.3"
FAMILIES = (
    "active_automata",
    "partial_nondeterministic",
    "probabilistic",
    "timed",
    "causal",
    "formats",
    "protocols",
    "hybrid",
    "physical",
    "process",
    "versions",
    "ai_behavior",
    "cleanroom",
    "residuals",
    "constraints",
    "sharded_campaigns",
)
VARIANTS = ("minimal", "ambiguous", "noisy", "boundary")
PERTURBATIONS = (
    "baseline",
    "label_permutation",
    "missing_observation",
    "duplicate_observation",
    "light_noise",
    "moderate_noise",
    "tight_budget",
    "wide_budget",
    "biased_prior",
    "version_mixture",
    "missing_provenance",
    "instrument_offset",
    "timing_jitter",
    "negative_control",
    "unobserved_region",
    "true_class_omitted",
)


def _digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class Seed:
    seed_id: str
    family: str
    variant: str
    title: str
    truth_model: Mapping[str, Any]
    observations: tuple[Mapping[str, Any], ...]
    candidate_models: tuple[Mapping[str, Any], ...]
    expected: Mapping[str, Any]
    controls: tuple[str, ...]
    failure_modes: tuple[str, ...]
    tags: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["digest"] = _digest(data)
        return data


def _family_truth(family: str, variant: str, index: int) -> dict[str, Any]:
    scale = index + 1
    mapping: dict[str, dict[str, Any]] = {
        "active_automata": {"type": "mealy", "states": 2 + index % 4, "alphabet": ["a", "b"], "distinguishing_depth": 1 + index % 3},
        "partial_nondeterministic": {"type": "nd_mealy", "states": 3 + index % 3, "nondeterministic_branches": 1 + index % 2, "partial": variant in {"ambiguous", "boundary"}},
        "probabilistic": {"type": "probabilistic_mealy", "states": 2 + index % 3, "entropy_bits": round(0.25 * scale, 3)},
        "timed": {"type": "timed_mealy", "states": 2 + index % 3, "latency_modes_ms": [10 * scale, 20 * scale]},
        "causal": {"type": "causal_dag", "variables": ["x", "m", "y"], "edges": [["x", "m"], ["m", "y"]], "effect": round(0.5 + 0.1 * index, 3)},
        "formats": {"type": "delimited_format", "delimiter": [",", "|", ";", "\t"][index % 4], "fields": 3 + index % 3},
        "protocols": {"type": "protocol_fsm", "states": 3 + index % 4, "supports_retry": variant != "minimal", "timeout_ms": 100 * scale},
        "hybrid": {"type": "piecewise_affine", "modes": 2 + index % 3, "state_dimension": 1 + index % 2, "switch_threshold": float(scale)},
        "physical": {"type": "low_order_physical", "model": ["damped_oscillator", "thermal_rc", "rlc", "first_order_lag"][index % 4], "parameter_scale": scale},
        "process": {"type": "process_graph", "activities": 4 + index, "contains_loop": variant != "minimal", "exceptions": index},
        "versions": {"type": "version_lineage", "versions": 4 + index, "forks": index % 2, "regression_at": 2 + index},
        "ai_behavior": {"type": "behavioral_cartography", "task_families": 3 + index, "context_sensitive": variant != "minimal", "calibration_error": round(0.02 * scale, 3)},
        "cleanroom": {"type": "cleanroom_pipeline", "roles": ["observer", "specifier", "implementer", "auditor"], "separation_required": True},
        "residuals": {"type": "residual_pattern", "pattern": ["bias", "drift", "periodic", "model_class_failure"][index % 4], "amplitude": round(0.1 * scale, 3)},
        "constraints": {"type": "constraint_system", "variables": 2 + index, "constraints": 3 + index, "negative_space": variant == "boundary"},
        "sharded_campaigns": {"type": "campaign", "logical_items": 2 ** (10 + index), "shard_size": 64 * scale, "forced_resume": variant != "minimal"},
    }
    return mapping[family]


def _observations(family: str, variant: str, index: int) -> tuple[Mapping[str, Any], ...]:
    count = 4 + index * 2
    records: list[Mapping[str, Any]] = []
    for observation_index in range(count):
        records.append(
            {
                "observation_id": f"obs-{observation_index:03d}",
                "input": f"u{observation_index % (2 + index % 3)}",
                "output": f"y{(observation_index + index) % (2 + index % 4)}",
                "time": observation_index,
                "uncertainty": round(0.01 * (1 + (observation_index + index) % 5), 3),
                "provenance": ["synthetic-generator", family, variant],
            }
        )
    return tuple(records)


def _candidates(family: str, index: int) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        {
            "candidate_id": f"{family}-m{candidate_index}",
            "family": family,
            "complexity": 1 + candidate_index + index,
            "prior": round(1.0 / (4 + index), 6),
            "status": "hypothesis",
        }
        for candidate_index in range(4 + index)
    )


def build_seeds() -> tuple[Seed, ...]:
    seeds: list[Seed] = []
    for family_index, family in enumerate(FAMILIES):
        for variant_index, variant in enumerate(VARIANTS):
            seed_id = f"RE64-{family_index:02d}-{variant_index:02d}"
            expected_level = "I2" if variant == "minimal" else "I1" if variant == "ambiguous" else "I3" if variant == "noisy" else "I0-I2"
            seeds.append(
                Seed(
                    seed_id=seed_id,
                    family=family,
                    variant=variant,
                    title=f"{family.replace('_', ' ').title()} / {variant}",
                    truth_model=_family_truth(family, variant, variant_index),
                    observations=_observations(family, variant, variant_index),
                    candidate_models=_candidates(family, variant_index),
                    expected={
                        "identifiability_level": expected_level,
                        "active_experiment_required": variant != "minimal",
                        "unknown_unknown_expected": family == "residuals" and variant == "boundary",
                        "cleanroom_required": family in {"formats", "protocols", "cleanroom"},
                        "oak_status_ceiling": "RECONSTRUCTED",
                    },
                    controls=("negative_control", "holdout", "provenance_check", "authorization_check"),
                    failure_modes=(
                        "behavioral_equivalence_confused_with_internal_identity",
                        "overfitting_to_observed_traces",
                        "missing_state_or_context",
                        "uncalibrated_uncertainty",
                    ),
                    tags=(family, variant, "synthetic", "oak-safe", "r0.3"),
                )
            )
    assert len(seeds) == 64
    return tuple(seeds)


def apply_perturbation(seed: Seed, perturbation: str, perturbation_index: int) -> dict[str, Any]:
    case = seed.to_dict()
    case_id = f"RE1024-{seed.seed_id}-{perturbation_index:02d}"
    case["case_id"] = case_id
    case["perturbation"] = {"id": f"P{perturbation_index:02d}", "name": perturbation}
    case["authorization"] = {
        "mode": "research_sandbox",
        "synthetic": True,
        "external_actions": False,
        "destructive_actions": False,
        "promotion_requires_independent_validation": True,
    }
    case["budget"] = {
        "max_experiments": 64,
        "max_sequence_length": 8,
        "cost": 100.0,
        "time_units": 1000,
    }
    if perturbation == "missing_observation" and case["observations"]:
        case["observations"] = case["observations"][:-1]
    elif perturbation == "duplicate_observation" and case["observations"]:
        case["observations"] = tuple(case["observations"]) + (case["observations"][0],)
    elif perturbation == "light_noise":
        case["perturbation"]["noise_probability"] = 0.01
    elif perturbation == "moderate_noise":
        case["perturbation"]["noise_probability"] = 0.10
    elif perturbation == "tight_budget":
        case["budget"]["max_experiments"] = 4
        case["budget"]["cost"] = 5.0
    elif perturbation == "wide_budget":
        case["budget"]["max_experiments"] = 512
        case["budget"]["cost"] = 1000.0
    elif perturbation == "biased_prior":
        if case["candidate_models"]:
            case["candidate_models"][0]["prior"] = 0.90
    elif perturbation == "version_mixture":
        case["perturbation"]["mixed_versions"] = ["v1", "v2"]
    elif perturbation == "missing_provenance":
        case["observations"] = [dict(item, provenance=[]) for item in case["observations"]]
        case["expected"]["oak_status_ceiling"] = "UNKNOWN"
    elif perturbation == "instrument_offset":
        case["perturbation"]["offset"] = round(0.1 * (perturbation_index + 1), 3)
    elif perturbation == "timing_jitter":
        case["perturbation"]["jitter_fraction"] = 0.20
    elif perturbation == "negative_control":
        case["perturbation"]["expected_effect"] = 0.0
    elif perturbation == "unobserved_region":
        case["perturbation"]["holdout_fraction"] = 0.50
    elif perturbation == "true_class_omitted":
        case["candidate_models"] = [item for item in case["candidate_models"] if item["candidate_id"] != f"{seed.family}-m0"]
        case["expected"]["unknown_unknown_expected"] = True
    elif perturbation == "label_permutation":
        case["perturbation"]["permutation"] = "deterministic-renaming"
    case["oak_claims"] = {
        "logical_case": True,
        "materialized": True,
        "executed": False,
        "scientifically_verified": False,
        "external_system_claim": False,
    }
    case["digest"] = _digest({key: value for key, value in case.items() if key != "digest"})
    return case


def iter_cases() -> Iterator[dict[str, Any]]:
    for seed, (perturbation_index, perturbation) in product(build_seeds(), enumerate(PERTURBATIONS)):
        yield apply_perturbation(seed, perturbation, perturbation_index)


def manifest(cases: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    materialized = list(cases) if cases is not None else list(iter_cases())
    family_counts = Counter(item["family"] for item in materialized)
    perturbation_counts = Counter(item["perturbation"]["id"] for item in materialized)
    digests = [item["digest"] for item in materialized]
    return {
        "schema": SCHEMA,
        "seed_count": 64,
        "perturbation_count": 16,
        "case_count": len(materialized),
        "family_counts": dict(sorted(family_counts.items())),
        "perturbation_counts": dict(sorted(perturbation_counts.items())),
        "merkle_like_digest": _digest(digests),
        "claims": {
            "logical_cases": 1024,
            "materialized_cases": len(materialized),
            "executed_cases": 0,
            "software_tested_cases": 0,
            "scientifically_verified_cases": 0,
            "logical_space_is_not_execution": True,
            "materialization_is_not_validation": True,
        },
        "authority": {
            "external_actions": False,
            "destructive_actions": False,
            "automatic_merge": False,
            "scientific_promotion": False,
        },
    }


def validate_case(case: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    for key in ("case_id", "seed_id", "family", "variant", "truth_model", "observations", "candidate_models", "authorization", "oak_claims", "digest"):
        if key not in case:
            errors.append(f"missing:{key}")
    if case.get("family") not in FAMILIES:
        errors.append("unknown_family")
    if case.get("variant") not in VARIANTS:
        errors.append("unknown_variant")
    auth = case.get("authorization", {})
    if not auth.get("synthetic") or auth.get("external_actions"):
        errors.append("authorization_boundary_violation")
    claims = case.get("oak_claims", {})
    if claims.get("executed") or claims.get("scientifically_verified"):
        errors.append("claim_boundary_violation")
    expected_digest = _digest({key: value for key, value in case.items() if key != "digest"})
    if case.get("digest") != expected_digest:
        errors.append("digest_mismatch")
    return tuple(errors)


def validate_frontier(cases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    errors: dict[str, tuple[str, ...]] = {}
    ids: set[str] = set()
    for case in cases:
        case_errors = list(validate_case(case))
        if case["case_id"] in ids:
            case_errors.append("duplicate_case_id")
        ids.add(case["case_id"])
        if case_errors:
            errors[case["case_id"]] = tuple(case_errors)
    return {"valid": not errors and len(cases) == 1024, "case_count": len(cases), "errors": errors}


def materialize(path: str | Path) -> dict[str, Any]:
    cases = list(iter_cases())
    validation = validate_frontier(cases)
    if not validation["valid"]:
        raise ValueError(f"invalid frontier: {validation}")
    payload = {"cases": cases, "manifest": manifest(cases)}
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload["manifest"]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="benchmarks/omega-re/re1024.json")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args(argv)
    cases = list(iter_cases())
    validation = validate_frontier(cases)
    if not validation["valid"]:
        print(json.dumps(validation, indent=2, sort_keys=True))
        return 1
    if args.verify_only:
        print(json.dumps(manifest(cases), indent=2, sort_keys=True))
        return 0
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {"cases": cases, "manifest": manifest(cases)}
    destination.write_text(
        json.dumps(payload, indent=None if args.compact else 2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload["manifest"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
