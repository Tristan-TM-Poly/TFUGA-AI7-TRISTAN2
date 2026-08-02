"""Dimensionless numbers and characteristic scales for plasma classification."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from math import pi, sqrt, inf
from .constants import *
from .state import PlasmaState, SpeciesState

@dataclass(frozen=True)
class SpeciesScales:
    name: str
    plasma_frequency_hz: float
    cyclotron_frequency_hz: float
    thermal_speed_m_s: float
    larmor_radius_m: float
    mean_free_path_m: float
    magnetization: float
    knudsen: float
    inertial_length_m: float

@dataclass(frozen=True)
class PlasmaScales:
    debye_length_m: float
    debye_number: float
    electron_plasma_frequency_hz: float
    electron_skin_depth_m: float
    coupling_parameter: float
    plasma_beta: float
    non_neutrality: float
    fermi_temperature_ratio: float
    relativistic_temperature_ratio: float
    alfven_speed_m_s: float
    sound_speed_m_s: float
    magnetic_reynolds_proxy: float
    species: tuple[SpeciesScales,...]
    assumptions: tuple[str,...]

    def to_dict(self):
        d=asdict(self); d["species"]=[asdict(x) for x in self.species]; return d

def _temp_j(ev: float) -> float: return ev * ELEMENTARY_CHARGE

def _safe_div(a:float,b:float,default:float=inf)->float: return a/b if b else default

def _electron(state: PlasmaState) -> SpeciesState:
    e=state.electron()
    if e is None: raise ValueError("an electron-like species is required for electron scales")
    return e

def debye_length(e: SpeciesState) -> float:
    if e.density_m3 <= 0: return inf
    return sqrt(EPSILON_0 * _temp_j(e.temperature_ev) / (e.density_m3 * ELEMENTARY_CHARGE**2))

def plasma_frequency(s: SpeciesState) -> float:
    q=abs(s.charge_state)*ELEMENTARY_CHARGE
    if q == 0 or s.density_m3 <= 0: return 0.0
    return sqrt(s.density_m3*q*q/(EPSILON_0*s.mass_kg))/(2*pi)

def cyclotron_frequency(s: SpeciesState, b_t:float) -> float:
    q=abs(s.charge_state)*ELEMENTARY_CHARGE
    return q*b_t/(2*pi*s.mass_kg) if q and b_t else 0.0

def thermal_speed(s: SpeciesState) -> float:
    return sqrt(max(0.0, 2*_temp_j(s.temperature_ev)/s.mass_kg))

def coupling_parameter(e: SpeciesState) -> float:
    if e.density_m3 <= 0 or e.temperature_ev <= 0: return inf
    a=(3/(4*pi*e.density_m3))**(1/3)
    return ELEMENTARY_CHARGE**2/(4*pi*EPSILON_0*a*_temp_j(e.temperature_ev))

def fermi_energy_j(e: SpeciesState) -> float:
    if e.density_m3 <= 0: return 0.0
    return (HBAR**2/(2*ELECTRON_MASS))*(3*pi*pi*e.density_m3)**(2/3)

def compute_scales(state: PlasmaState) -> PlasmaScales:
    errors=state.validate()
    if errors: raise ValueError("invalid plasma state: " + "; ".join(errors))
    e=_electron(state); L=state.geometry.characteristic_length_m
    lam=debye_length(e)
    debye_n=(4*pi/3)*e.density_m3*lam**3 if lam != inf else 0.0
    sp=[]
    for s in state.species:
        v=thermal_speed(s); fc=cyclotron_frequency(s,state.magnetic_field_t)
        omega=2*pi*fc
        rho=v/omega if omega else inf
        mfp=v/s.collision_frequency_hz if s.collision_frequency_hz else inf
        q=abs(s.charge_state)*ELEMENTARY_CHARGE
        wp=sqrt(s.density_m3*q*q/(EPSILON_0*s.mass_kg)) if q and s.density_m3 else 0.0
        skin=SPEED_OF_LIGHT/wp if wp else inf
        sp.append(SpeciesScales(
            name=s.name,
            plasma_frequency_hz=wp/(2*pi),
            cyclotron_frequency_hz=fc,
            thermal_speed_m_s=v,
            larmor_radius_m=rho,
            mean_free_path_m=mfp,
            magnetization=_safe_div(omega,s.collision_frequency_hz, inf if omega else 0.0),
            knudsen=_safe_div(mfp,L),
            inertial_length_m=skin,
        ))
    thermal_pressure=sum(s.density_m3*_temp_j(s.temperature_ev) for s in state.species)
    magnetic_pressure=state.magnetic_field_t**2/(2*MU_0)
    beta=_safe_div(thermal_pressure, magnetic_pressure, inf if thermal_pressure else 0.0)
    total_abs=sum(abs(s.charge_state)*s.density_m3 for s in state.species)
    net=abs(sum(s.charge_state*s.density_m3 for s in state.species))
    nonneutral=_safe_div(net,total_abs,0.0)
    ion_mass_density=sum(s.mass_kg*s.density_m3 for s in state.ion_species())
    va=state.magnetic_field_t/sqrt(MU_0*ion_mass_density) if ion_mass_density and state.magnetic_field_t else 0.0
    ion_density=sum(s.density_m3 for s in state.ion_species())
    mean_ion_mass=(ion_mass_density/ion_density) if ion_density else PROTON_MASS
    cs=sqrt(max(0.0,_temp_j(e.temperature_ev)/mean_ion_mass))
    ef=fermi_energy_j(e)
    theta_f=_safe_div(_temp_j(e.temperature_ev),ef,inf)
    theta_r=_safe_div(_temp_j(e.temperature_ev),ELECTRON_MASS*SPEED_OF_LIGHT**2,0.0)
    conductivity_proxy=e.density_m3*ELEMENTARY_CHARGE**2/(ELECTRON_MASS*max(e.collision_frequency_hz,1e-300))
    rm=MU_0*conductivity_proxy*max(e.drift_speed_m_s,thermal_speed(e))*L
    assumptions=(
        "temperatures interpreted as scalar eV",
        "electron Debye scale uses the first electron-like species",
        "thermal pressure is ideal and isotropic",
        "magnetic Reynolds number is a Drude proxy",
    )
    return PlasmaScales(lam,debye_n,plasma_frequency(e),SPEED_OF_LIGHT/(2*pi*plasma_frequency(e)) if plasma_frequency(e) else inf,coupling_parameter(e),beta,nonneutral,theta_f,theta_r,va,cs,rm,tuple(sp),assumptions)
