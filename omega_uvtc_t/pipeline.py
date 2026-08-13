"""R0.2 vertical slice: compile, optimize, certify, and abstract-check."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .certificates import certify_optimization
from .compiler import CompileRequest, compile_intent
from .model import stable_digest
from .optimizer import superoptimize
from .semantics import execute_abstract


@dataclass(frozen=True, slots=True)
class UVTCPipelineReceipt:
    request_fingerprint: str
    source_program_fingerprint: str
    optimized_program_fingerprint: str
    optimization_event_count: int
    optimization_certificate_status: str
    operational_status: str
    unresolved_obligations: tuple[str, ...]
    status: str
    semantic_equivalence_proven: bool
    boundary: str = "PASS is a deterministic local software-contract result, not a truth certificate"

    @property
    def fingerprint(self) -> str:
        return stable_digest(asdict(self))


def run_pipeline(request: CompileRequest) -> UVTCPipelineReceipt:
    source = compile_intent(request)
    optimization = superoptimize(source)
    certificate = certify_optimization(source, optimization)
    execution = execute_abstract(optimization.program)
    status = "PASS" if certificate.status == "PASS" and execution.status == "PASS" else "HOLD"
    return UVTCPipelineReceipt(
        request_fingerprint=stable_digest(asdict(request)),
        source_program_fingerprint=source.fingerprint,
        optimized_program_fingerprint=optimization.program.fingerprint,
        optimization_event_count=len(optimization.events),
        optimization_certificate_status=certificate.status,
        operational_status=execution.status,
        unresolved_obligations=execution.final_state.obligations,
        status=status,
        semantic_equivalence_proven=certificate.semantic_equivalence_proven,
    )
