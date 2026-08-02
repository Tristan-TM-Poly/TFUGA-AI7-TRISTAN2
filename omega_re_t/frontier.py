"""Deterministic expansion of RE-16 into the RE-256 perturbation frontier."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps
from pathlib import Path
from typing import Any, Iterable, Mapping

from .re16 import BenchmarkCase, catalog


@dataclass(frozen=True, slots=True)
class Perturbation:
    perturbation_id: str
    title: str
    category: str
    parameters: Mapping[str, Any]
    expected_effect: str
    oak_expectation: str


@dataclass(frozen=True, slots=True)
class FrontierCase:
    frontier_id: str
    seed_case_id: str
    perturbation_id: str
    family: str
    title: str
    objective: str
    seed_digest: str
    truth_model: Mapping[str, Any]
    observations: tuple[Mapping[str, Any], ...]
    candidate_models: tuple[Mapping[str, Any], ...]
    budget: Mapping[str, Any]
    expected: Mapping[str, Any]
    negative_controls: tuple[str, ...]
    failure_modes: tuple[str, ...]
    tags: tuple[str, ...]
    perturbation: Mapping[str, Any]
    authorization: Mapping[str, Any]
    provenance: tuple[str, ...]

    @property
    def digest(self) -> str:
        return sha256(
            dumps(
                asdict(self),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode()
        ).hexdigest()


def perturbations() -> tuple[Perturbation, ...]:
    return (
        Perturbation(
            "P00",
            "Baseline reproduction",
            "baseline",
            {},
            "no semantic change",
            "pass_if_seed_passes",
        ),
        Perturbation(
            "P01",
            "Label permutation",
            "representation",
            {"permute_labels": True},
            "behavior preserved; internal names change",
            "do_not_claim_internal_identity",
        ),
        Perturbation(
            "P02",
            "Observation dropout",
            "data_quality",
            {"drop_fraction": 0.25},
            "identifiability weakens",
            "increase_uncertainty",
        ),
        Perturbation(
            "P03",
            "Observation duplication",
            "data_quality",
            {"duplicate_fraction": 0.5},
            "naive confidence may inflate",
            "deduplicate_or_downweight",
        ),
        Perturbation(
            "P04",
            "Mild output noise",
            "noise",
            {"output_error": 0.01},
            "posterior broadens slightly",
            "calibrate_noise",
        ),
        Perturbation(
            "P05",
            "Moderate output noise",
            "noise",
            {"output_error": 0.10},
            "deterministic assumptions fail",
            "retain_alternatives",
        ),
        Perturbation(
            "P06",
            "Tight experiment budget",
            "budget",
            {"max_experiments": 2},
            "campaign may stop nonidentified",
            "report_debt",
        ),
        Perturbation(
            "P07",
            "Generous experiment budget",
            "budget",
            {"max_experiments": 256},
            "more discriminating tests possible",
            "avoid_waste",
        ),
        Perturbation(
            "P08",
            "Skewed prior",
            "bayes",
            {"top_prior": 0.9},
            "evidence must overcome prior",
            "report_prior_sensitivity",
        ),
        Perturbation(
            "P09",
            "Mixed version traces",
            "versioning",
            {"version_count": 2},
            "single-model fit leaves structure",
            "flag_version_mixture",
        ),
        Perturbation(
            "P10",
            "Missing provenance",
            "governance",
            {"remove_provenance": True},
            "technical fit remains but promotion blocked",
            "oak_fail_closed",
        ),
        Perturbation(
            "P11",
            "Instrument offset",
            "measurement",
            {"offset": 0.05},
            "bias appears in residuals",
            "separate_instrument_effect",
        ),
        Perturbation(
            "P12",
            "Latency jitter",
            "timing",
            {"jitter_std": 0.10},
            "timed separation weakens",
            "propagate_timing_uncertainty",
        ),
        Perturbation(
            "P13",
            "Activated negative control",
            "falsification",
            {"run_negative_control": True},
            "bad model should fail",
            "require_expected_failure",
        ),
        Perturbation(
            "P14",
            "Unseen input region",
            "generalization",
            {"holdout": 0.30},
            "fit cannot prove extrapolation",
            "bound_valid_domain",
        ),
        Perturbation(
            "P15",
            "True model class omitted",
            "unknown_unknown",
            {"omit_truth_family": True},
            "best candidate remains inadequate",
            "raise_unknown_unknown",
        ),
    )


def _mutate_observations(
    seed: BenchmarkCase,
    perturbation: Perturbation,
) -> tuple[Mapping[str, Any], ...]:
    observations = [dict(item) for item in seed.observations]
    parameters = perturbation.parameters
    if parameters.get("drop_fraction") and len(observations) > 1:
        keep = max(
            1,
            int(
                round(
                    len(observations)
                    * (1 - float(parameters["drop_fraction"]))
                )
            ),
        )
        observations = observations[:keep]
    if parameters.get("duplicate_fraction"):
        count = max(
            1,
            int(
                round(
                    len(observations)
                    * float(parameters["duplicate_fraction"])
                )
            ),
        )
        observations.extend(
            dict(item, duplicated=True)
            for item in observations[:count]
        )
    if "output_error" in parameters:
        observations = [
            dict(
                item,
                synthetic_output_error=parameters["output_error"],
            )
            for item in observations
        ]
    if "offset" in parameters:
        observations = [
            dict(
                item,
                synthetic_instrument_offset=parameters["offset"],
            )
            for item in observations
        ]
    if "jitter_std" in parameters:
        observations = [
            dict(
                item,
                synthetic_latency_jitter=parameters["jitter_std"],
            )
            for item in observations
        ]
    if parameters.get("remove_provenance"):
        observations = [
            dict(item, provenance_removed=True)
            for item in observations
        ]
    if parameters.get("version_count"):
        observations = [
            dict(
                item,
                synthetic_version=index
                % int(parameters["version_count"]),
            )
            for index, item in enumerate(observations)
        ]
    return tuple(observations)


def _mutate_candidates(
    seed: BenchmarkCase,
    perturbation: Perturbation,
) -> tuple[Mapping[str, Any], ...]:
    candidates = [dict(item) for item in seed.candidate_models]
    parameters = perturbation.parameters
    if parameters.get("permute_labels"):
        candidates = [
            dict(item, representation_permuted=True)
            for item in reversed(candidates)
        ]
    if parameters.get("top_prior") and candidates:
        remaining = (
            1 - float(parameters["top_prior"])
        ) / max(1, len(candidates) - 1)
        candidates = [
            dict(
                item,
                prior=(
                    parameters["top_prior"]
                    if index == 0
                    else remaining
                ),
            )
            for index, item in enumerate(candidates)
        ]
    if parameters.get("omit_truth_family") and candidates:
        candidates = candidates[1:] or [
            dict(candidates[0], deliberately_misspecified=True)
        ]
    return tuple(candidates)


def expand_case(
    seed: BenchmarkCase,
    perturbation: Perturbation,
) -> FrontierCase:
    budget = dict(seed.budget)
    budget.update(
        {
            key: value
            for key, value in perturbation.parameters.items()
            if key in {"max_experiments"}
        }
    )
    expected = dict(seed.expected)
    expected.update(
        {
            "perturbation_effect": perturbation.expected_effect,
            "oak_expectation": perturbation.oak_expectation,
        }
    )
    if perturbation.parameters.get("holdout"):
        expected["holdout_fraction"] = perturbation.parameters[
            "holdout"
        ]
        expected["generalization_claim_allowed"] = False
    authorization = {
        "mode": "research_sandbox",
        "synthetic": True,
        "external_actions": False,
        "promotion_requires_provenance": True,
        "oak_expectation": perturbation.oak_expectation,
    }
    return FrontierCase(
        frontier_id=(
            f"{seed.case_id}-{perturbation.perturbation_id}"
        ),
        seed_case_id=seed.case_id,
        perturbation_id=perturbation.perturbation_id,
        family=seed.family,
        title=f"{seed.title} / {perturbation.title}",
        objective=seed.objective,
        seed_digest=seed.digest,
        truth_model=dict(seed.truth_model),
        observations=_mutate_observations(seed, perturbation),
        candidate_models=_mutate_candidates(seed, perturbation),
        budget=budget,
        expected=expected,
        negative_controls=seed.negative_controls,
        failure_modes=seed.failure_modes
        + (f"perturbation:{perturbation.perturbation_id}",),
        tags=tuple(
            sorted(
                set(
                    seed.tags
                    + (perturbation.category, "re256")
                )
            )
        ),
        perturbation=asdict(perturbation),
        authorization=authorization,
        provenance=(
            f"seed:{seed.case_id}",
            f"seed-digest:{seed.digest}",
            "generator:omega_re_t.frontier/0.2",
        ),
    )


def frontier() -> tuple[FrontierCase, ...]:
    values = tuple(
        expand_case(seed, perturbation)
        for seed in catalog()
        for perturbation in perturbations()
    )
    assert len(values) == 256
    assert len({item.frontier_id for item in values}) == 256
    return values


def frontier_manifest(
    values: Iterable[FrontierCase] | None = None,
) -> dict[str, Any]:
    cases = tuple(values or frontier())
    digests = [case.digest for case in cases]
    root = sha256("".join(digests).encode()).hexdigest()
    family_counts: dict[str, int] = {}
    perturbation_counts: dict[str, int] = {}
    for case in cases:
        family_counts[case.family] = (
            family_counts.get(case.family, 0) + 1
        )
        perturbation_counts[case.perturbation_id] = (
            perturbation_counts.get(case.perturbation_id, 0) + 1
        )
    return {
        "schema": "omega-re-frontier/0.2",
        "case_count": len(cases),
        "seed_count": len(catalog()),
        "perturbation_count": len(perturbations()),
        "merkle_like_digest": root,
        "family_counts": dict(sorted(family_counts.items())),
        "perturbation_counts": dict(
            sorted(perturbation_counts.items())
        ),
        "claims": {
            "materialized_cases": len(cases),
            "executed_cases": 0,
            "scientifically_verified_cases": 0,
            "logical_space_is_not_execution": True,
        },
    }


def validate_frontier(
    values: Iterable[FrontierCase] | None = None,
) -> tuple[str, ...]:
    cases = tuple(values or frontier())
    issues: list[str] = []
    if len(cases) != 256:
        issues.append("expected_256_cases")
    if len({case.frontier_id for case in cases}) != len(cases):
        issues.append("duplicate_frontier_id")
    for case in cases:
        if not case.authorization.get("synthetic"):
            issues.append(f"{case.frontier_id}:not_synthetic")
        if case.authorization.get("external_actions"):
            issues.append(f"{case.frontier_id}:external_actions")
        if len(case.provenance) < 3:
            issues.append(f"{case.frontier_id}:weak_provenance")
        if (
            case.perturbation_id == "P10"
            and case.expected.get("oak_expectation")
            != "oak_fail_closed"
        ):
            issues.append(
                f"{case.frontier_id}:missing_fail_closed"
            )
        if (
            case.perturbation_id == "P15"
            and case.expected.get("oak_expectation")
            != "raise_unknown_unknown"
        ):
            issues.append(
                f"{case.frontier_id}:missing_unknown_unknown"
            )
    return tuple(issues)


def materialized_payload() -> dict[str, Any]:
    values = frontier()
    return {
        "manifest": frontier_manifest(values),
        "cases": [
            {**asdict(case), "digest": case.digest}
            for case in values
        ],
    }


def materialize(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        dumps(
            materialized_payload(),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-re-frontier")
    parser.add_argument(
        "--output",
        default="benchmarks/omega-re/re256.json",
    )
    parser.add_argument("--verify-only", action="store_true")
    arguments = parser.parse_args(argv)
    issues = validate_frontier()
    if issues:
        print(dumps({"issues": issues}, indent=2))
        return 2
    if not arguments.verify_only:
        target = materialize(arguments.output)
        print(
            dumps(
                {
                    "output": str(target),
                    "manifest": frontier_manifest(),
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
