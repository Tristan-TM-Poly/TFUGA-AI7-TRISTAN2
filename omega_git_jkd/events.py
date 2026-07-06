"""M- event registry for Git workflow friction."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GitEvent:
    id: str
    pattern: str
    adaptation: str
    result: str


def default_events() -> tuple[GitEvent, ...]:
    return (
        GitEvent(
            id="GJKD-001",
            pattern="large multi-role file failed to land",
            adaptation="split into small single-role files",
            result="smaller modules landed",
        ),
        GitEvent(
            id="GJKD-002",
            pattern="central config edit did not land",
            adaptation="add a parallel entrypoint instead",
            result="module entrypoint landed",
        ),
        GitEvent(
            id="GJKD-003",
            pattern="same-repo PR option rejected",
            adaptation="omit option that only applies elsewhere",
            result="PR metadata update landed",
        ),
    )


def summarize(events: tuple[GitEvent, ...]) -> dict[str, int]:
    return {
        "events": len(events),
        "adaptations": len({event.adaptation for event in events}),
        "successful_results": sum(1 for event in events if "landed" in event.result),
    }
