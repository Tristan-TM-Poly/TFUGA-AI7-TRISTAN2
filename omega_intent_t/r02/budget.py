from __future__ import annotations

from typing import Any

from .models import BudgetObservation, BudgetPolicy, BudgetState


class AdaptiveBudgetController:
    """Discover temporary throughput frontiers without a permanent total cap."""

    def __init__(self, policy: BudgetPolicy | None = None, state: BudgetState | None = None) -> None:
        self.policy = policy or BudgetPolicy()
        self.state = state or BudgetState(
            batch_items=self.policy.initial_items,
            batch_bytes=self.policy.initial_bytes,
        )
        self.history: list[dict[str, Any]] = []

    def observe(self, observation: BudgetObservation) -> BudgetState:
        constrained_reasons: list[str] = []
        if observation.failure_rate > self.policy.failure_ceiling:
            constrained_reasons.append("failure_rate")
        if observation.quality < self.policy.quality_floor:
            constrained_reasons.append("quality")
        if observation.queue_wait_seconds > self.policy.backpressure_seconds:
            constrained_reasons.append("queue_backpressure")
        if observation.peak_memory_ratio >= self.policy.memory_pressure_ratio:
            constrained_reasons.append("memory_pressure")

        if constrained_reasons:
            items = max(
                self.policy.minimum_items,
                int(self.state.batch_items * self.policy.shrink_factor),
            )
            byte_budget = max(
                self.policy.minimum_bytes,
                int(self.state.batch_bytes * self.policy.shrink_factor),
            )
            next_state = BudgetState(
                batch_items=items,
                batch_bytes=byte_budget,
                successful_batches=self.state.successful_batches,
                constrained_batches=self.state.constrained_batches + 1,
                frontier_events=self.state.frontier_events + 1,
                generation=self.state.generation + 1,
                last_reason="constrained:" + ",".join(constrained_reasons),
            )
        else:
            fully_utilized = observation.processed >= self.state.batch_items
            if fully_utilized and observation.processed > 0:
                items = max(self.state.batch_items + 1, int(self.state.batch_items * self.policy.growth_factor))
                byte_budget = max(self.state.batch_bytes + 1, int(self.state.batch_bytes * self.policy.growth_factor))
                reason = "frontier_expanded"
                events = self.state.frontier_events + 1
            else:
                items = self.state.batch_items
                byte_budget = self.state.batch_bytes
                reason = "stable_underutilized"
                events = self.state.frontier_events
            next_state = BudgetState(
                batch_items=items,
                batch_bytes=byte_budget,
                successful_batches=self.state.successful_batches + 1,
                constrained_batches=self.state.constrained_batches,
                frontier_events=events,
                generation=self.state.generation + 1,
                last_reason=reason,
            )

        self.history.append(
            {
                "generation": next_state.generation,
                "before": self.state.to_dict(),
                "observation": observation.to_dict(),
                "after": next_state.to_dict(),
            }
        )
        self.state = next_state
        return next_state

    def manifest(self) -> dict[str, Any]:
        return {
            "schema": "omega-intent-adaptive-budget/v2",
            "policy": {
                "initial_items": self.policy.initial_items,
                "initial_bytes": self.policy.initial_bytes,
                "minimum_items": self.policy.minimum_items,
                "minimum_bytes": self.policy.minimum_bytes,
                "growth_factor": self.policy.growth_factor,
                "shrink_factor": self.policy.shrink_factor,
                "quality_floor": self.policy.quality_floor,
                "failure_ceiling": self.policy.failure_ceiling,
                "backpressure_seconds": self.policy.backpressure_seconds,
                "memory_pressure_ratio": self.policy.memory_pressure_ratio,
                "permanent_total_cap": None,
            },
            "state": self.state.to_dict(),
            "observations": len(self.history),
            "boundary": (
                "The controller has no permanent total-work cap, but every execution remains finite and "
                "bounded by resources, quality, safety, legal constraints, provider quotas and rollback capacity."
            ),
        }
