from typing import Any, Iterable, Mapping
from omega_capability_os_t import compile_workunit
from omega_capability_os_t.core import plan, stable_digest
from .primitives import TTM_PRIMITIVES, primitive_contract

def program_payload(program: Any)->dict[str,Any]:
    return {"name":program.name,"instructions":[{"opcode":i.opcode.value,"args":list(i.args)} for i in program.instructions]}

def compile_report(computer:Any,work_unit:Any,*,completed_dependencies:Iterable[str]=(),health:Mapping[str,Any]|None=None)->dict[str,Any]:
    bridge=compile_workunit(work_unit,completed_dependencies=completed_dependencies)
    cap_plan=plan(bridge.capabilities,bridge.intent,dict(health or {}))
    report={
        "schema":"omega-ttm-exec-compile/v1",
        "work_unit":work_unit.to_dict(),
        "reuse_contract":{
            "workunit":"omega_intent_t.models.WorkUnit",
            "capability_runtime":"omega_capability_os_t.CapabilityRuntime",
            "cognitive_runtime":"omega_cognitive_computer_t.CognitiveComputer",
            "parallel_workunit_definition_created":False,
            "parallel_capability_ontology_created":False,
            "parallel_cognitive_isa_created":False,
        },
        "capability_plan":cap_plan,
        "cognitive_program":program_payload(computer.compile(work_unit.objective)),
        "ttm_primitive_contracts":[primitive_contract(n) for n in TTM_PRIMITIVES],
        "go_max_min":{
            "selected":[s["capability_id"] for s in cap_plan.get("steps",[])],
            "unresolved":list(cap_plan.get("unresolved_outputs",[])),
            "policy":"reuse_compose_extend_residual",
        },
        "boundary":"Compilation emits a bounded plan only.",
    }
    report["fingerprint"]=stable_digest(report)
    return report
