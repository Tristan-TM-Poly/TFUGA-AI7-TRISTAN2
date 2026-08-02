"""Composable instrument protocol with explicit safety gates."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class InstrumentProtocol:
    instrument_id: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    generators: tuple[str, ...]
    safety_limits: Mapping[str, float]
    rollback_steps: tuple[str, ...]
    status: str = "draft_not_executed"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def compile_protocol(specification: Mapping[str, object]) -> InstrumentProtocol:
    def sequence(key: str) -> tuple[str, ...]:
        raw = specification.get(key, ())
        if isinstance(raw, str):
            return (raw,)
        if not isinstance(raw, Sequence):
            raise ValueError(f"{key} must be a sequence")
        return tuple(str(item) for item in raw)

    limits_raw = specification.get("safety_limits", {})
    if not isinstance(limits_raw, Mapping):
        raise ValueError("safety_limits must be a mapping")
    limits = {str(key): float(value) for key, value in limits_raw.items()}
    if any(value < 0 for value in limits.values()):
        raise ValueError("Safety limits must be non-negative")
    protocol = InstrumentProtocol(
        instrument_id=str(specification.get("instrument_id", "unknown")),
        inputs=sequence("inputs"),
        outputs=sequence("outputs"),
        generators=sequence("generators"),
        safety_limits=limits,
        rollback_steps=sequence("rollback_steps"),
    )
    if not protocol.outputs:
        raise ValueError("At least one output is required")
    if not protocol.rollback_steps:
        raise ValueError("At least one rollback step is required")
    return protocol
