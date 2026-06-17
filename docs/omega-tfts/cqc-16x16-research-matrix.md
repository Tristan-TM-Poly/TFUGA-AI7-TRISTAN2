# Omega-CQC-TFTS-CRFT — Matrice 16x16 / 256 Familles de Recherche

**Status:** canonical expansion / OAK-gated roadmap.  
**Module family:** Omega-CQC, CRFT, TFTS, HGFM, CVCD, OAK.  
**Claim strength:** research generator and prioritization map, not experimental proof of all families.

## 0. Core upgrade

The previous `8 x 8` matrix produced 64 families. The `16 x 16` matrix expands the design space to:

```text
16 geometry / symmetry / material-topology classes
x
16 physical / functional regimes
=
256 research families
```

This is the new canonical design generator:

```text
F_ij = geometry_class_i tensor regime_j
```

where each family must carry:

```text
thesis + CVCD signature + OAK gate + prototype priority + control comparison
```

---

## 1. The 16 geometry / symmetry classes

```text
01 cubic_crft
02 tetragonal_crft
03 hexagonal_crft
04 trigonal_rhombohedral_crft
05 orthorhombic_crft
06 monoclinic_crft
07 triclinic_crft
08 quasicrystalline_crft
09 semcrystalline_defected_crft
10 amorphous_hyperuniform_crft
11 moire_twisted_bilayer_crft
12 2d_layered_vanderwaals_crft
13 perovskite_octahedral_crft
14 zeolite_mof_porous_crft
15 gyroid_minimal_surface_crft
16 cut_stretched_miller_slab_crft
```

### Why these 16 matter

The first seven cover classical crystal classes and their anisotropy ladder.  
`quasicrystalline` adds non-periodic long-range order.  
`semicrystalline_defected` turns disorder into programmable localization.  
`amorphous_hyperuniform` targets isotropic band gaps and suppressed density fluctuations.  
`moire_twisted_bilayer` adds twist-angle tunability and flat-band style localization.  
`2d_layered_vanderwaals` adds exfoliable anisotropic sheets and heterostructures.  
`perovskite_octahedral` adds octahedral tilts, soft phonons, polar domains, and photovoltaic/superconducting relevance.  
`zeolite_mof_porous` adds pre-existing porous crystalline channels.  
`gyroid_minimal_surface` adds triply periodic continuous surfaces and high connectivity.  
`cut_stretched_miller_slab` makes cuts, Miller planes, ports, and affine stretch first-class design variables.

---

## 2. The 16 physical / functional regimes

```text
01 absorber
02 selective_emitter
03 antenna
04 near_field_sensor
05 photonic_phononic_bandgap
06 plasmonic_metamaterial
07 superconducting_josephson
08 topological_nonreciprocal
09 thermophotovoltaic
10 raman_sers_spectroscopy
11 dielectric_resonator_array
12 phonon_thermal_management
13 optomechanical_cavity
14 magnonic_spintronic
15 quantum_microwave_cqed
16 sns_pd_single_photon_detector
```

### Why these 16 matter

The first eight are the original physical regimes.  
`thermophotovoltaic` turns selective emission into energy conversion.  
`raman_sers_spectroscopy` targets high-SNR molecular sensing and reduced baseline correction burden.  
`dielectric_resonator_array` makes the dielectric-filled holes into the main antenna/cavity objects.  
`phonon_thermal_management` uses the same fractal geometry for heat, acoustic and phononic control.  
`optomechanical_cavity` couples photons and phonons.  
`magnonic_spintronic` uses magnetic textures and spin waves.  
`quantum_microwave_cqed` targets low-volume microwave cavities and superconducting circuits.  
`sns_pd_single_photon_detector` targets fractal nanowire / nanocavity detector geometries.

---

## 3. 16 x 16 master formula

```text
Omega_16x16 = {
  Family(i,j) = G_i tensor R_j
  for i in 1..16,
      j in 1..16
}
```

Each family is scored by:

```text
Score(i,j) =
  OAK_gate(i,j)
  + CVCD_signature(i,j)
  + prototype_priority(i,j)
  + control_set(i,j)
```

Canonical family object:

```text
Family_ij = (
  geometry_class_i,
  regime_j,
  symmetry_group,
  material_tensor_map,
  void_operator,
  cut_or_port,
  stretch_or_strain,
  defect_field,
  observable_targets,
  controls,
  CVCD,
  OAK_gate,
  tier
)
```

---

## 4. OAK gates by regime

```text
absorber:                  A_T(omega) > A_control at matched thickness/mass/volume
selective_emitter:          epsilon_T improves target-band emission at controlled T
antenna:                   G_realized, bandwidth, efficiency or compactness beats control
near_field_sensor:          LDOS or SNR improves with useful outcoupling
photonic_phononic_bandgap:  gap exists and defect state has controlled eta_out
plasmonic_metamaterial:     hot spots improve useful signal without loss domination
superconducting_josephson:  Delta, Ic(B), R(T,B), flux signatures survive fractalization
topological_nonreciprocal:  nu != 0 or S_ij != S_ji with gap/robustness/energy balance
thermophotovoltaic:         weighted PV integral beats selective-emitter control
raman_sers_spectroscopy:    SNR/residual-error improves against baseline-corrected control
dielectric_resonator_array: measured resonant modes and eta_rad beat nonfractal DRA array
phonon_thermal_management:  thermal/acoustic metric improves without EM penalty
optomechanical_cavity:      g0, Q, V_mode or transduction beats control
magnonic_spintronic:        magnon mode, nonreciprocity or spin signal beats control
quantum_microwave_cqed:     coherence/coupling improves without added loss dominating
sns_pd_single_photon_detector: detection efficiency improves without dark-count/jitter penalty
```

---

## 5. Tiering rule

```text
Tier 1 = simulate/prototype first
Tier 2 = needs EM/material solver and careful controls
Tier 3 = advanced / OAK strict / quantum or topological evidence required
```

Default Tier 1 families:

```text
crystal classes with absorber, selective_emitter, antenna, DRA, thermophotovoltaic, Raman/SERS
```

Default Tier 2 families:

```text
near_field_sensor, bandgap, plasmonic, phonon_thermal, optomechanical, magnonic
```

Default Tier 3 families:

```text
superconducting/Josephson, topological/nonreciprocal, quantum microwave/cQED, SNSPD
```

---

## 6. Top 16 immediate Tier-1 families

```text
01 cubic_crft x absorber
02 cubic_crft x dielectric_resonator_array
03 tetragonal_crft x antenna
04 tetragonal_crft x selective_emitter
05 hexagonal_crft x raman_sers_spectroscopy
06 hexagonal_crft x antenna
07 orthorhombic_crft x thermophotovoltaic
08 orthorhombic_crft x selective_emitter
09 quasicrystalline_crft x absorber
10 quasicrystalline_crft x bandgap
11 semcrystalline_defected_crft x near_field_sensor
12 semcrystalline_defected_crft x raman_sers_spectroscopy
13 zeolite_mof_porous_crft x absorber
14 zeolite_mof_porous_crft x selective_emitter
15 gyroid_minimal_surface_crft x antenna
16 gyroid_minimal_surface_crft x absorber
```

Why these first: they can be prototyped or simulated without immediately requiring proof of superconductivity, topology, quantum coherence, or nonreciprocal thermodynamic claims.

---

## 7. Top 16 high-risk / high-reward families

```text
01 moire_twisted_bilayer_crft x topological_nonreciprocal
02 moire_twisted_bilayer_crft x superconducting_josephson
03 2d_layered_vanderwaals_crft x quantum_microwave_cqed
04 2d_layered_vanderwaals_crft x sns_pd_single_photon_detector
05 perovskite_octahedral_crft x thermophotovoltaic
06 perovskite_octahedral_crft x phonon_thermal_management
07 quasicrystalline_crft x topological_nonreciprocal
08 gyroid_minimal_surface_crft x superconducting_josephson
09 cut_stretched_miller_slab_crft x topological_nonreciprocal
10 cut_stretched_miller_slab_crft x quantum_microwave_cqed
11 amorphous_hyperuniform_crft x photonic_phononic_bandgap
12 amorphous_hyperuniform_crft x near_field_sensor
13 trigonal_rhombohedral_crft x magnonic_spintronic
14 hexagonal_crft x magnonic_spintronic
15 zeolite_mof_porous_crft x quantum_microwave_cqed
16 semicrystalline_defected_crft x sns_pd_single_photon_detector
```

These are fertile but require strict OAK gates: gap, robustness, energy balance, coherence, device controls, or low-temperature measurements.

---

## 8. Top 16 synergies introduced by 16x16

1. `gyroid_minimal_surface + antenna` -> continuous high-connectivity radiating skeleton.  
2. `zeolite_mof_porous + absorber` -> porous crystalline channels become ready-made functional voids.  
3. `moire_twisted_bilayer + topological` -> twist-angle tunability meets fractal ports and defects.  
4. `amorphous_hyperuniform + bandgap` -> isotropic gap candidates without ordinary periodicity.  
5. `cut_stretched_miller_slab + DRA` -> crystal cuts become directional dielectric resonator arrays.  
6. `perovskite_octahedral + phonon_thermal` -> soft lattice and octahedral tilts shape heat/phonon transport.  
7. `hexagonal + Raman/SERS` -> 2D symmetry and high-interface fractal hotspots improve sensing.  
8. `orthorhombic + thermophotovoltaic` -> three-axis anisotropy sculpts selective emission.  
9. `semicrystalline_defected + near_field_sensor` -> defects become deliberate LDOS concentrators.  
10. `quasicrystalline + absorber` -> nonperiodic modal density supports broadband capture.  
11. `2d_layered_vanderwaals + SNSPD` -> layered nanosheets plus fractal nanowires target photon capture.  
12. `trigonal + magnonic` -> chirality and rotation channels guide spin-wave asymmetry.  
13. `cubic + DRA` -> controlled baseline for dielectric-filled cavity arrays.  
14. `tetragonal + antenna` -> one privileged axis gives natural directionality.  
15. `monoclinic_triclinic + selective_emitter` -> low symmetry breaks degeneracies and enriches spectra.  
16. `CQC + OAK` -> the matrix itself becomes a falsifiable research generator.

---

## 9. CVCD-16x16

```text
CVCD_16x16 = (
  geometry_id,
  regime_id,
  symmetry_group,
  lattice_or_pointset,
  unit_cell_or_tile,
  void_operator,
  cut_port,
  stretch_tensor,
  defect_field,
  epsilon_tensor,
  mu_tensor,
  sigma_tensor,
  A_over_V,
  beta_vector,
  rho_Bragg,
  rho_modes,
  LDOS_gain,
  eta_out,
  G_real,
  Gamma_band,
  thermal_score,
  quantum_score,
  fabrication_score,
  OAK_gate,
  tier
)
```

---

## 10. Final 16x16 mantra

```text
8x8 made the map.
16x16 makes the atlas.
The cube is no longer the object.
The object is a generator of functional symmetries.
Each geometry class chooses structure.
Each physical regime chooses measurement.
Each crossing is a research family.
CVCD compresses the family.
OAK rejects the beautiful but false.
```
