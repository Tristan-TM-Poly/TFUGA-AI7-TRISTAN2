"""Explainable multi-label regime classifier.

Thresholds are policy defaults, not universal laws. Every label carries evidence.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from .state import PlasmaState
from .dimensions import PlasmaScales, compute_scales

@dataclass(frozen=True)
class Evidence:
    label: str
    value: float | str | bool
    rule: str
    confidence: str

@dataclass(frozen=True)
class RegimeAssessment:
    labels: tuple[str,...]
    evidence: tuple[Evidence,...]
    scales: PlasmaScales
    unknowns: tuple[str,...]
    contradictions: tuple[str,...]
    epistemic_status: str = "computed_model_assessment"

    def to_dict(self):
        d=asdict(self); d["scales"]=self.scales.to_dict(); return d

def classify_regime(state: PlasmaState, scales: PlasmaScales|None=None) -> RegimeAssessment:
    s=scales or compute_scales(state); labels=[]; ev=[]; unknown=[]; contradictions=[]
    def add(label,value,rule,confidence="medium"):
        if label not in labels: labels.append(label)
        ev.append(Evidence(label,value,rule,confidence))
    if s.debye_number >= 100: add("collective_plasma",s.debye_number,"N_D >= 100","high")
    elif s.debye_number >= 1: add("marginal_collectivity",s.debye_number,"1 <= N_D < 100")
    else: add("noncollective_or_unresolved",s.debye_number,"N_D < 1","high")
    if s.coupling_parameter < 0.1: add("weakly_coupled",s.coupling_parameter,"Gamma < 0.1","high")
    elif s.coupling_parameter <= 1: add("moderately_coupled",s.coupling_parameter,"0.1 <= Gamma <= 1")
    else: add("strongly_coupled",s.coupling_parameter,"Gamma > 1","high")
    if s.plasma_beta < 0.1: add("magnetically_dominated",s.plasma_beta,"beta < 0.1")
    elif s.plasma_beta > 10: add("thermally_dominated",s.plasma_beta,"beta > 10")
    else: add("mixed_pressure_regime",s.plasma_beta,"0.1 <= beta <= 10")
    if s.non_neutrality < 1e-3: add("quasi_neutral_bulk",s.non_neutrality,"delta_Q < 1e-3")
    elif s.non_neutrality > 0.1: add("non_neutral",s.non_neutrality,"delta_Q > 0.1","high")
    else: add("weakly_non_neutral",s.non_neutrality,"1e-3 <= delta_Q <= 0.1")
    if s.fermi_temperature_ratio <= 1: add("quantum_degenerate_candidate",s.fermi_temperature_ratio,"Theta_F <= 1")
    else: add("classical_statistics_candidate",s.fermi_temperature_ratio,"Theta_F > 1")
    if s.relativistic_temperature_ratio >= 0.1 or state.relativistic_bulk_gamma >= 1.1:
        add("relativistic_effects_candidate",max(s.relativistic_temperature_ratio,state.relativistic_bulk_gamma-1),"Theta_r >= 0.1 or bulk gamma >= 1.1")
    else: add("nonrelativistic_candidate",s.relativistic_temperature_ratio,"Theta_r < 0.1 and bulk gamma < 1.1")
    electron=state.electron(); ions=state.ion_species(); neutrals=state.neutral_species()
    if electron and ions:
        ti=sum(x.temperature_ev*x.density_m3 for x in ions)/max(sum(x.density_m3 for x in ions),1e-300)
        ratio=electron.temperature_ev/max(ti,1e-300)
        if ratio >= 5: add("electron_heavy_nonequilibrium",ratio,"Te/Ti >= 5")
        elif 0.5 <= ratio <= 2: add("near_thermal_equilibrium",ratio,"0.5 <= Te/Ti <= 2")
        else: add("multi_temperature",ratio,"temperature ratio outside equilibrium band")
    else: unknown.append("electron-ion temperature ratio")
    if state.ionization_fraction is not None:
        if state.ionization_fraction < 0.01: add("weakly_ionized",state.ionization_fraction,"chi < 0.01")
        elif state.ionization_fraction < 0.9: add("partially_ionized",state.ionization_fraction,"0.01 <= chi < 0.9")
        else: add("highly_ionized",state.ionization_fraction,"chi >= 0.9")
    elif neutrals: unknown.append("ionization_fraction")
    for x in s.species:
        key=x.name.lower().replace(" ","_")
        if x.magnetization >= 10: add(f"magnetized_{key}",x.magnetization,"Omega_c/nu >= 10")
        elif x.magnetization <= 0.1: add(f"unmagnetized_{key}",x.magnetization,"Omega_c/nu <= 0.1")
        else: add(f"partially_magnetized_{key}",x.magnetization,"0.1 < Omega_c/nu < 10")
        if x.knudsen <= 0.01: add(f"fluid_{key}",x.knudsen,"Kn <= 0.01")
        elif x.knudsen >= 0.1: add(f"kinetic_{key}",x.knudsen,"Kn >= 0.1")
        else: add(f"transitional_{key}",x.knudsen,"0.01 < Kn < 0.1")
    if state.geometry.surface_present: add("plasma_surface_coupled",True,"surface_present")
    if state.radiation_energy_density_j_m3 > 0: add("radiation_coupled_candidate",state.radiation_energy_density_j_m3,"radiation energy density provided")
    if "strongly_coupled" in labels and "weakly_coupled" in labels: contradictions.append("coupling labels conflict")
    if "non_neutral" in labels and "quasi_neutral_bulk" in labels: contradictions.append("charge labels conflict")
    return RegimeAssessment(tuple(labels),tuple(ev),s,tuple(unknown),tuple(contradictions))
