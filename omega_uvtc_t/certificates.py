"""Structural certificates for GO MIN / superoptimizer transformations."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass

from .model import UTIRInstruction, UTIRProgram, stable_digest
from .optimizer import ELIDABLE_EFFECTS, OptimizationReport, PROTECTED


def _non_elidable(inst: UTIRInstruction) -> bool:
    return any(effect not in ELIDABLE_EFFECTS for effect in inst.effects)


@dataclass(frozen=True, slots=True)
class OptimizationCertificate:
    source_fingerprint: str
    optimized_fingerprint: str
    protected_trace_preserved: bool
    replication_multiset_preserved: bool
    non_elidable_effect_trace_preserved: bool
    event_count: int
    status: str
    semantic_equivalence_proven: bool = False
    boundary: str = "PASS is structural preservation, not general semantic equivalence"

    @property
    def fingerprint(self) -> str:
        return stable_digest(asdict(self))


def certify_optimization(source: UTIRProgram, report: OptimizationReport) -> OptimizationCertificate:
    optimized = report.program
    protected_source = tuple(i.fingerprint for i in source.instructions if i.primitive in PROTECTED)
    protected_target = tuple(i.fingerprint for i in optimized.instructions if i.primitive in PROTECTED)
    reps_source = Counter(i.fingerprint for i in source.instructions if i.independent_replication)
    reps_target = Counter(i.fingerprint for i in optimized.instructions if i.independent_replication)
    effects_source = tuple(i.fingerprint for i in source.instructions if _non_elidable(i))
    effects_target = tuple(i.fingerprint for i in optimized.instructions if _non_elidable(i))
    ok_protected = protected_source == protected_target
    ok_replication = reps_source == reps_target
    ok_effects = effects_source == effects_target
    return OptimizationCertificate(
        source_fingerprint=source.fingerprint,
        optimized_fingerprint=optimized.fingerprint,
        protected_trace_preserved=ok_protected,
        replication_multiset_preserved=ok_replication,
        non_elidable_effect_trace_preserved=ok_effects,
        event_count=len(report.events),
        status="PASS" if ok_protected and ok_replication and ok_effects else "BLOCK",
    )


def protected_observable_trace(program: UTIRProgram) -> tuple[str, ...]:
    return tuple(
        inst.fingerprint
        for inst in program.instructions
        if inst.primitive in PROTECTED or inst.independent_replication or _non_elidable(inst)
    )
