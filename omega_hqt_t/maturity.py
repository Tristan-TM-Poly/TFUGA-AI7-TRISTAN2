from __future__ import annotations
from dataclasses import asdict, dataclass

LEVELS=(
    'fertile_speculation','structured_hypothesis','preliminary_simulation','reproducible_result',
    'robust_multi_model_result','authorized_real_data_validation','demonstrator','field_pilot',
    'qualified_solution','institutionalized_practice',
)

@dataclass(frozen=True)
class MaturityAssessment:
    artifact_id: str
    current_level: str
    passed_gates: tuple[str,...]
    missing_gates: tuple[str,...]
    promotable: bool
    next_level: str|None
    def to_dict(self): return asdict(self)

GATES={
    'fertile_speculation':(),
    'structured_hypothesis':('definition','falsifier','scope'),
    'preliminary_simulation':('executable_model','fixture','baseline'),
    'reproducible_result':('determinism','tests','provenance'),
    'robust_multi_model_result':('model_pluralism','sensitivity','counterexamples'),
    'authorized_real_data_validation':('authorization','data_governance','privacy_security'),
    'demonstrator':('integration','human_review','rollback'),
    'field_pilot':('site_approval','monitoring','incident_plan'),
    'qualified_solution':('standards','independent_validation','acceptance_criteria'),
    'institutionalized_practice':('governance','training','continuous_audit'),
}

def assess_maturity(artifact_id: str, current_level: str, evidence_gates: set[str]) -> MaturityAssessment:
    if current_level not in LEVELS: raise ValueError('unknown maturity level')
    index=LEVELS.index(current_level); next_level=LEVELS[index+1] if index+1<len(LEVELS) else None
    required=set(GATES.get(next_level,())) if next_level else set()
    missing=required-evidence_gates
    return MaturityAssessment(artifact_id,current_level,tuple(sorted(required& evidence_gates)),tuple(sorted(missing)),not missing if next_level else False,next_level)
