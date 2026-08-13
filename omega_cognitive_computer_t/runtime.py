from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .cir import CognitiveState
from .crystallization import validate_crystallization
from .isa import Instruction, Opcode, OperatorRegistry, Program, default_registry
from .memory import CognitiveMemory


Hook = Callable[[CognitiveState, Instruction, "RuntimeContext"], CognitiveState]


@dataclass
class RuntimeContext:
    budget: float = 30.0
    branch_limit: int = 16
    max_steps: int = 128
    stagnation_limit: int = 3
    max_meta_depth: int = 3
    hooks: dict[Opcode, Hook] = field(default_factory=dict)
    memory: CognitiveMemory | None = None
    problem_text: str = ""


@dataclass(frozen=True)
class CognitiveTransaction:
    step: int
    instruction: str
    before_fingerprint: str
    after_fingerprint: str
    cost: float
    rolled_back: bool
    note: str = ""


@dataclass
class ExecutionResult:
    state: CognitiveState
    trace: list[CognitiveTransaction]
    spent: float
    halted_reason: str
    injected: tuple[str, ...] = ()


class CognitiveRuntime:
    def __init__(self, registry: OperatorRegistry | None = None) -> None:
        self.registry = registry or default_registry()

    def run(self, program: Program, state: CognitiveState, *, context: RuntimeContext | None = None) -> ExecutionResult:
        ctx = context or RuntimeContext()
        current = state.clone()
        queue = list(program.instructions)
        trace: list[CognitiveTransaction] = []
        spent = 0.0
        stagnation = 0
        injected: list[str] = []
        jit_fired = False
        reason = "completed"

        while queue and len(trace) < ctx.max_steps:
            inst = queue.pop(0)
            spec = self.registry.get(inst.opcode)
            if spent + spec.base_cost > ctx.budget:
                reason = "budget_exhausted"
                break
            before = current.clone()
            before_fp = before.fingerprint()
            rolled_back = False
            note = ""
            try:
                hook = ctx.hooks.get(inst.opcode) or spec.executor
                current = hook(current, inst, ctx) if hook else self._builtin(current, inst, ctx)
                if not isinstance(current, CognitiveState):
                    raise TypeError("Operator hook must return CognitiveState")
            except Exception as exc:
                current = before
                rolled_back = True
                note = f"rollback:{type(exc).__name__}:{exc}"
            after_fp = current.fingerprint()
            spent += spec.base_cost
            trace.append(CognitiveTransaction(len(trace), str(inst), before_fp, after_fp, spec.base_cost, rolled_back, note))

            if after_fp == before_fp:
                stagnation += 1
            else:
                stagnation = 0

            if len(current.hypotheses) > ctx.branch_limit and (not queue or queue[0].opcode != Opcode.PRUNE):
                queue.insert(0, Instruction(Opcode.PRUNE, (str(ctx.branch_limit),)))
                injected.append("PRUNE:branch_limit")

            if stagnation >= ctx.stagnation_limit and not jit_fired:
                queue.insert(0, Instruction(Opcode.ATTACK, ("jit-stagnation",)))
                queue.insert(0, Instruction(Opcode.REPRESENT, ("alternative",)))
                injected.extend(("REPRESENT:stagnation", "ATTACK:stagnation"))
                jit_fired = True
                stagnation = 0

        if queue and len(trace) >= ctx.max_steps:
            reason = "max_steps"
        return ExecutionResult(current, trace, spent, reason, tuple(injected))

    def _builtin(self, state: CognitiveState, inst: Instruction, ctx: RuntimeContext) -> CognitiveState:
        s = state.clone()
        op = inst.opcode
        arg0 = inst.args[0] if inst.args else ""
        obligations = s.metadata.setdefault("obligations", [])

        if op == Opcode.DECOMPOSE:
            if s.goals:
                s.metadata["subgoals"] = [f"decompose:{g}" for g in s.goals]
        elif op == Opcode.REPRESENT:
            name = arg0 or f"representation_{len(s.representations)+1}"
            s.representations.setdefault(name, {"status": "requested", "source": "cognitive_isa"})
        elif op == Opcode.ZOOM:
            s.scale += 1
            s.metadata.setdefault("scale_trace", []).append({"direction": "zoom", "target": arg0 or None, "scale": s.scale})
        elif op == Opcode.DEZOOM:
            s.scale -= 1
            s.metadata.setdefault("scale_trace", []).append({"direction": "dezoom", "target": arg0 or None, "scale": s.scale})
        elif op == Opcode.EXPAND:
            source = s.hypotheses or s.goals or ["problem"]
            for h in list(source):
                s.hypotheses.extend((f"variant(inverse): {h}", f"variant(relax): {h}", f"variant/lift: {h}"))
        elif op in (Opcode.COMPRESS, Opcode.MERGE):
            s.deduplicate()
            s.metadata["compression_kernel"] = {"hypotheses": len(s.hypotheses), "assumptions": len(s.assumptions), "evidence": len(s.evidence)}
        elif op == Opcode.PRUNE:
            limit = int(arg0) if arg0.isdigit() else ctx.branch_limit
            s.hypotheses = s.hypotheses[:limit]
            s.metadata.setdefault("pruning", []).append({"limit": limit, "policy": "stable_first_v0"})
        elif op == Opcode.INVARIANTS:
            obligations.append("Identify candidate invariants and specify transformations under which each must remain stable.")
        elif op == Opcode.GENERALIZE:
            for h in list(s.hypotheses):
                s.hypotheses.append(f"generalization-candidate: {h}")
        elif op == Opcode.SPECIALIZE:
            obligations.append("Instantiate at least one boundary/simple case and test whether the claim survives.")
        elif op == Opcode.TRANSFER:
            obligations.extend(("State source/target structural mapping.", "Check units, causal structure, boundaries and invariants before accepting analogy."))
        elif op == Opcode.SPLIT:
            s.metadata.setdefault("branches", []).extend(s.goals or s.hypotheses[:2])
        elif op == Opcode.ATTACK:
            target = s.hypotheses or s.goals
            obligations.extend(f"falsify: {h}" for h in target)
        elif op == Opcode.COUNTER:
            existing = set(s.metadata.setdefault("counter_hypotheses", []))
            for h in s.hypotheses or s.goals:
                existing.add(f"counter: not({h})")
            s.metadata["counter_hypotheses"] = sorted(existing)
        elif op == Opcode.CONTRADICT:
            obligations.append("Find the smallest incompatible claim/assumption pair; do not average contradictions away.")
        elif op == Opcode.RESIDUAL:
            obligations.append("Model residuals explicitly; test whether another representation compresses them better than noise baselines.")
        elif op == Opcode.META:
            depth = int(s.metadata.get("meta_depth", 0)) + 1
            if depth > ctx.max_meta_depth:
                raise RuntimeError("meta-depth gate exceeded")
            s.metadata["meta_depth"] = depth
        elif op == Opcode.ABSTRACT:
            obligations.append("Extract a schema that preserves declared invariants across instances.")
        elif op == Opcode.CONCRETIZE:
            obligations.append("Produce a concrete falsifiable instance with inputs, outputs and success criteria.")
        elif op == Opcode.INTERVENE:
            obligations.append(f"intervention: do({arg0 or 'variable'} := alternative) and specify confounders")
        elif op == Opcode.COUNTERFACTUAL:
            obligations.append("Specify what should be observed if the focal hypothesis were false while alternatives were held explicit.")
        elif op == Opcode.PROVE:
            obligations.append("proof: produce a replayable certificate/kernel check; heuristic reasoning is not a proof")
        elif op == Opcode.SIMULATE:
            obligations.append("simulation: declare model, units, boundary conditions, solver, error and baseline")
        elif op == Opcode.MEASURE:
            obligations.append("measurement: declare instrument/data source, calibration, uncertainty and observable")
        elif op == Opcode.BENCHMARK:
            obligations.append("benchmark: declare baseline, dataset/cases, metric and acceptance threshold before reading results")
        elif op == Opcode.OAK:
            blockers: list[str] = []
            if s.hypotheses and not s.evidence:
                blockers.append("evidence_required")
            if s.hypotheses and not s.metadata.get("counter_hypotheses"):
                blockers.append("counter_hypothesis_required")
            if any(not 0.0 <= float(v) <= 1.0 for v in s.uncertainty.values()):
                blockers.append("invalid_uncertainty_range")
            s.metadata["oak"] = {"status": "blocked" if blockers else "review_ready", "blockers": blockers, "note": "review_ready is not proof/truth"}
        elif op == Opcode.REMEMBER:
            if ctx.memory is None:
                obligations.append("memory: no CognitiveMemory attached; nothing persisted")
        elif op == Opcode.FORGET:
            obligations.append("forget: requires an explicit retention policy; automatic deletion is disabled")
        elif op == Opcode.CRYSTALLIZE:
            payload = s.metadata.get("crystallization", {})
            report = validate_crystallization(payload)
            s.metadata["crystallization_gate"] = {"is_clear": report.is_clear, "missing": list(report.missing)}
            if report.record:
                artifact = report.record.to_dict()
                if artifact not in s.artifacts:
                    s.artifacts.append(artifact)
        return s
