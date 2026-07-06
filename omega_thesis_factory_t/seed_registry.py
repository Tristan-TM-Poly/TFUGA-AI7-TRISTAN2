"""Canonical ThesisSeed registry for first Tristan branches.

The registry keeps the first expansion set executable without requiring YAML or
third-party dependencies. JSON files in examples/thesis_seeds are the portable
artifacts; this module is the importable Python surface for tests and demos.
"""

from __future__ import annotations

from .core import ThesisSeed


CANONICAL_SEED_IDS: tuple[str, ...] = (
    "OMEGA_TRANSFORM_T",
    "OMEGA_FCRYST_T",
    "OMEGA_PREUVE_T",
    "OMEGA_AUTO2_T",
    "OMEGA_ENERGY_T",
)


def canonical_seeds() -> dict[str, ThesisSeed]:
    """Return the first five thesis seeds selected for expansion."""

    seeds = {
        "OMEGA_TRANSFORM_T": ThesisSeed(
            id="OMEGA_TRANSFORM_T",
            name="Ω-TRANSFORM-T / Transformées de Tristan",
            status="C",
            domain=("mathematics", "signal-processing", "compression", "software", "anomaly-detection"),
            core_axiom=(
                "A transform is a LOG/EXP bridge that compresses raw objects into multi-scale invariants "
                "and decompresses them into reconstruction, prediction, detection, or generation."
            ),
            cvcd_invariants=(
                "reconstruction error is measured",
                "energy or information conservation is tracked when applicable",
                "compression ratio is explicit",
                "multi-scale stability is benchmarked",
                "residuals feed M-",
            ),
            oak_risks=(
                "claiming FFWT superiority without benchmark",
                "confusing fertile fractal weighting with proof",
                "hiding reconstruction loss",
                "overfitting anomaly examples",
            ),
            code_targets=(
                "omega_transforms_package",
                "ffwt_module",
                "ffwtn_module",
                "compression_benchmark",
                "anomaly_detection_benchmark",
                "visualization_demo",
            ),
            git_targets=(
                "docs_transform_theory",
                "python_package",
                "pytest_suite",
                "oakbench_results",
                "negative_memory_report",
            ),
            venture_targets=(
                "signal_compression_toolkit",
                "scientific_anomaly_detection_api",
                "industrial_sensor_monitoring",
                "research_license",
            ),
            m_minus=(
                "Naive fractal weighting did not yet beat simple FWT on reconstruction in an earlier local OAK test.",
            ),
        ),
        "OMEGA_FCRYST_T": ThesisSeed(
            id="OMEGA_FCRYST_T",
            name="Ω-FCRYST-T / Théorie des Cristaux Fractals de Tristan",
            status="B",
            domain=("materials-science", "crystallography", "fractals", "diffraction", "simulation"),
            core_axiom=(
                "A fractal crystal is a system where order persists partially across scales, defects become "
                "informative residues, holes become operators, and spectral signatures compress the structure."
            ),
            cvcd_invariants=(
                "symmetry must specify space metric tolerance and scale",
                "diffraction prediction is separated from experimental proof",
                "holes are modeled as operators only after geometry and boundary conditions are explicit",
                "classical crystal and quasicrystal limits remain reference baselines",
            ),
            oak_risks=(
                "presenting visual motifs as crystallographic proof",
                "mixing exact point groups with approximate fractal symmetries",
                "claiming material properties without simulation or fabrication",
                "ignoring manufacturability and metrology limits",
            ),
            code_targets=(
                "fractal_lattice_generator",
                "fractal_point_group_analyzer",
                "diffraction_simulator_stub",
                "symmetry_residue_metrics",
                "materials_oakbench",
            ),
            git_targets=(
                "docs_fractal_crystals",
                "schema_fractal_crystal",
                "python_simulator_package",
                "simulation_examples",
                "oak_status_report",
            ),
            venture_targets=(
                "materials_discovery_tool",
                "metamaterial_design_studio",
                "mems_cpu_geometry_library",
                "photonics_pattern_ip",
            ),
            m_minus=(
                "Fractal symmetry language remains Status B until generator, metric, tolerance, scale and diffraction tests are explicit.",
            ),
        ),
        "OMEGA_PREUVE_T": ThesisSeed(
            id="OMEGA_PREUVE_T",
            name="Ω-PREUVE-T / Evidence Graphs for Fraud, Corruption and Crime Detection",
            status="B",
            domain=("evidence-analysis", "anti-fraud", "audit", "legaltech", "graph-systems"),
            core_axiom=(
                "A proof system is a chain-of-custody hypergraph where each claim must remain attached to "
                "source, timestamp, uncertainty, counter-hypothesis, legal boundary, and OAK status."
            ),
            cvcd_invariants=(
                "source provenance is mandatory",
                "claim evidence and inference are separated",
                "chain-of-custody is append-only",
                "false-positive cost is explicit",
                "human legal review remains a gate for accusations",
            ),
            oak_risks=(
                "defamation or wrongful accusation",
                "privacy violation",
                "treating correlation as guilt",
                "evidence contamination",
                "unsafe autonomous reporting",
            ),
            code_targets=(
                "evidence_graph_schema",
                "claim_evidence_linker",
                "chain_of_custody_ledger",
                "contradiction_detector",
                "legal_oak_report",
            ),
            git_targets=(
                "docs_evidence_graphs",
                "schemas_evidence",
                "red_team_examples",
                "audit_trail_tests",
                "safety_policy_report",
            ),
            venture_targets=(
                "audit_intelligence_platform",
                "investigative_research_os",
                "compliance_graph_api",
                "journalistic_evidence_assistant",
            ),
            m_minus=(
                "The system must never label a person guilty; it can only organize evidence, uncertainty and hypotheses for qualified review.",
            ),
        ),
        "OMEGA_AUTO2_T": ThesisSeed(
            id="OMEGA_AUTO2_T",
            name="Ω-AUTO²-T / Automatisation de l'Automatisation de Tristan",
            status="B",
            domain=("automation", "workflow-systems", "software-safety", "governance", "productivity"),
            core_axiom=(
                "Every repeated friction can become a workflow genome only after intent, permissions, dry-run, "
                "rollback, telemetry, and human sovereignty gates are explicit."
            ),
            cvcd_invariants=(
                "dry-run before deployment",
                "least privilege for external actions",
                "rollback or compensation path is required",
                "irreversible actions require explicit approval",
                "telemetry feeds M- and regeneration",
            ),
            oak_risks=(
                "unsafe autonomous actions",
                "secret leakage",
                "accidental deletion or publication",
                "platform lock-in",
                "automation without accountability",
            ),
            code_targets=(
                "workflow_manifest_schema",
                "dry_run_engine",
                "risk_permission_tensor",
                "rollback_ledger",
                "action_queue",
            ),
            git_targets=(
                "docs_auto2_architecture",
                "schemas_workflow_dna",
                "sandbox_examples",
                "incident_tests",
                "oakgate_ci_candidate",
            ),
            venture_targets=(
                "personal_research_os",
                "automation_consulting_toolkit",
                "safe_workflow_marketplace",
                "company_ops_copilot",
            ),
            m_minus=(
                "Zero-touch must never mean zero-control; the more sensitive the actuator, the stronger the gate.",
            ),
        ),
        "OMEGA_ENERGY_T": ThesisSeed(
            id="OMEGA_ENERGY_T",
            name="Ω-ENERGY-T / Systèmes Énergétiques de Tristan",
            status="B",
            domain=("energy-systems", "simulation", "control", "power-electronics", "safety"),
            core_axiom=(
                "Energy is not created; it is captured, converted, stored, routed, synchronized, filtered, "
                "recovered partially, or dissipated with explicit losses and safety boundaries."
            ),
            cvcd_invariants=(
                "energy conservation is mandatory",
                "losses and efficiency are measured",
                "thermal and electrical safety are explicit",
                "baselines include ideal and non-ideal models",
                "claims above 100 percent efficiency are rejected unless classified as measurement error or boundary mismatch",
            ),
            oak_risks=(
                "free-energy claims",
                "unsafe high-voltage or battery experimentation",
                "missing thermal balance",
                "confusing resonance with net energy gain",
                "publishing patent-sensitive details prematurely",
            ),
            code_targets=(
                "microgrid_simulator",
                "loss_accounting_module",
                "mppt_controller_stub",
                "storage_model",
                "energy_oakbench",
            ),
            git_targets=(
                "docs_energy_systems",
                "schemas_energy_flow",
                "simulation_examples",
                "safety_report",
                "benchmark_results",
            ),
            venture_targets=(
                "low_voltage_microgrid_lab",
                "energy_digital_twin",
                "power_loss_audit_tool",
                "education_simulator",
            ),
            m_minus=(
                "No energy-free or over-unity claim can be promoted; every gain claim must include boundary, units, losses and measurement uncertainty.",
            ),
        ),
    }
    for expected_id in CANONICAL_SEED_IDS:
        seeds[expected_id].validate()
    return seeds


def canonical_seed(seed_id: str) -> ThesisSeed:
    """Return one canonical seed by id."""

    seeds = canonical_seeds()
    try:
        return seeds[seed_id]
    except KeyError as exc:
        known = ", ".join(sorted(seeds))
        raise KeyError(f"unknown ThesisSeed {seed_id!r}; known ids: {known}") from exc
