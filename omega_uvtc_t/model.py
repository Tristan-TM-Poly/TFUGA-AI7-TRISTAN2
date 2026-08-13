"""Ω-UVTC-T R0.1 typed Universal Transformation IR.

The 16 primitives are the semantic ISA for this prototype. They are not claimed
to be mathematically minimal or irreducible.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def stable_digest(value: Any) -> str:
    return sha256(stable_json(value).encode("utf-8")).hexdigest()


class Kernel(str, Enum):
    TRANSFORMATION = "TransformationKernel"
    EVIDENCE = "EvidenceKernel"
    MEMORY = "MemoryKernel"
    OPTIMIZATION = "OptimizationKernel"
    PERMISSION = "PermissionKernel"
    CRYSTALLIZATION = "CrystallizationKernel"


class Primitive(str, Enum):
    STATE = "STATE"
    GOAL = "GOAL"
    REPRESENT = "REPRESENT"
    SEARCH = "SEARCH"
    TRANSFORM = "TRANSFORM"
    COMPOSE = "COMPOSE"
    BRANCH = "BRANCH"
    MEASURE = "MEASURE"
    FALSIFY = "FALSIFY"
    PROVE = "PROVE"
    OAK = "OAK"
    MEMORIZE = "MEMORIZE"
    RESIDUAL = "RESIDUAL"
    CRYSTALLIZE = "CRYSTALLIZE"
    LEARN_PRIMITIVE = "LEARN_PRIMITIVE"
    ALLOCATE = "ALLOCATE"


PRIMITIVE_KERNEL = {
    Primitive.STATE: Kernel.TRANSFORMATION,
    Primitive.GOAL: Kernel.TRANSFORMATION,
    Primitive.TRANSFORM: Kernel.TRANSFORMATION,
    Primitive.COMPOSE: Kernel.TRANSFORMATION,
    Primitive.BRANCH: Kernel.TRANSFORMATION,
    Primitive.MEASURE: Kernel.EVIDENCE,
    Primitive.FALSIFY: Kernel.EVIDENCE,
    Primitive.PROVE: Kernel.EVIDENCE,
    Primitive.OAK: Kernel.EVIDENCE,
    Primitive.SEARCH: Kernel.MEMORY,
    Primitive.MEMORIZE: Kernel.MEMORY,
    Primitive.RESIDUAL: Kernel.MEMORY,
    Primitive.REPRESENT: Kernel.OPTIMIZATION,
    Primitive.LEARN_PRIMITIVE: Kernel.OPTIMIZATION,
    Primitive.ALLOCATE: Kernel.PERMISSION,
    Primitive.CRYSTALLIZE: Kernel.CRYSTALLIZATION,
}


class Effect(str, Enum):
    READ = "read"
    WRITE = "write"
    NETWORK = "network"
    COMPUTE = "compute"
    EXTERNAL_MUTATION = "external_mutation"
    IRREVERSIBLE = "irreversible"


class MemoryClass(str, Enum):
    M_PLUS = "M+"
    M_MINUS = "M-"
    M_QUERY = "M?"
    COLD = "COLD"


@dataclass(frozen=True, slots=True)
class EpistemicState:
    state_id: str
    knowledge_hashes: tuple[str, ...] = ()
    goals: tuple[str, ...] = ()
    memory_refs: tuple[str, ...] = ()
    uncertainty: float = 1.0
    artifacts: tuple[str, ...] = ()
    residuals: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("uncertainty must be in [0,1]")

    @property
    def fingerprint(self) -> str:
        return stable_digest(asdict(self))


@dataclass(frozen=True, slots=True)
class Goal:
    goal_id: str
    target: str
    success_contracts: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()

    @property
    def fingerprint(self) -> str:
        return stable_digest(asdict(self))


@dataclass(frozen=True, slots=True)
class UTIRInstruction:
    primitive: Primitive
    args: Mapping[str, Any] = field(default_factory=dict)
    effects: tuple[Effect, ...] = ()
    predicted_verified_gain: float | None = None
    gain_uncertainty: float = 0.0
    cost: float = 0.0
    risk: float = 0.0
    independent_replication: bool = False
    deterministic: bool = True

    def __post_init__(self) -> None:
        if self.gain_uncertainty < 0 or self.cost < 0 or self.risk < 0:
            raise ValueError("uncertainty/cost/risk must be non-negative")

    @property
    def kernel(self) -> Kernel:
        return PRIMITIVE_KERNEL[self.primitive]

    @property
    def fingerprint(self) -> str:
        payload = {
            "primitive": self.primitive.value,
            "args": dict(self.args),
            "effects": [x.value for x in self.effects],
            "independent_replication": self.independent_replication,
            "deterministic": self.deterministic,
        }
        return stable_digest(payload)


@dataclass(frozen=True, slots=True)
class UTIRProgram:
    program_id: str
    instructions: tuple[UTIRInstruction, ...]
    source_intent: str = ""
    schema_version: str = "uvtc-utir-r0.1"

    @property
    def fingerprint(self) -> str:
        return stable_digest({
            "schema_version": self.schema_version,
            "program_id": self.program_id,
            "source_intent": self.source_intent,
            "instructions": [i.fingerprint for i in self.instructions],
        })

    def count(self, primitive: Primitive) -> int:
        return sum(i.primitive == primitive for i in self.instructions)


def instruction(primitive: Primitive | str, **kwargs: Any) -> UTIRInstruction:
    p = primitive if isinstance(primitive, Primitive) else Primitive(primitive)
    return UTIRInstruction(primitive=p, **kwargs)
