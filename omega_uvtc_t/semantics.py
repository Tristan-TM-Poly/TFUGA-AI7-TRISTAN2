"""Abstract operational semantics for UTIR.

The interpreter checks ordering and evidence obligations only. It does not invoke
providers or treat a visited instruction as completed evidence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Iterable

from .model import Primitive, UTIRInstruction, UTIRProgram, stable_digest


@dataclass(frozen=True, slots=True)
class AbstractMachineState:
    cursor: int = 0
    state_declared: bool = False
    goal_declared: bool = False
    search_declared: bool = False
    transform_declared: bool = False
    measured: bool = False
    falsification_declared: bool = False
    oak_checked: bool = False
    memorized: bool = False
    crystallized: bool = False
    obligations: tuple[str, ...] = ()
    effects_seen: tuple[str, ...] = ()

    @property
    def fingerprint(self) -> str:
        return stable_digest(asdict(self))


@dataclass(frozen=True, slots=True)
class TransitionReceipt:
    index: int
    primitive: str
    before_hash: str
    after_hash: str
    status: str
    added_obligations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProgramExecutionReceipt:
    program_fingerprint: str
    initial_state_hash: str
    final_state_hash: str
    transitions: tuple[TransitionReceipt, ...]
    status: str
    blockers: tuple[str, ...]
    final_state: AbstractMachineState
    boundary: str = "local operational-contract result only; not scientific validation"


class OperationalSemanticsError(ValueError):
    pass


def _append_unique(items: tuple[str, ...], values: Iterable[str]) -> tuple[str, ...]:
    out = list(items)
    for value in values:
        if value not in out:
            out.append(value)
    return tuple(out)


def _step(state: AbstractMachineState, inst: UTIRInstruction) -> tuple[AbstractMachineState, tuple[str, ...]]:
    p = inst.primitive
    obligations: list[str] = []
    effects = _append_unique(state.effects_seen, (effect.value for effect in inst.effects))
    next_state = replace(state, cursor=state.cursor + 1, effects_seen=effects)

    if p == Primitive.STATE:
        if state.cursor != 0:
            raise OperationalSemanticsError("STATE must be first")
        next_state = replace(next_state, state_declared=True)
    elif p == Primitive.GOAL:
        if not state.state_declared:
            raise OperationalSemanticsError("GOAL requires STATE")
        next_state = replace(next_state, goal_declared=True)
    elif p == Primitive.SEARCH:
        if not state.goal_declared:
            raise OperationalSemanticsError("SEARCH requires GOAL")
        next_state = replace(next_state, search_declared=True)
        obligations.append("search_result_not_execution_evidence")
    elif p in {Primitive.REPRESENT, Primitive.ALLOCATE}:
        if not state.goal_declared:
            raise OperationalSemanticsError(f"{p.value} requires GOAL")
    elif p in {Primitive.TRANSFORM, Primitive.COMPOSE, Primitive.BRANCH}:
        if not state.goal_declared or not state.search_declared:
            raise OperationalSemanticsError(f"{p.value} requires GOAL + SEARCH")
        next_state = replace(next_state, transform_declared=True)
        if any(effect.value not in {"read", "compute"} for effect in inst.effects):
            obligations.append("elevated_effect_receipt_required")
        if any(effect.value == "compute" for effect in inst.effects):
            obligations.append("execution_receipt_required")
    elif p == Primitive.MEASURE:
        if not state.transform_declared:
            raise OperationalSemanticsError("MEASURE requires transformation")
        next_state = replace(next_state, measured=True)
        obligations.append("measurement_evidence_required")
    elif p == Primitive.FALSIFY:
        if not state.measured:
            raise OperationalSemanticsError("FALSIFY requires MEASURE")
        next_state = replace(next_state, falsification_declared=True)
        obligations.append("falsification_result_required")
    elif p == Primitive.PROVE:
        if not state.goal_declared:
            raise OperationalSemanticsError("PROVE requires GOAL")
        obligations.append("formal_proof_receipt_required")
    elif p == Primitive.OAK:
        if not state.measured or not state.falsification_declared:
            raise OperationalSemanticsError("OAK requires MEASURE + FALSIFY")
        next_state = replace(next_state, oak_checked=True)
        obligations.append("oak_gate_evidence_required")
    elif p == Primitive.RESIDUAL:
        if not state.oak_checked:
            raise OperationalSemanticsError("RESIDUAL requires OAK")
    elif p == Primitive.MEMORIZE:
        if not state.oak_checked:
            raise OperationalSemanticsError("MEMORIZE requires OAK")
        next_state = replace(next_state, memorized=True)
    elif p == Primitive.LEARN_PRIMITIVE:
        if not state.memorized:
            raise OperationalSemanticsError("LEARN_PRIMITIVE requires MEMORIZE")
        obligations.append("macro_promotion_benchmark_required")
    elif p == Primitive.CRYSTALLIZE:
        if not state.oak_checked:
            raise OperationalSemanticsError("CRYSTALLIZE requires OAK")
        next_state = replace(next_state, crystallized=True)
        obligations.append("goartifact_validation_required")
    else:
        raise OperationalSemanticsError(f"unsupported primitive: {p}")

    return replace(next_state, obligations=_append_unique(next_state.obligations, obligations)), tuple(obligations)


def execute_abstract(program: UTIRProgram, initial: AbstractMachineState | None = None) -> ProgramExecutionReceipt:
    state = initial or AbstractMachineState()
    initial_hash = state.fingerprint
    receipts: list[TransitionReceipt] = []
    blockers: list[str] = []
    for index, inst in enumerate(program.instructions):
        before = state.fingerprint
        try:
            state, added = _step(state, inst)
        except OperationalSemanticsError as exc:
            blockers.append(f"step:{index}:{inst.primitive.value}:{exc}")
            receipts.append(TransitionReceipt(index, inst.primitive.value, before, before, "BLOCK"))
            break
        receipts.append(TransitionReceipt(index, inst.primitive.value, before, state.fingerprint, "PASS", added))
    return ProgramExecutionReceipt(
        program_fingerprint=program.fingerprint,
        initial_state_hash=initial_hash,
        final_state_hash=state.fingerprint,
        transitions=tuple(receipts),
        status="PASS" if not blockers else "BLOCK",
        blockers=tuple(blockers),
        final_state=state,
    )
