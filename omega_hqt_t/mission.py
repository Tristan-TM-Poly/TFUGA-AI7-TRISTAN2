from __future__ import annotations
from dataclasses import asdict, dataclass
from .hashutil import sha256
from .security import safety_gate

@dataclass(frozen=True)
class MissionGraph:
    mission_id: str
    objective: str
    scope: str
    horizon: int
    constraints: tuple[str,...]
    workflows: tuple[str,...]
    required_evidence: tuple[str,...]
    stop_conditions: tuple[str,...]
    status: str
    evidence_hash: str
    def to_dict(self): return asdict(self)

DEFAULT_WORKFLOWS=(
    'map_public_evidence','build_synthetic_projection','generate_scenario_worlds','identify_dependencies',
    'generate_interventions','run_robustness_tests','perform_oak_review','compile_decision_package',
)

def compile_mission(objective: str, *, scope: str='quebec-regional-synthetic', horizon: int=2040, public_data_only: bool=True) -> MissionGraph:
    decision=safety_gate(requested_level='public',content=objective,public_data_only=public_data_only)
    status='READY_FOR_SYNTHETIC_RESEARCH' if decision.allowed else 'BLOCKED_BY_SAFETY_GATE'
    workflows=DEFAULT_WORKFLOWS if decision.allowed else ('security_review',)
    core={'objective':objective,'scope':scope,'horizon':horizon,'constraints':('public_or_synthetic_only','no_operational_control','human_authorization','provenance_required'),'workflows':workflows,'required_evidence':('source register','model card','uncertainty budget','benchmark receipt'),'stop_conditions':('safety gate failure','missing provenance','non-finite simulation','claim exceeds evidence'),'status':status}
    return MissionGraph('mission:'+sha256(core)[:16],**core,evidence_hash=sha256(core))
