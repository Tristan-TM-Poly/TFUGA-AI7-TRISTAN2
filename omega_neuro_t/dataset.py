from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from math import isfinite, sin
from typing import Iterable, List, Sequence, Tuple

from .provenance import DatasetManifest, build_manifest, verify_payload


@dataclass(frozen=True)
class NeuroObservation:
    """Small tabular observation contract for benchmark adapters."""

    sample_id: str
    group_id: str
    signal: float
    address: str
    context: float
    target: float

    def __post_init__(self) -> None:
        if not self.sample_id or not self.group_id or not self.address:
            raise ValueError("sample_id, group_id and address must be non-empty")
        for name in ("signal", "context", "target"):
            if not isfinite(getattr(self, name)):
                raise ValueError(f"{name} must be finite")


def observations_to_jsonl(records: Iterable[NeuroObservation]) -> bytes:
    lines = [json.dumps(asdict(record), sort_keys=True, separators=(",", ":")) for record in records]
    return (("\n".join(lines) + "\n") if lines else "").encode("utf-8")


def observations_from_jsonl(payload: bytes, manifest: DatasetManifest | None = None) -> List[NeuroObservation]:
    if manifest is not None and not verify_payload(manifest, payload):
        raise ValueError("dataset payload does not match manifest sha256")
    records: List[NeuroObservation] = []
    for line_number, raw in enumerate(payload.decode("utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            item = json.loads(raw)
            records.append(NeuroObservation(**item))
        except Exception as exc:  # boundary adapter: normalize malformed input
            raise ValueError(f"invalid JSONL observation at line {line_number}: {exc}") from exc
    if not records:
        raise ValueError("dataset must contain at least one observation")
    return records


def synthetic_p1_dataset(
    *,
    groups: int = 24,
    trials_per_group: int = 8,
    noise_scale: float = 0.03,
) -> List[NeuroObservation]:
    """Deterministic synthetic data where dendritic address carries signal.

    This is a software test fixture, not a biological simulation or evidence.
    The planted interaction lets the benchmark verify that the evaluation
    machinery can recover a known address-dependent effect.
    """

    if groups < 4 or trials_per_group < 2:
        raise ValueError("synthetic benchmark needs >=4 groups and >=2 trials/group")
    if noise_scale < 0 or not isfinite(noise_scale):
        raise ValueError("noise_scale must be finite and >= 0")

    records: List[NeuroObservation] = []
    addresses = ("proximal", "distal")
    for group_index in range(groups):
        group_id = f"cell-{group_index:03d}"
        group_shift = ((group_index % 5) - 2) * 0.015
        for trial in range(trials_per_group):
            address = addresses[(group_index + trial) % len(addresses)]
            signal = 0.15 + 0.10 * trial + 0.015 * (group_index % 3)
            context = 0.75 + 0.05 * ((2 * group_index + trial) % 7)
            distal = 1.0 if address == "distal" else 0.0
            proximal = 1.0 - distal
            deterministic_noise = noise_scale * sin((group_index + 1) * (trial + 1) * 1.173)
            target = (
                0.20
                + 1.05 * signal
                + 1.25 * signal * distal
                - 0.35 * signal * proximal
                + 0.30 * context
                + group_shift
                + deterministic_noise
            )
            records.append(
                NeuroObservation(
                    sample_id=f"{group_id}:trial-{trial:02d}",
                    group_id=group_id,
                    signal=signal,
                    address=address,
                    context=context,
                    target=target,
                )
            )
    return records


def synthetic_p1_bundle(**kwargs: object) -> Tuple[List[NeuroObservation], bytes, DatasetManifest]:
    records = synthetic_p1_dataset(**kwargs)
    payload = observations_to_jsonl(records)
    manifest = build_manifest(
        payload,
        dataset_id="omega-neuro-p1-address-synthetic",
        version="1.0.0",
        source_uri="synthetic://omega-neuro/p1/address-v1",
        license_id="synthetic-test-fixture",
        access_mode="synthetic",
        citation="Generated deterministically by omega_neuro_t.dataset.synthetic_p1_dataset",
    )
    return records, payload, manifest
