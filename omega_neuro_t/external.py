from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

from .benchmark import _address_features, _evaluate_model, _full_features, _scalar_features
from .dataset import NeuroObservation, observations_from_jsonl
from .oakbench import OAKBench
from .provenance import DatasetManifest
from .split import group_kfold, split_signature


def manifest_from_json(payload: bytes) -> DatasetManifest:
    try:
        raw = json.loads(payload.decode("utf-8"))
        return DatasetManifest(**raw)
    except Exception as exc:
        raise ValueError(f"invalid dataset manifest: {exc}") from exc


def load_verified_jsonl_bundle(
    data_path: str | Path,
    manifest_path: str | Path,
) -> tuple[list[NeuroObservation], DatasetManifest]:
    data_bytes = Path(data_path).read_bytes()
    manifest = manifest_from_json(Path(manifest_path).read_bytes())
    records = observations_from_jsonl(data_bytes, manifest)
    sample_ids = [record.sample_id for record in records]
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("sample_id values must be unique")
    return records, manifest


def run_p1_records_benchmark(
    records: Sequence[NeuroObservation],
    manifest: DatasetManifest,
    *,
    folds: int = 5,
    split_seed: str = "omega-neuro-p1-external",
    complexity_penalty: float = 0.002,
    uncertainty_penalty: float = 0.05,
) -> Mapping[str, object]:
    """Run the fixed P1 tournament on a verified observation bundle.

    A public/consented label is treated as a provenance claim that still needs
    human/source review. No result from this function auto-promotes a biological
    hypothesis.
    """

    if len({record.group_id for record in records}) < folds:
        raise ValueError("unique group count must be >= folds")
    splits = group_kfold(records, folds=folds, seed=split_seed)
    specs = (
        ("scalar", _scalar_features, 2.0),
        ("address_aware", _address_features, 6.0),
        ("address_plus_context", _full_features, 7.0),
    )
    results = [_evaluate_model(name, builder, complexity, splits) for name, builder, complexity in specs]
    by_name = {result.name: result for result in results}
    oak = OAKBench(complexity_penalty=complexity_penalty, uncertainty_penalty=uncertainty_penalty)
    ranked = oak.rank(result.as_model_score() for result in results)
    baseline = by_name["scalar"].as_model_score()
    candidate = by_name["address_plus_context"].as_model_score()
    claimed_empirical = manifest.access_mode in {"public", "consented"}

    return {
        "benchmark_id": "omega-neuro-p1-external-r04",
        "hypothesis": "P1_DENDRITIC_ADDRESS",
        "manifest": dict(manifest.to_dict()),
        "records": len(records),
        "groups": len({record.group_id for record in records}),
        "folds": folds,
        "split_seed": split_seed,
        "split_signature": split_signature(splits),
        "models": [
            {
                "name": result.name,
                "fold_losses": list(result.fold_losses),
                "predictive_loss": result.predictive_loss,
                "uncertainty": result.uncertainty,
                "complexity": result.complexity,
            }
            for result in results
        ],
        "ranking": [model.name for model in ranked],
        "oak": {
            "baseline_score": oak.score(baseline),
            "candidate_score": oak.score(candidate),
            "candidate_justified": oak.justified(baseline, candidate),
            "predictive_improvement": baseline.predictive_loss - candidate.predictive_loss,
        },
        "source_claim": "claimed_empirical" if claimed_empirical else "synthetic",
        "provenance_review_required": True,
        "automatic_biological_promotion": False,
        "epistemic_notice": (
            "Hash verification proves payload identity only. Source authenticity, experimental quality, "
            "causal interpretation and biological promotion require independent review."
        ),
    }
