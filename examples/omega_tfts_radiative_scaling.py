"""Radiative scaling seed for CRFT — Corps Radiatif Fractal de Tristan.

This script estimates geometry-level gains only. It does not compute full-wave
radiation, emissivity, or thermodynamic output.

Run:
    python examples/omega_tfts_radiative_scaling.py
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class RadiativeScaling:
    n: int
    menger_volume_fraction: float
    menger_area: float
    menger_surface_volume_gain: float
    cantor_volume_fraction: float
    cantor_area_if_exposed: float
    cantor_surface_volume_gain: float
    dielectric_resonance_compression: float
    resonance_frequency_ratio: float


def scaling(n: int, epsilon_eff: float, initial_area: float = 6.0) -> RadiativeScaling:
    """Return simple geometric and dielectric scaling estimates.

    Menger formulas assume a unit initial cube:
        V_M(n) = (20/27)^n
        A_M(n) = 6 (4/3)^n
        (A/V)_M gain = (9/5)^n

    Cantor sparse formulas assume every surviving micro-cube has exposed faces:
        V_K(n) = (8/27)^n
        A_K(n) = 6 (8/9)^n
        (A/V)_K gain = 3^n

    Dielectric resonance proxy:
        f_res(epsilon_eff) / f_res(vacuum) = 1 / sqrt(epsilon_eff)
    """

    if n < 0:
        raise ValueError("n must be non-negative")
    if epsilon_eff <= 0:
        raise ValueError("epsilon_eff must be positive")

    menger_volume = (20 / 27) ** n
    menger_area = initial_area * (4 / 3) ** n
    menger_sv_gain = (9 / 5) ** n

    cantor_volume = (8 / 27) ** n
    cantor_area = initial_area * (8 / 9) ** n
    cantor_sv_gain = 3**n

    compression = sqrt(epsilon_eff)
    freq_ratio = 1 / compression

    return RadiativeScaling(
        n=n,
        menger_volume_fraction=menger_volume,
        menger_area=menger_area,
        menger_surface_volume_gain=menger_sv_gain,
        cantor_volume_fraction=cantor_volume,
        cantor_area_if_exposed=cantor_area,
        cantor_surface_volume_gain=cantor_sv_gain,
        dielectric_resonance_compression=compression,
        resonance_frequency_ratio=freq_ratio,
    )


def main() -> None:
    for epsilon_eff in (2.2, 4.0, 10.0, 30.0):
        print(f"epsilon_eff={epsilon_eff}")
        for n in range(0, 6):
            print(scaling(n=n, epsilon_eff=epsilon_eff))
        print()


if __name__ == "__main__":
    main()
