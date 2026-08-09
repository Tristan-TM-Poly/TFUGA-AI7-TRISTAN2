from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite, sin
from statistics import pstdev
from typing import Callable, List, Mapping, Sequence, Tuple

from .oakbench import ModelScore, OAKBench
from .provenance import DatasetManifest, build_manifest
from .regression import fit_ridge, mean_squared_error
from .split import group_kfold, split_signature


@dataclass(frozen=True)
class SynapseEvidenceObservation:
    sample_id: str
    group_id: str
    release_probability: float
    quantal_scale: float
    delay_ms: float
    short_term_gain: float
    long_term_gain: float
    context: float
    target: float

    def __post_init__(self) -> None:
        if not self.sample_id or not self.group_id:
            raise ValueError("sample_id and group_id must be non-empty")
        for name in (
            "release_probability",
            "quantal_scale",
            "delay_ms",
            "short_term_gain",
            "long_term_gain",
            "context",
            "target",
        ):
            if not isfinite(getattr(self, name)):
                raise ValueError(f"{name} must be finite")
        if not 0.0 <= self.release_probability <= 1.0:
            raise ValueError("release_probability must be in [0, 1]")


@dataclass(frozen=True)
class CircuitEvidenceObservation:
    sample_id: str
    group_id: str
    pairwise_strength: float
    recurrence: float
    motif_order3: float
    motif_order4: float
    context: float
    target: float

    def __post_init__(self) -> None:
        if not self.sample_id or not self.group_id:
            raise ValueError("sample_id and group_id must be non-empty")
        for name in (
            "pairwise_strength",
            "recurrence",
            "motif_order3",
            "motif_order4",
            "context",
            "target",
        ):
            if not isfinite(getattr(self, name)):
                raise ValueError(f"{name} must be finite")


@dataclass(frozen=True)
class CampaignModelResult:
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


FeatureBuilder = Callable[[object], Sequence[float]]


def _jsonl(records: Sequence[object]) -> bytes:
    lines = [json.dumps(asdict(record), sort_keys=True, separators=(",", ":")) for record in records]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _evaluate(
    records: Sequence[object],
    *,
    name: str,
    builder: FeatureBuilder,
    complexity: float,
    folds: int,
    split_seed: str,
) -> CampaignModelResult:
    splits = group_kfold(records, folds=folds, seed=split_seed)
    losses: List[float] = []
    for train, test in splits:
        train_x = [builder(record) for record in train]
        train_y = [record.target for record in train]
        test_x = [builder(record) for record in test]
        test_y = [record.target for record in test]
        model = fit_ridge(train_x, train_y)
        losses.append(mean_squared_error(model, test_x, test_y))
    return CampaignModelResult(
        name=name,
        fold_losses=tuple(losses),
        predictive_loss=sum(losses) / len(losses),
        uncertainty=pstdev(losses),
        complexity=complexity,
    )


def synthetic_p2_bundle(
    *, groups: int = 24, trials_per_group: int = 8, noise_scale: float = 0.03
) -> Tuple[List[SynapseEvidenceObservation], bytes, DatasetManifest]:
    """Deterministic planted-effect fixture for P2 software validation only."""

    if groups < 4 or trials_per_group < 2:
        raise ValueError("P2 fixture needs >=4 groups and >=2 trials/group")
    if noise_scale < 0 or not isfinite(noise_scale):
        raise ValueError("noise_scale must be finite and >= 0")

    records: List[SynapseEvidenceObservation] = []
    for group_index in range(groups):
        group_id = f"synapse-{group_index:03d}"
        group_shift = ((group_index % 5) - 2) * 0.02
        for trial in range(trials_per_group):
            release_probability = 0.25 + 0.06 * ((group_index + trial) % 8)
            quantal_scale = 0.70 + 0.08 * (trial % 6) + 0.02 * (group_index % 3)
            delay_ms = 0.60 + 0.20 * ((2 * group_index + trial) % 7)
            short_term_gain = 0.75 + 0.06 * ((group_index + 2 * trial) % 6)
            long_term_gain = 0.80 + 0.05 * ((3 * group_index + trial) % 7)
            context = 0.70 + 0.07 * ((group_index + 3 * trial) % 7)
            scalar_weight = release_probability * quantal_scale
            noise = noise_scale * sin((group_index + 2) * (trial + 1) * 1.071)
            target = (
                0.15
                + 0.95 * scalar_weight
                - 0.10 * delay_ms
                + 0.55 * short_term_gain
                + 0.70 * long_term_gain
                + 0.45 * context
                + 0.85 * scalar_weight * context
                + group_shift
                + noise
            )
            records.append(
                SynapseEvidenceObservation(
                    sample_id=f"{group_id}:trial-{trial:02d}",
                    group_id=group_id,
                    release_probability=release_probability,
                    quantal_scale=quantal_scale,
                    delay_ms=delay_ms,
                    short_term_gain=short_term_gain,
                    long_term_gain=long_term_gain,
                    context=context,
                    target=target,
                )
            )
    payload = _jsonl(records)
    manifest = build_manifest(
        payload,
        dataset_id="omega-neuro-p2-synapse-state-synthetic",
        version="1.0.0",
        source_uri="synthetic://omega-neuro/p2/synapse-state-v1",
        license_id="synthetic-test-fixture",
        access_mode="synthetic",
        citation="Generated deterministically by omega_neuro_t.hypothesis_campaign.synthetic_p2_bundle",
    )
    return records, payload, manifest


def _p2_scalar(record: object) -> Sequence[float]:
    r = record
    return (r.release_probability * r.quantal_scale,)


def _p2_state(record: object) -> Sequence[float]:
    r = record
    scalar = r.release_probability * r.quantal_scale
    return (
        scalar,
        r.delay_ms,
        r.short_term_gain,
        r.long_term_gain,
        r.context,
        scalar * r.context,
    )


def _p2_no_context(record: object) -> Sequence[float]:
    r = record
    return (
        r.release_probability * r.quantal_scale,
        r.delay_ms,
        r.short_term_gain,
        r.long_term_gain,
    )


def _p2_no_plasticity(record: object) -> Sequence[float]:
    r = record
    scalar = r.release_probability * r.quantal_scale
    return (scalar, r.delay_ms, r.context, scalar * r.context)


def _permute_p2_context(
    records: Sequence[SynapseEvidenceObservation], *, seed: str
) -> List[SynapseEvidenceObservation]:
    ordered = sorted(
        records,
        key=lambda record: sha256(f"{seed}|{record.sample_id}".encode("utf-8")).hexdigest(),
    )
    contexts = [record.context for record in ordered]
    offset = max(1, len(contexts) // 7)
    rotated = contexts[offset:] + contexts[:offset]
    replacement = {record.sample_id: value for record, value in zip(ordered, rotated)}
    return [
        SynapseEvidenceObservation(
            sample_id=record.sample_id,
            group_id=record.group_id,
            release_probability=record.release_probability,
            quantal_scale=record.quantal_scale,
            delay_ms=record.delay_ms,
            short_term_gain=record.short_term_gain,
            long_term_gain=record.long_term_gain,
            context=replacement[record.sample_id],
            target=record.target,
        )
        for record in records
    ]


def run_p2_benchmark(
    *,
    folds: int = 5,
    split_seed: str = "omega-neuro-p2",
    groups: int = 24,
    trials_per_group: int = 8,
    noise_scale: float = 0.03,
    complexity_penalty: float = 0.002,
    uncertainty_penalty: float = 0.05,
) -> Mapping[str, object]:
    records, payload, manifest = synthetic_p2_bundle(
        groups=groups,
        trials_per_group=trials_per_group,
        noise_scale=noise_scale,
    )
    scalar = _evaluate(
        records,
        name="scalar_synapse",
        builder=_p2_scalar,
        complexity=2.0,
        folds=folds,
        split_seed=split_seed,
    )
    candidate = _evaluate(
        records,
        name="synapse_state_tensor",
        builder=_p2_state,
        complexity=7.0,
        folds=folds,
        split_seed=split_seed,
    )
    no_context = _evaluate(
        records,
        name="remove_context",
        builder=_p2_no_context,
        complexity=5.0,
        folds=folds,
        split_seed=split_seed,
    )
    no_plasticity = _evaluate(
        records,
        name="collapse_plasticity",
        builder=_p2_no_plasticity,
        complexity=5.0,
        folds=folds,
        split_seed=split_seed,
    )
    permuted = _permute_p2_context(records, seed=f"{split_seed}-negative-control")
    negative = _evaluate(
        permuted,
        name="permute_context",
        builder=_p2_state,
        complexity=7.0,
        folds=folds,
        split_seed=split_seed,
    )
    oak = OAKBench(
        complexity_penalty=complexity_penalty,
        uncertainty_penalty=uncertainty_penalty,
    )
    baseline_score = scalar.as_model_score()
    candidate_score = candidate.as_model_score()
    splits = group_kfold(records, folds=folds, seed=split_seed)
    return {
        "benchmark_id": "omega-neuro-p2-synthetic-r05",
        "hypothesis": "P2_SYNAPTIC_STATE_TENSOR",
        "source_class": "synthetic_test_fixture",
        "biological_promotion_allowed": False,
        "manifest": dict(manifest.to_dict()),
        "payload_bytes": len(payload),
        "records": len(records),
        "groups": len({record.group_id for record in records}),
        "folds": folds,
        "split_seed": split_seed,
        "split_signature": split_signature(splits),
        "models": [asdict(scalar), asdict(candidate)],
        "ablations": [
            {
                "name": no_context.name,
                "predictive_loss": no_context.predictive_loss,
                "loss_delta_vs_full": no_context.predictive_loss - candidate.predictive_loss,
            },
            {
                "name": no_plasticity.name,
                "predictive_loss": no_plasticity.predictive_loss,
                "loss_delta_vs_full": no_plasticity.predictive_loss - candidate.predictive_loss,
            },
        ],
        "negative_control": {
            "name": negative.name,
            "predictive_loss": negative.predictive_loss,
            "degradation_vs_candidate": negative.predictive_loss - candidate.predictive_loss,
        },
        "oak": {
            "baseline": baseline_score.name,
            "candidate": candidate_score.name,
            "baseline_score": oak.score(baseline_score),
            "candidate_score": oak.score(candidate_score),
            "candidate_justified": oak.justified(baseline_score, candidate_score),
            "predictive_improvement": scalar.predictive_loss - candidate.predictive_loss,
            "improvement_required": oak.improvement_required(baseline_score, candidate_score),
        },
        "epistemic_notice": (
            "Synthetic P2 planted-effect benchmark: validates the state-tensor evidence machinery only; "
            "it is not evidence that the chosen variables are sufficient or causal in biological synapses."
        ),
    }


def synthetic_p3_bundle(
    *, groups: int = 24, trials_per_group: int = 8, noise_scale: float = 0.03
) -> Tuple[List[CircuitEvidenceObservation], bytes, DatasetManifest]:
    """Deterministic planted-effect fixture for higher-order wiring tests only."""

    if groups < 4 or trials_per_group < 2:
        raise ValueError("P3 fixture needs >=4 groups and >=2 trials/group")
    if noise_scale < 0 or not isfinite(noise_scale):
        raise ValueError("noise_scale must be finite and >= 0")

    records: List[CircuitEvidenceObservation] = []
    for group_index in range(groups):
        group_id = f"circuit-{group_index:03d}"
        group_shift = ((group_index % 7) - 3) * 0.015
        for trial in range(trials_per_group):
            pairwise_strength = 0.30 + 0.05 * ((group_index + trial) % 9)
            recurrence = 0.20 + 0.07 * ((2 * group_index + trial) % 8)
            motif_order3 = 0.10 + 0.09 * ((group_index + 2 * trial) % 7)
            motif_order4 = 0.05 + 0.08 * ((3 * group_index + trial) % 6)
            context = 0.65 + 0.06 * ((group_index + 4 * trial) % 7)
            noise = noise_scale * sin((group_index + 1) * (trial + 3) * 1.137)
            target = (
                0.10
                + 0.75 * pairwise_strength
                + 0.30 * recurrence
                + 1.05 * motif_order3
                + 0.85 * motif_order4
                + 0.70 * motif_order3 * context
                + 0.45 * motif_order4 * context
                + group_shift
                + noise
            )
            records.append(
                CircuitEvidenceObservation(
                    sample_id=f"{group_id}:trial-{trial:02d}",
                    group_id=group_id,
                    pairwise_strength=pairwise_strength,
                    recurrence=recurrence,
                    motif_order3=motif_order3,
                    motif_order4=motif_order4,
                    context=context,
                    target=target,
                )
            )
    payload = _jsonl(records)
    manifest = build_manifest(
        payload,
        dataset_id="omega-neuro-p3-higher-order-synthetic",
        version="1.0.0",
        source_uri="synthetic://omega-neuro/p3/higher-order-v1",
        license_id="synthetic-test-fixture",
        access_mode="synthetic",
        citation="Generated deterministically by omega_neuro_t.hypothesis_campaign.synthetic_p3_bundle",
    )
    return records, payload, manifest


def _p3_pairwise(record: object) -> Sequence[float]:
    r = record
    return (r.pairwise_strength, r.recurrence)


def _p3_higher_order(record: object) -> Sequence[float]:
    r = record
    return (
        r.pairwise_strength,
        r.recurrence,
        r.motif_order3,
        r.motif_order4,
        r.context,
        r.motif_order3 * r.context,
        r.motif_order4 * r.context,
    )


def _p3_no_context(record: object) -> Sequence[float]:
    r = record
    return (r.pairwise_strength, r.recurrence, r.motif_order3, r.motif_order4)


def _permute_p3_motifs(
    records: Sequence[CircuitEvidenceObservation], *, seed: str
) -> List[CircuitEvidenceObservation]:
    ordered = sorted(
        records,
        key=lambda record: sha256(f"{seed}|{record.sample_id}".encode("utf-8")).hexdigest(),
    )
    motifs = [(record.motif_order3, record.motif_order4) for record in ordered]
    offset = max(1, len(motifs) // 9)
    rotated = motifs[offset:] + motifs[:offset]
    replacement = {record.sample_id: value for record, value in zip(ordered, rotated)}
    return [
        CircuitEvidenceObservation(
            sample_id=record.sample_id,
            group_id=record.group_id,
            pairwise_strength=record.pairwise_strength,
            recurrence=record.recurrence,
            motif_order3=replacement[record.sample_id][0],
            motif_order4=replacement[record.sample_id][1],
            context=record.context,
            target=record.target,
        )
        for record in records
    ]


def run_p3_benchmark(
    *,
    folds: int = 5,
    split_seed: str = "omega-neuro-p3",
    groups: int = 24,
    trials_per_group: int = 8,
    noise_scale: float = 0.03,
    complexity_penalty: float = 0.002,
    uncertainty_penalty: float = 0.05,
) -> Mapping[str, object]:
    records, payload, manifest = synthetic_p3_bundle(
        groups=groups,
        trials_per_group=trials_per_group,
        noise_scale=noise_scale,
    )
    pairwise = _evaluate(
        records,
        name="pairwise_graph",
        builder=_p3_pairwise,
        complexity=3.0,
        folds=folds,
        split_seed=split_seed,
    )
    candidate = _evaluate(
        records,
        name="higher_order_hypergraph",
        builder=_p3_higher_order,
        complexity=8.0,
        folds=folds,
        split_seed=split_seed,
    )
    no_context = _evaluate(
        records,
        name="remove_context",
        builder=_p3_no_context,
        complexity=5.0,
        folds=folds,
        split_seed=split_seed,
    )
    permuted = _permute_p3_motifs(records, seed=f"{split_seed}-negative-control")
    negative = _evaluate(
        permuted,
        name="permute_higher_order_motifs",
        builder=_p3_higher_order,
        complexity=8.0,
        folds=folds,
        split_seed=split_seed,
    )
    oak = OAKBench(
        complexity_penalty=complexity_penalty,
        uncertainty_penalty=uncertainty_penalty,
    )
    baseline_score = pairwise.as_model_score()
    candidate_score = candidate.as_model_score()
    splits = group_kfold(records, folds=folds, seed=split_seed)
    return {
        "benchmark_id": "omega-neuro-p3-synthetic-r05",
        "hypothesis": "P3_HIGHER_ORDER_WIRING",
        "source_class": "synthetic_test_fixture",
        "biological_promotion_allowed": False,
        "manifest": dict(manifest.to_dict()),
        "payload_bytes": len(payload),
        "records": len(records),
        "groups": len({record.group_id for record in records}),
        "folds": folds,
        "split_seed": split_seed,
        "split_signature": split_signature(splits),
        "models": [asdict(pairwise), asdict(candidate)],
        "ablations": [
            {
                "name": "collapse_to_pairwise",
                "predictive_loss": pairwise.predictive_loss,
                "loss_delta_vs_full": pairwise.predictive_loss - candidate.predictive_loss,
            },
            {
                "name": no_context.name,
                "predictive_loss": no_context.predictive_loss,
                "loss_delta_vs_full": no_context.predictive_loss - candidate.predictive_loss,
            },
        ],
        "negative_control": {
            "name": negative.name,
            "predictive_loss": negative.predictive_loss,
            "degradation_vs_candidate": negative.predictive_loss - candidate.predictive_loss,
        },
        "oak": {
            "baseline": baseline_score.name,
            "candidate": candidate_score.name,
            "baseline_score": oak.score(baseline_score),
            "candidate_score": oak.score(candidate_score),
            "candidate_justified": oak.justified(baseline_score, candidate_score),
            "predictive_improvement": pairwise.predictive_loss - candidate.predictive_loss,
            "improvement_required": oak.improvement_required(baseline_score, candidate_score),
        },
        "epistemic_notice": (
            "Synthetic P3 planted-effect benchmark: validates whether the harness can detect planted higher-order "
            "structure beyond pairwise features; it is not evidence that a biological circuit requires this model."
        ),
    }


def run_p2_p3_campaign() -> Mapping[str, object]:
    p2 = run_p2_benchmark()
    p3 = run_p3_benchmark()
    p2_gate = bool(p2["oak"]["candidate_justified"]) and p2["negative_control"]["degradation_vs_candidate"] > 0.005
    p3_gate = bool(p3["oak"]["candidate_justified"]) and p3["negative_control"]["degradation_vs_candidate"] > 0.02
    return {
        "campaign_id": "omega-neuro-p2-p3-synthetic-r05",
        "software_validation_passed": p2_gate and p3_gate,
        "biological_promotion_allowed": False,
        "reports": {"P2": p2, "P3": p3},
        "epistemic_notice": (
            "Campaign gates only verify deterministic benchmark behavior on planted synthetic effects. "
            "They cannot promote P2 or P3 without independent neuroscience data and provenance review."
        ),
    }
