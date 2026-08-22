from __future__ import annotations

from .model import (
    BarrierClass,
    CertificateFamily,
    EpistemicStatus,
    MMinusRecord,
    MomentTensorSpec,
    MomentWordMode,
    ResearchBundle,
    ResearchRoute,
)


ANTHROPIC_2026_FAMILY = CertificateFamily(
    family_id="anthropic-weil-bandwidth-one-2026",
    current_bound=0.6725,
    method_ceiling=0.6818,
    fourier_support_radius=1.0,
    status=EpistemicStatus.EXTERNAL_REPORTED,
    assumptions=(
        "Use only the theorem family and information class declared by the external 2026 source.",
        "Do not infer the Riemann Hypothesis from the reported proportion bound.",
    ),
    source_refs=(
        "https://www.anthropic.com/research/riemann-zeta",
        "https://github.com/anthropics/zeta-23-lean",
    ),
    notes=(
        "0.6725 and 0.6818 are stored as external reported values pending independent local reconstruction.",
    ),
)


def default_bundle(target_bound: float = 0.70) -> ResearchBundle:
    # R0.2 defaults to the weaker, generally valid cyclic trace quotient rather
    # than silently assuming arbitrary permutation symmetry for products of
    # noncommuting compressed operators.
    moment_spec = MomentTensorSpec(
        max_order=4,
        window_count=3,
        base_support_radius=1.0,
        include_cross_moments=True,
        word_mode=MomentWordMode.CYCLIC,
    )
    routes = [
        ResearchRoute(
            route_id="higher-spectral-moments",
            title="Lift from M1/M2 to higher and cyclic cross spectral moments",
            expected_information_gain=0.92,
            verification_strength=0.78,
            novelty_potential=0.82,
            estimated_cost=0.78,
            epistemic_risk=0.38,
            barrier_target=BarrierClass.NEW_ARITHMETIC_INFORMATION,
            dependencies=("explicit-formula", "moment-identities", "support-audit"),
        ),
        ResearchRoute(
            route_id="ffwt-weil-window-search",
            title="Search Gabor/FFWT-style test windows under an explicit support budget",
            expected_information_gain=0.62,
            verification_strength=0.87,
            novelty_potential=0.58,
            estimated_cost=0.42,
            epistemic_risk=0.22,
            barrier_target=BarrierClass.WINDOW_OPTIMIZATION,
            dependencies=("window-parameterization", "deterministic-optimizer", "baseline-replay"),
        ),
        ResearchRoute(
            route_id="lean-statement-roundtrip",
            title="Formalize the exact restricted theorem statement before proof search",
            expected_information_gain=0.48,
            verification_strength=0.98,
            novelty_potential=0.35,
            estimated_cost=0.55,
            epistemic_risk=0.12,
            barrier_target=BarrierClass.FORMALIZATION_DEBT,
            dependencies=("Lean4", "mathlib", "semantic-roundtrip"),
        ),
        ResearchRoute(
            route_id="countermodel-court",
            title="Attack candidate lemmas and compression quotients with exact countermodels",
            expected_information_gain=0.80,
            verification_strength=0.94,
            novelty_potential=0.50,
            estimated_cost=0.32,
            epistemic_risk=0.08,
            barrier_target=BarrierClass.COUNTERMODEL_FAILURE,
            dependencies=("counterexample-family", "first-invalid-step-tracer"),
        ),
        ResearchRoute(
            route_id="theorem-debt-compiler",
            title="Reverse-engineer the minimal theorem debt for a requested certificate target",
            expected_information_gain=0.88,
            verification_strength=0.84,
            novelty_potential=0.86,
            estimated_cost=0.54,
            epistemic_risk=0.20,
            barrier_target=BarrierClass.NEW_ARITHMETIC_INFORMATION,
            dependencies=("support-debt", "moment-word-spec", "dual-sensitivity-interface"),
        ),
    ]
    mminus = [
        MMinusRecord(
            record_id="m-zeta-window-ceiling-001",
            barrier=BarrierClass.NEW_ARITHMETIC_INFORMATION,
            summary="Do not treat brute-force window search as a route above the declared bandwidth-one ceiling.",
            falsifier="A proposed >ceiling result must identify a theorem/input outside the declared information class.",
            source_refs=("anthropic-weil-bandwidth-one-2026",),
        ),
        MMinusRecord(
            record_id="m-zeta-fractal-proof-002",
            barrier=BarrierClass.NUMERICAL_ONLY,
            summary="Fractal or orbit structure is hypothesis generation, not RH evidence by itself.",
            falsifier="Require a precise statement plus analytical/formal obligations before promotion.",
            source_refs=("PR-149-omega-zeta-mandel-t",),
        ),
        MMinusRecord(
            record_id="m-zeta-full-symmetrization-003",
            barrier=BarrierClass.NONCOMMUTATIVE_COMPRESSION,
            summary=(
                "Do not compress noncommutative trace words using arbitrary permutation symmetry "
                "when only cyclic trace invariance has been justified."
            ),
            falsifier=(
                "The exact 2x2 E12/E21/E11 court has tr(ABC)=tr(BCA)=tr(CAB)=1 but tr(ACB)=0."
            ),
            source_refs=("omega_zeta_cert_t:moments",),
        ),
    ]
    return ResearchBundle(
        family=ANTHROPIC_2026_FAMILY,
        target_bound=target_bound,
        moment_spec=moment_spec,
        routes=routes,
        mminus=mminus,
    )
