from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class PhaseNode:
    phase_id: str
    label: str
    order_parameters: Mapping[str, float] = field(default_factory=dict)
    evidence_status: str = "MODEL"

    def __post_init__(self) -> None:
        if not self.phase_id or not self.label:
            raise ValueError("phase_id and label are required")


@dataclass(frozen=True)
class TransitionHyperedge:
    transition_id: str
    source_phase_ids: tuple[str, ...]
    target_phase_ids: tuple[str, ...]
    mechanism: str
    control_parameters: Mapping[str, float] = field(default_factory=dict)
    evidence_status: str = "MODEL"

    def __post_init__(self) -> None:
        if not self.transition_id:
            raise ValueError("transition_id is required")
        if not self.source_phase_ids or not self.target_phase_ids:
            raise ValueError("a transition needs source and target phases")


class PhaseHypergraphAtlas:
    """Small machine-readable atlas for phase/transition evidence graphs."""

    def __init__(self) -> None:
        self._phases: dict[str, PhaseNode] = {}
        self._transitions: dict[str, TransitionHyperedge] = {}

    @property
    def phases(self) -> tuple[PhaseNode, ...]:
        return tuple(self._phases.values())

    @property
    def transitions(self) -> tuple[TransitionHyperedge, ...]:
        return tuple(self._transitions.values())

    def add_phase(self, phase: PhaseNode) -> None:
        if phase.phase_id in self._phases:
            raise ValueError(f"duplicate phase_id: {phase.phase_id}")
        self._phases[phase.phase_id] = phase

    def add_transition(self, transition: TransitionHyperedge) -> None:
        if transition.transition_id in self._transitions:
            raise ValueError(f"duplicate transition_id: {transition.transition_id}")
        known = set(self._phases)
        referenced = set(transition.source_phase_ids) | set(transition.target_phase_ids)
        missing = referenced - known
        if missing:
            raise ValueError(f"transition references unknown phases: {sorted(missing)}")
        self._transitions[transition.transition_id] = transition

    def to_dict(self) -> dict[str, object]:
        return {
            "phases": [
                {
                    "phase_id": p.phase_id,
                    "label": p.label,
                    "order_parameters": dict(p.order_parameters),
                    "evidence_status": p.evidence_status,
                }
                for p in self.phases
            ],
            "transitions": [
                {
                    "transition_id": t.transition_id,
                    "source_phase_ids": list(t.source_phase_ids),
                    "target_phase_ids": list(t.target_phase_ids),
                    "mechanism": t.mechanism,
                    "control_parameters": dict(t.control_parameters),
                    "evidence_status": t.evidence_status,
                }
                for t in self.transitions
            ],
        }
