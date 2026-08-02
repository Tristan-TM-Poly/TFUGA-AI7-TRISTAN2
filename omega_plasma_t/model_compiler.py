"""Rule-based compilation from a plasma signature to model candidates."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from .state import PlasmaState
from .regime_classifier import RegimeAssessment, classify_regime

@dataclass(frozen=True)
class ModelCandidate:
    name: str
    status: str
    score: float
    reasons: tuple[str,...]
    blockers: tuple[str,...]
    required_extensions: tuple[str,...]

@dataclass(frozen=True)
class ModelDecision:
    recommended: tuple[ModelCandidate,...]
    conditional: tuple[ModelCandidate,...]
    rejected: tuple[ModelCandidate,...]
    assessment: RegimeAssessment
    residual_questions: tuple[str,...]

    def to_dict(self):
        d=asdict(self); d["assessment"]=self.assessment.to_dict(); return d

MODELS={
"global_chemistry":("volume-averaged reactive kinetics",),
"drift_diffusion":("collisional charged transport",),
"single_fluid_mhd":("large-scale conducting fluid",),
"resistive_mhd":("MHD with finite conductivity",),
"hall_mhd":("ion-electron decoupling",),
"two_fluid":("separate electron and ion moments",),
"multi_fluid":("multiple charged and neutral fluids",),
"vlasov_poisson":("electrostatic collisionless kinetics",),
"vlasov_maxwell":("electromagnetic collisionless kinetics",),
"pic_es":("particle electrostatic simulation",),
"pic_em":("particle electromagnetic simulation",),
"pic_mcc":("particle simulation with Monte-Carlo collisions",),
"hybrid_kinetic_ion":("kinetic ions fluid electrons",),
"gyrokinetic":("strongly magnetized low-frequency kinetics",),
"quantum_hydrodynamics":("degenerate quantum fluid approximation",),
"wigner_poisson":("quantum kinetic electrostatic model",),
"radiation_mhd":("MHD coupled to radiation",),
"relativistic_pic":("relativistic electromagnetic particles",),
"dusty_plasma":("charged grain dynamics",),
"sheath_model":("boundary electrostatic layer",),
"surface_reaction_model":("surface charging emission and chemistry",),
"warm_dense_matter_eos":("strong coupling and degeneracy EOS",),
}

def compile_models(state: PlasmaState, assessment: RegimeAssessment|None=None) -> ModelDecision:
    a=assessment or classify_regime(state); L=set(a.labels); candidates=[]
    def c(name,score,reasons=(),blockers=(),ext=()):
        status="recommended" if score>=0.7 and not blockers else "conditional" if score>=0.35 else "rejected"
        if blockers: status="rejected" if score<0.7 else "conditional"
        candidates.append(ModelCandidate(name,status,round(score,3),tuple(reasons),tuple(blockers),tuple(ext)))
    kinetic=any(x.startswith("kinetic_") for x in L); fluid=any(x.startswith("fluid_") for x in L)
    magnetized=any(x.startswith("magnetized_") for x in L); partial="partially_ionized" in L or "weakly_ionized" in L
    noneq="electron_heavy_nonequilibrium" in L or "multi_temperature" in L
    quantum="quantum_degenerate_candidate" in L; relativistic="relativistic_effects_candidate" in L
    strong="strongly_coupled" in L; nonneutral="non_neutral" in L
    reactive=partial or bool(state.neutral_species())
    surface=state.geometry.surface_present
    c("global_chemistry",0.82 if reactive else 0.25,["neutral/reactive species present"] if reactive else [],["spatial gradients may invalidate zero-D closure"] if state.geometry.dimensionality>0 else [])
    c("drift_diffusion",0.78 if fluid and partial else 0.4,["collisional fluid indicators","partial ionization"] if partial else ["fluid indicator"] if fluid else [],["kinetic tails unresolved"] if kinetic else [])
    c("single_fluid_mhd",0.78 if fluid and not partial and not noneq else 0.25,["bulk fluid regime"] if fluid else [],["partial ionization"] if partial else [],["ambipolar/Hall terms"] if partial else [])
    c("resistive_mhd",0.76 if fluid else 0.35,["fluid closure and finite collision frequency"] if fluid else [],["kinetic scale requested"] if kinetic else [])
    c("hall_mhd",0.72 if magnetized and fluid else 0.4,["magnetized species and fluid bulk"] if magnetized and fluid else [],["no magnetic field"] if state.magnetic_field_t==0 else [])
    c("two_fluid",0.84 if noneq or magnetized else 0.55,["species temperatures or magnetization differ"] if noneq or magnetized else [])
    c("multi_fluid",0.86 if partial and len(state.species)>=3 else 0.5,["charged-neutral coupling"] if partial else [])
    c("vlasov_poisson",0.82 if kinetic and state.magnetic_field_t==0 else 0.48,["collisionless electrostatic candidate"] if kinetic else [],["electromagnetic effects may matter"] if state.magnetic_field_t>0 else [])
    c("vlasov_maxwell",0.86 if kinetic and (state.magnetic_field_t>0 or relativistic) else 0.55,["kinetic electromagnetic regime"] if kinetic else [])
    c("pic_es",0.8 if kinetic and state.magnetic_field_t==0 else 0.5,["kinetic electrostatic resolution"] if kinetic else [])
    c("pic_em",0.84 if kinetic and state.magnetic_field_t>0 else 0.55,["kinetic magnetized resolution"] if kinetic and state.magnetic_field_t>0 else [])
    c("pic_mcc",0.9 if kinetic and partial else 0.52,["kinetic and neutral collisions"] if kinetic and partial else [])
    c("hybrid_kinetic_ion",0.76 if kinetic and magnetized else 0.46,["ion kinetic/magnetized candidate"] if kinetic and magnetized else [])
    c("gyrokinetic",0.8 if magnetized and not relativistic else 0.3,["strong magnetization"] if magnetized else [],["requires low-frequency anisotropic ordering","not a sheath model"])
    c("quantum_hydrodynamics",0.78 if quantum else 0.15,["degeneracy indicator"] if quantum else [])
    c("wigner_poisson",0.82 if quantum and kinetic else 0.12,["quantum and kinetic indicators"] if quantum and kinetic else [])
    c("radiation_mhd",0.74 if state.radiation_energy_density_j_m3>0 and fluid else 0.2,["radiation field supplied"] if state.radiation_energy_density_j_m3>0 else [])
    c("relativistic_pic",0.9 if relativistic and kinetic else 0.18,["relativistic kinetic indicators"] if relativistic and kinetic else [])
    dusty=any("dust" in x.name.lower() or "grain" in x.name.lower() for x in state.species)
    c("dusty_plasma",0.93 if dusty else 0.05,["charged grain species"] if dusty else [])
    c("sheath_model",0.9 if surface or nonneutral else 0.3,["surface or non-neutral layer"] if surface or nonneutral else [])
    c("surface_reaction_model",0.88 if surface and reactive else 0.35,["reactive plasma-surface loop"] if surface and reactive else [])
    c("warm_dense_matter_eos",0.9 if strong and quantum else 0.68 if strong or quantum else 0.08,["strong coupling and/or degeneracy"] if strong or quantum else [])
    rec=tuple(sorted((x for x in candidates if x.status=="recommended"),key=lambda x:-x.score))
    cond=tuple(sorted((x for x in candidates if x.status=="conditional"),key=lambda x:-x.score))
    rej=tuple(sorted((x for x in candidates if x.status=="rejected"),key=lambda x:-x.score))
    residual=list(a.unknowns)
    if not state.requested_observables: residual.append("requested observables and accuracy target")
    residual.extend(["time-scale hierarchy","gradient scale lengths","distribution-function shape"])
    return ModelDecision(rec,cond,rej,a,tuple(dict.fromkeys(residual)))
