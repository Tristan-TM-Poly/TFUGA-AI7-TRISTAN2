"""Content-addressed registry for authorized experiments and immutable observations."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ExperimentSpec:
    experiment_id: str
    controls: Mapping[str, float]
    observable: str
    authorized_scope: str
    reversible: bool
    maximum_risk: float
    cost_units: float


@dataclass(frozen=True)
class ObservationRecord:
    experiment_digest: str
    sequence: int
    value: float
    uncertainty: float
    instrument_digest: str
    timestamp_label: str
    source: str


@dataclass(frozen=True)
class RegisteredExperiment:
    spec: ExperimentSpec
    spec_digest: str
    observations: tuple[ObservationRecord, ...]


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def validate_spec(spec: ExperimentSpec) -> None:
    if not spec.experiment_id.strip() or not spec.observable.strip() or not spec.authorized_scope.strip():
        raise ValueError("experiment identity fields cannot be blank")
    if not spec.controls or any(not math.isfinite(value) for value in spec.controls.values()):
        raise ValueError("controls must be finite and non-empty")
    if not 0 <= spec.maximum_risk <= 1 or spec.cost_units < 0 or not math.isfinite(spec.cost_units):
        raise ValueError("invalid risk or cost")


class ExperimentRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, ExperimentSpec] = {}
        self._digests: dict[str, str] = {}
        self._observations: dict[str, list[ObservationRecord]] = {}

    def register(self, spec: ExperimentSpec) -> str:
        validate_spec(spec)
        spec_digest = digest(asdict(spec))
        existing = self._digests.get(spec.experiment_id)
        if existing is not None and existing != spec_digest:
            raise ValueError("experiment id already bound to a different specification")
        self._specs[spec.experiment_id] = spec
        self._digests[spec.experiment_id] = spec_digest
        self._observations.setdefault(spec.experiment_id, [])
        return spec_digest

    def append_observation(
        self,
        experiment_id: str,
        *,
        value: float,
        uncertainty: float,
        instrument_digest: str,
        timestamp_label: str,
        source: str,
    ) -> ObservationRecord:
        if experiment_id not in self._specs:
            raise KeyError("experiment not registered")
        if not math.isfinite(value) or not math.isfinite(uncertainty) or uncertainty <= 0:
            raise ValueError("invalid observation")
        if not instrument_digest.startswith("sha256:") or not timestamp_label.strip() or not source.strip():
            raise ValueError("invalid observation provenance")
        sequence = len(self._observations[experiment_id])
        record = ObservationRecord(
            experiment_digest=self._digests[experiment_id],
            sequence=sequence,
            value=value,
            uncertainty=uncertainty,
            instrument_digest=instrument_digest,
            timestamp_label=timestamp_label,
            source=source,
        )
        self._observations[experiment_id].append(record)
        return record

    def snapshot(self) -> tuple[RegisteredExperiment, ...]:
        return tuple(
            RegisteredExperiment(self._specs[key], self._digests[key], tuple(self._observations[key]))
            for key in sorted(self._specs)
        )

    def snapshot_digest(self) -> str:
        return digest([asdict(item) for item in self.snapshot()])

    def audit(self) -> Mapping[str, object]:
        errors: list[str] = []
        for item in self.snapshot():
            if digest(asdict(item.spec)) != item.spec_digest:
                errors.append(f"spec_digest:{item.spec.experiment_id}")
            for index, observation in enumerate(item.observations):
                if observation.sequence != index:
                    errors.append(f"sequence:{item.spec.experiment_id}:{index}")
                if observation.experiment_digest != item.spec_digest:
                    errors.append(f"binding:{item.spec.experiment_id}:{index}")
        return {"valid": not errors, "errors": tuple(errors), "snapshot_digest": self.snapshot_digest()}
