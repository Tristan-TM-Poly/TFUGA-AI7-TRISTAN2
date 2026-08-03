"""Proof-obligation compiler for sourced problem leads."""
from __future__ import annotations

from itertools import cycle
from typing import Iterable, Iterator

from .models import EvidenceClass, ProblemLead, ProofObligation


OBLIGATION_OPERATORS: tuple[str, ...] = (
    "statement_normalization",
    "quantifier_audit",
    "assumption_audit",
    "definition_dependency_audit",
    "known_result_baseline",
    "equivalent_formulation_forward",
    "equivalent_formulation_reverse",
    "contrapositive_formulation",
    "dual_formulation",
    "variational_formulation",
    "spectral_formulation",
    "probabilistic_formulation",
    "algebraic_formulation",
    "geometric_formulation",
    "categorical_formulation",
    "algorithmic_reduction",
    "finite_surrogate",
    "small_parameter_cases",
    "low_dimension_cases",
    "symmetric_cases",
    "extremal_cases",
    "generic_cases",
    "degenerate_cases",
    "boundary_cases",
    "asymptotic_regimes",
    "singular_limits",
    "perturbation_stability",
    "regularization_stability",
    "dimension_dependence",
    "constant_uniformity",
    "upper_bound",
    "lower_bound",
    "matching_construction",
    "minimal_obstruction",
    "counterexample_search",
    "adversarial_hypothesis_removal",
    "adversarial_quantifier_flip",
    "adversarial_norm_change",
    "adversarial_parenthesization",
    "random_small_model",
    "exact_arithmetic_probe",
    "interval_arithmetic_probe",
    "symbolic_computation_probe",
    "integer_programming_probe",
    "sat_smt_probe",
    "graph_search_probe",
    "numerical_stability_probe",
    "independent_implementation",
    "benchmark_against_known_cases",
    "negative_control",
    "ablation",
    "formalize_definitions",
    "formalize_known_lemmas",
    "formalize_candidate_lemma",
    "kernel_rebuild",
    "citation_provenance_audit",
    "license_audit",
    "open_status_recheck",
    "method_transfer_forward",
    "method_transfer_reverse",
    "cross_domain_round_trip",
    "failure_memory_update",
    "reproduction_packet",
    "human_expert_review",
)


def obligation_id(problem_id: str, operator: str, ordinal: int) -> str:
    safe = operator.replace("_", "-").upper()
    return f"OPA-OBL-{problem_id}-{ordinal:04d}-{safe}"


def compile_obligations(
    lead: ProblemLead,
    operators: Iterable[str] = OBLIGATION_OPERATORS,
    per_operator_budget: int = 1,
) -> tuple[ProofObligation, ...]:
    if per_operator_budget <= 0:
        raise ValueError("per_operator_budget must be positive")
    obligations: list[ProofObligation] = []
    for ordinal, operator in enumerate(operators):
        expected = _expected_evidence(operator)
        obligations.append(
            ProofObligation(
                obligation_id=obligation_id(lead.lead_id, operator, ordinal),
                problem_id=lead.lead_id,
                operator=operator,
                objective=f"Apply {operator} to sourced lead {lead.lead_id}",
                assumptions=("problem statement and source metadata are stable for this run",),
                falsifiers=_falsifiers(operator),
                expected_evidence=expected,
                finite_budget_units=per_operator_budget,
                universal_claim=False,
                generated_from_template=True,
            )
        )
    return tuple(obligations)


def stream_obligations(
    leads: Iterable[ProblemLead],
    total_budget: int,
    operators: tuple[str, ...] = OBLIGATION_OPERATORS,
) -> Iterator[ProofObligation]:
    """Allocate exactly ``total_budget`` one-unit obligations lazily.

    No permanent total cap is encoded. Each invocation is finite and explicit.
    """
    if total_budget < 0:
        raise ValueError("total_budget must be non-negative")
    materialized = tuple(leads)
    if total_budget and not materialized:
        raise ValueError("cannot allocate budget without leads")
    pairs = cycle((lead, operator) for lead in materialized for operator in operators)
    for ordinal in range(total_budget):
        lead, operator = next(pairs)
        yield ProofObligation(
            obligation_id=obligation_id(lead.lead_id, operator, ordinal),
            problem_id=lead.lead_id,
            operator=operator,
            objective=f"Finite campaign unit {ordinal}: {operator} on {lead.lead_id}",
            assumptions=("finite campaign fixture",),
            falsifiers=_falsifiers(operator),
            expected_evidence=_expected_evidence(operator),
            finite_budget_units=1,
            universal_claim=False,
            generated_from_template=True,
        )


def _expected_evidence(operator: str) -> tuple[EvidenceClass, ...]:
    if operator.startswith("formalize") or operator == "kernel_rebuild":
        return (EvidenceClass.FORMAL_CHECK, EvidenceClass.INDEPENDENT_REPRODUCTION)
    if operator.endswith("audit") or operator in {"open_status_recheck", "known_result_baseline"}:
        return (EvidenceClass.SOURCE_SNAPSHOT, EvidenceClass.LITERATURE_CHECK)
    if "reproduction" in operator or operator == "independent_implementation":
        return (EvidenceClass.COMPUTATION, EvidenceClass.INDEPENDENT_REPRODUCTION)
    if operator in {"human_expert_review"}:
        return (EvidenceClass.PEER_REVIEW,)
    return (EvidenceClass.COMPUTATION,)


def _falsifiers(operator: str) -> tuple[str, ...]:
    common = (
        "counterexample on a declared finite or symbolic case",
        "inconsistent result under independent implementation",
    )
    if "equivalent_formulation" in operator or "round_trip" in operator:
        return common + ("failure of one implication direction",)
    if operator.startswith("formalize") or operator == "kernel_rebuild":
        return common + ("proof assistant rejects the term", "placeholder remains")
    if operator in {"upper_bound", "lower_bound"}:
        return common + ("known example violates the claimed bound",)
    return common
