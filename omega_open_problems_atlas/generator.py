"""Deterministic research-cell generator.

The 1,024 cells are addressable research slots, not 1,024 verified open
problems. Real problem records must enter through sourced ProblemGenome data.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Iterable

from .models import ResearchCell

DOMAINS: tuple[str, ...] = (
    "algebra",
    "algebraic_geometry",
    "analysis",
    "arithmetic_geometry",
    "category_theory",
    "combinatorics",
    "complex_analysis",
    "computability",
    "convex_geometry",
    "differential_geometry",
    "dynamical_systems",
    "functional_analysis",
    "geometric_group_theory",
    "graph_theory",
    "harmonic_analysis",
    "information_theory",
    "logic",
    "mathematical_biology",
    "mathematical_physics",
    "number_theory",
    "numerical_analysis",
    "operator_algebras",
    "optimization",
    "partial_differential_equations",
    "probability",
    "representation_theory",
    "set_theory",
    "spectral_theory",
    "statistics",
    "theoretical_computer_science",
    "topology",
    "transcendence_theory",
)

RESEARCH_OPERATORS: tuple[str, ...] = (
    "normalize_statement",
    "audit_quantifiers",
    "audit_assumptions",
    "find_equivalent_formulation",
    "derive_contrapositive",
    "construct_small_cases",
    "classify_low_dimension",
    "search_extremal_examples",
    "search_counterexamples",
    "weaken_hypotheses",
    "strengthen_conclusion",
    "identify_minimal_obstruction",
    "derive_upper_bound",
    "derive_lower_bound",
    "seek_asymptotic_regime",
    "seek_probabilistic_model",
    "seek_spectral_formulation",
    "seek_variational_formulation",
    "seek_algebraic_formulation",
    "seek_geometric_formulation",
    "seek_algorithmic_reduction",
    "construct_finite_surrogate",
    "design_exact_computation",
    "design_interval_computation",
    "formalize_definitions",
    "formalize_known_lemmas",
    "generate_adversarial_mutations",
    "audit_dimension_dependence",
    "audit_limit_exchange",
    "map_transfer_methods",
    "record_failed_approaches",
    "design_independent_reproduction",
)


def generate_seed_cells() -> tuple[ResearchCell, ...]:
    cells: list[ResearchCell] = []
    for domain_index, domain in enumerate(DOMAINS):
        for operator_index, operator in enumerate(RESEARCH_OPERATORS):
            ordinal = domain_index * len(RESEARCH_OPERATORS) + operator_index
            cells.append(
                ResearchCell(
                    cell_id=f"OPA-RC-{ordinal:04d}",
                    domain=domain,
                    research_operator=operator,
                    objective=f"Apply {operator} to a sourced problem in {domain}",
                )
            )
    return tuple(cells)


def seed_manifest(cells: Iterable[ResearchCell] | None = None) -> dict[str, object]:
    materialized = tuple(cells or generate_seed_cells())
    payload = [cell.to_dict() for cell in materialized]
    canonical = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return {
        "system": "OMEGA-OPEN-PROBLEMS-ATLAS-T-INFINITY",
        "version": "R0.1",
        "research_cell_count": len(payload),
        "domain_count": len(DOMAINS),
        "operator_count": len(RESEARCH_OPERATORS),
        "verified_open_problem_count": sum(
            bool(cell["is_verified_open_problem"]) for cell in payload
        ),
        "solution_claimed": False,
        "finite_computation_is_not_proof": True,
        "permanent_total_cap": None,
        "seed_sha256": sha256(canonical).hexdigest(),
        "cells": payload,
    }
