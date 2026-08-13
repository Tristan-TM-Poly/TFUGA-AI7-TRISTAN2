"""GO MAX / GO MIN cognitive superoptimizer."""
from __future__ import annotations

from dataclasses import dataclass, replace
from math import inf
from .model import Effect, Primitive, UTIRInstruction, UTIRProgram

PROTECTED = {
    Primitive.STATE, Primitive.GOAL, Primitive.MEASURE, Primitive.FALSIFY,
    Primitive.PROVE, Primitive.OAK, Primitive.MEMORIZE, Primitive.CRYSTALLIZE,
}
ELIDABLE_EFFECTS = {Effect.READ, Effect.COMPUTE}

@dataclass(frozen=True, slots=True)
class OptimizationEvent:
    pass_name: str
    index: int
    primitive: str
    reason: str

@dataclass(frozen=True, slots=True)
class OptimizationReport:
    before_count: int
    after_count: int
    events: tuple[OptimizationEvent, ...]
    program: UTIRProgram

def _dedup(program: UTIRProgram) -> tuple[list[UTIRInstruction], list[OptimizationEvent]]:
    out: list[UTIRInstruction] = []
    events: list[OptimizationEvent] = []
    seen: set[str] = set()
    for idx, inst in enumerate(program.instructions):
        reusable = inst.deterministic and not inst.independent_replication and all(effect in ELIDABLE_EFFECTS for effect in inst.effects)
        if reusable and inst.fingerprint in seen:
            events.append(OptimizationEvent("common_subproblem_elimination", idx, inst.primitive.value, "identical deterministic subproblem already available"))
            continue
        out.append(inst)
        if reusable:
            seen.add(inst.fingerprint)
    return out, events

def _peephole(items: list[UTIRInstruction]) -> tuple[list[UTIRInstruction], list[OptimizationEvent]]:
    out: list[UTIRInstruction] = []
    events: list[OptimizationEvent] = []
    for idx, inst in enumerate(items):
        if out and inst.primitive == Primitive.REPRESENT and out[-1].primitive == Primitive.REPRESENT and inst.args == out[-1].args:
            events.append(OptimizationEvent("peephole", idx, inst.primitive.value, "consecutive identical representation removed"))
            continue
        out.append(inst)
    return out, events

def _safe_prune(items: list[UTIRInstruction], z: float = 2.0) -> tuple[list[UTIRInstruction], list[OptimizationEvent]]:
    out: list[UTIRInstruction] = []
    events: list[OptimizationEvent] = []
    for idx, inst in enumerate(items):
        gain = inst.predicted_verified_gain
        if gain is None or inst.primitive in PROTECTED or inst.independent_replication or any(effect not in ELIDABLE_EFFECTS for effect in inst.effects):
            out.append(inst)
            continue
        upper = gain + z * inst.gain_uncertainty
        burden = inst.cost + inst.risk
        if upper <= burden:
            events.append(OptimizationEvent("safe_speculative_pruning", idx, inst.primitive.value, f"optimistic_gain={upper:.6g} <= burden={burden:.6g}"))
            continue
        out.append(inst)
    return out, events

def superoptimize(program: UTIRProgram) -> OptimizationReport:
    """Optimize structure only. Independent replication and non-elidable side effects are preserved."""
    a, e1 = _dedup(program)
    b, e2 = _peephole(a)
    c, e3 = _safe_prune(b)
    optimized = replace(program, instructions=tuple(c))
    return OptimizationReport(len(program.instructions), len(c), tuple(e1 + e2 + e3), optimized)

@dataclass(frozen=True, slots=True)
class PowerDensityInput:
    verified_frontier_gain: float
    reachable_value_gain: float
    compute_cost: float
    k0_complexity: float
    proof_debt: float
    uncertainty_debt: float
    risk: float

def power_density(x: PowerDensityInput) -> float:
    numer = x.verified_frontier_gain + x.reachable_value_gain
    denom = x.compute_cost + x.k0_complexity + x.proof_debt + x.uncertainty_debt + x.risk
    if min(numer, denom) < 0:
        raise ValueError("power-density inputs must be non-negative")
    return numer / denom if denom > 0 else (inf if numer > 0 else 0.0)
