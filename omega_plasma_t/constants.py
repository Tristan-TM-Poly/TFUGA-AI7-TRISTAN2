"""CODATA-like constants used by the zero-dependency Ω-PLASMA kernel.

Values are intentionally centralized so numerical assumptions are inspectable.
This package is educational/research software, not a certified metrology tool.
"""
from math import pi

ELEMENTARY_CHARGE = 1.602176634e-19
ELECTRON_MASS = 9.1093837015e-31
PROTON_MASS = 1.67262192369e-27
BOLTZMANN = 1.380649e-23
EPSILON_0 = 8.8541878128e-12
MU_0 = 1.25663706212e-6
SPEED_OF_LIGHT = 299_792_458.0
PLANCK = 6.62607015e-34
HBAR = PLANCK / (2.0 * pi)
EV_TO_K = ELEMENTARY_CHARGE / BOLTZMANN
ATOMIC_MASS_UNIT = 1.66053906660e-27
VACUUM_IMPEDANCE = (MU_0 / EPSILON_0) ** 0.5
