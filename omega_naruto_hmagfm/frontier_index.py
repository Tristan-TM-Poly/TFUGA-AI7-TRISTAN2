"""Streaming indexes and M⁻ telemetry for compressed frontier-scale corpora."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import gzip
import json
from pathlib import Path
from typing import Iterator

from .frontier import CorpusAxes, default_axes


@dataclass(frozen=True)
class FrontierScaleIndex:
    schema: str
    indexed_records: int
    indexed_shards: int
    start_ordinal: int
    next_ordinal: int
    axis_cardinality: int
    covered_local_combinations: int
    local_coverage_fraction: float
    completed_epochs: int
    partial_epoch_records: int
    repeated_axis_realizations: int
    counts_by_epoch: dict[str, int]
    counts_by_operator: dict[str, int]
    counts_by_domain: dict[str, int]
    counts_by_epistemic_state: dict[str, int]
    counts_by_evidence_mode: dict[str, int]
    counts_by_perturbation: dict[str, int]
    counts_by_gate_profile: dict[str, int]
    counts_by_oak_action: dict[str, int]
    mminus_records: int
    blocked_records: int
    human_review_records: int
    locally_ranked_records: int
    mminus_fraction: float
    blocked_fraction: float
    samples: tuple[dict[str, object], ...]
    non_claim: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["samples"] = list(self.samples)
        return payload


def _ordered(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def _iter_records(output_dir: Path, shard_entries: list[dict[str, object]]) -> Iterator[dict[str, object]]:
    for shard in sorted(shard_entries, key=lambda item: int(item["partition_id"])):
        path = output_dir / str(shard["path"])
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def build_scale_index(
    output_dir: Path,
    *,
    axes: CorpusAxes | None = None,
    sample_limit: int = 64,
) -> FrontierScaleIndex:
    """Build an exact streaming aggregate index with bounded sample memory."""

    if sample_limit < 0:
        raise ValueError("sample_limit must be non-negative")
    axes = axes or default_axes()
    manifest_path = output_dir / "scale-manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    shards = manifest.get("shards", [])
    if not isinstance(shards, list):
        raise ValueError("manifest shards must be a list")

    epoch_counts: Counter[str] = Counter()
    operator_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    epistemic_counts: Counter[str] = Counter()
    evidence_counts: Counter[str] = Counter()
    perturbation_counts: Counter[str] = Counter()
    gate_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    covered = bytearray(axes.cardinality)
    samples: list[dict[str, object]] = []
    indexed = 0
    mminus_records = 0
    blocked_records = 0
    human_review_records = 0
    locally_ranked_records = 0

    expected_total = int(manifest.get("written_records", 0))
    sample_stride = max(1, expected_total // sample_limit) if sample_limit else 0

    for record in _iter_records(output_dir, shards):
        indexed += 1
        epoch = int(record["epoch"])
        local_ordinal = int(record["local_ordinal"])
        action = str(record["expected_oak_action"])
        epoch_counts[str(epoch)] += 1
        operator_counts[str(record["operator"])] += 1
        domain_counts[str(record["domain"])] += 1
        epistemic_counts[str(record["epistemic_state"])] += 1
        evidence_counts[str(record["evidence_mode"])] += 1
        perturbation_counts[str(record["perturbation"])] += 1
        gate_counts[str(record["gate_profile"])] += 1
        action_counts[action] += 1
        covered[local_ordinal] = 1

        if "MMINUS" in action:
            mminus_records += 1
        if action.startswith("BLOCK_"):
            blocked_records += 1
        if "HUMAN_REVIEW" in action:
            human_review_records += 1
        if action == "RANK_LOCALLY_WITHOUT_CERTIFICATION":
            locally_ranked_records += 1

        if sample_limit and len(samples) < sample_limit and (indexed - 1) % sample_stride == 0:
            samples.append(
                {
                    "ordinal": int(record["ordinal"]),
                    "record_id": str(record["record_id"]),
                    "epoch": epoch,
                    "operator": str(record["operator"]),
                    "domain": str(record["domain"]),
                    "expected_oak_action": action,
                }
            )

    coverage = sum(covered)
    cardinality = axes.cardinality
    next_ordinal = int(manifest.get("next_ordinal", indexed))
    start_ordinal = int(manifest.get("start_ordinal", 0))
    return FrontierScaleIndex(
        schema="omega_naruto_frontier.scale_index.v2",
        indexed_records=indexed,
        indexed_shards=len(shards),
        start_ordinal=start_ordinal,
        next_ordinal=next_ordinal,
        axis_cardinality=cardinality,
        covered_local_combinations=coverage,
        local_coverage_fraction=(coverage / cardinality if cardinality else 0.0),
        completed_epochs=next_ordinal // cardinality,
        partial_epoch_records=next_ordinal % cardinality,
        repeated_axis_realizations=max(0, indexed - coverage),
        counts_by_epoch=_ordered(epoch_counts),
        counts_by_operator=_ordered(operator_counts),
        counts_by_domain=_ordered(domain_counts),
        counts_by_epistemic_state=_ordered(epistemic_counts),
        counts_by_evidence_mode=_ordered(evidence_counts),
        counts_by_perturbation=_ordered(perturbation_counts),
        counts_by_gate_profile=_ordered(gate_counts),
        counts_by_oak_action=_ordered(action_counts),
        mminus_records=mminus_records,
        blocked_records=blocked_records,
        human_review_records=human_review_records,
        locally_ranked_records=locally_ranked_records,
        mminus_fraction=(mminus_records / indexed if indexed else 0.0),
        blocked_fraction=(blocked_records / indexed if indexed else 0.0),
        samples=tuple(samples),
        non_claim=(
            "Index counts measure generated fixture distribution and OAK routing only; "
            "they do not measure scientific validity, utility, or market value."
        ),
    )


def write_scale_index(
    output_dir: Path,
    *,
    destination: Path | None = None,
    sample_limit: int = 64,
) -> FrontierScaleIndex:
    index = build_scale_index(output_dir, sample_limit=sample_limit)
    target = destination or output_dir / "scale-index.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(index.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return index
