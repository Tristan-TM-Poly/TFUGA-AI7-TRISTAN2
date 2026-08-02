from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from io import StringIO
from math import isfinite, log10
from typing import Any, Iterable


@dataclass(frozen=True)
class PolarSample:
    alpha_deg: float
    reynolds: float
    mach: float
    lift_coefficient: float
    drag_coefficient: float
    moment_coefficient: float = 0.0
    lift_sigma: float | None = None
    drag_sigma: float | None = None

    def validate(self) -> None:
        values = (
            self.alpha_deg,
            self.reynolds,
            self.mach,
            self.lift_coefficient,
            self.drag_coefficient,
            self.moment_coefficient,
        )
        if not all(isfinite(value) for value in values):
            raise ValueError("polar samples must be finite")
        if self.reynolds <= 0 or self.mach < 0 or self.drag_coefficient < 0:
            raise ValueError("invalid Reynolds, Mach or drag coefficient")
        for name, value in (("lift_sigma", self.lift_sigma), ("drag_sigma", self.drag_sigma)):
            if value is not None and (not isfinite(value) or value < 0):
                raise ValueError(f"{name} must be finite and non-negative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PolarEvaluation:
    airfoil_id: str
    alpha_deg: float
    reynolds: float
    mach: float
    lift_coefficient: float
    drag_coefficient: float
    moment_coefficient: float
    source_type: str
    support_states: tuple[tuple[float, float, float], ...]
    alpha_extrapolated: bool
    condition_extrapolated: bool
    model: str = "tabulated-polar-idw-r0.2"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["support_states"] = [list(item) for item in self.support_states]
        return payload


@dataclass(frozen=True)
class PolarTable:
    airfoil_id: str
    samples: tuple[PolarSample, ...]
    source_type: str = "unknown"
    provenance: str = "unspecified"

    @classmethod
    def from_samples(
        cls,
        airfoil_id: str,
        samples: Iterable[PolarSample],
        *,
        source_type: str = "unknown",
        provenance: str = "unspecified",
    ) -> "PolarTable":
        table = cls(airfoil_id, tuple(samples), source_type, provenance)
        table.validate()
        return table

    @classmethod
    def from_csv_text(
        cls,
        airfoil_id: str,
        text: str,
        *,
        source_type: str = "unknown",
        provenance: str = "inline-csv",
    ) -> "PolarTable":
        reader = csv.DictReader(StringIO(text))
        required = {"alpha_deg", "reynolds", "mach", "cl", "cd"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError(f"polar CSV must include {sorted(required)}")
        samples: list[PolarSample] = []
        for line_number, row in enumerate(reader, start=2):
            try:
                samples.append(
                    PolarSample(
                        alpha_deg=float(row["alpha_deg"]),
                        reynolds=float(row["reynolds"]),
                        mach=float(row["mach"]),
                        lift_coefficient=float(row["cl"]),
                        drag_coefficient=float(row["cd"]),
                        moment_coefficient=float(row.get("cm") or 0.0),
                        lift_sigma=None if not row.get("cl_sigma") else float(row["cl_sigma"]),
                        drag_sigma=None if not row.get("cd_sigma") else float(row["cd_sigma"]),
                    )
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid polar CSV row {line_number}: {exc}") from exc
        return cls.from_samples(
            airfoil_id,
            samples,
            source_type=source_type,
            provenance=provenance,
        )

    def validate(self) -> None:
        if not self.airfoil_id.strip() or not self.source_type.strip() or not self.provenance.strip():
            raise ValueError("airfoil id, source type and provenance are required")
        if len(self.samples) < 2:
            raise ValueError("at least two polar samples are required")
        keys: set[tuple[float, float, float]] = set()
        state_counts: dict[tuple[float, float], int] = {}
        for sample in self.samples:
            sample.validate()
            key = (sample.reynolds, sample.mach, sample.alpha_deg)
            if key in keys:
                raise ValueError("duplicate polar sample")
            keys.add(key)
            state = (sample.reynolds, sample.mach)
            state_counts[state] = state_counts.get(state, 0) + 1
        if any(count < 2 for count in state_counts.values()):
            raise ValueError("each Reynolds/Mach state needs at least two alpha samples")

    @property
    def operating_states(self) -> tuple[tuple[float, float], ...]:
        return tuple(sorted({(sample.reynolds, sample.mach) for sample in self.samples}))

    def _samples_for_state(self, state: tuple[float, float]) -> tuple[PolarSample, ...]:
        reynolds, mach = state
        return tuple(
            sorted(
                (sample for sample in self.samples if sample.reynolds == reynolds and sample.mach == mach),
                key=lambda sample: sample.alpha_deg,
            )
        )

    @staticmethod
    def _alpha_interpolate(
        samples: tuple[PolarSample, ...], alpha_deg: float
    ) -> tuple[float, float, float, bool]:
        if alpha_deg <= samples[0].alpha_deg:
            left, right = samples[0], samples[1]
            extrapolated = alpha_deg < left.alpha_deg
        elif alpha_deg >= samples[-1].alpha_deg:
            left, right = samples[-2], samples[-1]
            extrapolated = alpha_deg > right.alpha_deg
        else:
            extrapolated = False
            left = samples[0]
            right = samples[1]
            for candidate_left, candidate_right in zip(samples, samples[1:]):
                if candidate_left.alpha_deg <= alpha_deg <= candidate_right.alpha_deg:
                    left, right = candidate_left, candidate_right
                    break
        span = right.alpha_deg - left.alpha_deg
        fraction = 0.0 if span == 0 else (alpha_deg - left.alpha_deg) / span

        def blend(a: float, b: float) -> float:
            return a + fraction * (b - a)

        return (
            blend(left.lift_coefficient, right.lift_coefficient),
            max(0.0, blend(left.drag_coefficient, right.drag_coefficient)),
            blend(left.moment_coefficient, right.moment_coefficient),
            extrapolated,
        )

    def evaluate(
        self,
        alpha_deg: float,
        *,
        reynolds: float,
        mach: float,
        maximum_support_states: int = 4,
    ) -> PolarEvaluation:
        self.validate()
        if reynolds <= 0 or mach < 0 or maximum_support_states < 1:
            raise ValueError("invalid polar evaluation request")
        query_log_re = log10(reynolds)
        state_values: list[tuple[float, tuple[float, float], float, float, float, bool]] = []
        for state in self.operating_states:
            state_re, state_mach = state
            distance = ((log10(state_re) - query_log_re) ** 2 + (2.0 * (state_mach - mach)) ** 2) ** 0.5
            cl, cd, cm, alpha_extrapolated = self._alpha_interpolate(
                self._samples_for_state(state), alpha_deg
            )
            state_values.append((distance, state, cl, cd, cm, alpha_extrapolated))
        state_values.sort(key=lambda item: item[0])
        selected = state_values[:maximum_support_states]
        if selected[0][0] <= 1e-14:
            selected = [selected[0]]
            weights = [1.0]
        else:
            inverse = [1.0 / max(item[0], 1e-12) ** 2 for item in selected]
            total = sum(inverse)
            weights = [weight / total for weight in inverse]
        cl = sum(weight * item[2] for weight, item in zip(weights, selected))
        cd = max(0.0, sum(weight * item[3] for weight, item in zip(weights, selected)))
        cm = sum(weight * item[4] for weight, item in zip(weights, selected))
        re_values = [state[0] for state in self.operating_states]
        mach_values = [state[1] for state in self.operating_states]
        condition_extrapolated = not (
            min(re_values) <= reynolds <= max(re_values)
            and min(mach_values) <= mach <= max(mach_values)
        )
        support = tuple((item[1][0], item[1][1], weight) for weight, item in zip(weights, selected))
        return PolarEvaluation(
            airfoil_id=self.airfoil_id,
            alpha_deg=alpha_deg,
            reynolds=reynolds,
            mach=mach,
            lift_coefficient=cl,
            drag_coefficient=cd,
            moment_coefficient=cm,
            source_type=self.source_type,
            support_states=support,
            alpha_extrapolated=any(item[5] for item in selected),
            condition_extrapolated=condition_extrapolated,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "airfoil_id": self.airfoil_id,
            "source_type": self.source_type,
            "provenance": self.provenance,
            "samples": [sample.to_dict() for sample in self.samples],
            "operating_states": [list(state) for state in self.operating_states],
        }


class PolarRegistry:
    def __init__(self, tables: Iterable[PolarTable] = ()) -> None:
        self._tables: dict[str, PolarTable] = {}
        for table in tables:
            self.register(table)

    def register(self, table: PolarTable, *, replace: bool = False) -> None:
        table.validate()
        if table.airfoil_id in self._tables and not replace:
            raise ValueError(f"polar table already registered: {table.airfoil_id}")
        self._tables[table.airfoil_id] = table

    def contains(self, airfoil_id: str) -> bool:
        return airfoil_id in self._tables

    def get(self, airfoil_id: str) -> PolarTable:
        try:
            return self._tables[airfoil_id]
        except KeyError as exc:
            raise KeyError(f"unknown polar table: {airfoil_id}") from exc

    def evaluate(self, airfoil_id: str, alpha_deg: float, *, reynolds: float, mach: float) -> PolarEvaluation:
        return self.get(airfoil_id).evaluate(alpha_deg, reynolds=reynolds, mach=mach)

    def to_dict(self) -> dict[str, Any]:
        return {"tables": [self._tables[key].to_dict() for key in sorted(self._tables)]}


def demo_polar_table() -> PolarTable:
    rows = []
    for reynolds, mach in ((150_000.0, 0.05), (600_000.0, 0.20)):
        for alpha, cl, cd in (
            (-10.0, -0.90, 0.050),
            (-5.0, -0.48, 0.025),
            (0.0, 0.00, 0.012),
            (5.0, 0.52, 0.024),
            (10.0, 0.94, 0.052),
            (15.0, 1.08, 0.110),
        ):
            scale = 1.0 + 0.06 * (mach / 0.20) - 0.03 * (reynolds / 600_000.0)
            rows.append(
                PolarSample(
                    alpha_deg=alpha,
                    reynolds=reynolds,
                    mach=mach,
                    lift_coefficient=cl * (1.0 + 0.04 * (reynolds / 600_000.0)),
                    drag_coefficient=cd * scale,
                )
            )
    return PolarTable.from_samples(
        "demo-tabulated-symmetric",
        rows,
        source_type="synthetic-regression-fixture",
        provenance="generated deterministic fixture; not measured data",
    )
