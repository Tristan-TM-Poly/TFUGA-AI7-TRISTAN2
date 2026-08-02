"""Canonical deterministic demo cells for R0.1."""

from __future__ import annotations

from .models import (
    ActionProposal,
    ActionSensitivity,
    DiscoveryCell,
    Evidence,
    EvidenceKind,
    Hypothesis,
    MMinusRule,
    OakStatus,
    Quantity,
)


def build_demo_cells() -> tuple[DiscoveryCell, ...]:
    raman_hypothesis = Hypothesis(
        statement=(
            "A temperature-like condition changes the synthetic Raman fixture through "
            "peak shift, broadening and baseline drift."
        ),
        domain="raman-synthetic",
        assumptions=(
            "peaks are represented by Lorentzian components",
            "condition response is locally linear in the fixture",
        ),
        falsification_conditions=(
            "holdout RMSE is not better than the nearest-condition baseline",
            "residual structure remains above the declared threshold",
        ),
        value_potential=0.75,
        information_gain=0.85,
        falsifiability=0.9,
        reusability=0.8,
        cost=1.2,
        time_cost=1.0,
        operational_uncertainty=0.25,
        dependency_load=0.2,
        status=OakStatus.SIMULATED,
    )
    raman = DiscoveryCell(
        title="Raman mechanism discrimination",
        domain="spectroscopy",
        problem="Multiple mechanisms can produce similar apparent peak changes.",
        user="spectroscopy researcher",
        observable_pain="manual model selection can conflate shift, width and baseline effects",
        current_baseline="nearest-condition spectrum and standard nonlinear fit",
        hypotheses=[raman_hypothesis],
        evidence=[
            Evidence(
                kind=EvidenceKind.BASELINE,
                title="Nearest-condition baseline",
                source="omega_revolution_diversification_t.raman_loop",
                supports=(raman_hypothesis.hypothesis_id,),
                reproducibility="deterministic fixture",
            ),
            Evidence(
                kind=EvidenceKind.SIMULATION,
                title="Synthetic Lorentzian holdout experiment",
                source="canonical_raman_fixture",
                supports=(raman_hypothesis.hypothesis_id,),
                reproducibility="seeded",
                limitations=("synthetic only", "analytic model family known"),
            ),
        ],
        m_minus=[
            MMinusRule(
                trigger="training fit is used as superiority evidence",
                root_cause="holdout and baseline comparisons were omitted",
                forbidden_inference="A lower training residual proves a better mechanism.",
                safe_replacement="Require holdout and credible baseline comparison.",
                prevention_test="best_holdout_rmse < baseline_rmse",
                domain="spectroscopy",
                source_event_ids=(raman_hypothesis.hypothesis_id,),
            )
        ],
        quantities={
            "condition": Quantity(2.5, "relative_condition", uncertainty=0.0),
        },
        code_refs=["omega_revolution_diversification_t/raman_loop.py"],
        test_refs=["tests/test_omega_revolution_diversification_r0_1.py"],
        next_actions=[
            ActionProposal(
                title="Run external Raman benchmark",
                rationale="Synthetic success must be compared on a public calibrated dataset.",
                sensitivity=ActionSensitivity.REVIEW_REQUIRED,
                reversible=True,
                expected_value=0.9,
                required_approvals=("spectroscopy-reviewer",),
            )
        ],
        scientific_value=0.75,
        engineering_value=0.8,
        product_value=0.55,
        ip_status="review-before-disclosure",
        status=OakStatus.SIMULATED,
    )

    truth_hypothesis = Hypothesis(
        statement=(
            "Structured code–documentation–test comparison detects actionable repository "
            "divergences with lower review effort than unstructured inspection."
        ),
        domain="software-audit",
        assumptions=(
            "repository inventory is complete enough for the audited scope",
            "documentation claims are normalized without changing meaning",
        ),
        falsification_conditions=(
            "precision on reviewed findings falls below 0.8",
            "review time is not reduced against a manual baseline",
        ),
        value_potential=0.9,
        information_gain=0.75,
        falsifiability=0.85,
        reusability=0.95,
        cost=0.8,
        time_cost=0.7,
        operational_uncertainty=0.25,
        dependency_load=0.25,
        status=OakStatus.IMPLEMENTED,
    )
    truth = DiscoveryCell(
        title="GitHub Truth Audit",
        domain="software-quality",
        problem="Documentation, code, tests and benchmarks drift independently.",
        user="software maintainer",
        observable_pain="manual audits are slow and miss cross-artifact contradictions",
        current_baseline="manual repository review",
        hypotheses=[truth_hypothesis],
        evidence=[
            Evidence(
                kind=EvidenceKind.CODE,
                title="Structured truth-audit implementation",
                source="omega_revolution_diversification_t/truth_audit.py",
                supports=(truth_hypothesis.hypothesis_id,),
                reproducibility="deterministic",
            ),
            Evidence(
                kind=EvidenceKind.TEST,
                title="Known-fixture divergence tests",
                source="tests/test_omega_revolution_diversification_r0_1.py",
                supports=(truth_hypothesis.hypothesis_id,),
                reproducibility="CI",
                limitations=("fixture precision is not external precision",),
            ),
        ],
        code_refs=["omega_revolution_diversification_t/truth_audit.py"],
        test_refs=["tests/test_omega_revolution_diversification_r0_1.py"],
        next_actions=[
            ActionProposal(
                title="Audit a repository with human-reviewed labels",
                rationale="Measure precision, recall and review-time reduction externally.",
                sensitivity=ActionSensitivity.REVIEW_REQUIRED,
                reversible=True,
                expected_value=0.95,
                required_approvals=("repository-owner",),
            )
        ],
        scientific_value=0.45,
        engineering_value=0.9,
        product_value=0.9,
        ip_status="open-source-candidate",
        status=OakStatus.IMPLEMENTED,
    )

    mminus_hypothesis = Hypothesis(
        statement=(
            "A linked negative-memory registry reduces repeated deterministic failures "
            "without an unacceptable false-block rate."
        ),
        domain="epistemic-control",
        assumptions=(
            "failure fingerprints identify materially equivalent conditions",
            "rules are scoped and reviewable",
        ),
        falsification_conditions=(
            "repeated failures are not reduced",
            "false blocks erase the prevention benefit",
        ),
        value_potential=0.95,
        information_gain=0.9,
        falsifiability=0.95,
        reusability=0.95,
        cost=0.6,
        time_cost=0.5,
        operational_uncertainty=0.2,
        dependency_load=0.15,
        status=OakStatus.DEMONSTRATED,
    )
    mminus = DiscoveryCell(
        title="M⁻ ablation",
        domain="negative-memory",
        problem="Systems repeat costly failures when negative results are not operationalized.",
        user="research and software organization",
        observable_pain="the same invalid inference or defect recurs across cycles",
        current_baseline="unstructured issue history",
        hypotheses=[mminus_hypothesis],
        evidence=[
            Evidence(
                kind=EvidenceKind.BASELINE,
                title="Controller without negative memory",
                source="canonical_ablation_fixture",
                supports=(mminus_hypothesis.hypothesis_id,),
                reproducibility="deterministic fixture",
            ),
            Evidence(
                kind=EvidenceKind.RESULT,
                title="Controller with scoped negative-memory rules",
                source="run_mminus_ablation",
                supports=(mminus_hypothesis.hypothesis_id,),
                reproducibility="deterministic fixture",
                limitations=("requires external domain ablations",),
            ),
        ],
        m_minus=[
            MMinusRule(
                trigger="negative-memory rule matches a near but materially different case",
                root_cause="fingerprint is too broad",
                forbidden_inference="Any lexical similarity implies causal equivalence.",
                safe_replacement="Require domain, mechanism and condition match.",
                prevention_test="false_block_rate <= declared threshold",
                domain="negative-memory",
                source_event_ids=(mminus_hypothesis.hypothesis_id,),
            )
        ],
        code_refs=["omega_revolution_diversification_t/ablation.py"],
        test_refs=["tests/test_omega_revolution_diversification_r0_1.py"],
        next_actions=[
            ActionProposal(
                title="Run ablation on historical repository defects",
                rationale="External history is needed to measure real recurrence prevention.",
                sensitivity=ActionSensitivity.REVIEW_REQUIRED,
                reversible=True,
                expected_value=0.95,
                required_approvals=("repository-owner",),
            )
        ],
        scientific_value=0.8,
        engineering_value=0.95,
        product_value=0.85,
        ip_status="review-before-disclosure",
        status=OakStatus.DEMONSTRATED,
    )
    return raman, truth, mminus
