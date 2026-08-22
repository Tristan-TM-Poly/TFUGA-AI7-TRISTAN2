from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List
import json

from omega_morphogenesis import Residual

@dataclass(frozen=True)
class Evidence:
    id: str
    statement: str
    scope: float
    provenance: str
    independent: bool = False
    kind: str = "observation"
    uncertainty: float = 0.0

    def __post_init__(self):
        if not 0 <= self.scope <= 1:
            raise ValueError("evidence scope must be in [0,1]")
        if not 0 <= self.uncertainty <= 1:
            raise ValueError("uncertainty must be in [0,1]")

@dataclass(frozen=True)
class Claim:
    id: str
    statement: str
    scope: float
    epistemic_status: str
    evidence_ids: List[str] = field(default_factory=list)
    falsifiers: List[str] = field(default_factory=list)
    provenance: str = ""
    version: str = "0.1.0"

    def __post_init__(self):
        if not 0 <= self.scope <= 1:
            raise ValueError("claim scope must be in [0,1]")

@dataclass(frozen=True)
class Capability:
    id: str
    name: str
    verified: bool
    evidence_ids: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class Receipt:
    """Interchange receipt; execution governance remains in omega_morphogenesis."""
    id: str
    input_refs: List[str]
    transformation: str
    output_refs: List[str]
    evidence_refs: List[str]
    uncertainty: float
    authority: str
    provenance: str
    rollback: str
    version: str = "0.1.0"

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, indent=2)

@dataclass
class SystemGenome:
    id: str
    goal: str
    state: Dict[str, Any] = field(default_factory=dict)
    rules: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    actors: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    residuals: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=lambda: {"M+": [], "M-": []})

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
