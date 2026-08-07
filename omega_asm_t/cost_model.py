from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class StaticCostProfile:
    """Versioned ordinal cost profile used only for P2 heuristic ranking.

    `loop_cost_units` are deliberately *not* cycles.  A profile remains
    uncalibrated until target-machine measurements establish a mapping to
    hardware observations.
    """

    model_id: str
    architecture: str
    variant: str
    loop_cost_units: float
    memory_score: float
    basis: str
    calibrated: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def canonical_architecture(architecture: str) -> str:
    normalized = architecture.lower().replace("-", "_")
    if normalized in {"x86_64", "amd64"}:
        return "x86_64"
    if normalized in {"aarch64", "arm64"}:
        return "aarch64"
    raise ValueError(f"unsupported architecture: {architecture}")


_BASIS = (
    "hand-authored deterministic ordinal heuristic for R1/P2; "
    "not calibrated to cycles, IPC, energy, ports or a named microarchitecture"
)

_PROFILES: dict[tuple[str, str], StaticCostProfile] = {
    ("x86_64", "indexed"): StaticCostProfile(
        model_id="omega-asm-r1-p2-static-v1",
        architecture="x86_64",
        variant="indexed",
        loop_cost_units=8.0,
        memory_score=2.0,
        basis=_BASIS,
    ),
    ("x86_64", "ptr"): StaticCostProfile(
        model_id="omega-asm-r1-p2-static-v1",
        architecture="x86_64",
        variant="ptr",
        loop_cost_units=9.0,
        memory_score=2.0,
        basis=_BASIS,
    ),
    ("aarch64", "ptr"): StaticCostProfile(
        model_id="omega-asm-r1-p2-static-v1",
        architecture="aarch64",
        variant="ptr",
        loop_cost_units=7.0,
        memory_score=2.0,
        basis=_BASIS,
    ),
}


def get_static_cost_profile(architecture: str, variant: str) -> StaticCostProfile:
    key = (canonical_architecture(architecture), variant.lower())
    try:
        return _PROFILES[key]
    except KeyError as exc:
        raise ValueError(f"no static cost profile for {key[0]}/{key[1]}") from exc


def static_cost_profiles() -> tuple[StaticCostProfile, ...]:
    return tuple(_PROFILES[key] for key in sorted(_PROFILES))
