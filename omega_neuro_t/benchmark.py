from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import pstdev
from typing import Callable, Dict, Iterable, List, Mapping, Sequence, Tuple

from .dataset import NeuroObservation, synthetic_p1_bundle
from .oakbench import ModelScore, OAKBench
from .regression import fit_ridge, mean_squared_error
from .split import group_kfold, split_signature


FeatureBuilder = Callable[[NeuroObservation], Sequence[float]]


def _scalar_features(record: NeuroObservation) -> Sequence[float]:
    return (record.signal,)


def _address_features(record: NeuroObservation) -> Sequence[float]:
    distal = 1.0 if record.address == "distal" else 0.0
    proximal = 1.0 if record.address == "proximal" else 0.0
    return (
        record.signal,
        distal,
        proximal,
        record.signal * distal,
        record.signal * proximal,
    )


def _full_features(record: NeuroObservation) -> Sequence[float]:
    return (*_address_features(record), record.context)


def _full_no_address_interactions(record: NeuroObservation) -> Sequence[float]:
    distal = 1.0 if record.address == "distal" else 0.0
    proximal = 1.0 if record.address == "proximal" else 0.0
    return (record.signal, distal, proximal, record.context)


def _full_no_context(record: NeuroObservation) -> Sequence[float]:
    return _address_features(record)


@dataclass(frozen=True)
class BenchmarkModelResult:
    name: str
    fold_losses: Tuple[float, ...]
    predictive_loss: float
    uncertainty: float
    complexity: float

    def as_model_score(self) -> ModelScore:
        return ModelScore(
            self.name,
            predictive_loss=self.predictive_loss,
            complexity=self.complexity,
            uncertainty=self.uncertainty,
        )


@dataclass(frozen=True)
class AblationResult:
    name: str
    predictive_loss: float
    loss_delta_vs_full: float


def _evaluate_model(
    name: str,
    builder: FeatureBuilder,
    complexity: float,
    splits: Sequence[Tuple[Sequence[NeuroObservation], Sequence[NeuroObservation]]],
) -> BenchmarkModelResult:
    fold_losses: List[float] = []
    for train, test in splits:
        train_x = [builder(record) for record in train]
        train_y = [record.target for record in train]
        test_x = [builder(record) for record in test]
        test_y = [record.target for record in test]
        model = fit_ridge(train_x, train_y)
        fold_losses.append(mean_squared_error(model, test_x, test_y))
    predictive_loss = sum(fold_losses) / len(fold_losses)
    return BenchmarkModelResult(
        name=name,
        fold_losses=tuple(fold_losses),
        predictive_loss=predictive_loss,
        uncertainty=pstdev(fold_losses),
        complexity=complexity,
    )


def run_p1_benchmark(
    *,
    folds: int = 5,
    split_seed: str = "omega-neuro-p1",
    groups: int = 24,
    trials_per_group: int = 8,
    noise_scale: float = 0.03,
    complexity_penalty: float = 0.002,
    uncertainty_penalty: float = 0.05,
) -> Mapping[str, object]:
    """Run a deterministic P1 baseline tournament on a planted synthetic effect.

    This validates the benchmark machinery only. It is deliberately incapable
    of promoting P1 as a biological result because the source is synthetic.
    """

    records, payload, manifest = synthetic_p1_bundle(
        groups=groups,
        trials_per_group=trials_per_group,
        noise_scale=noise_scale,
    )
    splits = group_kfold(records, folds=folds, seed=split_seed)

    specs = (
        ("scalar", _scalar_features, 2.0),
        ("address_aware", _address_features, 6.0),
        ("address_plus_context", _full_features, 7.0),
    )
    results = [_evaluate_model(name, builder, complexity, splits) for name, builder, complexity in specs]
    by_name = {result.name: result for result in results}
    full = by_name["address_plus_context"]

    ablation_specs = (
        ("remove_address_interactions", _full_no_address_interactions, 5.0),
        ("remove_context", _full_no_context, 6.0),
    )
    ablations: List[AblationResult] = []
    for name, builder, complexity in ablation_specs:
        result = _evaluate_model(name, builder, complexity, splits)
        ablations.append(
            AblationResult(
                name=name,
                predictive_loss=result.predictive_loss,
                loss_delta_vs_full=result.predictive_loss - full.predictive_loss,
            )
        )

    oak = OAKBench(
        complexity_penalty=complexity_penalty,
        uncertainty_penalty=uncertainty_penalty,
    )
    ranked = oak.rank(result.as_model_score() for result in results)
    baseline = by_name["scalar"].as_model_score()
    candidate = full.as_model_score()

    return {
        "benchmark_id": "omega-neuro-p1-synthetic-r03",
        "hypothesis": "P1_DENDRITIC_ADDRESS",
        "source_class": "synthetic_test_fixture",
        "biological_promotion_allowed": False,
        "manifest": dict(manifest.to_dict()),
        "payload_bytes": len(payload),
        "records": len(records),
        "groups": len({record.group_id for record in records}),
        "folds": folds,
        "split_seed": split_seed,
        "split_signature": split_signature(splits),
        "models": [asdict(result) for result in results],
        "ranking": [model.name for model in ranked],
        "ablations": [asdict(result) for result in ablations],
        "oak": {
            "baseline": baseline.name,
            "candidate": candidate.name,
            "baseline_score": oak.score(baseline),
            "candidate_score": oak.score(candidate),
            "candidate_justified": oak.justified(baseline, candidate),
            "predictive_improvement": baseline.predictive_loss - candidate.predictive_loss,
            "improvement_required": oak.improvement_required(baseline, candidate),
        },
        "epistemic_notice": (
            "Synthetic planted-effect benchmark: validates software, splitting, scoring and ablation logic only; "
            "it is not neuroscience evidence and cannot promote P1."
        ),
    }
