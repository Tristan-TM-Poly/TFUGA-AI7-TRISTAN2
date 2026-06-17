"""Omega-CQC-TFTS-CRFT 16x16 research matrix.

Generates 256 research families by crossing 16 geometry/symmetry classes with
16 physical/functional regimes. This is an OAK-gated roadmap generator, not a
physics solver.

Run:
    python examples/omega_cqc_16x16_matrix.py
"""

from __future__ import annotations

from dataclasses import dataclass


GEOMETRIES = [
    ("cubic_crft", "high isotropy and controlled 3D baseline"),
    ("tetragonal_crft", "one privileged axis for directional tuning"),
    ("hexagonal_crft", "sixfold planar order and valley-like channels"),
    ("trigonal_rhombohedral_crft", "chirality potential and rotational coupling"),
    ("orthorhombic_crft", "three independent axes and natural spectral separation"),
    ("monoclinic_crft", "oblique coupling and strong anisotropy"),
    ("triclinic_crft", "maximal anisotropy and dense nondegenerate spectra"),
    ("quasicrystalline_crft", "non-periodic long-range order and rich diffraction"),
    ("semicrystalline_defected_crft", "controlled defects and localizations"),
    ("amorphous_hyperuniform_crft", "isotropic disorder with suppressed density fluctuations"),
    ("moire_twisted_bilayer_crft", "twist-angle tunability and flat-band-like localization"),
    ("2d_layered_vanderwaals_crft", "exfoliable layered anisotropy and heterostructures"),
    ("perovskite_octahedral_crft", "octahedral tilts, polar domains, and soft phonons"),
    ("zeolite_mof_porous_crft", "ready-made porous crystalline channels"),
    ("gyroid_minimal_surface_crft", "triply periodic connected minimal-surface skeleton"),
    ("cut_stretched_miller_slab_crft", "Miller cuts, ports, and affine stretch as design variables"),
]

REGIMES = [
    ("absorber", "maximize absorption with loss and impedance matching"),
    ("selective_emitter", "shape emissivity in a target thermal band"),
    ("antenna", "radiate efficiently with compact multi-scale aperture"),
    ("near_field_sensor", "maximize LDOS and useful local signal"),
    ("photonic_phononic_bandgap", "create and use localized states in a wave gap"),
    ("plasmonic_metamaterial", "surface hot spots and strong light-matter coupling"),
    ("superconducting_josephson", "flux quantization and Josephson response"),
    ("topological_nonreciprocal", "robust modes or direction-dependent scattering"),
    ("thermophotovoltaic", "match emission spectrum to a PV response"),
    ("raman_sers_spectroscopy", "improve molecular SNR and reduce baseline burden"),
    ("dielectric_resonator_array", "turn filled voids into DRA-like cavity arrays"),
    ("phonon_thermal_management", "shape acoustic/thermal transport"),
    ("optomechanical_cavity", "couple optical and mechanical modes"),
    ("magnonic_spintronic", "control spin waves or spin-dependent signals"),
    ("quantum_microwave_cqed", "low-volume microwave cavities and superconducting circuits"),
    ("sns_pd_single_photon_detector", "fractal nanowire/cavity photon capture"),
]

OAK_GATES = {
    "absorber": "A_T(omega) > A_control at matched thickness/mass/volume",
    "selective_emitter": "epsilon_T improves target-band emission at controlled T",
    "antenna": "G_realized, bandwidth, efficiency, or compactness beats control",
    "near_field_sensor": "LDOS or SNR improves with useful outcoupling",
    "photonic_phononic_bandgap": "gap exists and defect state has controlled eta_out",
    "plasmonic_metamaterial": "hot spots improve useful signal without loss domination",
    "superconducting_josephson": "Delta, Ic(B), R(T,B), flux signatures survive fractalization",
    "topological_nonreciprocal": "nu != 0 or S_ij != S_ji with gap/robustness/energy balance",
    "thermophotovoltaic": "PV-weighted spectral integral beats emitter/control",
    "raman_sers_spectroscopy": "SNR/residual-error improves against baseline-corrected control",
    "dielectric_resonator_array": "resonant modes and eta_rad beat nonfractal DRA array",
    "phonon_thermal_management": "thermal/acoustic metric improves without EM penalty",
    "optomechanical_cavity": "g0, Q, V_mode, or transduction beats control",
    "magnonic_spintronic": "magnon mode, nonreciprocity, or spin signal beats control",
    "quantum_microwave_cqed": "coherence/coupling improves without added loss domination",
    "sns_pd_single_photon_detector": "detection efficiency improves without dark-count/jitter penalty",
}

TIER1_REGIMES = {
    "absorber",
    "selective_emitter",
    "antenna",
    "thermophotovoltaic",
    "raman_sers_spectroscopy",
    "dielectric_resonator_array",
}

TIER2_REGIMES = {
    "near_field_sensor",
    "photonic_phononic_bandgap",
    "plasmonic_metamaterial",
    "phonon_thermal_management",
    "optomechanical_cavity",
    "magnonic_spintronic",
}

TIER1_GEOMETRIES = {
    "cubic_crft",
    "tetragonal_crft",
    "hexagonal_crft",
    "orthorhombic_crft",
    "quasicrystalline_crft",
    "semicrystalline_defected_crft",
    "zeolite_mof_porous_crft",
    "gyroid_minimal_surface_crft",
}


@dataclass(frozen=True)
class Family256:
    index: int
    geometry: str
    regime: str
    thesis: str
    oak_gate: str
    tier: str
    cvcd_key: str


def tier_for(geometry: str, regime: str) -> str:
    """Heuristic priority; not evidence of feasibility."""
    if regime in TIER1_REGIMES and geometry in TIER1_GEOMETRIES:
        return "Tier 1: simulate/prototype first"
    if regime in TIER2_REGIMES:
        return "Tier 2: requires solver/material controls"
    return "Tier 3: advanced / OAK strict"


def cvcd_key(geometry: str, regime: str) -> str:
    return f"CVCD16::{geometry}::{regime}"


def generate_families() -> list[Family256]:
    families: list[Family256] = []
    index = 1
    for geometry, geometry_note in GEOMETRIES:
        for regime, regime_note in REGIMES:
            families.append(
                Family256(
                    index=index,
                    geometry=geometry,
                    regime=regime,
                    thesis=f"{geometry}: {geometry_note} | {regime}: {regime_note}",
                    oak_gate=OAK_GATES[regime],
                    tier=tier_for(geometry, regime),
                    cvcd_key=cvcd_key(geometry, regime),
                )
            )
            index += 1
    return families


def summarize_by_tier(families: list[Family256]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for family in families:
        counts[family.tier] = counts.get(family.tier, 0) + 1
    return counts


def main() -> None:
    families = generate_families()
    print(f"families={len(families)}")
    print("tier_counts=")
    for tier, count in summarize_by_tier(families).items():
        print(f"  {tier}: {count}")
    print()
    for family in families:
        print(
            f"{family.index:03d}. {family.geometry} x {family.regime}\n"
            f"    thesis: {family.thesis}\n"
            f"    OAK: {family.oak_gate}\n"
            f"    tier: {family.tier}\n"
            f"    cvcd: {family.cvcd_key}\n"
        )


if __name__ == "__main__":
    main()
