from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TelemetrySnapshot:
    runs: int = 0
    successes: int = 0
    failures: int = 0
    manual_steps_removed: int = 0
    errors_prevented: int = 0
    artifacts_created: int = 0
    time_saved_minutes: float = 0.0
    cost_units: float = 0.0
    noise_events: int = 0

    @property
    def success_rate(self) -> float:
        return round(self.successes / self.runs, 4) if self.runs else 0.0

    def value_score(self) -> float:
        positive = (
            0.18 * min(1.0, self.success_rate)
            + 0.18 * min(1.0, self.manual_steps_removed / 20)
            + 0.16 * min(1.0, self.errors_prevented / 10)
            + 0.16 * min(1.0, self.artifacts_created / 10)
            + 0.18 * min(1.0, self.time_saved_minutes / 240)
        )
        penalty = 0.08 * min(1.0, self.cost_units / 100) + 0.06 * min(1.0, self.noise_events / 20)
        return round(max(0.0, min(1.0, positive - penalty)), 4)

    def to_dict(self) -> dict[str, float | int]:
        data = self.__dict__.copy()
        data["success_rate"] = self.success_rate
        data["value_score"] = self.value_score()
        return data
