"""Deterministic Raman closed-loop demonstration for Ω-DISCOVERY-KERNEL-T∞."""
from __future__ import annotations

from omega_generator_discovery_t import compile_morph_ir

from .events import DiscoveryEvent
from .kernel import DiscoveryLedger, generator_event_from_morph_ir


def build_raman_closed_loop() -> DiscoveryLedger:
    subject_id = "RAMAN-TEMPERATURE-MORPH-001"
    ledger = DiscoveryLedger()

    observation = ledger.append(
        DiscoveryEvent.create(
            "ObservationEvent",
            subject_id,
            "2026-08-02T17:00:00Z",
            source_hash="sha256:demo-spectrum-pair",
            provenance=("examples/omega_discovery_kernel_demo.py",),
            domain="raman-spectroscopy",
            status="synthetic_observation",
            payload={
                "before_peak_cm-1": 1000.0,
                "after_peak_cm-1": 1002.0,
                "before_hwhm_cm-1": 4.0,
                "after_hwhm_cm-1": 5.0,
                "temperature_delta_K": 20.0,
            },
            units={"peak": "cm^-1", "hwhm": "cm^-1", "temperature": "K"},
            uncertainty={"peak": 0.2, "hwhm": 0.3, "temperature": 0.5},
        )
    )

    claim = ledger.append(
        DiscoveryEvent.create(
            "ClaimEvent",
            subject_id,
            "2026-08-02T17:00:01Z",
            parent_ids=(observation.event_id,),
            provenance=("docs/omega_discovery_kernel_r0_1.md",),
            domain="raman-spectroscopy",
            status="hypothesis",
            payload={
                "text": "Temperature produces a reusable shift-plus-broadening Raman generator.",
                "canonical_key": "temperature causes reusable Raman shift and broadening generator",
                "scope": "synthetic single-peak Lorentzian pair",
                "assumptions": ["single isolated peak", "matched calibration", "no phase transition"],
                "failure_conditions": [
                    "held-out spectra exceed the preregistered error tolerance",
                    "a simpler independent peak tracker predicts equally well or better",
                ],
            },
        )
    )

    morph = compile_morph_ir(
        {
            "name": "raman_temperature_shift_broadening",
            "domain": "raman_spectrum",
            "codomain": "raman_spectrum",
            "continuous_generators": ["peak_translation", "linewidth_broadening"],
            "discrete_events": ["peak_birth", "peak_death"],
            "singular_events": ["peak_merge"],
            "invariants": ["nonnegative_intensity"],
            "residual": 0.03,
            "uncertainty": 0.02,
        }
    )
    generator = ledger.append(
        generator_event_from_morph_ir(
            morph,
            claim,
            timestamp="2026-08-02T17:00:02Z",
        )
    )

    experiment = ledger.append(
        DiscoveryEvent.create(
            "ExperimentSpec",
            subject_id,
            "2026-08-02T17:00:03Z",
            parent_ids=(generator.event_id,),
            provenance=("examples/omega_discovery_kernel_demo.py",),
            domain="raman-spectroscopy",
            status="dry_run_approved",
            payload={
                "name": "held_out_temperature_ramp",
                "baseline": "independent Lorentzian nonlinear least squares",
                "metric": "normalized spectral RMSE",
                "success_threshold": 0.02,
                "safety_limits": {"laser_power_mW": 1.0, "temperature_K": 350.0},
                "rollback_steps": ["restore_previous_temperature", "disable_laser"],
            },
            units={"laser_power": "mW", "temperature": "K"},
            human_approval=True,
            reversible=True,
        )
    )

    result = ledger.append(
        DiscoveryEvent.create(
            "ResultPacket",
            subject_id,
            "2026-08-02T17:00:04Z",
            parent_ids=(experiment.event_id,),
            source_hash="sha256:demo-held-out-result",
            provenance=("generated/omega_discovery_kernel_t/raman/result.json",),
            domain="raman-spectroscopy",
            status="reproduced",
            payload={
                "title": "Held-out Raman prediction missed the preregistered tolerance",
                "success": False,
                "metric": "normalized spectral RMSE",
                "value": 0.031,
                "threshold": 0.02,
                "baseline": {"name": "Lorentzian NLLS", "value": 0.018},
                "protocol": "held_out_temperature_ramp",
                "interpretation": "The two-generator model is insufficient for this scoped task.",
            },
            units={"spectral_rmse": "dimensionless"},
            uncertainty={"spectral_rmse": 0.003},
        )
    )

    transition = ledger.append(
        DiscoveryEvent.create(
            "OAKTransition",
            subject_id,
            "2026-08-02T17:00:05Z",
            parent_ids=(result.event_id,),
            provenance=("generated/omega_discovery_kernel_t/raman/audit.json",),
            domain="epistemic-governance",
            status="approved_transition",
            payload={
                "from_status": "SIMULATED",
                "to_status": "REFUTED",
                "cause": "Held-out error exceeded tolerance and lost to the declared baseline.",
                "scope": "two-generator single-peak model only",
            },
            human_approval=True,
        )
    )

    mminus = ledger.append(
        DiscoveryEvent.create(
            "MMinusRule",
            subject_id,
            "2026-08-02T17:00:06Z",
            parent_ids=(result.event_id, transition.event_id),
            provenance=("generated/omega_discovery_kernel_t/raman/m_minus.json",),
            domain="epistemic-governance",
            status="active_constraint",
            payload={
                "failure_context": "Held-out temperature ramp with overlapping background drift.",
                "prohibited_inference": "Shift plus broadening alone is a reusable physical explanation.",
                "reusable_rules": [
                    "include baseline drift as a competing generator",
                    "compare against independently tuned nonlinear least squares",
                    "declare held-out tolerance before fitting",
                ],
            },
        )
    )

    ledger.append(
        DiscoveryEvent.create(
            "ActionProposal",
            subject_id,
            "2026-08-02T17:00:07Z",
            parent_ids=(mminus.event_id,),
            provenance=("generated/omega_discovery_kernel_t/raman/action.json",),
            domain="experiment-planning",
            status="human_review_draft",
            payload={
                "action": "Fit shift, broadening, and baseline-drift candidates with matched cross-validation.",
                "expected_information_gain": 0.72,
                "risk": 0.05,
                "cost": 0.15,
                "rollback": "retain previous model and event ledger",
            },
            human_approval=False,
            reversible=True,
        )
    )
    return ledger
