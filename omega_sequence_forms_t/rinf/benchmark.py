"""Deterministic R∞ OAKBench fixtures and adversarial campaigns."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
from math import comb
from typing import Callable, Iterable, Iterator, Mapping, Sequence

from .address import CellSpace, cell_space_receipt, sample_addresses
from .catalog import assert_catalog_invariants, catalog_payload
from .campaign import campaign_summary, run_campaign
from .hypergeometric import central_binomial_fixture, discover_hypergeometric, factorial_fixture
from .models import CampaignBudget
from .p_recursive import discover_p_recursive
from .quasipolynomial import discover_quasi_polynomials, quasi_polynomial_fixture
from .rational_index import discover_rational_indices, rational_fixture


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    family: str
    terms: tuple[Fraction, ...]
    expectation: Callable[[tuple[Fraction, ...]], bool]
    adversarial: bool = False


@dataclass(frozen=True)
class BenchmarkResult:
    case_id: str
    family: str
    passed: bool
    term_count: int
    adversarial: bool
    diagnostics: Mapping[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "family": self.family,
            "passed": self.passed,
            "term_count": self.term_count,
            "adversarial": self.adversarial,
            "diagnostics": dict(self.diagnostics),
        }


def _quasi_expectation(terms: tuple[Fraction, ...]) -> bool:
    found = discover_quasi_polynomials(terms, max_period=8, max_degree=5)
    return bool(found and found[0].predicts_holdout)


def _rational_expectation(terms: tuple[Fraction, ...]) -> bool:
    found = discover_rational_indices(terms, max_numerator_degree=4, max_denominator_degree=4)
    return bool(found and found[0].predicts_holdout)


def _hyper_expectation(terms: tuple[Fraction, ...]) -> bool:
    found = discover_hypergeometric(terms, max_numerator_degree=4, max_denominator_degree=4)
    return bool(found and found[0].predicts_holdout)


def _prec_expectation(terms: tuple[Fraction, ...]) -> bool:
    found = discover_p_recursive(terms, max_order=3, max_degree=3)
    return bool(found and found[0].predicts_holdout)


def _broken_quasi_expectation(terms: tuple[Fraction, ...]) -> bool:
    found = discover_quasi_polynomials(terms, max_period=8, max_degree=5)
    return not found or not found[0].predicts_holdout


def _broken_hyper_expectation(terms: tuple[Fraction, ...]) -> bool:
    found = discover_hypergeometric(terms, max_numerator_degree=4, max_denominator_degree=4)
    return not found or not found[0].predicts_holdout


def benchmark_cases() -> tuple[BenchmarkCase, ...]:
    quasi = quasi_polynomial_fixture(period=3, degree=3, count=48)
    rational = rational_fixture((2, 3, 1), (1, 2), 48)
    factorial = factorial_fixture(32)
    central = central_binomial_fixture(36)
    broken_quasi = list(quasi)
    broken_quasi[-2] += 1
    broken_hyper = list(central)
    broken_hyper[-1] += 1
    return (
        BenchmarkCase("quasi.period3.degree3", "quasi_polynomial", quasi, _quasi_expectation),
        BenchmarkCase("rational.p2.q1", "rational_index", rational, _rational_expectation),
        BenchmarkCase("hyper.factorial", "hypergeometric", factorial, _hyper_expectation),
        BenchmarkCase("hyper.central_binomial", "hypergeometric", central, _hyper_expectation),
        BenchmarkCase("prec.factorial", "p_recursive", factorial, _prec_expectation),
        BenchmarkCase("adversarial.broken_quasi", "quasi_polynomial", tuple(broken_quasi), _broken_quasi_expectation, True),
        BenchmarkCase("adversarial.broken_hyper", "hypergeometric", tuple(broken_hyper), _broken_hyper_expectation, True),
    )


def run_case(case: BenchmarkCase) -> BenchmarkResult:
    passed = case.expectation(case.terms)
    digest = sha256(
        json.dumps([str(value) for value in case.terms], separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return BenchmarkResult(
        case_id=case.case_id,
        family=case.family,
        passed=passed,
        term_count=len(case.terms),
        adversarial=case.adversarial,
        diagnostics={"terms_digest": digest},
    )


def run_benchmark(*, campaign_cells: int = 512, seed: int = 314159) -> dict[str, object]:
    assert_catalog_invariants()
    cases = tuple(run_case(case) for case in benchmark_cases())
    space = CellSpace()
    budget = CampaignBudget(
        compute_units=max(1, campaign_cells * 5),
        materialized_cell_cap=campaign_cells,
        minimum_marginal_value=0.0,
        minimum_value_cost_ratio=0.0,
    )
    campaign = run_campaign(
        campaign_id="oakbench-rinf",
        seed=seed,
        budget=budget,
        initial_frontier=max(64, min(4096, campaign_cells * 4)),
    )
    payload = {
        "schema": "omega-sequence-forms-rinf-benchmark/1",
        "catalog": catalog_payload(),
        "cell_space": cell_space_receipt(space),
        "cases": [case.to_dict() for case in cases],
        "campaign": campaign_summary(campaign),
        "passed": all(case.passed for case in cases),
        "adversarial_cases": sum(case.adversarial for case in cases),
        "adversarial_passed": sum(case.adversarial and case.passed for case in cases),
        "global_identity_proved": False,
        "formal_proof_completed": False,
        "status": "OAK_SOFTWARE_RESEARCH_FIXTURES_RINF",
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["benchmark_digest"] = sha256(canonical.encode("utf-8")).hexdigest()
    return payload


def synthetic_fixture_stream(seed: int = 0) -> Iterator[dict[str, object]]:
    """Unbounded deterministic fixture descriptors; terms are generated lazily."""

    index = 0
    while True:
        family = (index + seed) % 4
        shell = index // 4 + 1
        if family == 0:
            period = 2 + shell % 15
            degree = shell % 8
            count = max(32, 4 * period + degree + 8)
            yield {
                "fixture_id": f"synthetic.quasi.{index:012d}",
                "family": "quasi_polynomial",
                "parameters": {"period": period, "degree": degree, "count": count},
            }
        elif family == 1:
            p_degree = shell % 6
            q_degree = (shell // 3) % 5
            yield {
                "fixture_id": f"synthetic.rational.{index:012d}",
                "family": "rational_index",
                "parameters": {"p_degree": p_degree, "q_degree": q_degree, "count": 48 + shell % 64},
            }
        elif family == 2:
            yield {
                "fixture_id": f"synthetic.hyper.{index:012d}",
                "family": "hypergeometric",
                "parameters": {"ratio_shell": shell, "count": 32 + shell % 96},
            }
        else:
            yield {
                "fixture_id": f"synthetic.prec.{index:012d}",
                "family": "p_recursive",
                "parameters": {"order": 1 + shell % 6, "degree": shell % 6, "count": 64 + shell % 128},
            }
        index += 1
