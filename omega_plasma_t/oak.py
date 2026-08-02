"""OAK validation gate: validity, assumptions, residues, risk, next tests."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from .state import PlasmaState
from .regime_classifier import RegimeAssessment, classify_regime
from .model_compiler import ModelDecision, compile_models

@dataclass(frozen=True)
class OAKFinding:
    code:str
    severity:str
    message:str
    evidence:dict
    remediation:str

@dataclass(frozen=True)
class OAKReport:
    status:str
    findings:tuple[OAKFinding,...]
    checks:dict[str,bool]
    epistemic_status:str
    assessment:RegimeAssessment|None=None
    model_decision:ModelDecision|None=None

    def to_dict(self):
        d=asdict(self)
        if self.assessment: d["assessment"]=self.assessment.to_dict()
        if self.model_decision: d["model_decision"]=self.model_decision.to_dict()
        return d

def audit_state(state:PlasmaState)->OAKReport:
    findings=[]; validation=state.validate()
    for e in validation: findings.append(OAKFinding("STATE_INVALID","error",e,{},"correct the input state"))
    if validation:
        return OAKReport("blocked",tuple(findings),{"state_valid":False},"input_invalid")
    a=classify_regime(state); m=compile_models(state,a); L=set(a.labels)
    if "noncollective_or_unresolved" in L:
        findings.append(OAKFinding("COLLECTIVITY_WEAK","warning","Debye-sphere population is below one; continuum plasma interpretation may fail.",{"debye_number":a.scales.debye_number},"resolve smaller scales or use a particle/correlated-matter description"))
    if state.geometry.characteristic_length_m <= 10*a.scales.debye_length_m:
        findings.append(OAKFinding("DEBYE_UNRESOLVED","warning","System size is not much larger than the Debye length.",{"L":state.geometry.characteristic_length_m,"lambda_D":a.scales.debye_length_m},"resolve electrostatic layers and avoid blanket quasi-neutrality"))
    if "strongly_coupled" in L:
        findings.append(OAKFinding("IDEAL_GAS_CLOSURE_RISK","warning","Strong coupling invalidates simple ideal-gas closures.",{"Gamma":a.scales.coupling_parameter},"use correlation-aware EOS/transport and benchmark against data"))
    if "quantum_degenerate_candidate" in L:
        findings.append(OAKFinding("QUANTUM_CLOSURE_REQUIRED","warning","Fermi degeneracy may matter.",{"Theta_F":a.scales.fermi_temperature_ratio},"compare classical and quantum closures"))
    if state.geometry.surface_present:
        findings.append(OAKFinding("SHEATH_REQUIRED","info","A material boundary generally creates a sheath and surface feedback.",{},"resolve or parameterize sheath, emission, charging and surface chemistry"))
    if not state.requested_observables:
        findings.append(OAKFinding("TARGET_UNSPECIFIED","warning","No requested observables or accuracy target were provided.",{},"define observables, tolerances and comparison data before selecting a final model"))
    checks={"state_valid":True,"charge_inputs_present":bool(state.charged_species()),"electron_present":state.electron() is not None,"geometry_bounded":state.geometry.characteristic_length_m>0,"model_candidates_generated":bool(m.recommended or m.conditional),"contradiction_free":not a.contradictions}
    status="blocked" if any(x.severity=="error" for x in findings) else "review" if any(x.severity=="warning" for x in findings) else "passed"
    return OAKReport(status,tuple(findings),checks,"computed_not_experimentally_certified",a,m)
