"""Mass knowledge, benchmark, and GitHub-addition factory for R0.2.

The factory diversifies the frontier instead of repeating one synthetic record.
Its canonical profile emits 50,100 logical additions across knowledge cells,
claims, evidence, experiments, results, actions, negative memories, identities,
and benchmark cases.  The count is a finite validation target, never a
permanent controller ceiling.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

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
    *,
    observables: Sequence[str],
    generators: Sequence[str],
    events: Sequence[str],
    baselines: Sequence[str],
    metrics: Sequence[str],
    noise: Sequence[str],
    units: Mapping[str, str],
    failures: Sequence[str],
    safety: str = "simulation_or_public_data_only",
) -> BenchmarkFamily:
    return BenchmarkFamily(
        family_id=family_id,
        domain=domain,
        purpose=purpose,
        observables=tuple(observables),
        continuous_generators=tuple(generators),
        discrete_events=tuple(events),
        baselines=tuple(baselines),
        metrics=tuple(metrics),
        noise_models=tuple(noise),
        units=dict(units),
        failure_conditions=tuple(failures),
        safety_boundary=safety,
    )


BENCHMARK_FAMILIES: tuple[BenchmarkFamily, ...] = (
    _family(
        "raman_peak_morphology", "raman-spectroscopy",
        "Separate peak translation, broadening, amplitude, baseline drift, and peak birth/death.",
        observables=("wavenumber", "intensity", "temperature"),
        generators=("translation", "broadening", "amplitude", "baseline_drift"),
        events=("peak_birth", "peak_death", "peak_merge", "phase_transition_candidate"),
        baselines=("scipy_curve_fit_lorentzian", "voigt_nlls", "independent_peak_tracker"),
        metrics=("held_out_rmse", "center_error", "area_error", "coverage_probability", "runtime"),
        noise=("gaussian", "poisson", "fluorescence_background", "cosmic_spike"),
        units={"wavenumber": "cm^-1", "intensity": "a.u.", "temperature": "K"},
        failures=("candidate loses to matched NLLS", "uncertainty undercovers", "peak count is unstable"),
    ),
    _family(
        "ftir_band_morphology", "ftir-spectroscopy",
        "Resolve overlapping absorption bands and baseline/scattering effects.",
        observables=("wavenumber", "absorbance"),
        generators=("translation", "broadening", "area_change", "baseline_curvature"),
        events=("band_birth", "band_death", "shoulder_emergence"),
        baselines=("voigt_nlls", "rubberband_baseline", "second_derivative_peak_pick"),
        metrics=("held_out_rmse", "band_area_error", "species_ratio_error", "runtime"),
        noise=("gaussian", "multiplicative", "water_vapor", "scattering"),
        units={"wavenumber": "cm^-1", "absorbance": "1"},
        failures=("species ratio is biased", "derivative artifacts dominate", "baseline choice changes conclusion"),
    ),
    _family(
        "xrd_peak_and_phase", "xray-diffraction",
        "Track lattice shift, strain broadening, texture, and phase appearance.",
        observables=("two_theta", "intensity"),
        generators=("peak_shift", "microstrain_broadening", "size_broadening", "texture_change"),
        events=("phase_birth", "phase_death", "peak_split"),
        baselines=("rietveld_refinement", "pseudo_voigt_fit", "cross_correlation_shift"),
        metrics=("lattice_error", "phase_fraction_error", "profile_r_factor", "runtime"),
        noise=("poisson", "background", "preferred_orientation", "instrument_broadening"),
        units={"two_theta": "deg", "intensity": "counts"},
        failures=("generator confounds size and strain", "phase fraction is not identifiable"),
    ),
    _family(
        "nmr_line_shape", "nmr-spectroscopy",
        "Separate chemical shift, coupling, relaxation, exchange, and baseline effects.",
        observables=("frequency", "intensity", "time"),
        generators=("chemical_shift", "linewidth", "phase", "exchange_rate"),
        events=("resonance_birth", "resonance_overlap", "exchange_regime_change"),
        baselines=("lorentzian_mixture", "bayesian_lineshape", "fourier_peak_pick"),
        metrics=("shift_error", "coupling_error", "held_out_likelihood", "coverage_probability"),
        noise=("complex_gaussian", "phase_error", "baseline_roll", "truncation"),
        units={"frequency": "Hz", "intensity": "a.u.", "time": "s"},
        failures=("phase correction dominates gain", "exchange model is nonidentifiable"),
    ),
    _family(
        "uvvis_absorption", "uv-visible-spectroscopy",
        "Track spectral shifts, oscillator strength, scattering, and species mixtures.",
        observables=("wavelength", "absorbance"),
        generators=("spectral_shift", "amplitude", "width", "scattering_background"),
        events=("species_birth", "species_death", "aggregation_candidate"),
        baselines=("gaussian_mixture", "beer_lambert_linear_unmixing", "nonnegative_least_squares"),
        metrics=("concentration_error", "held_out_rmse", "component_recovery", "runtime"),
        noise=("gaussian", "shot_noise", "stray_light", "baseline_offset"),
        units={"wavelength": "nm", "absorbance": "1"},
        failures=("Beer-Lambert residual is structured", "component count is unstable"),
    ),
    _family(
        "fluorescence_lifetime", "fluorescence-spectroscopy",
        "Identify lifetime components, quenching, transfer, and instrument-response effects.",
        observables=("time", "counts"),
        generators=("decay_rate", "amplitude", "background", "instrument_response"),
        events=("lifetime_component_birth", "quenching_regime_change"),
        baselines=("multi_exponential_nlls", "maximum_likelihood_decay", "phasor_analysis"),
        metrics=("lifetime_error", "held_out_deviance", "component_count_accuracy"),
        noise=("poisson", "dark_counts", "timing_jitter"),
        units={"time": "ns", "counts": "counts"},
        failures=("extra lifetime is unsupported", "instrument response explains apparent component"),
    ),
    _family(
        "mass_spectrometry_isotopes", "mass-spectrometry",
        "Separate mass shift, isotopic envelopes, adducts, fragmentation, and detector saturation.",
        observables=("mass_to_charge", "intensity"),
        generators=("mass_shift", "intensity_scale", "resolution_broadening"),
        events=("adduct_birth", "fragment_birth", "isotope_envelope_change"),
        baselines=("centroid_peak_pick", "isotope_pattern_match", "nonnegative_deconvolution"),
        metrics=("mass_error_ppm", "formula_rank", "envelope_similarity", "runtime"),
        noise=("poisson", "chemical_background", "saturation", "missing_peaks"),
        units={"mass_to_charge": "1", "intensity": "counts"},
        failures=("candidate formula rank degrades", "adduct model overfits background"),
    ),
    _family(
        "chromatographic_elution", "chromatography",
        "Track retention shift, width, tailing, co-elution, and new components.",
        observables=("time", "detector_signal"),
        generators=("retention_shift", "broadening", "tailing", "amplitude"),
        events=("compound_birth", "coelution", "column_regime_change"),
        baselines=("emg_peak_fit", "multivariate_curve_resolution", "traditional_integration"),
        metrics=("retention_error", "area_error", "resolution", "false_peak_rate"),
        noise=("gaussian", "baseline_drift", "spikes", "carryover"),
        units={"time": "s", "detector_signal": "a.u."},
        failures=("area bias exceeds tolerance", "co-elution remains unresolved"),
    ),
    _family(
        "electrochemical_impedance", "electrochemistry",
        "Identify circuit or distributed-process changes from complex impedance spectra.",
        observables=("frequency", "real_impedance", "imag_impedance"),
        generators=("resistance_change", "capacitance_change", "diffusion_change"),
        events=("new_arc", "inductive_loop", "model_order_change"),
        baselines=("equivalent_circuit_nlls", "distribution_of_relaxation_times", "complex_spline"),
        metrics=("complex_rmse", "parameter_error", "kramers_kronig_residual", "runtime"),
        noise=("complex_gaussian", "frequency_jitter", "drift", "outlier"),
        units={"frequency": "Hz", "real_impedance": "ohm", "imag_impedance": "ohm"},
        failures=("Kramers-Kronig consistency fails", "circuit parameters are nonunique"),
    ),
    _family(
        "battery_degradation", "battery-systems",
        "Distinguish capacity fade, resistance growth, lithium loss, and thermal effects.",
        observables=("cycle", "capacity", "voltage", "temperature", "resistance"),
        generators=("capacity_fade_rate", "resistance_growth", "hysteresis_change"),
        events=("knee_point", "thermal_anomaly", "cell_failure_candidate"),
        baselines=("linear_fade", "exponential_fade", "gaussian_process", "physics_informed_ecm"),
        metrics=("remaining_useful_life_error", "calibration_error", "false_alarm_rate"),
        noise=("sensor_noise", "usage_variability", "temperature_drift", "missing_cycles"),
        units={"capacity": "1", "voltage": "V", "temperature": "K", "resistance": "ohm"},
        failures=("RUL undercovers", "knee detection is late", "temperature confounds degradation"),
        safety="public_or_certified_low_voltage_data_only",
    ),
    _family(
        "microgrid_dispatch", "energy-systems",
        "Evaluate source, storage, converter, and load-control generators under losses.",
        observables=("power", "energy", "voltage", "state_of_charge"),
        generators=("solar_input", "load_change", "charge_discharge", "converter_loss"),
        events=("islanding", "load_spike", "storage_limit"),
        baselines=("rule_based_dispatch", "linear_programming", "model_predictive_control"),
        metrics=("unserved_energy", "cost", "losses", "constraint_violations"),
        noise=("forecast_error", "sensor_noise", "outage", "price_variation"),
        units={"power": "W", "energy": "J", "voltage": "V", "state_of_charge": "%"},
        failures=("energy balance fails", "constraint violation occurs", "baseline cost is lower"),
        safety="simulation_only_no_grid_actuation",
    ),
    _family(
        "thermoelectric_conversion", "energy-materials",
        "Model coupled temperature, voltage, current, and heat-flow transformations.",
        observables=("temperature", "voltage", "current", "power"),
        generators=("seebeck_response", "joule_heating", "thermal_conduction"),
        events=("contact_change", "material_transition", "thermal_runaway_candidate"),
        baselines=("lumped_thermoelectric_model", "finite_difference_heat", "linear_response"),
        metrics=("power_error", "temperature_error", "energy_balance_residual"),
        noise=("temperature_noise", "contact_resistance", "ambient_drift"),
        units={"temperature": "K", "voltage": "V", "current": "A", "power": "W"},
        failures=("energy conservation residual exceeds tolerance", "contact effect dominates"),
        safety="simulation_or_certified_bench_only",
    ),
    _family(
        "metasurface_optics", "photonics",
        "Relate geometry and material changes to bounded optical response.",
        observables=("wavelength", "reflectance", "transmittance", "phase"),
        generators=("resonance_shift", "linewidth", "coupling", "loss"),
        events=("mode_birth", "mode_crossing", "symmetry_breaking"),
        baselines=("transfer_matrix", "coupled_mode_theory", "fdtd_reference"),
        metrics=("spectral_rmse", "phase_error", "energy_balance_residual"),
        noise=("fabrication_variation", "material_loss", "angle_jitter"),
        units={"wavelength": "nm", "reflectance": "1", "transmittance": "1", "phase": "rad"},
        failures=("R+T exceeds physical tolerance", "reduced model fails near mode crossing"),
    ),
    _family(
        "temporal_photonic_crystal", "photonics",
        "Track frequency conversion and temporal modulation without violating energy accounting.",
        observables=("time", "frequency", "field_amplitude"),
        generators=("temporal_modulation", "frequency_shift", "parametric_coupling"),
        events=("bandgap_opening", "instability_candidate", "mode_conversion"),
        baselines=("floquet_model", "time_domain_integration", "coupled_mode_theory"),
        metrics=("frequency_error", "field_rmse", "energy_exchange_residual"),
        noise=("timing_jitter", "modulation_noise", "measurement_noise"),
        units={"time": "s", "frequency": "Hz", "field_amplitude": "a.u."},
        failures=("Floquet baseline wins", "energy exchange is unaccounted"),
    ),
    _family(
        "mems_resonator", "mems",
        "Identify resonance, damping, nonlinear stiffness, and thermal drift.",
        observables=("frequency", "displacement", "temperature"),
        generators=("frequency_shift", "damping_change", "duffing_nonlinearity"),
        events=("mode_jump", "contact_event", "failure_candidate"),
        baselines=("linear_oscillator", "duffing_fit", "state_space_identification"),
        metrics=("frequency_error", "quality_factor_error", "forecast_rmse"),
        noise=("readout_noise", "temperature_drift", "drive_jitter"),
        units={"frequency": "Hz", "displacement": "nm", "temperature": "K"},
        failures=("linear baseline is sufficient", "nonlinear coefficient is unstable"),
        safety="simulation_or_low_energy_certified_device_only",
    ),
    _family(
        "ebsd_orientation_field", "crystallography",
        "Measure orientation gradients, disorientation, holonomy, and uncertainty on crystal maps.",
        observables=("orientation", "position", "confidence_index"),
        generators=("rotation_gradient", "lattice_curvature", "registration_drift"),
        events=("grain_boundary", "orientation_jump", "unindexed_region"),
        baselines=("minimum_disorientation", "kernel_average_misorientation", "crystal_plasticity_reference"),
        metrics=("orientation_error", "boundary_f1", "loop_residual", "uncertainty_coverage"),
        noise=("orientation_noise", "indexing_error", "missing_pixels", "symmetry_alias"),
        units={"orientation": "rad", "position": "um", "confidence_index": "1"},
        failures=("point-group quotient is mishandled", "holonomy is misread as defect density"),
    ),
    _family(
        "stress_strain_constitutive", "solid-mechanics",
        "Separate elastic, plastic, viscoelastic, damage, and thermal components.",
        observables=("strain", "stress", "time", "temperature"),
        generators=("elastic_response", "plastic_flow", "viscous_relaxation", "damage_growth"),
        events=("yield", "unloading", "damage_onset", "fracture_candidate"),
        baselines=("linear_elasticity", "ramberg_osgood", "maxwell_kelvin", "j2_plasticity"),
        metrics=("stress_rmse", "yield_error", "energy_dissipation_residual"),
        noise=("load_cell_noise", "strain_gauge_drift", "temperature_drift"),
        units={"strain": "1", "stress": "MPa", "time": "s", "temperature": "K"},
        failures=("dissipation becomes negative", "simpler constitutive law predicts equally well"),
        safety="public_data_or_professionally_supervised_test_only",
    ),
    _family(
        "mass_action_kinetics", "chemical-kinetics",
        "Recover reaction-order and rate candidates under conservation constraints.",
        observables=("time", "concentration"),
        generators=("mass_action_rate", "source", "sink", "transport"),
        events=("species_birth", "regime_change", "measurement_limit"),
        baselines=("standard_ode_fit", "log_linear_rate_fit", "sindy"),
        metrics=("parameter_error", "held_out_rmse", "mass_balance_residual"),
        noise=("gaussian", "lognormal", "censoring", "sampling_jitter"),
        units={"time": "s", "concentration": "mol/L"},
        failures=("mass conservation fails", "log transform biases low concentrations"),
        safety="simulation_or_public_kinetics_data_only",
    ),
    _family(
        "michaelis_menten", "enzyme-kinetics",
        "Distinguish saturation, inhibition, substrate depletion, and transport limitation.",
        observables=("time", "substrate", "product", "rate"),
        generators=("catalytic_rate", "binding_saturation", "inhibition"),
        events=("inhibition_onset", "enzyme_deactivation"),
        baselines=("michaelis_menten_nlls", "lineweaver_burk", "full_mass_action_ode"),
        metrics=("km_error", "vmax_error", "held_out_rate_rmse"),
        noise=("gaussian", "heteroscedastic", "detection_limit"),
        units={"time": "s", "substrate": "mol/L", "product": "mol/L", "rate": "mol/L"},
        failures=("linearized fit is biased", "full ODE is required"),
    ),
    _family(
        "belousov_zhabotinsky", "nonlinear-chemistry",
        "Identify oscillatory regime, phase, amplitude, bifurcation, and hidden-variable residues.",
        observables=("time", "concentration", "optical_signal"),
        generators=("oscillation_frequency", "amplitude_growth", "phase_drift"),
        events=("bifurcation", "oscillation_birth", "oscillation_death"),
        baselines=("oregonator", "fourier_model", "koopman_dmd"),
        metrics=("phase_error", "period_error", "forecast_horizon", "semigroup_defect"),
        noise=("measurement_noise", "parameter_drift", "sampling_jitter"),
        units={"time": "s", "concentration": "mol/L", "optical_signal": "a.u."},
        failures=("phase forecast diverges", "hidden variable residue remains structured"),
        safety="simulation_or_public_data_only",
    ),
    _family(
        "carbon_cycle_reduced", "earth-systems",
        "Audit reduced carbon-reservoir flux models and conservation residues.",
        observables=("time", "carbon_stock", "flux"),
        generators=("emission", "uptake", "exchange", "decay"),
        events=("policy_scenario", "disturbance", "regime_shift_candidate"),
        baselines=("linear_box_model", "published_reduced_model", "persistence"),
        metrics=("stock_rmse", "flux_error", "mass_balance_residual", "forecast_calibration"),
        noise=("observation_error", "forcing_uncertainty", "missing_data"),
        units={"time": "s", "carbon_stock": "kg", "flux": "kg"},
        failures=("mass balance fails", "uncertainty excludes observed trajectory"),
    ),
    _family(
        "predator_prey_ecology", "ecology",
        "Distinguish interaction, carrying-capacity, seasonal, and intervention effects.",
        observables=("time", "prey_count", "predator_count"),
        generators=("growth", "predation", "mortality", "seasonality"),
        events=("intervention", "extinction_candidate", "regime_shift"),
        baselines=("lotka_volterra", "logistic_predator_prey", "state_space_model"),
        metrics=("forecast_rmse", "coverage_probability", "extinction_false_alarm"),
        noise=("count_noise", "missing_observation", "seasonal_forcing"),
        units={"time": "s", "prey_count": "1", "predator_count": "1"},
        failures=("interaction sign is unstable", "seasonality explains apparent coupling"),
    ),
    _family(
        "instrument_calibration", "metrology",
        "Track offset, scale, nonlinearity, hysteresis, drift, and environmental sensitivity.",
        observables=("reference", "reading", "temperature", "time"),
        generators=("offset_drift", "scale_drift", "nonlinearity", "temperature_sensitivity"),
        events=("recalibration", "firmware_change", "range_change", "fault_candidate"),
        baselines=("linear_calibration", "polynomial_calibration", "gaussian_process_calibration"),
        metrics=("calibration_error", "uncertainty_coverage", "drift_detection_delay"),
        noise=("repeatability", "reference_uncertainty", "environmental_drift"),
        units={"reference": "1", "reading": "1", "temperature": "K", "time": "s"},
        failures=("traceability is missing", "uncertainty budget undercovers", "firmware version is unknown"),
    ),
    _family(
        "time_series_drift", "monitoring",
        "Detect continuous drift, abrupt events, seasonality, and model failure.",
        observables=("time", "signal"),
        generators=("level_drift", "scale_drift", "frequency_drift", "seasonality"),
        events=("change_point", "outage", "sensor_replacement"),
        baselines=("cusum", "ewma", "kalman_filter", "change_point_detection"),
        metrics=("detection_delay", "false_alarm_rate", "forecast_rmse"),
        noise=("gaussian", "heavy_tail", "missing_data", "outlier"),
        units={"time": "s", "signal": "1"},
        failures=("false alarm exceeds limit", "seasonality is mistaken for drift"),
    ),
    _family(
        "multiscale_anomaly", "signal-processing",
        "Compare FFWT-style representations against established multiscale baselines.",
        observables=("time", "signal"),
        generators=("local_scale_change", "transient", "frequency_change"),
        events=("anomaly_birth", "anomaly_death", "overlap"),
        baselines=("dwt", "wavelet_packet", "scattering_transform", "matched_filter"),
        metrics=("auroc", "f1", "localization_error", "runtime", "memory"),
        noise=("gaussian", "colored", "impulsive", "nonstationary"),
        units={"time": "s", "signal": "1"},
        failures=("unweighted transform wins", "hyperparameter budget is unmatched"),
    ),
    _family(
        "image_deconvolution", "imaging",
        "Recover sources under known or uncertain PSF while auditing super-resolution claims.",
        observables=("pixel", "intensity"),
        generators=("blur", "translation", "amplitude", "background"),
        events=("source_birth", "source_overlap", "psf_change"),
        baselines=("wiener", "richardson_lucy", "sparse_deconvolution"),
        metrics=("reconstruction_rmse", "localization_error", "resolution_curve", "runtime"),
        noise=("gaussian", "poisson", "read_noise", "psf_mismatch"),
        units={"pixel": "pixel", "intensity": "counts"},
        failures=("claimed resolution fails held-out simulation", "PSF mismatch explains gain"),
    ),
    _family(
        "local_linearization", "scientific-computing",
        "Map validity domains and residuals of local linear models.",
        observables=("state", "response"),
        generators=("jacobian", "affine_offset", "local_residual"),
        events=("validity_boundary", "equilibrium_change", "singularity_candidate"),
        baselines=("constant_model", "direct_nonlinear_evaluation", "quadratic_taylor"),
        metrics=("local_rmse", "validity_radius", "runtime", "stability_mismatch"),
        noise=("state_noise", "response_noise", "sampling_gap"),
        units={"state": "1", "response": "1"},
        failures=("residual exceeds tolerance inside claimed domain", "quadratic baseline wins"),
    ),
    _family(
        "koopman_dmd", "dynamical-systems",
        "Compare linear operator embeddings for nonlinear trajectory prediction.",
        observables=("time", "state"),
        generators=("koopman_operator", "continuous_generator", "forcing"),
        events=("mode_birth", "regime_change", "rank_change"),
        baselines=("dmd", "extended_dmd", "sindy", "neural_state_space"),
        metrics=("forecast_rmse", "spectral_error", "rank", "description_length"),
        noise=("gaussian", "process_noise", "missing_state", "irregular_sampling"),
        units={"time": "s", "state": "1"},
        failures=("out-of-sample forecast degrades", "embedding dimension is unstable"),
    ),
    _family(
        "control_lqr_mpc", "control-systems",
        "Compare local and predictive controllers under constraints and model mismatch.",
        observables=("time", "state", "control"),
        generators=("closed_loop_dynamics", "control_action", "disturbance"),
        events=("constraint_activation", "saturation", "instability_candidate"),
        baselines=("pid", "lqr", "linear_mpc", "nonlinear_mpc"),
        metrics=("tracking_error", "control_effort", "constraint_violations", "runtime"),
        noise=("sensor_noise", "disturbance", "model_mismatch"),
        units={"time": "s", "state": "1", "control": "1"},
        failures=("stability is lost", "constraint violation occurs", "simpler controller wins"),
        safety="simulation_only_until_professional_review",
    ),
    _family(
        "error_correction", "information-systems",
        "Relate expected and observed code syndromes to correctable and uncorrectable errors.",
        observables=("bit", "syndrome", "error_rate"),
        generators=("bit_flip_rate", "burst_error", "channel_drift"),
        events=("uncorrectable_pattern", "decoder_failure", "channel_regime_change"),
        baselines=("hamming_decoder", "repetition_code", "maximum_likelihood_decoder"),
        metrics=("ber", "fer", "decoder_latency", "miscorrection_rate"),
        noise=("binary_symmetric", "burst", "erasure", "nonstationary"),
        units={"bit": "1", "syndrome": "1", "error_rate": "1"},
        failures=("miscorrection exceeds baseline", "syndrome classification is ambiguous"),
    ),
    _family(
        "software_ci_regression", "software-engineering",
        "Treat commits, tests, performance, and incidents as reproducible transformation events.",
        observables=("test_status", "runtime", "memory", "coverage"),
        generators=("code_change", "dependency_change", "configuration_change"),
        events=("test_failure", "performance_regression", "security_alert"),
        baselines=("previous_main", "release_tag", "control_branch"),
        metrics=("failure_count", "runtime_delta", "memory_delta", "coverage_delta"),
        noise=("flaky_test", "runner_variance", "network_variance"),
        units={"test_status": "1", "runtime": "s", "memory": "MiB", "coverage": "%"},
        failures=("change is not reproducible", "runner variance explains delta"),
    ),
    _family(
        "epistemic_density", "knowledge-engineering",
        "Measure evidence growth, falsification coverage, proof density, and stale status.",
        observables=("concept_count", "claim_count", "evidence_count", "test_count"),
        generators=("concept_expansion", "evidence_growth", "refutation", "canonization"),
        events=("evidence_regression", "stale_status", "contradiction", "promotion"),
        baselines=("raw_count_dashboard", "manual_audit", "repository_history"),
        metrics=("evidence_coverage", "falsification_coverage", "canonical_density", "audit_time"),
        noise=("duplicate_claim", "self_citation", "stale_file", "alias_collision"),
        units={"concept_count": "1", "claim_count": "1", "evidence_count": "1", "test_count": "1"},
        failures=("count growth is mistaken for truth", "internal coherence replaces external evidence"),
    ),
    _family(
        "legal_ip_gate", "legal-ip",
        "Route public, patent, trade-secret, licensed, confidential, and prior-art states.",
        observables=("artifact", "disclosure", "license", "prior_art"),
        generators=("publication", "license_change", "ownership_change", "prior_art_discovery"),
        events=("disclosure", "conflict", "permission_change", "filing_candidate"),
        baselines=("manual_ip_checklist", "license_scanner", "prior_art_search"),
        metrics=("unclassified_rate", "license_conflict_rate", "review_latency"),
        noise=("missing_metadata", "ambiguous_ownership", "stale_license"),
        units={"artifact": "1", "disclosure": "1", "license": "1", "prior_art": "1"},
        failures=("public disclosure precedes review", "license conflict remains unresolved"),
        safety="human_legal_review_required",
    ),
    _family(
        "product_market_evidence", "product",
        "Separate product hypotheses, usage, customer outcomes, costs, and revenue evidence.",
        observables=("usage", "outcome", "cost", "revenue"),
        generators=("onboarding", "feature_change", "pricing_change", "support_change"),
        events=("activation", "churn", "purchase", "incident"),
        baselines=("previous_version", "manual_service", "no_intervention"),
        metrics=("activation_rate", "retention", "outcome_delta", "gross_margin"),
        noise=("selection_bias", "seasonality", "small_sample", "missing_feedback"),
        units={"usage": "1", "outcome": "1", "cost": "CAD", "revenue": "CAD"},
        failures=("no external user evidence", "revenue is confused with forecast"),
        safety="consent_privacy_and_financial_review_required",
    ),
    _family(
        "document_code_divergence", "documentation",
        "Detect mismatches between claims, examples, APIs, tests, and generated outputs.",
        observables=("claim", "code_signature", "test_result", "example_output"),
        generators=("code_change", "doc_change", "dependency_change"),
        events=("semantic_diff", "stale_example", "broken_claim", "repair"),
        baselines=("manual_review", "doctest", "api_snapshot"),
        metrics=("divergence_precision", "divergence_recall", "repair_latency"),
        noise=("format_change", "alias", "generated_timestamp"),
        units={"claim": "1", "code_signature": "1", "test_result": "1", "example_output": "1"},
        failures=("format-only change is reported as semantic", "real divergence is missed"),
    ),
    _family(
        "repository_supply_chain", "software-security",
        "Track dependencies, licenses, vulnerabilities, provenance, and update risk.",
        observables=("dependency", "version", "license", "vulnerability"),
        generators=("dependency_update", "license_change", "advisory_publish"),
        events=("vulnerability", "typosquat_candidate", "provenance_gap", "patch"),
        baselines=("sbom_diff", "lockfile_audit", "manual_review"),
        metrics=("unresolved_vulnerabilities", "provenance_coverage", "patch_latency"),
        noise=("false_positive_advisory", "transitive_dependency", "stale_database"),
        units={"dependency": "1", "version": "1", "license": "1", "vulnerability": "1"},
        failures=("critical advisory is missed", "untrusted source is automatically executed"),
        safety="sandbox_and_human_review_required",
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
        issues: list[str] = []
        for key, value in asdict(self).items():
            if int(value) < 0:
                issues.append(f"{key} cannot be negative")
        if self.cells == 0 and any(
            value for key, value in asdict(self).items() if key != "benchmark_cases"
        ):
            issues.append("non-benchmark targets require at least one cell")
        return issues

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
            self.cells
            + self.claim_count
            + self.evidence_count
            + self.experiment_count
            + self.result_count
            + self.action_count
            + self.memory_count
            + self.identity_count
            + self.benchmark_cases
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
    encoded = json.dumps(parts, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(encoded.encode("utf-8")).hexdigest()


def iter_benchmark_cases(count: int, *, seed_offset: int = 0) -> Iterator[BenchmarkCase]:
    if count < 0:
        raise ValueError("count cannot be negative")
    if not BENCHMARK_FAMILIES and count:
        raise RuntimeError("benchmark family registry is empty")
    for index in range(count):
        family = BENCHMARK_FAMILIES[index % len(BENCHMARK_FAMILIES)]
        cycle = index // len(BENCHMARK_FAMILIES)
        seed = seed_offset + cycle
        noise_model = family.noise_models[(cycle // max(len(family.continuous_generators), 1)) % len(family.noise_models)]
        generator_variant = family.continuous_generators[cycle % len(family.continuous_generators)]
        baseline = family.baselines[(cycle // max(len(family.noise_models), 1)) % len(family.baselines)]
        metric = family.metrics[(cycle // max(len(family.baselines), 1)) % len(family.metrics)]
        difficulty = ((index % 101) + 1) / 101.0
        case_id = f"BCASE-{family.family_id.upper()}-{index:08d}-{_digest(family.family_id, index)[:10]}"
        yield BenchmarkCase(
            case_id=case_id,
            family_id=family.family_id,
            seed=seed,
            noise_model=noise_model,
            generator_variant=generator_variant,
            baseline=baseline,
            metric=metric,
            difficulty=difficulty,
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
    *,
    provenance: Sequence[str],
    risk: str = "normal",
    metadata: Mapping[str, Any] | None = None,
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
            **dict(metadata or {}),
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

    for cell_index in range(targets.cells):
        family = BENCHMARK_FAMILIES[cell_index % len(BENCHMARK_FAMILIES)]
        cell_id = f"KC-FRONTIER-{cell_index:05d}"
        namespace = f"knowledge/{family.domain}"
        yield _addition(
            cell_id,
            namespace,
            "knowledge_cell",
            {
                "cell_id": cell_id,
                "subject": f"Frontier cell {cell_index} — {family.family_id}",
                "definition": family.purpose,
                "domain": family.domain,
                "oak_status": "FORMALIZED",
                "benchmark_family": family.family_id,
                "failure_conditions": list(family.failure_conditions),
                "safety_boundary": family.safety_boundary,
            },
            provenance=provenance,
        )

        for claim_offset in range(targets.claims_per_cell):
            claim_index = cell_index * targets.claims_per_cell + claim_offset
            claim_id = f"CLM-FRONTIER-{claim_index:07d}"
            generator = family.continuous_generators[claim_offset % len(family.continuous_generators)]
            metric = family.metrics[claim_offset % len(family.metrics)]
            claim_payload = {
                "claim_id": claim_id,
                "knowledge_cell_id": cell_id,
                "text": (
                    f"Generator candidate {generator} may improve or explain {metric} "
                    f"for the scoped {family.family_id} benchmark under matched protocols."
                ),
                "canonical_key": f"{family.family_id}:{generator}:{metric}",
                "scope": f"generated frontier case family={family.family_id}",
                "assumptions": [
                    "data split is isolated",
                    "baseline tuning budget is matched",
                    "units and uncertainty are preserved",
                ],
                "failure_conditions": list(family.failure_conditions),
                "status": "hypothesis",
            }
            yield _addition(
                claim_id,
                namespace,
                "claim",
                claim_payload,
                provenance=provenance,
            )

            for identity_offset in range(targets.identities_per_claim):
                identity_id = f"UID-FRONTIER-{claim_index:07d}-{identity_offset:02d}"
                yield _addition(
                    identity_id,
                    "identity",
                    "universal_identity",
                    {
                        "local_id": claim_id,
                        "kind": "claim",
                        "version": f"0.{identity_offset + 1}.0",
                        "content_hash": _digest(claim_payload, identity_offset),
                        "source_ids": [cell_id],
                        "semantic_equivalence": "not_assumed",
                    },
                    provenance=provenance,
                )

            for evidence_offset in range(targets.evidence_per_claim):
                evidence_id = f"EVD-FRONTIER-{claim_index:07d}-{evidence_offset:02d}"
                evidence_kinds = ("source", "equation", "code", "test", "baseline", "result", "counterexample")
                evidence_kind = evidence_kinds[evidence_offset % len(evidence_kinds)]
                yield _addition(
                    evidence_id,
                    namespace,
                    "evidence",
                    {
                        "evidence_id": evidence_id,
                        "claim_id": claim_id,
                        "kind": evidence_kind,
                        "title": f"Generated {evidence_kind} placeholder for {claim_id}",
                        "status": "candidate",
                        "content_hash": _digest(claim_id, evidence_kind, evidence_offset),
                        "boundary": "placeholder contract requiring real source, code, test, or measurement replacement",
                    },
                    provenance=provenance,
                )

            for experiment_offset in range(targets.experiments_per_claim):
                experiment_id = f"EXP-FRONTIER-{claim_index:07d}-{experiment_offset:02d}"
                benchmark = family.baselines[experiment_offset % len(family.baselines)]
                yield _addition(
                    experiment_id,
                    f"experiment/{family.domain}",
                    "experiment_spec",
                    {
                        "experiment_id": experiment_id,
                        "claim_id": claim_id,
                        "benchmark_family": family.family_id,
                        "generator": generator,
                        "baseline": benchmark,
                        "metric": metric,
                        "protocol": "generated matched-budget dry-run protocol",
                        "success_criteria": "candidate beats or explains baseline under held-out evaluation",
                        "rollback": "delete generated artifacts and retain previous canon",
                        "safety_boundary": family.safety_boundary,
                        "reversible": True,
                    },
                    provenance=provenance,
                )

                for result_offset in range(targets.results_per_experiment):
                    result_index = (
                        (claim_index * targets.experiments_per_claim + experiment_offset)
                        * targets.results_per_experiment
                        + result_offset
                    )
                    result_id = f"RES-FRONTIER-{result_index:09d}"
                    success = result_offset % 3 == 0
                    candidate_value = round(0.01 + (result_offset % 11) * 0.005, 6)
                    baseline_value = round(0.02 + (result_offset % 7) * 0.004, 6)
                    yield _addition(
                        result_id,
                        f"result/{family.domain}",
                        "result_packet",
                        {
                            "result_id": result_id,
                            "experiment_id": experiment_id,
                            "claim_id": claim_id,
                            "success": success,
                            "metric": metric,
                            "candidate_value": candidate_value,
                            "baseline_value": baseline_value,
                            "uncertainty": round(0.001 + (result_offset % 5) * 0.0005, 6),
                            "units": dict(family.units),
                            "seed": result_offset,
                            "status": "generated_result_contract_not_measured_result",
                        },
                        provenance=provenance,
                    )

                    for action_offset in range(targets.actions_per_result):
                        action_id = f"ACT-FRONTIER-{result_index:09d}-{action_offset:02d}"
                        yield _addition(
                            action_id,
                            f"action/{family.domain}",
                            "action_proposal",
                            {
                                "action_id": action_id,
                                "result_id": result_id,
                                "action": (
                                    "promote to external validation queue" if success
                                    else "record failure and redesign discriminating benchmark"
                                ),
                                "expected_information_gain": round(0.2 + (result_offset % 8) * 0.08, 4),
                                "risk": 0.05,
                                "cost": 0.1,
                                "rollback": "retain previous status and remove generated action",
                                "human_review_required": True,
                            },
                            provenance=provenance,
                        )

                    for memory_offset in range(targets.memory_rules_per_result):
                        memory_id = f"MMINUS-FRONTIER-{result_index:09d}-{memory_offset:02d}"
                        yield _addition(
                            memory_id,
                            f"memory/{family.domain}",
                            "negative_memory",
                            {
                                "memory_id": memory_id,
                                "result_id": result_id,
                                "context": f"generated {family.family_id} benchmark result",
                                "prohibited_inference": "generated result contract is real scientific evidence",
                                "reusable_rule": (
                                    "require real provenance, matched baseline, held-out data, and uncertainty "
                                    "before promotion"
                                ),
                                "active_constraint": True,
                            },
                            provenance=provenance,
                        )

    for case in iter_benchmark_cases(targets.benchmark_cases):
        yield _addition(
            case.case_id,
            f"benchmark/{case.family_id}",
            "benchmark_case",
            case.to_dict(),
            provenance=provenance,
            risk="normal",
        )


def benchmark_registry_manifest() -> dict[str, object]:
    return {
        "schema": "omega_discovery_kernel.benchmark_registry.v0.2",
        "family_count": len(BENCHMARK_FAMILIES),
        "domains": sorted({family.domain for family in BENCHMARK_FAMILIES}),
        "families": [family.to_dict() for family in BENCHMARK_FAMILIES],
        "oak_boundary": (
            "Registry entries define benchmark contracts and failure conditions. They are not datasets, "
            "measurements, comparative results, safety approvals, or scientific certification."
        ),
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
    Path(output_dir, "knowledge-frontier-summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    Path(output_dir, "benchmark-registry.json").write_text(
        json.dumps(benchmark_registry_manifest(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


assert len(BENCHMARK_FAMILIES) == 32
assert KnowledgeFrontierTargets().total_additions == 50_100
