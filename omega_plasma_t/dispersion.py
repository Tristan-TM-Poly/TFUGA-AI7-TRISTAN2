"""Analytical baseline dispersion relations and stability helpers."""
from __future__ import annotations
from dataclasses import dataclass
from math import sqrt, pi
from .constants import ELEMENTARY_CHARGE, EPSILON_0, ELECTRON_MASS, BOLTZMANN

@dataclass(frozen=True)
class DispersionPoint:
    k_rad_m: float
    omega_rad_s: complex
    branch: str
    assumptions: tuple[str,...]

def electron_plasma_angular_frequency(n_e_m3:float)->float:
    if n_e_m3<0: raise ValueError("density must be non-negative")
    return sqrt(n_e_m3*ELEMENTARY_CHARGE**2/(EPSILON_0*ELECTRON_MASS))

def langmuir_bohm_gross(k_rad_m:float,n_e_m3:float,t_e_ev:float)->DispersionPoint:
    wp=electron_plasma_angular_frequency(n_e_m3)
    vth2=2*t_e_ev*ELEMENTARY_CHARGE/ELECTRON_MASS
    omega=sqrt(max(0.0,wp*wp+1.5*k_rad_m*k_rad_m*vth2))
    return DispersionPoint(k_rad_m,complex(omega,0),"langmuir_bohm_gross",("Maxwellian electrons","immobile ions","weak damping"))

def ion_acoustic(k_rad_m:float,t_e_ev:float,ion_mass_kg:float,lambda_d_m:float=0.0)->DispersionPoint:
    if ion_mass_kg<=0: raise ValueError("ion_mass_kg must be positive")
    cs=sqrt(t_e_ev*ELEMENTARY_CHARGE/ion_mass_kg)
    omega=k_rad_m*cs/sqrt(1+(k_rad_m*lambda_d_m)**2)
    return DispersionPoint(k_rad_m,complex(omega,0),"ion_acoustic",("Te >> Ti","quasi-neutral bulk","fluid ions"))

def alfven(k_parallel_rad_m:float,b_t:float,mass_density_kg_m3:float)->DispersionPoint:
    from .constants import MU_0
    if mass_density_kg_m3<=0: raise ValueError("mass_density_kg_m3 must be positive")
    va=b_t/sqrt(MU_0*mass_density_kg_m3)
    return DispersionPoint(k_parallel_rad_m,complex(abs(k_parallel_rad_m)*va,0),"shear_alfven",("ideal MHD","parallel propagation","uniform background"))

def cold_two_stream_growth_proxy(n_beam_m3:float,n_bulk_m3:float,v_beam_m_s:float)->float:
    """Return a scale proxy, not the exact root of the quartic dispersion relation."""
    if min(n_beam_m3,n_bulk_m3)<0: raise ValueError("densities must be non-negative")
    if not v_beam_m_s or not n_beam_m3 or not n_bulk_m3: return 0.0
    wp=electron_plasma_angular_frequency(n_bulk_m3)
    alpha=n_beam_m3/max(n_bulk_m3,1e-300)
    return wp*(sqrt(3)/2)*(alpha/2)**(1/3)
