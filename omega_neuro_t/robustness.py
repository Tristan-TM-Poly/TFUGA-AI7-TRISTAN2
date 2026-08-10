from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from statistics import mean, pstdev
from typing import Mapping, Sequence

from .benchmark import _evaluate_model, _full_features, run_p1_benchmark
from .dataset import NeuroObservation, synthetic_p1_dataset
from .split import group_kfold


def permute_addresses(
    records: Sequence[NeuroObservation],
    *,
    seed: str = "omega-neuro-negative-control",
) -> list[NeuroObservation]:
    """Distribution-preserving deterministic permutation of address labels."""

    if len(records) < 2:
        raise ValueError("at least two observations are required")
    ordered = sorted(
        records,
        key=lambda record: sha256(f"{seed}|{record.sample_id}".encode("utf-8")).hexdigest(),
    )
    values = [record.address for record in ordered]
    shift = max(1, len(values) // 3)
    shifted = values[shift:] + values[:shift]
    reassignment = {record.sample_id: address for record, address in zip(ordered, shifted)}
    return [replace(record, address=reassignment[record.sample_id]) for record in records]


def p1_permutation_negative_control(
    *,
    groups: int = 24,
    trials_per_group: int = 8,
    noise_scale: float = 0.03,
    folds: int = 5,
    split_seed: str = "omega-neuro-p1",
    permutation_seed: str = "omega-neuro-negative-control",
) -> Mapping[str, float | str | bool]:
    """Break address/target correspondence while preserving address counts."""

    original = synthetic_p1_dataset(
        groups=groups,
        trials_per_group=trials_per_group,
        noise_scale=noise_scale,
    )
    permuted = permute_addresses(original, seed=permutation_seed)
    original_splits = group_kfold(original, folds=folds, seed=split_seed)
    permuted_splits = group_kfold(permuted, folds=folds, seed=split_seed)
    original_result = _evaluate_model("address_plus_context", _full_features, 7.0, original_splits)
    permuted_result = _evaluate_model("address_plus_context_permuted", _full_features, 7.0, permuted_splits)
    ratio = permuted_result.predictive_loss / max(original_result.predictive_loss, 1e-15)
    return {
        "control": "address_label_permutation",
        "original_predictive_loss": original_result.predictive_loss,
        "permuted_predictive_loss": permuted_result.predictive_loss,
        "loss_ratio": ratio,
        "control_degrades_prediction": permuted_result.predictive_loss > original_result.predictive_loss,
    }


def p1_split_stability(
    seeds: Sequence[str] = ("split-a", "split-b", "split-c", "split-d", "split-e"),
    *,
    groups: int = 24,
    trials_per_group: int = 8,
    noise_scale: float = 0.03,
) -> Mapping[str, object]:
    """Measure whether the OAK decision survives several group partitions."""

    if len(seeds) < 2:
        raise ValueError("at least two split seeds are required")
    improvements = []
    decisions = []
    signatures = []
    for seed in seeds:
        report = run_p1_benchmark(
            groups=groups,
            trials_per_group=trials_per_group,
            noise_scale=noise_scale,
            split_seed=seed,
        )
        improvements.append(float(report["oak"]["predictive_improvement"]))
        decisions.append(bool(report["oak"]["candidate_justified"]))
        signatures.append(str(report["split_signature"]))
    return {
        "seeds": list(seeds),
        "distinct_split_signatures": len(set(signatures)),
        "justified_fraction": sum(decisions) / len(decisions),
        "predictive_improvement_mean": mean(improvements),
        "predictive_improvement_stdev": pstdev(improvements),
        "predictive_improvement_min": min(improvements),
        "predictive_improvement_max": max(improvements),
        "epistemic_notice": "Split stability is robustness evidence for the benchmark, not biological validation.",
    }
