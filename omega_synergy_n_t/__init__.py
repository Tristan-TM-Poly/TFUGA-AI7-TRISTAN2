"""Ω-SYNERGY-N-T∞ R2 — exact higher-order interaction laboratory."""
from .mobius import decompose_measurements,direct_interaction,mobius_decompose,zeta_reconstruct
from .factorial import full_factorial_design,fractional_half_design,mobius_contrast,orthogonal_effect
from .spectrum import order_spectrum
from .hypergraph import SynergyComplex
from .experiment import compile_design
from .oak import hard_gate
__all__=["decompose_measurements","direct_interaction","mobius_decompose","zeta_reconstruct","full_factorial_design","fractional_half_design","mobius_contrast","orthogonal_effect","order_spectrum","SynergyComplex","compile_design","hard_gate"]
