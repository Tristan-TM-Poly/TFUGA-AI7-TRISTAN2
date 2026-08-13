from dataclasses import dataclass

@dataclass(frozen=True)
class OAKDecision:
    accepted: bool
    reason: str
