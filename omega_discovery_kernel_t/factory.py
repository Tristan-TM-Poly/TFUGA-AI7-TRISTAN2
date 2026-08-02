"""Diversified 50,100-addition factory for Ω-DISCOVERY-KERNEL-T∞ R0.2.

The factory produces heterogeneous logical additions rather than repeating one
record shape.  Its canonical finite profile contains 100 cells, 1,000 claims,
5,000 evidence records, 1,000 experiments, 10,000 results, 10,000 actions,
10,000 M-minus rules, 1,000 universal identities, and 12,000 benchmark cases.
The profile is a scale test, not a permanent total-addition ceiling.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from omega_unbounded_t import GitHubDryRunPlanner, GitHubPlanPolicy


@dataclass(frozen=True, slots=True)
class BenchmarkFamily:
    family_id: str
    domain: str
    purpose: str
    observables: tuple[str, ...]
    continuous_generators: tuple[str, ...]
    discrete_events: tuple[str, ...]
    baselines: tuple[str, ...]
    metrics: tuple[str, ...]
    noise_models: tuple[str, ...]
    units: Mapping[str, str]
    failure_conditions: tuple[str, ...]
    safety_boundary: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _family(
    family_id: str,
    domain: str,
    purpose: str,
    observables: str,
    generators: str,
    events: str,
    baselines: str,
    metrics: str,
    noise: str,
    units: Mapping[str, str],
    failures: str,
    safety: str = "simulation_or_public_data_only",
) -> BenchmarkFamily:
    split = lambda value: tuple(item.strip() for item in value.split("|") if item.strip())
    return BenchmarkFamily(
        family_id=family_id,
        domain=domain,
        purpose=purpose,
        observables=split(observables),
        continuous_generators=split(generators),
        discrete_events=split(events),
        baselines=split(baselines),
        metrics=split(metrics),
        noise_models=split(noise),
        units=dict(units),
        failure_conditions=split(failures),
        safety_boundary=safety,
    )


BENCHMARK_FAMILIES: tuple[BenchmarkFamily, ...] = (
    _family(
        "raman_peak_morphology", "raman-spectroscopy",
        "Separate peak translation, broadening, amplitude, baseline drift, and topology changes.",
        "wavenumber|intensity|temperature", "translation|broadening|amplitude|baseline_drift",
        "peak_birth|peak_death|peak_merge", "lorentzian_nlls|voigt_nlls|independent_peak_tracker",
        "held_out_rmse|center_error|area_error|coverage|runtime",
        "gaussian|poisson|fluorescence_background|cosmic_spike",
        {"wavenumber": "cm^-1", "intensity": "a.u.", "temperature": "K"},
        "candidate loses to matched NLLS|uncertainty undercovers|peak count is unstable",
    ),
    _family(
        "ftir_band_morphology", "ftir-spectroscopy",
        "Resolve overlapping absorption bands, scattering, and baseline curvature.",
        "wavenumber|absorbance", "translation|broadening|area_change|baseline_curvature",
        "band_birth|band_death|shoulder_emergence", "voigt_nlls|rubberband_baseline|second_derivative",
        "held_out_rmse|band_area_error|species_ratio_error|runtime",
        "gaussian|multiplicative|water_vapor|scattering",
        {"wavenumber": "cm^-1", "absorbance": "1"},
        "species ratio is biased|derivative artifacts dominate|baseline changes conclusion",
    ),
    _family(
        "xrd_peak_and_phase", "xray-diffraction",
        "Track lattice shift, strain/size broadening, texture, and phase changes.",
        "two_theta|intensity", "peak_shift|microstrain|crystallite_size|texture",
        "phase_birth|phase_death|peak_split", "rietveld|pseudo_voigt|cross_correlation",
        "lattice_error|phase_fraction_error|profile_r_factor|runtime",
        "poisson|background|preferred_orientation|instrument_broadening",
        {"two_theta": "deg", "intensity": "counts"},
        "size and strain are confounded|phase fraction is nonidentifiable",
    ),
    _family(
        "nmr_line_shape", "nmr-spectroscopy",
        "Separate chemical shift, coupling, relaxation, exchange, phase, and baseline.",
        "frequency|intensity|time", "chemical_shift|linewidth|phase|exchange_rate",
        "resonance_birth|overlap|exchange_regime", "lorentzian_mixture|bayesian_lineshape|fourier_peak_pick",
        "shift_error|coupling_error|held_out_likelihood|coverage",
        "complex_gaussian|phase_error|baseline_roll|truncation",
        {"frequency": "Hz", "intensity": "a.u.", "time": "s"},
        "phase correction explains gain|exchange model is nonidentifiable",
    ),
    _family(
        "uvvis_absorption", "uv-visible-spectroscopy",
        "Track spectral shifts, oscillator strength, scattering, and mixtures.",
        "wavelength|absorbance", "spectral_shift|amplitude|width|scattering_background",
        "species_birth|species_death|aggregation", "gaussian_mixture|beer_lambert|nnls",
        "concentration_error|held_out_rmse|component_recovery|runtime",
        "gaussian|shot_noise|stray_light|baseline_offset",
        {"wavelength": "nm", "absorbance": "1"},
        "Beer-Lambert residual is structured|component count is unstable",
    ),
    _family(
        "fluorescence_lifetime", "fluorescence-spectroscopy",
        "Identify lifetime components, quenching, transfer, and instrument response.",
        "time|counts", "decay_rate|amplitude|background|instrument_response",
        "lifetime_birth|quenching_regime", "multi_exponential_nlls|poisson_mle|phasor",
        "lifetime_error|held_out_deviance|component_count",
        "poisson|dark_counts|timing_jitter",
        {"time": "ns", "counts": "counts"},
        "extra lifetime is unsupported|instrument response explains component",
    ),
    _family(
        "mass_spectrometry_isotopes", "mass-spectrometry",
        "Separate mass shift, isotope envelopes, adducts, fragments, and saturation.",
        "mass_to_charge|intensity", "mass_shift|intensity_scale|resolution_broadening",
        "adduct_birth|fragment_birth|envelope_change", "centroid_pick|isotope_match|nonnegative_deconvolution",
        "mass_error_ppm|formula_rank|envelope_similarity|runtime",
        "poisson|chemical_background|saturation|missing_peaks",
        {"mass_to_charge": "1", "intensity": "counts"},
        "formula rank degrades|adduct model overfits background",
    ),
    _family(
        "chromatographic_elution", "chromatography",
        "Track retention shift, width, tailing, co-elution, and new components.",
        "time|detector_signal", "retention_shift|broadening|tailing|amplitude",
        "compound_birth|coelution|column_regime", "emg_fit|mcr_als|traditional_integration",
        "retention_error|area_error|resolution|false_peak_rate",
        "gaussian|baseline_drift|spikes|carryover",
        {"time": "s", "detector_signal": "a.u."},
        "area bias exceeds tolerance|co-elution remains unresolved",
    ),
    _family(
        "electrochemical_impedance", "electrochemistry",
        "Identify resistance, capacitance, diffusion, and model-order changes.",
        "frequency|real_impedance|imag_impedance", "resistance|capacitance|diffusion",
        "new_arc|inductive_loop|model_order_change", "equivalent_circuit|drt|complex_spline",
        "complex_rmse|parameter_error|kk_residual|runtime",
        "complex_gaussian|frequency_jitter|drift|outlier",
        {"frequency": "Hz", "real_impedance": "ohm", "imag_impedance": "ohm"},
        "Kramers-Kronig fails|circuit parameters are nonunique",
    ),
    _family(
        "battery_degradation", "battery-systems",
        "Distinguish capacity fade, resistance growth, hysteresis, and thermal effects.",
        "cycle|capacity|voltage|temperature|resistance", "capacity_fade|resistance_growth|hysteresis",
        "knee_point|thermal_anomaly|failure_candidate", "linear_fade|exponential_fade|gaussian_process|ecm",
        "rul_error|calibration_error|false_alarm_rate",
        "sensor_noise|usage_variability|temperature_drift|missing_cycles",
        {"capacity": "1", "voltage": "V", "temperature": "K", "resistance": "ohm"},
        "RUL undercovers|knee detection is late|temperature confounds degradation",
        "public_or_certified_low_voltage_data_only",
    ),
    _family(
        "microgrid_dispatch", "energy-systems",
        "Audit source, storage, converter, load, loss, and control transformations.",
        "power|energy|voltage|state_of_charge", "solar_input|load_change|charge_discharge|converter_loss",
        "islanding|load_spike|storage_limit", "rule_dispatch|linear_programming|mpc",
        "unserved_energy|cost|losses|constraint_violations",
        "forecast_error|sensor_noise|outage|price_variation",
        {"power": "W", "energy": "J", "voltage": "V", "state_of_charge": "%"},
        "energy balance fails|constraint violation|baseline cost is lower",
        "simulation_only_no_grid_actuation",
    ),
    _family(
        "thermoelectric_conversion", "energy-materials",
        "Model coupled thermal, electrical, and loss transformations.",
        "temperature|voltage|current|power", "seebeck|joule_heating|thermal_conduction",
        "contact_change|material_transition|runaway_candidate", "lumped_model|finite_difference|linear_response",
        "power_error|temperature_error|energy_balance_residual",
        "temperature_noise|contact_resistance|ambient_drift",
        {"temperature": "K", "voltage": "V", "current": "A", "power": "W"},
        "energy residual exceeds tolerance|contact effect dominates",
        "simulation_or_certified_bench_only",
    ),
    _family(
        "metasurface_optics", "photonics",
        "Relate geometry and material changes to bounded optical response.",
        "wavelength|reflectance|transmittance|phase", "resonance_shift|linewidth|coupling|loss",
        "mode_birth|mode_crossing|symmetry_breaking", "transfer_matrix|coupled_mode|fdtd",
        "spectral_rmse|phase_error|energy_balance_residual",
        "fabrication_variation|material_loss|angle_jitter",
        {"wavelength": "nm", "reflectance": "1", "transmittance": "1", "phase": "rad"},
        "R plus T exceeds tolerance|reduced model fails near crossing",
    ),
    _family(
        "temporal_photonic_crystal", "photonics",
        "Track temporal modulation, conversion, and bounded energy exchange.",
        "time|frequency|field_amplitude", "temporal_modulation|frequency_shift|parametric_coupling",
        "bandgap_opening|instability|mode_conversion", "floquet|time_domain|coupled_mode",
        "frequency_error|field_rmse|energy_exchange_residual",
        "timing_jitter|modulation_noise|measurement_noise",
        {"time": "s", "frequency": "Hz", "field_amplitude": "a.u."},
        "Floquet baseline wins|energy exchange is unaccounted",
    ),
    _family(
        "mems_resonator", "mems",
        "Identify resonance, damping, nonlinear stiffness, and thermal drift.",
        "frequency|displacement|temperature", "frequency_shift|damping|duffing",
        "mode_jump|contact|failure_candidate", "linear_oscillator|duffing_fit|state_space",
        "frequency_error|quality_factor_error|forecast_rmse",
        "readout_noise|temperature_drift|drive_jitter",
        {"frequency": "Hz", "displacement": "nm", "temperature": "K"},
        "linear baseline is sufficient|nonlinear coefficient is unstable",
        "simulation_or_low_energy_certified_device_only",
    ),
    _family(
        "ebsd_orientation_field", "crystallography",
        "Measure orientation gradients, disorientation, holonomy, and uncertainty.",
        "orientation|position|confidence", "rotation_gradient|lattice_curvature|registration_drift",
        "grain_boundary|orientation_jump|unindexed_region", "minimum_disorientation|kam|crystal_plasticity",
        "orientation_error|boundary_f1|loop_residual|coverage",
        "orientation_noise|indexing_error|missing_pixels|symmetry_alias",
        {"orientation": "rad", "position": "um", "confidence": "1"},
        "point-group quotient is wrong|holonomy is misread as defect density",
    ),
    _family(
        "stress_strain_constitutive", "solid-mechanics",
        "Separate elastic, plastic, viscous, damage, and thermal components.",
        "strain|stress|time|temperature", "elastic|plastic_flow|relaxation|damage",
        "yield|unloading|damage_onset|fracture_candidate", "linear_elastic|ramberg_osgood|maxwell_kelvin|j2",
        "stress_rmse|yield_error|dissipation_residual",
        "load_noise|strain_drift|temperature_drift",
        {"strain": "1", "stress": "MPa", "time": "s", "temperature": "K"},
        "dissipation becomes negative|simpler law predicts equally well",
        "public_data_or_professionally_supervised_test_only",
    ),
    _family(
        "mass_action_kinetics", "chemical-kinetics",
        "Recover reaction-rate candidates under conservation constraints.",
        "time|concentration", "mass_action_rate|source|sink|transport",
        "species_birth|regime_change|measurement_limit", "ode_fit|log_linear|sindy",
        "parameter_error|held_out_rmse|mass_balance_residual",
        "gaussian|lognormal|censoring|sampling_jitter",
        {"time": "s", "concentration": "mol/L"},
        "mass conservation fails|log transform biases low concentrations",
    ),
    _family(
        "michaelis_menten", "enzyme-kinetics",
        "Distinguish saturation, inhibition, depletion, and transport limitation.",
        "time|substrate|product|rate", "catalytic_rate|binding_saturation|inhibition",
        "inhibition_onset|enzyme_deactivation", "mm_nlls|lineweaver_burk|mass_action_ode",
        "km_error|vmax_error|held_out_rate_rmse",
        "gaussian|heteroscedastic|detection_limit",
        {"time": "s", "substrate": "mol/L", "product": "mol/L", "rate": "mol/L"},
        "linearized fit is biased|full ODE is required",
    ),
    _family(
        "belousov_zhabotinsky", "nonlinear-chemistry",
        "Identify oscillation, phase, amplitude, bifurcation, and hidden-variable residue.",
        "time|concentration|optical_signal", "frequency|amplitude_growth|phase_drift",
        "bifurcation|oscillation_birth|oscillation_death", "oregonator|fourier|koopman_dmd",
        "phase_error|period_error|forecast_horizon|semigroup_defect",
        "measurement_noise|parameter_drift|sampling_jitter",
        {"time": "s", "concentration": "mol/L", "optical_signal": "a.u."},
        "phase forecast diverges|hidden-variable residue remains",
    ),
    _family(
        "carbon_cycle_reduced", "earth-systems",
        "Audit reduced carbon-reservoir flux models and conservation.",
        "time|carbon_stock|flux", "emission|uptake|exchange|decay",
        "policy_scenario|disturbance|regime_shift", "linear_box|published_reduced|persistence",
        "stock_rmse|flux_error|mass_balance|forecast_calibration",
        "observation_error|forcing_uncertainty|missing_data",
        {"time": "s", "carbon_stock": "kg", "flux": "kg"},
        "mass balance fails|uncertainty excludes observations",
    ),
    _family(
        "predator_prey_ecology", "ecology",
        "Distinguish interaction, capacity, seasonality, and intervention effects.",
        "time|prey_count|predator_count", "growth|predation|mortality|seasonality",
        "intervention|extinction|regime_shift", "lotka_volterra|logistic_pair|state_space",
        "forecast_rmse|coverage|extinction_false_alarm",
        "count_noise|missing_observation|seasonal_forcing",
        {"time": "s", "prey_count": "1", "predator_count": "1"},
        "interaction sign is unstable|seasonality explains coupling",
    ),
    _family(
        "instrument_calibration", "metrology",
        "Track offset, scale, nonlinearity, hysteresis, drift, and environment.",
        "reference|reading|temperature|time", "offset_drift|scale_drift|nonlinearity|temperature_sensitivity",
        "recalibration|firmware_change|range_change|fault", "linear_calibration|polynomial|gaussian_process",
        "calibration_error|coverage|drift_delay",
        "repeatability|reference_uncertainty|environmental_drift",
        {"reference": "1", "reading": "1", "temperature": "K", "time": "s"},
        "traceability missing|uncertainty undercovers|firmware unknown",
    ),
    _family(
        "time_series_drift", "monitoring",
        "Detect continuous drift, abrupt events, seasonality, and model failure.",
        "time|signal", "level_drift|scale_drift|frequency_drift|seasonality",
        "change_point|outage|sensor_replacement", "cusum|ewma|kalman|change_point",
        "detection_delay|false_alarm_rate|forecast_rmse",
        "gaussian|heavy_tail|missing_data|outlier",
        {"time": "s", "signal": "1"},
        "false alarm exceeds limit|seasonality is mistaken for drift",
    ),
    _family(
        "multiscale_anomaly", "signal-processing",
        "Compare FFWT candidates against established multiscale baselines.",
        "time|signal", "local_scale_change|transient|frequency_change",
        "anomaly_birth|anomaly_death|overlap", "dwt|wavelet_packet|scattering|matched_filter",
        "auroc|f1|localization_error|runtime|memory",
        "gaussian|colored|impulsive|nonstationary",
        {"time": "s", "signal": "1"},
        "unweighted transform wins|tuning budget is unmatched",
    ),
    _family(
        "image_deconvolution", "imaging",
        "Recover sources under known or uncertain PSF and audit resolution claims.",
        "pixel|intensity", "blur|translation|amplitude|background",
        "source_birth|overlap|psf_change", "wiener|richardson_lucy|sparse_deconvolution",
        "reconstruction_rmse|localization_error|resolution_curve|runtime",
        "gaussian|poisson|read_noise|psf_mismatch",
        {"pixel": "pixel", "intensity": "counts"},
        "resolution fails held-out simulation|PSF mismatch explains gain",
    ),
    _family(
        "local_linearization", "scientific-computing",
        "Map residual and validity domains of local linear models.",
        "state|response", "jacobian|affine_offset|local_residual",
        "validity_boundary|equilibrium_change|singularity", "constant|direct_nonlinear|quadratic_taylor",
        "local_rmse|validity_radius|runtime|stability_mismatch",
        "state_noise|response_noise|sampling_gap",
        {"state": "1", "response": "1"},
        "residual exceeds tolerance|quadratic baseline wins",
    ),
    _family(
        "koopman_dmd", "dynamical-systems",
        "Compare operator embeddings for nonlinear trajectory prediction.",
        "time|state", "koopman_operator|continuous_generator|forcing",
        "mode_birth|regime_change|rank_change", "dmd|extended_dmd|sindy|neural_state_space",
        "forecast_rmse|spectral_error|rank|description_length",
        "gaussian|process_noise|missing_state|irregular_sampling",
        {"time": "s", "state": "1"},
        "forecast degrades|embedding dimension is unstable",
    ),
    _family(
        "control_lqr_mpc", "control-systems",
        "Compare controllers under constraints, disturbances, and model mismatch.",
        "time|state|control", "closed_loop_dynamics|control_action|disturbance",
        "constraint_activation|saturation|instability", "pid|lqr|linear_mpc|nonlinear_mpc",
        "tracking_error|control_effort|constraint_violations|runtime",
        "sensor_noise|disturbance|model_mismatch",
        {"time": "s", "state": "1", "control": "1"},
        "stability is lost|constraint violation|simpler controller wins",
        "simulation_only_until_professional_review",
    ),
    _family(
        "error_correction", "information-systems",
        "Relate expected and observed syndromes to channel errors.",
        "bit|syndrome|error_rate", "bit_flip_rate|burst_error|channel_drift",
        "uncorrectable_pattern|decoder_failure|regime_change", "hamming|repetition|maximum_likelihood",
        "ber|fer|latency|miscorrection_rate",
        "binary_symmetric|burst|erasure|nonstationary",
        {"bit": "1", "syndrome": "1", "error_rate": "1"},
        "miscorrection exceeds baseline|syndrome is ambiguous",
    ),
    _family(
        "software_ci_regression", "software-engineering",
        "Treat commits, tests, performance, coverage, and incidents as transformations.",
        "test_status|runtime|memory|coverage", "code_change|dependency_change|configuration_change",
        "test_failure|performance_regression|security_alert", "previous_main|release_tag|control_branch",
        "failure_count|runtime_delta|memory_delta|coverage_delta",
        "flaky_test|runner_variance|network_variance",
        {"test_status": "1", "runtime": "s", "memory": "MiB", "coverage": "%"},
        "change is not reproducible|runner variance explains delta",
    ),
    _family(
        "epistemic_density", "knowledge-engineering",
        "Measure evidence growth, falsification coverage, proof density, and staleness.",
        "concept_count|claim_count|evidence_count|test_count", "concept_expansion|evidence_growth|refutation|canonization",
        "evidence_regression|stale_status|contradiction|promotion", "raw_counts|manual_audit|repository_history",
        "evidence_coverage|falsification_coverage|canonical_density|audit_time",
        "duplicate_claim|self_citation|stale_file|alias_collision",
        {"concept_count": "1", "claim_count": "1", "evidence_count": "1", "test_count": "1"},
        "count growth is mistaken for truth|internal coherence replaces external evidence",
    ),
    _family(
        "legal_ip_gate", "legal-ip",
        "Route disclosure, license, prior art, patent, secret, and confidentiality states.",
        "artifact|disclosure|license|prior_art", "publication|license_change|ownership_change|prior_art_discovery",
        "disclosure|conflict|permission_change|filing_candidate", "manual_checklist|license_scanner|prior_art_search",
        "unclassified_rate|license_conflict_rate|review_latency",
        "missing_metadata|ambiguous_ownership|stale_license",
        {"artifact": "1", "disclosure": "1", "license": "1", "prior_art": "1"},
        "disclosure precedes review|license conflict remains",
        "human_legal_review_required",
    ),
    _family(
        "product_market_evidence", "product",
        "Separate hypotheses, usage, outcomes, cost, revenue, and retention evidence.",
        "usage|outcome|cost|revenue", "onboarding|feature_change|pricing_change|support_change",
        "activation|churn|purchase|incident", "previous_version|manual_service|no_intervention",
        "activation_rate|retention|outcome_delta|gross_margin",
        "selection_bias|seasonality|small_sample|missing_feedback",
        {"usage": "1", "outcome": "1", "cost": "CAD", "revenue": "CAD"},
        "no external user evidence|revenue is confused with forecast",
        "consent_privacy_and_financial_review_required",
    ),
    _family(
        "document_code_divergence", "documentation",
        "Detect mismatches between claims, examples, APIs, tests, and outputs.",
        "claim|code_signature|test_result|example_output", "code_change|doc_change|dependency_change",
        "semantic_diff|stale_example|broken_claim|repair", "manual_review|doctest|api_snapshot",
        "divergence_precision|divergence_recall|repair_latency",
        "format_change|alias|generated_timestamp",
        {"claim": "1", "code_signature": "1", "test_result": "1", "example_output": "1"},
        "format-only change is semantic|real divergence is missed",
    ),
    _family(
        "repository_supply_chain", "software-security",
        "Track dependencies, licenses, vulnerabilities, provenance, and updates.",
        "dependency|version|license|vulnerability", "dependency_update|license_change|advisory_publish",
        "vulnerability|typosquat|provenance_gap|patch", "sbom_diff|lockfile_audit|manual_review",
        "unresolved_vulnerabilities|provenance_coverage|patch_latency",
        "false_positive_advisory|transitive_dependency|stale_database",
        {"dependency": "1", "version": "1", "license": "1", "vulnerability": "1"},
        "critical advisory is missed|untrusted source is executed",
        "sandbox_and_human_review_required",
    ),
)


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    case_id: str
    family_id: str
    seed: int
    noise_model: str
    generator_variant: str
    baseline: str
    metric: str
    difficulty: float
    metadata: Mapping[str, Any]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class KnowledgeFrontierTargets:
    cells: int = 100
    claims_per_cell: int = 10
    evidence_per_claim: int = 5
    experiments_per_claim: int = 1
    results_per_experiment: int = 10
    actions_per_result: int = 1
    memory_rules_per_result: int = 1
    identities_per_claim: int = 1
    benchmark_cases: int = 12_000

    def validate(self) -> list[str]:
        return [f"{key} cannot be negative" for key, value in asdict(self).items() if int(value) < 0]

    @property
    def claim_count(self) -> int:
        return self.cells * self.claims_per_cell

    @property
    def evidence_count(self) -> int:
        return self.claim_count * self.evidence_per_claim

    @property
    def experiment_count(self) -> int:
        return self.claim_count * self.experiments_per_claim

    @property
    def result_count(self) -> int:
        return self.experiment_count * self.results_per_experiment

    @property
    def action_count(self) -> int:
        return self.result_count * self.actions_per_result

    @property
    def memory_count(self) -> int:
        return self.result_count * self.memory_rules_per_result

    @property
    def identity_count(self) -> int:
        return self.claim_count * self.identities_per_claim

    @property
    def total_additions(self) -> int:
        return (
            self.cells + self.claim_count + self.evidence_count + self.experiment_count
            + self.result_count + self.action_count + self.memory_count
            + self.identity_count + self.benchmark_cases
        )

    def to_dict(self) -> dict[str, int]:
        return {
            **{key: int(value) for key, value in asdict(self).items()},
            "claim_count": self.claim_count,
            "evidence_count": self.evidence_count,
            "experiment_count": self.experiment_count,
            "result_count": self.result_count,
            "action_count": self.action_count,
            "memory_count": self.memory_count,
            "identity_count": self.identity_count,
            "total_additions": self.total_additions,
        }


def _digest(*parts: object) -> str:
    text = json.dumps(parts, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(text.encode("utf-8")).hexdigest()


def iter_benchmark_cases(count: int, *, seed_offset: int = 0) -> Iterator[BenchmarkCase]:
    if count < 0:
        raise ValueError("count cannot be negative")
    for index in range(count):
        family = BENCHMARK_FAMILIES[index % len(BENCHMARK_FAMILIES)]
        cycle = index // len(BENCHMARK_FAMILIES)
        case_id = f"BCASE-{family.family_id.upper()}-{index:08d}-{_digest(family.family_id, index)[:10]}"
        yield BenchmarkCase(
            case_id=case_id,
            family_id=family.family_id,
            seed=seed_offset + cycle,
            noise_model=family.noise_models[cycle % len(family.noise_models)],
            generator_variant=family.continuous_generators[cycle % len(family.continuous_generators)],
            baseline=family.baselines[cycle % len(family.baselines)],
            metric=family.metrics[cycle % len(family.metrics)],
            difficulty=((index % 101) + 1) / 101.0,
            metadata={
                "domain": family.domain,
                "purpose": family.purpose,
                "units": dict(family.units),
                "failure_conditions": list(family.failure_conditions),
                "safety_boundary": family.safety_boundary,
                "status": "generated_benchmark_case_not_scientific_result",
            },
        )


def _addition(
    addition_id: str,
    namespace: str,
    kind: str,
    payload: Mapping[str, Any],
    provenance: Sequence[str],
    *,
    risk: str = "normal",
) -> dict[str, object]:
    return {
        "addition_id": addition_id,
        "namespace": namespace,
        "kind": kind,
        "payload": dict(payload),
        "provenance": list(provenance),
        "risk": risk,
        "metadata": {
            "generated_by": "omega_discovery_kernel_t.factory",
            "oak_status": "logical_addition_candidate_not_external_validation",
        },
    }


def iter_knowledge_frontier_additions(
    targets: KnowledgeFrontierTargets | None = None,
) -> Iterator[dict[str, object]]:
    targets = targets or KnowledgeFrontierTargets()
    issues = targets.validate()
    if issues:
        raise ValueError("; ".join(issues))
    provenance = ("omega_discovery_kernel_t/factory.py",)
    evidence_kinds = ("source", "equation", "code", "test", "baseline")

    for cell_index in range(targets.cells):
        family = BENCHMARK_FAMILIES[cell_index % len(BENCHMARK_FAMILIES)]
        cell_id = f"KC-FRONTIER-{cell_index:05d}"
        namespace = f"knowledge/{family.domain}"
        yield _addition(cell_id, namespace, "knowledge_cell", {
            "cell_id": cell_id,
            "subject": f"Frontier cell {cell_index} — {family.family_id}",
            "definition": family.purpose,
            "domain": family.domain,
            "oak_status": "FORMALIZED",
            "benchmark_family": family.family_id,
            "failure_conditions": list(family.failure_conditions),
            "safety_boundary": family.safety_boundary,
        }, provenance)

        for claim_offset in range(targets.claims_per_cell):
            claim_index = cell_index * targets.claims_per_cell + claim_offset
            claim_id = f"CLM-FRONTIER-{claim_index:07d}"
            generator = family.continuous_generators[claim_offset % len(family.continuous_generators)]
            metric = family.metrics[claim_offset % len(family.metrics)]
            claim_payload = {
                "claim_id": claim_id,
                "knowledge_cell_id": cell_id,
                "text": f"{generator} may improve or explain {metric} under matched protocols.",
                "canonical_key": f"{family.family_id}:{generator}:{metric}",
                "scope": f"generated frontier family={family.family_id}",
                "assumptions": ["isolated split", "matched tuning", "units preserved"],
                "failure_conditions": list(family.failure_conditions),
                "status": "hypothesis",
            }
            yield _addition(claim_id, namespace, "claim", claim_payload, provenance)

            for identity_offset in range(targets.identities_per_claim):
                identity_id = f"UID-FRONTIER-{claim_index:07d}-{identity_offset:02d}"
                yield _addition(identity_id, "identity", "universal_identity", {
                    "local_id": claim_id,
                    "kind": "claim",
                    "version": f"0.{identity_offset + 1}.0",
                    "content_hash": _digest(claim_payload, identity_offset),
                    "source_ids": [cell_id],
                    "semantic_equivalence": "not_assumed",
                }, provenance)

            for evidence_offset in range(targets.evidence_per_claim):
                evidence_id = f"EVD-FRONTIER-{claim_index:07d}-{evidence_offset:02d}"
                evidence_kind = evidence_kinds[evidence_offset % len(evidence_kinds)]
                yield _addition(evidence_id, namespace, "evidence", {
                    "evidence_id": evidence_id,
                    "claim_id": claim_id,
                    "kind": evidence_kind,
                    "title": f"Generated {evidence_kind} contract for {claim_id}",
                    "status": "candidate",
                    "content_hash": _digest(claim_id, evidence_kind, evidence_offset),
                    "boundary": "replace with real source, code, test, baseline, or measurement",
                }, provenance)

            for experiment_offset in range(targets.experiments_per_claim):
                experiment_id = f"EXP-FRONTIER-{claim_index:07d}-{experiment_offset:02d}"
                baseline = family.baselines[experiment_offset % len(family.baselines)]
                yield _addition(experiment_id, f"experiment/{family.domain}", "experiment_spec", {
                    "experiment_id": experiment_id,
                    "claim_id": claim_id,
                    "benchmark_family": family.family_id,
                    "generator": generator,
                    "baseline": baseline,
                    "metric": metric,
                    "protocol": "generated matched-budget dry-run",
                    "success_criteria": "candidate beats or explains held-out baseline",
                    "rollback": "delete generated artifacts and retain previous canon",
                    "safety_boundary": family.safety_boundary,
                    "reversible": True,
                }, provenance)

                for result_offset in range(targets.results_per_experiment):
                    result_index = (
                        (claim_index * targets.experiments_per_claim + experiment_offset)
                        * targets.results_per_experiment + result_offset
                    )
                    result_id = f"RES-FRONTIER-{result_index:09d}"
                    success = result_offset % 3 == 0
                    yield _addition(result_id, f"result/{family.domain}", "result_packet", {
                        "result_id": result_id,
                        "experiment_id": experiment_id,
                        "claim_id": claim_id,
                        "success": success,
                        "metric": metric,
                        "candidate_value": round(0.01 + (result_offset % 11) * 0.005, 6),
                        "baseline_value": round(0.02 + (result_offset % 7) * 0.004, 6),
                        "uncertainty": round(0.001 + (result_offset % 5) * 0.0005, 6),
                        "units": dict(family.units),
                        "seed": result_offset,
                        "status": "generated_result_contract_not_measured_result",
                    }, provenance)

                    for action_offset in range(targets.actions_per_result):
                        action_id = f"ACT-FRONTIER-{result_index:09d}-{action_offset:02d}"
                        yield _addition(action_id, f"action/{family.domain}", "action_proposal", {
                            "action_id": action_id,
                            "result_id": result_id,
                            "action": "external validation queue" if success else "record failure and redesign",
                            "expected_information_gain": round(0.2 + (result_offset % 8) * 0.08, 4),
                            "risk": 0.05,
                            "cost": 0.1,
                            "rollback": "retain previous status and remove generated action",
                            "human_review_required": True,
                        }, provenance)

                    for memory_offset in range(targets.memory_rules_per_result):
                        memory_id = f"MMINUS-FRONTIER-{result_index:09d}-{memory_offset:02d}"
                        yield _addition(memory_id, f"memory/{family.domain}", "negative_memory", {
                            "memory_id": memory_id,
                            "result_id": result_id,
                            "context": f"generated {family.family_id} benchmark result",
                            "prohibited_inference": "generated contract is real scientific evidence",
                            "reusable_rule": "require provenance, matched baseline, held-out data, and uncertainty",
                            "active_constraint": True,
                        }, provenance)

    for case in iter_benchmark_cases(targets.benchmark_cases):
        yield _addition(
            case.case_id,
            f"benchmark/{case.family_id}",
            "benchmark_case",
            case.to_dict(),
            provenance,
        )


def benchmark_registry_manifest() -> dict[str, object]:
    return {
        "schema": "omega_discovery_kernel.benchmark_registry.v0.2",
        "family_count": len(BENCHMARK_FAMILIES),
        "domains": sorted({family.domain for family in BENCHMARK_FAMILIES}),
        "families": [family.to_dict() for family in BENCHMARK_FAMILIES],
        "oak_boundary": "Benchmark contracts are not datasets, measurements, comparative results, or certification.",
    }


def plan_knowledge_frontier(
    output_dir: str | Path,
    *,
    targets: KnowledgeFrontierTargets | None = None,
    initial_shard_bytes: int = 262_144,
    shard_growth_factor: float = 2.0,
    proposed_branch: str = "feat/omega-discovery-frontier-generated",
) -> dict[str, object]:
    targets = targets or KnowledgeFrontierTargets()
    issues = targets.validate()
    if issues:
        raise ValueError("; ".join(issues))
    planner = GitHubDryRunPlanner(
        output_dir,
        policy=GitHubPlanPolicy(
            initial_shard_bytes=initial_shard_bytes,
            shard_growth_factor=shard_growth_factor,
            strict_records=True,
            require_provenance=True,
        ),
        proposed_branch=proposed_branch,
    )
    report = planner.plan(iter_knowledge_frontier_additions(targets))
    result = {
        "schema": "omega_discovery_kernel.knowledge_frontier_plan.v0.2",
        "targets": targets.to_dict(),
        "report": report.to_dict(),
        "count_matches_target": report.unique_additions == targets.total_additions,
        "finite_target_is_not_permanent_ceiling": True,
        "remote_mutations": 0,
    }
    root = Path(output_dir)
    (root / "knowledge-frontier-summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (root / "benchmark-registry.json").write_text(
        json.dumps(benchmark_registry_manifest(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


assert len(BENCHMARK_FAMILIES) == 36
assert KnowledgeFrontierTargets().total_additions == 50_100
