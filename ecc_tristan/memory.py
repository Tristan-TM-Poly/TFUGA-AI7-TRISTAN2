"""M⁻ memory for ECC failures and uncertain corrections."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class MMinusEvent:
    kind: str
    channel: str
    payload: Dict[str, Any]
    lesson: str


def append_event(path: str | Path, event: MMinusEvent) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")


def event_from_failed_decode(channel: str, received: list[int], syndrome: tuple[int, ...], reason: str) -> MMinusEvent:
    return MMinusEvent(
        kind="failed_or_uncertain_decode",
        channel=channel,
        payload={"received": received, "syndrome": list(syndrome), "reason": reason},
        lesson="Do not promote correction to canon when OAK rejects or trust is low.",
    )
