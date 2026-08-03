from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List

@dataclass
class ModuleManifest:
    id: str
    name: str
    path: str
    family: str
    capabilities: List[str] = field(default_factory=list)
    oak_status: str = "unknown"
    risk: float = 0.5
    utility: float = 0.5
    fertility: float = 0.5
    verifiability: float = 0.5
    compression: float = 0.5
    complexity: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)

    def score_omega(self) -> float:
        return (self.utility * self.fertility * self.verifiability * self.compression) / (1 + self.risk + self.complexity)

    def to_dict(self):
        d = asdict(self)
        d["score_omega"] = self.score_omega()
        return d

@dataclass
class ProbeResult:
    module_id: str
    status: str
    duration_s: float
    checks: Dict[str, bool]
    metrics: Dict[str, int | float | str]
    risks: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
