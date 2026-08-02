"""Partitioned million-record Ω-GENERATOR-DISCOVERY campaigns.

Generated records are candidate templates and synthetic benchmarks, not
scientific discoveries, proofs, empirical validation, or patentability claims.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

DOMAINS = (
    "spectral", "crystal", "elastic", "thermal", "electromagnetic", "chemical",
    "quantum", "stochastic", "fluid", "battery", "optical", "photonic",
    "acoustic", "biological", "ecological", "climate", "materials", "calibration",
    "control", "robotics", "computing", "neural", "epistemic", "software",
    "economic", "energy", "transport", "geological", "astronomical", "linguistic",
    "social", "game",
)
FAMILIES = (
    "translation", "dilation", "rotation", "shear", "diffusion", "advection",
    "reaction", "relaxation", "oscillation", "coupling", "projection", "lift",
    "convolution", "deconvolution", "phase_shift", "amplitude", "broadening",
    "splitting", "merging", "branching", "threshold", "saturation", "hysteresis",
    "memory", "symmetry_break", "topology_change", "rank_change", "noise",
    "measurement", "control", "correction", "compression",
)
SCALES = ("atomic", "molecular", "micro", "meso", "macro", "system", "network", "multiscale")
REPRESENTATIONS = ("state", "operator", "observable", "hypergraph")
EVIDENCE_MODES = ("reconstruction", "prediction", "intervention", "counterfactual")
INVARIANTS = ("mass", "energy", "charge", "probability", "norm", "symmetry", "positivity", "causality", "trace", "rank", "entropy_budget", "none")
RISKS = ("branch_ambiguity", "non_identifiability", "hidden_state", "numerical_instability", "unit_mismatch", "causal_overclaim", "none")
NON_INVERTIBLE = frozenset({"projection", "merging", "rank_change", "measurement", "compression"})
DEFAULT_CAMPAIGN_ID = "omega-generator-discovery-r03-million"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _axis(name: str, values: Sequence[str]) -> tuple[str, ...]:
    result = tuple(str(value).strip() for value in values)
    if not result or any(not value for value in result):
        raise ValueError(f"axis {name!r} must contain non-empty values")
    if len(result) != len(set(result)):
        raise ValueError(f"axis {name!r} contains duplicates")
    return result


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


@dataclass(frozen=True, slots=True)
class CampaignAxes:
    domains: tuple[str, ...] = DOMAINS
    families: tuple[str, ...] = FAMILIES
    scales: tuple[str, ...] = SCALES
    representations: tuple[str, ...] = REPRESENTATIONS
    evidence_modes: tuple[str, ...] = EVIDENCE_MODES

    def __post_init__(self) -> None:
        for name in ("domains", "families", "scales", "representations", "evidence_modes"):
            object.__setattr__(self, name, _axis(name, getattr(self, name)))

    @property
    def radices(self) -> tuple[int, ...]:
        return tuple(len(getattr(self, name)) for name in ("domains", "families", "scales", "representations", "evidence_modes"))

    @property
    def generator_count(self) -> int:
        return math.prod(self.radices)

    def to_dict(self) -> dict[str, list[str]]:
        return {name: list(getattr(self, name)) for name in ("domains", "families", "scales", "representations", "evidence_modes")}


@dataclass(frozen=True, slots=True)
class CampaignSpec:
    campaign_id: str = DEFAULT_CAMPAIGN_ID
    axes: CampaignAxes = field(default_factory=CampaignAxes)
    benchmark_variants: int = 8
    schema_version: str = "R0.3"
    _fingerprint: str = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.campaign_id.strip() or self.benchmark_variants < 1:
            raise ValueError("campaign_id must be non-empty and benchmark_variants positive")
        object.__setattr__(self, "_fingerprint", _hash(_json(self.definition())))

    @property
    def generator_count(self) -> int:
        return self.axes.generator_count

    @property
    def benchmark_count(self) -> int:
        return self.generator_count * self.benchmark_variants

    @property
    def logical_record_count(self) -> int:
        return self.generator_count + self.benchmark_count

    @property
    def records_per_bundle(self) -> int:
        return self.benchmark_variants + 1

    @property
    def fingerprint(self) -> str:
        return self._fingerprint

    def definition(self) -> dict[str, Any]:
        return {"campaign_id": self.campaign_id, "schema_version": self.schema_version, "axes": self.axes.to_dict(), "benchmark_variants": self.benchmark_variants}

    def manifest(self) -> dict[str, Any]:
        return {
            **self.definition(),
            "generator_candidates": self.generator_count,
            "synthetic_benchmarks": self.benchmark_count,
            "logical_records": self.logical_record_count,
            "records_per_generator_bundle": self.records_per_bundle,
            "campaign_fingerprint": self.fingerprint,
            "no_permanent_total_addition_cap": True,
            "oak_boundary": "Generated volume is not scientific validation.",
        }

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "CampaignSpec":
        axes_raw = raw.get("axes", {})
        if not isinstance(axes_raw, Mapping):
            raise ValueError("axes must be an object")
        defaults = CampaignAxes()
        axes = CampaignAxes(**{name: tuple(axes_raw.get(name, getattr(defaults, name))) for name in defaults.to_dict()})
        return cls(
            campaign_id=str(raw.get("campaign_id", DEFAULT_CAMPAIGN_ID)),
            axes=axes,
            benchmark_variants=int(raw.get("benchmark_variants", 8)),
            schema_version=str(raw.get("schema_version", "R0.3")),
        )


def load_campaign_spec(path: str | Path | None = None) -> CampaignSpec:
    if path is None:
        return CampaignSpec()
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError("campaign specification must be a JSON object")
    return CampaignSpec.from_mapping(raw)


def mixed_radix_decode(index: int, radices: Sequence[int]) -> tuple[int, ...]:
    if any(radix < 1 for radix in radices):
        raise ValueError("radices must be positive")
    total = math.prod(radices)
    if not 0 <= index < total:
        raise IndexError(f"index {index} outside [0, {total})")
    digits = [0] * len(radices)
    for position in range(len(radices) - 1, -1, -1):
        index, digits[position] = divmod(index, radices[position])
    return tuple(digits)


def _generator(spec: CampaignSpec, index: int) -> dict[str, Any]:
    axes = spec.axes
    d, f, s, r, e = mixed_radix_decode(index, axes.radices)
    domain, family = axes.domains[d], axes.families[f]
    seed = int(_hash(f"{spec.fingerprint}:{index}")[:16], 16)
    return {
        "id": f"GEN-R03-{index:09d}", "generator_index": index,
        "domain": domain, "family": family, "scale": axes.scales[s],
        "representation": axes.representations[r], "evidence_mode": axes.evidence_modes[e],
        "status": "machine_generated_candidate_template",
        "invariant": INVARIANTS[seed % len(INVARIANTS)],
        "risk": RISKS[(seed // len(INVARIANTS)) % len(RISKS)],
        "parameter_count": 1 + seed % 16,
        "supports_inverse": family not in NON_INVERTIBLE,
        "oak_gate": "typed_units+baseline+uncertainty+domain+negative_control+out_of_sample+falsification",
        "benchmark_ids": [f"BEN-R03-{index:09d}-{variant:02d}" for variant in range(spec.benchmark_variants)],
    }


def _wrap(spec: CampaignSpec, index: int, kind: str, namespace: str, payload: Mapping[str, Any], role: str, provenance: list[str]) -> dict[str, Any]:
    return {
        "addition_id": payload["id"], "namespace": namespace, "kind": kind,
        "payload": dict(payload), "provenance": provenance, "risk": "normal",
        "metadata": {"schema_version": spec.schema_version, "bundle_index": index, "record_role": role},
    }


def generator_addition(spec: CampaignSpec, generator_index: int) -> dict[str, Any]:
    payload = _generator(spec, generator_index)
    return _wrap(spec, generator_index, "generator_candidate", f"omega-generator/{payload['domain']}", payload, "generator", [spec.campaign_id, spec.fingerprint])


def _benchmark(spec: CampaignSpec, generator: Mapping[str, Any], index: int, variant: int) -> dict[str, Any]:
    if not 0 <= variant < spec.benchmark_variants:
        raise IndexError("benchmark variant outside campaign range")
    benchmark_id = f"BEN-R03-{index:09d}-{variant:02d}"
    seed = int(_hash(f"{generator['id']}:{variant}")[:16], 16)
    payload = {
        "id": benchmark_id, "generator_id": generator["id"], "generator_index": index, "variant": variant,
        "input_seed": seed % 2_147_483_647,
        "parameters": {
            "amplitude": round(0.5 + (seed % 10_000) / 4_000, 6),
            "shift": round(((seed // 10_000) % 20_001 - 10_000) / 1_000, 6),
            "scale": round(0.1 + ((seed // 200_010_000) % 50_000) / 10_000, 6),
        },
        "expected": {"finite": True, "reconstruction_error_max": 10.0 ** (-(4 + variant % 5)), "preserve": generator["invariant"]},
        "negative_control": "wrong_family" if variant % 2 == 0 else "scrambled_parameters",
        "oak_status": "synthetic_template_not_empirical_evidence",
    }
    return _wrap(spec, index, "synthetic_benchmark", f"omega-benchmark/{generator['domain']}", payload, "benchmark", [spec.campaign_id, spec.fingerprint, str(generator["id"])])


def benchmark_addition(spec: CampaignSpec, generator_index: int, variant: int) -> dict[str, Any]:
    return _benchmark(spec, _generator(spec, generator_index), generator_index, variant)


def iter_generator_bundles(spec: CampaignSpec, *, start: int = 0, stop: int | None = None) -> Iterator[dict[str, Any]]:
    upper = spec.generator_count if stop is None else stop
    if not 0 <= start <= upper <= spec.generator_count:
        raise ValueError("range must satisfy 0 <= start <= stop <= generator_count")
    for index in range(start, upper):
        generator = _generator(spec, index)
        yield _wrap(spec, index, "generator_candidate", f"omega-generator/{generator['domain']}", generator, "generator", [spec.campaign_id, spec.fingerprint])
        for variant in range(spec.benchmark_variants):
            yield _benchmark(spec, generator, index, variant)


@dataclass(frozen=True, slots=True)
class CampaignPartition:
    partition_index: int
    partition_count: int
    generator_start: int
    generator_stop: int
    generator_bundles: int
    logical_records: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def partition_campaign(spec: CampaignSpec, partition_count: int) -> tuple[CampaignPartition, ...]:
    if partition_count < 1:
        raise ValueError("partition_count must be positive")
    base, remainder, cursor = *divmod(spec.generator_count, partition_count), 0
    parts = []
    for index in range(partition_count):
        size = base + (index < remainder)
        stop = cursor + size
        parts.append(CampaignPartition(index, partition_count, cursor, stop, size, size * spec.records_per_bundle))
        cursor = stop
    return tuple(parts)


def stream_digest(records: Iterable[Mapping[str, Any]]) -> tuple[int, str]:
    digest, count = hashlib.sha256(), 0
    for record in records:
        digest.update((_json(record) + "\n").encode("utf-8"))
        count += 1
    return count, digest.hexdigest()


class CampaignEmitter:
    """Atomic resumable JSONL emitter; shard size is not a total-addition cap."""

    def __init__(self, spec: CampaignSpec, partition: CampaignPartition, output_dir: str | Path, *, bundles_per_shard: int = 2_048):
        if bundles_per_shard < 1:
            raise ValueError("bundles_per_shard must be positive")
        self.spec, self.partition = spec, partition
        self.output_dir, self.bundles_per_shard = Path(output_dir), bundles_per_shard
        self.checkpoint = self.output_dir / "checkpoint.json"
        self.shards = self.output_dir / "shards.jsonl"

    def emit(self, *, resume: bool = False) -> "CampaignEmissionReport":
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if not resume and any(self.output_dir.iterdir()):
            raise FileExistsError(f"output directory is not empty: {self.output_dir}")
        next_index, bundles, records, shard_count = self.partition.generator_start, 0, 0, 0
        if resume and self.checkpoint.exists():
            saved = json.loads(self.checkpoint.read_text(encoding="utf-8"))
            if saved.get("campaign_fingerprint") != self.spec.fingerprint or saved.get("partition") != self.partition.to_dict() or int(saved.get("bundles_per_shard", -1)) != self.bundles_per_shard:
                raise ValueError("checkpoint does not match campaign, partition, or shard policy")
            next_index, bundles, records, shard_count = (int(saved[key]) for key in ("next_generator", "emitted_generator_bundles", "emitted_logical_records", "shards"))
        while next_index < self.partition.generator_stop:
            stop = min(next_index + self.bundles_per_shard, self.partition.generator_stop)
            shard = self._emit_shard(next_index, stop)
            with self.shards.open("a", encoding="utf-8") as handle:
                handle.write(_json(shard) + "\n"); handle.flush(); os.fsync(handle.fileno())
            shard_count += 1; bundles += stop - next_index; records += int(shard["logical_records"]); next_index = stop
            _atomic_json(self.checkpoint, {
                "status": "completed" if next_index == self.partition.generator_stop else "running",
                "campaign_fingerprint": self.spec.fingerprint, "partition": self.partition.to_dict(),
                "bundles_per_shard": self.bundles_per_shard, "next_generator": next_index,
                "emitted_generator_bundles": bundles, "emitted_logical_records": records, "shards": shard_count,
            })
        report = CampaignEmissionReport(
            "completed", self.spec.campaign_id, self.spec.fingerprint,
            self.partition.partition_index, self.partition.partition_count,
            self.partition.generator_start, self.partition.generator_stop,
            bundles, records, shard_count, str(self.output_dir), datetime.now(timezone.utc).isoformat(),
        )
        _atomic_json(self.output_dir / "report.json", report.to_dict())
        return report

    def _emit_shard(self, start: int, stop: int) -> dict[str, Any]:
        relative = Path("records") / f"bundle-{start:09d}-{stop:09d}.jsonl"
        final = self.output_dir / relative; final.parent.mkdir(parents=True, exist_ok=True)
        temporary = final.with_suffix(final.suffix + ".tmp")
        digest, count, byte_count = hashlib.sha256(), 0, 0
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            for record in iter_generator_bundles(self.spec, start=start, stop=stop):
                line = _json(record) + "\n"; encoded = line.encode("utf-8")
                handle.write(line); digest.update(encoded); count += 1; byte_count += len(encoded)
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, final)
        expected = (stop - start) * self.spec.records_per_bundle
        if count != expected:
            raise RuntimeError(f"expected {expected} records, emitted {count}")
        return {"path": relative.as_posix(), "generator_start": start, "generator_stop": stop, "generator_bundles": stop - start, "logical_records": count, "bytes": byte_count, "sha256": digest.hexdigest()}


@dataclass(frozen=True, slots=True)
class CampaignEmissionReport:
    status: str
    campaign_id: str
    campaign_fingerprint: str
    partition_index: int
    partition_count: int
    generator_start: int
    generator_stop: int
    emitted_generator_bundles: int
    emitted_logical_records: int
    shards: int
    output_dir: str
    completed_at: str
    no_permanent_total_addition_cap: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
