"""Frequency, wavelength and photon-energy classification utilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass

C_M_S = 299_792_458.0
H_J_S = 6.626_070_15e-34
E_CHARGE_C = 1.602_176_634e-19


@dataclass(frozen=True)
class SpectralClassification:
    frequency_hz: float
    wavelength_m: float
    photon_energy_j: float
    photon_energy_ev: float
    region: str
    ionizing_candidate: bool
    boundary_note: str

    def to_dict(self) -> dict[str, float | str | bool]:
        return asdict(self)


def spectral_region(frequency_hz: float) -> str:
    """Return a disjoint engineering partition of the EM spectrum.

    The boundaries are intentionally documented as functional bins rather than
    absolute physical discontinuities.
    """

    if frequency_hz <= 0:
        raise ValueError("frequency_hz must be positive")
    if frequency_hz < 3e3:
        return "quasi_static_and_elf"
    if frequency_hz < 3e8:
        return "radio"
    if frequency_hz < 3e11:
        return "microwave_and_millimeter"
    if frequency_hz < 3e13:
        return "terahertz_and_submillimeter"
    if frequency_hz < 4e14:
        return "infrared"
    if frequency_hz < 7.9e14:
        return "visible"
    if frequency_hz < 3e16:
        return "ultraviolet"
    if frequency_hz < 3e19:
        return "x_ray"
    return "gamma"


def classify_frequency(frequency_hz: float) -> SpectralClassification:
    if frequency_hz <= 0:
        raise ValueError("frequency_hz must be positive")
    wavelength_m = C_M_S / frequency_hz
    photon_energy_j = H_J_S * frequency_hz
    photon_energy_ev = photon_energy_j / E_CHARGE_C
    # Ten electron-volts is a deliberately conservative routing heuristic, not
    # a universal material-independent ionization boundary.
    ionizing_candidate = photon_energy_ev >= 10.0
    return SpectralClassification(
        frequency_hz=frequency_hz,
        wavelength_m=wavelength_m,
        photon_energy_j=photon_energy_j,
        photon_energy_ev=photon_energy_ev,
        region=spectral_region(frequency_hz),
        ionizing_candidate=ionizing_candidate,
        boundary_note=(
            "Spectrum labels and the 10 eV ionization flag are engineering "
            "routing conventions; material response and regulation require "
            "case-specific review."
        ),
    )
