"""OAK validation for Ω-GAME-T."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .core import Event, RuleKernel, WorldGraph


@dataclass(slots=True)
class OAKReport:
    coherent: bool
    fair: bool
    fun: bool
    safe: bool
    testable: bool
    non_exploitative: bool
    agency: float = 1.0
    reasons: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def accepted(self) -> bool:
        return (
            self.coherent
            and self.fair
            and self.fun
            and self.safe
            and self.testable
            and self.non_exploitative
            and self.agency >= 0.5
        )


class OAKGate:
    """Rejects incoherent, unfair, unsafe, untestable or manipulative events."""

    banned_payload_flags = {
        "dark_pattern",
        "predatory_loot_box",
        "addiction_pressure",
        "toxic_content",
        "cheat_online_game",
        "unsafe_real_world_instruction",
        "military_operationalization",
    }

    def validate(
        self,
        world: WorldGraph,
        event: Event,
        rule_kernel: RuleKernel | None = None,
    ) -> OAKReport:
        reasons: list[str] = []

        coherent = self._has_known_actors(world, event, reasons)
        if rule_kernel is not None:
            passed, failures = rule_kernel.evaluate(world, event)
            coherent = coherent and passed
            reasons.extend(failures)

        fair = bool(event.payload.get("fair", True))
        fun = bool(event.payload.get("fun", True))
        safe = self._is_safe(event, reasons)
        testable = "metric" in event.payload or "expected_signal" in event.payload
        non_exploitative = self._is_non_exploitative(event, reasons)
        agency = float(event.payload.get("agency", 1.0))

        if not fair:
            reasons.append("Event marked unfair.")
        if not fun:
            reasons.append("Event marked not fun.")
        if not testable:
            reasons.append("Event lacks metric or expected_signal.")
        if agency < 0.5:
            reasons.append("Player agency below OAK threshold.")

        return OAKReport(
            coherent=coherent,
            fair=fair,
            fun=fun,
            safe=safe,
            testable=testable,
            non_exploitative=non_exploitative,
            agency=agency,
            reasons=reasons,
            metrics={
                "actor_count": len(event.actors),
                "target_count": len(event.targets),
                "payload_keys": sorted(event.payload.keys()),
            },
        )

    def _has_known_actors(self, world: WorldGraph, event: Event, reasons: list[str]) -> bool:
        ok = True
        for entity_id in event.actors + event.targets:
            if entity_id not in world.entities:
                reasons.append(f"Unknown event entity: {entity_id}")
                ok = False
        return ok

    def _is_safe(self, event: Event, reasons: list[str]) -> bool:
        flags = set(event.payload.get("risk_flags", []))
        unsafe = flags & self.banned_payload_flags
        if unsafe:
            reasons.append(f"Unsafe payload flags: {sorted(unsafe)}")
            return False
        return True

    def _is_non_exploitative(self, event: Event, reasons: list[str]) -> bool:
        flags = set(event.payload.get("risk_flags", []))
        exploit_flags = {"dark_pattern", "predatory_loot_box", "addiction_pressure"}
        found = flags & exploit_flags
        if found:
            reasons.append(f"Exploitative design flags: {sorted(found)}")
            return False
        return True
