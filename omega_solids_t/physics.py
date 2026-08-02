from __future__ import annotations
import math
from dataclasses import dataclass
@dataclass(frozen=True)
class IsotropicElasticity:
    young_modulus_Pa:float; poisson_ratio:float
    def __post_init__(self):
        if self.young_modulus_Pa<=0: raise ValueError('Young modulus must be positive')
        if not -1<self.poisson_ratio<0.5: raise ValueError('Poisson ratio outside stable isotropic range')
    @property
    def shear_modulus_Pa(self): return self.young_modulus_Pa/(2*(1+self.poisson_ratio))
    @property
    def bulk_modulus_Pa(self): return self.young_modulus_Pa/(3*(1-2*self.poisson_ratio))
    @property
    def lame_lambda_Pa(self): return self.young_modulus_Pa*self.poisson_ratio/((1+self.poisson_ratio)*(1-2*self.poisson_ratio))
def rule_of_mixtures(values,fractions,mode='voigt'):
    values=tuple(float(v) for v in values); fractions=tuple(float(f) for f in fractions)
    if len(values)!=len(fractions) or not values: raise ValueError('values/fractions mismatch')
    if any(v<=0 for v in values) or any(f<0 for f in fractions): raise ValueError('non-positive values or negative fractions')
    if not math.isclose(sum(fractions),1.0,abs_tol=1e-9): raise ValueError('fractions must sum to one')
    voigt=sum(v*f for v,f in zip(values,fractions)); reuss=1/sum(f/v for v,f in zip(values,fractions))
    if mode=='voigt': return voigt
    if mode=='reuss': return reuss
    if mode=='hill': return 0.5*(voigt+reuss)
    raise ValueError('mode must be voigt, reuss or hill')
def hall_petch_strength(sigma0_Pa,k_Pa_sqrt_m,grain_size_m):
    if min(sigma0_Pa,k_Pa_sqrt_m,grain_size_m)<=0: raise ValueError('positive inputs required')
    return sigma0_Pa+k_Pa_sqrt_m/math.sqrt(grain_size_m)
def gibson_ashby_modulus(solid_modulus_Pa,relative_density,coefficient=1.0,exponent=2.0):
    if solid_modulus_Pa<=0 or coefficient<=0 or exponent<=0 or not 0<relative_density<=1: raise ValueError('invalid Gibson-Ashby inputs')
    return coefficient*solid_modulus_Pa*relative_density**exponent
def fracture_safety_factor(toughness_Pa_sqrt_m,stress_Pa,crack_m,geometry_factor=1.0):
    if min(toughness_Pa_sqrt_m,stress_Pa,crack_m,geometry_factor)<=0: raise ValueError('positive inputs required')
    return toughness_Pa_sqrt_m/(geometry_factor*stress_Pa*math.sqrt(math.pi*crack_m))
def arrhenius_diffusivity(prefactor_m2_s,activation_J_mol,temperature_K):
    if min(prefactor_m2_s,temperature_K)<=0 or activation_J_mol<0: raise ValueError('invalid Arrhenius inputs')
    return prefactor_m2_s*math.exp(-activation_J_mol/(8.31446261815324*temperature_K))
def constrained_thermal_stress(young_modulus_Pa,thermal_expansion_1_K,delta_T_K,poisson_ratio=0.0):
    if young_modulus_Pa<=0 or not -1<poisson_ratio<0.5: raise ValueError('invalid elasticity inputs')
    return young_modulus_Pa*thermal_expansion_1_K*delta_T_K/(1-poisson_ratio)
