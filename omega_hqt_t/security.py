from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable

SENSITIVITY_ORDER = {"public": 0, "aggregated": 1, "restricted": 2, "critical": 3}
FORBIDDEN_TERMS = (
    "scada credential", "relay setting", "protection setting", "control room password",
    "exploit", "bypass authentication", "live switching command", "operational topology",
)

@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    level: str
    reasons: tuple[str, ...]
    required_controls: tuple[str, ...]
    def to_dict(self): return asdict(self)

def classify_text(text: str) -> str:
    lowered=text.casefold()
    if any(term in lowered for term in FORBIDDEN_TERMS): return "critical"
    if any(term in lowered for term in ("precise vulnerability", "exact asset location", "customer interval data")): return "restricted"
    if any(term in lowered for term in ("regional aggregate", "synthetic", "open data")): return "aggregated"
    return "public"

def safety_gate(*, requested_level: str, content: str, public_data_only: bool = True) -> GateDecision:
    detected=classify_text(content)
    level=max((requested_level, detected), key=lambda x: SENSITIVITY_ORDER.get(x, 99))
    reasons=[]; controls=[]
    if level == "critical":
        reasons.append("critical-infrastructure operational detail is outside the public/synthetic kernel")
        controls.extend(("official authorization", "isolated environment", "human operational authority"))
        return GateDecision(False, level, tuple(reasons), tuple(controls))
    if public_data_only and level == "restricted":
        reasons.append("restricted composite information is blocked in public-data-only mode")
        controls.extend(("aggregation", "security review", "need-to-know access"))
        return GateDecision(False, level, tuple(reasons), tuple(controls))
    if level == "aggregated": controls.append("preserve aggregation and provenance")
    else: controls.append("retain source and license metadata")
    return GateDecision(True, level, tuple(reasons), tuple(controls))

def assert_public_safe(texts: Iterable[str]) -> None:
    for text in texts:
        decision=safety_gate(requested_level="public", content=text, public_data_only=True)
        if not decision.allowed:
            raise ValueError("SafetyGate blocked content: " + "; ".join(decision.reasons))
