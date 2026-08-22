from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, Tuple


@dataclass(frozen=True)
class MactBook0:
    version: str
    primitives: Tuple[str, ...]
    hard_invariants: Tuple[str, ...]
    default_weights: Dict[str, float]

    def digest(self) -> str:
        payload = asdict(self)
        payload["primitives"] = list(self.primitives)
        payload["hard_invariants"] = list(self.hard_invariants)
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


DEFAULT_BOOK0 = MactBook0(
    version="1.0.0",
    primitives=("OBSERVE", "REPRESENT", "GENERATE", "COUNTERGENERATE", "VERIFY", "SELECT", "DISTILL", "REGENERATE"),
    hard_invariants=("Generated != Verified", "Simulation != Reality", "Capability != Authority", "Generator != Judge", "NO_ACTION and GO_MIN are candidates", "Minimum != Brittle", "Deletion requires reconstructibility or explicit authority", "External action performed == false in planning kernel"),
    default_weights={"action": 1.0, "compute": 1.0, "memory_persistent": 1.0, "observation": 1.0, "human_attention": 2.0, "time": 1.0, "persistent_complexity": 2.0, "risk": 4.0, "irreversibility": 5.0},
)


def ablation_candidates(book0: MactBook0 = DEFAULT_BOOK0) -> Iterable[MactBook0]:
    """Yield candidate smaller kernels. No ablated kernel is self-promoted."""
    for i in range(len(book0.primitives)):
        yield MactBook0(version=book0.version + f"-ablate-{i}", primitives=book0.primitives[:i] + book0.primitives[i + 1 :], hard_invariants=book0.hard_invariants, default_weights=book0.default_weights)
