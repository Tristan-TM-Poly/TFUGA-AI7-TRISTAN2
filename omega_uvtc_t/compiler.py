"""Intent -> UTIR compilation and capability-plan bridge."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .model import Effect, Primitive, UTIRInstruction, UTIRProgram, instruction, stable_digest


@dataclass(frozen=True, slots=True)
class CompileRequest:
    intent: str
    goal: str
    formal: bool = False
    branching: bool = True
    learn: bool = True
    crystallize: bool = True
    max_compute_cost: float = 1.0
    max_risk: float = 1.0


def compile_intent(request: CompileRequest) -> UTIRProgram:
    """Compile intent to a deterministic review program; it does not execute tools."""
    ops: list[UTIRInstruction] = [
        instruction(Primitive.STATE, args={"source": "current"}),
        instruction(Primitive.GOAL, args={"target": request.goal}),
        instruction(Primitive.SEARCH, args={"policy": "reuse-before-create"}, effects=(Effect.READ,)),
        instruction(Primitive.REPRESENT, args={"policy": "lowest_verified_resolution_cost"}),
    ]
    if request.branching:
        ops.append(instruction(Primitive.BRANCH, args={"worlds": "bounded_counterfactual_ensemble"}, predicted_verified_gain=0.20, gain_uncertainty=0.10, cost=0.04))
    ops.extend([
        instruction(Primitive.ALLOCATE, args={"compute_budget": request.max_compute_cost, "risk_budget": request.max_risk}),
        instruction(Primitive.TRANSFORM, args={"operation": "solve_residual"}, effects=(Effect.COMPUTE,), predicted_verified_gain=0.5, gain_uncertainty=0.2, cost=0.1),
        instruction(Primitive.MEASURE, args={"residual": "vector"}),
        instruction(Primitive.FALSIFY, args={"policy": "minimal_decisive_test"}),
    ])
    if request.formal:
        ops.append(instruction(Primitive.PROVE, args={"backend": "formal_adapter"}))
    ops.extend([
        instruction(Primitive.OAK, args={"policy": "fail_closed"}),
        instruction(Primitive.RESIDUAL, args={"representation": "typed_generalized"}),
        instruction(Primitive.MEMORIZE, args={"classes": ["M+", "M-", "M?", "COLD"]}),
    ])
    if request.learn:
        ops.append(instruction(Primitive.LEARN_PRIMITIVE, args={"source": "recurring_verified_sequences"}))
    if request.crystallize:
        ops.append(instruction(Primitive.CRYSTALLIZE, args={"artifact": "GOArtifact"}))
    pid = "utir-" + stable_digest({"intent": request.intent, "goal": request.goal})[:16]
    return UTIRProgram(pid, tuple(ops), source_intent=request.intent)


AUTHORITY_EFFECTS: dict[str, tuple[Effect, ...]] = {
    "read": (Effect.READ,),
    "draft": (Effect.READ,),
    "write": (Effect.WRITE,),
    "irreversible": (Effect.WRITE, Effect.IRREVERSIBLE),
}


def capability_plan_to_utir(plan_payload: Mapping[str, Any]) -> UTIRProgram:
    """Compile an existing Ω-CAPABILITY-OS plan into UTIR TRANSFORM instructions."""
    ops = [
        instruction(Primitive.STATE, args={"intent_id": plan_payload.get("intent_id")}),
        instruction(Primitive.GOAL, args={"required_outputs": plan_payload.get("required_outputs", [])}),
        instruction(Primitive.SEARCH, args={"source": "capability_os_plan"}),
    ]
    for step in plan_payload.get("steps", []):
        authority = str(step.get("authority", "read"))
        ops.append(instruction(
            Primitive.TRANSFORM,
            args={"capability_id": step.get("capability_id"), "consumes": step.get("consumes", []), "produces": step.get("produces", []), "health": step.get("health", "UNKNOWN")},
            effects=AUTHORITY_EFFECTS.get(authority, ()),
            cost=max(0.0, 1.0 - float(step.get("effective_utility", 0.0))),
        ))
    ops.extend([
        instruction(Primitive.MEASURE, args={"source": "capability_receipt"}),
        instruction(Primitive.OAK, args={"requires": ["plan_coverage", "fresh_evidence"]}),
        instruction(Primitive.MEMORIZE, args={"source": "capability_outcome"}),
    ])
    return UTIRProgram(program_id="cap-" + str(plan_payload.get("fingerprint", stable_digest(dict(plan_payload))))[:16], instructions=tuple(ops), source_intent=str(plan_payload.get("intent_id", "")))
