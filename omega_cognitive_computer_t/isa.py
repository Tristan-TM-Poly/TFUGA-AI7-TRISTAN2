from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from .cir import CognitiveState


class Opcode(str, Enum):
    DECOMPOSE = "DECOMPOSE"
    EXPAND = "EXPAND"
    COMPRESS = "COMPRESS"
    ZOOM = "ZOOM"
    DEZOOM = "DEZOOM"
    REPRESENT = "REPRESENT"
    INVARIANTS = "INVARIANTS"
    GENERALIZE = "GENERALIZE"
    SPECIALIZE = "SPECIALIZE"
    TRANSFER = "TRANSFER"
    MERGE = "MERGE"
    SPLIT = "SPLIT"
    PRUNE = "PRUNE"
    ATTACK = "ATTACK"
    COUNTER = "COUNTER"
    CONTRADICT = "CONTRADICT"
    RESIDUAL = "RESIDUAL"
    META = "META"
    ABSTRACT = "ABSTRACT"
    CONCRETIZE = "CONCRETIZE"
    INTERVENE = "INTERVENE"
    COUNTERFACTUAL = "COUNTERFACTUAL"
    PROVE = "PROVE"
    SIMULATE = "SIMULATE"
    MEASURE = "MEASURE"
    BENCHMARK = "BENCHMARK"
    OAK = "OAK"
    REMEMBER = "REMEMBER"
    FORGET = "FORGET"
    CRYSTALLIZE = "CRYSTALLIZE"


ALIASES = {
    "EXP": Opcode.EXPAND,
    "COMP": Opcode.COMPRESS,
    "REP": Opcode.REPRESENT,
    "INV": Opcode.INVARIANTS,
    "GEN": Opcode.GENERALIZE,
    "RES": Opcode.RESIDUAL,
    "SIM": Opcode.SIMULATE,
    "CRYST": Opcode.CRYSTALLIZE,
}


@dataclass(frozen=True)
class Instruction:
    opcode: Opcode
    args: tuple[str, ...] = ()
    options: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        suffix = " " + " ".join(self.args) if self.args else ""
        return f"{self.opcode.value}{suffix}"


@dataclass(frozen=True)
class Program:
    name: str
    instructions: tuple[Instruction, ...]
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def opcodes(self) -> tuple[Opcode, ...]:
        return tuple(i.opcode for i in self.instructions)

    def without_indices(self, indices: set[int]) -> "Program":
        return Program(
            name=f"{self.name}:ablated",
            instructions=tuple(i for idx, i in enumerate(self.instructions) if idx not in indices),
            tags=self.tags,
            metadata=dict(self.metadata),
        )


Executor = Callable[[CognitiveState, Instruction, Any], CognitiveState]


@dataclass(frozen=True)
class OperatorSpec:
    opcode: Opcode
    category: str
    description: str
    dual: Opcode | None = None
    base_cost: float = 1.0
    failure_modes: tuple[str, ...] = ()
    executor: Executor | None = None


class OperatorRegistry:
    def __init__(self) -> None:
        self._specs: dict[Opcode, OperatorSpec] = {}

    def register(self, spec: OperatorSpec, *, replace: bool = False) -> None:
        if spec.opcode in self._specs and not replace:
            raise KeyError(f"Operator already registered: {spec.opcode.value}")
        self._specs[spec.opcode] = spec

    def get(self, opcode: Opcode) -> OperatorSpec:
        try:
            return self._specs[opcode]
        except KeyError as exc:
            raise KeyError(f"Unregistered cognitive opcode: {opcode.value}") from exc

    def list(self, category: str | None = None) -> tuple[OperatorSpec, ...]:
        specs = tuple(sorted(self._specs.values(), key=lambda s: s.opcode.value))
        return specs if category is None else tuple(s for s in specs if s.category == category)

    def dual(self, opcode: Opcode) -> Opcode | None:
        return self.get(opcode).dual

    def categories(self) -> tuple[str, ...]:
        return tuple(sorted({s.category for s in self._specs.values()}))


def default_registry() -> OperatorRegistry:
    r = OperatorRegistry()
    specs = [
        (Opcode.DECOMPOSE, "structure", "Split a problem into explicit subgoals.", Opcode.MERGE, 0.6),
        (Opcode.EXPAND, "generation", "Generate explicit candidate variations.", Opcode.COMPRESS, 0.8),
        (Opcode.COMPRESS, "compression", "Reduce duplication and surface a smaller kernel.", Opcode.EXPAND, 0.6),
        (Opcode.ZOOM, "representation", "Move to a finer scale.", Opcode.DEZOOM, 0.3),
        (Opcode.DEZOOM, "representation", "Move to a coarser scale.", Opcode.ZOOM, 0.3),
        (Opcode.REPRESENT, "representation", "Add or switch a representation.", None, 0.5),
        (Opcode.INVARIANTS, "structure", "Create obligations to identify properties stable under transformations.", None, 0.8),
        (Opcode.GENERALIZE, "generation", "Lift a statement into a wider family.", Opcode.SPECIALIZE, 0.7),
        (Opcode.SPECIALIZE, "structure", "Restrict a statement to a concrete case.", Opcode.GENERALIZE, 0.5),
        (Opcode.TRANSFER, "generation", "Propose a cross-domain structural transfer with proof obligations.", None, 0.9),
        (Opcode.MERGE, "compression", "Merge compatible branches without erasing provenance.", Opcode.SPLIT, 0.7),
        (Opcode.SPLIT, "structure", "Separate a mixed object into branches.", Opcode.MERGE, 0.6),
        (Opcode.PRUNE, "compression", "Bound branch explosion using explicit limits.", Opcode.EXPAND, 0.4),
        (Opcode.ATTACK, "critique", "Generate falsification obligations.", None, 0.8),
        (Opcode.COUNTER, "critique", "Generate explicit rival hypotheses.", None, 0.7),
        (Opcode.CONTRADICT, "critique", "Surface contradictory claims or assumptions.", None, 0.7),
        (Opcode.RESIDUAL, "learning", "Treat unexplained residuals as candidate structure.", None, 0.8),
        (Opcode.META, "meta", "Inspect or modify the reasoning strategy itself.", None, 1.1),
        (Opcode.ABSTRACT, "representation", "Move from instances to an abstract schema.", Opcode.CONCRETIZE, 0.6),
        (Opcode.CONCRETIZE, "representation", "Ground an abstract schema in a testable instance.", Opcode.ABSTRACT, 0.6),
        (Opcode.INTERVENE, "causal", "Specify an intervention rather than an observation.", None, 1.0),
        (Opcode.COUNTERFACTUAL, "causal", "Create a counterfactual test obligation.", None, 1.0),
        (Opcode.PROVE, "validation", "Create or execute a proof obligation; never self-certifies truth.", None, 2.5),
        (Opcode.SIMULATE, "validation", "Create or execute a simulation obligation.", Opcode.MEASURE, 1.6),
        (Opcode.MEASURE, "validation", "Request empirical measurement or observation.", Opcode.SIMULATE, 1.4),
        (Opcode.BENCHMARK, "validation", "Compare against a declared baseline.", None, 1.4),
        (Opcode.OAK, "validation", "Audit evidence, counter-hypotheses, uncertainty and limitations.", None, 1.0),
        (Opcode.REMEMBER, "learning", "Write a successful strategy/result to positive memory.", Opcode.FORGET, 0.3),
        (Opcode.FORGET, "learning", "Remove or de-prioritize a memory record by policy.", Opcode.REMEMBER, 0.3),
        (Opcode.CRYSTALLIZE, "production", "Gate a result into a concrete artifact contract.", None, 1.2),
    ]
    for opcode, category, desc, dual, cost in specs:
        r.register(OperatorSpec(opcode, category, desc, dual=dual, base_cost=cost))
    return r
