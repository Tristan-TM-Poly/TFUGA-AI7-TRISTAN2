"""Deterministic fixture metadata registry for Omega Compute Physics R0.6.

Fixtures describe how a trusted external benchmark adapter is expected to build
inputs. This module does not import target repositories and does not execute a
fixture. The registry exists so a benchmark candidate cannot silently invent
inputs that do not match the callable being studied.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class FixtureSpec:
    fixture_id: str
    description: str
    axis_names: tuple[str, ...]
    input_schema: Mapping[str, str]
    deterministic: bool = True
    pure_data: bool = True
    requires_files: bool = False
    requires_network: bool = False
    notes: tuple[str, ...] = ()
    status: str = "fixture-spec-candidate"

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.fixture_id:
            errors.append("fixture_id missing")
        if not self.axis_names:
            errors.append("at least one benchmark axis is required")
        if len(set(self.axis_names)) != len(self.axis_names):
            errors.append("axis_names must be unique")
        missing = [name for name in self.axis_names if name not in self.input_schema]
        if missing:
            errors.append(f"axis_names missing from input_schema: {missing}")
        if not self.deterministic:
            errors.append("fixture must be deterministic for automatic benchmark planning")
        if not self.pure_data:
            errors.append("automatic planning requires a pure-data fixture")
        if self.requires_network:
            errors.append("network-backed fixtures are quarantined")
        return tuple(errors)

    @property
    def plannable(self) -> bool:
        return not self.validate()

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "validation_errors": list(self.validate())}


@dataclass
class FixtureRegistry:
    fixtures: dict[str, FixtureSpec] = field(default_factory=dict)

    def register(self, fixture: FixtureSpec) -> None:
        if fixture.fixture_id in self.fixtures:
            raise ValueError(f"fixture already registered: {fixture.fixture_id}")
        self.fixtures[fixture.fixture_id] = fixture

    def replace(self, fixture: FixtureSpec) -> None:
        self.fixtures[fixture.fixture_id] = fixture

    def get(self, fixture_id: str) -> FixtureSpec:
        try:
            return self.fixtures[fixture_id]
        except KeyError as exc:
            raise KeyError(f"unknown fixture: {fixture_id}") from exc

    def compatible(self, axis_names: Sequence[str]) -> tuple[FixtureSpec, ...]:
        required = set(axis_names)
        return tuple(
            fixture
            for fixture in sorted(self.fixtures.values(), key=lambda row: row.fixture_id)
            if fixture.plannable and required.issubset(set(fixture.axis_names))
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixtures": [fixture.to_dict() for fixture in sorted(self.fixtures.values(), key=lambda row: row.fixture_id)],
            "status": "deterministic-fixture-registry",
            "oak_warning": (
                "Fixture metadata describes intended deterministic inputs. An external "
                "trusted adapter must still implement and validate the actual fixture."
            ),
        }


def conservative_default_registry() -> FixtureRegistry:
    """Return only generic pure-data fixture specifications.

    They are intentionally metadata-only; target-specific argument wiring must be
    reviewed before any contract can become executable.
    """
    registry = FixtureRegistry()
    registry.register(FixtureSpec(
        fixture_id="scalar-n",
        description="One non-negative integer-like size axis named n.",
        axis_names=("n",),
        input_schema={"n": "integer size; adapter-defined argument mapping"},
    ))
    registry.register(FixtureSpec(
        fixture_id="matrix-mnk",
        description="Three positive integer matrix-shape axes m, n, k.",
        axis_names=("m", "n", "k"),
        input_schema={
            "m": "positive integer rows",
            "n": "positive integer shared dimension",
            "k": "positive integer columns",
        },
    ))
    return registry
