"""Small executable tour of Ω-SUITE-FORM-T∞ R∞."""
from __future__ import annotations

from fractions import Fraction
import json

from omega_sequence_forms_t.rinf import (
    CampaignBudget,
    CellSpace,
    CandidatePredictor,
    catalog_payload,
    discover_hypergeometric,
    discover_p_recursive,
    discover_quasi_polynomials,
    discover_rational_indices,
    rank_discriminating_indices,
    run_campaign,
)
from omega_sequence_forms_t.rinf.benchmark import central_binomial_fixture
from omega_sequence_forms_t.rinf.campaign import campaign_summary
from omega_sequence_forms_t.rinf.quasipolynomial import quasi_polynomial_fixture
from omega_sequence_forms_t.rinf.rational_index import rational_fixture


def main() -> None:
    quasi_terms = quasi_polynomial_fixture(period=3, degree=3, count=48)
    rational_terms = rational_fixture((2, 3, 1), (1, 2), 48)
    hyper_terms = central_binomial_fixture(36)

    quasi = discover_quasi_polynomials(quasi_terms, max_period=8, max_degree=5)
    rational = discover_rational_indices(rational_terms, max_numerator_degree=4, max_denominator_degree=4)
    hyper = discover_hypergeometric(hyper_terms, max_numerator_degree=4, max_denominator_degree=4)
    prec = discover_p_recursive(hyper_terms, max_order=4, max_degree=4)

    predictors = []
    if quasi:
        predictors.append(CandidatePredictor("quasi", quasi[0].evaluate))
    if rational:
        predictors.append(CandidatePredictor("rational", rational[0].evaluate))
    discriminating = rank_discriminating_indices(predictors, range(48, 80), limit=5) if len(predictors) > 1 else ()

    budget = CampaignBudget(materialized_cell_cap=64, compute_units=512)
    campaign = run_campaign(campaign_id="demo", seed=20260803, budget=budget, initial_frontier=256)

    payload = {
        "catalog": catalog_payload(),
        "logical_cells": CellSpace().logical_cells,
        "quasi_candidates": len(quasi),
        "rational_candidates": len(rational),
        "hypergeometric_candidates": len(hyper),
        "p_recursive_candidates": len(prec),
        "discriminating_indices": [item.to_dict() for item in discriminating],
        "campaign": campaign_summary(campaign),
        "global_identity_proved": False,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, default=str))


if __name__ == "__main__":
    main()
