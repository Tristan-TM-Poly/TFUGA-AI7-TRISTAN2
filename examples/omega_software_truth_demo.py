"""Minimal Ω-CS-SOFTWARE-TRUTH demo.

Run:
    python examples/omega_software_truth_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow direct execution by path from the repository root without installing the
# package first. This keeps the demo aligned with the README command.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from omega_software_truth import Contract, ExampleCase, OAKValidator, SoftwareState, probe_mutant


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        raise ZeroDivisionError("denominator must not be zero")
    return numerator / denominator


def mutant_ratio(numerator: float, denominator: float) -> float:
    return numerator * denominator


def main() -> int:
    contract = Contract(
        name="safe_ratio_contract",
        input_predicates={
            "two_numbers": lambda args, kwargs: len(args) == 2 and all(isinstance(x, (int, float)) for x in args),
        },
        output_predicates={"finite_float": lambda output: isinstance(output, float)},
        exception_predicates={"zero_division_allowed": lambda exc: isinstance(exc, ZeroDivisionError)},
    )

    state = SoftwareState(
        name="safe_ratio",
        target=safe_ratio,
        contract=contract,
        examples=(
            ExampleCase("half", args=(1.0, 2.0), expected=0.5),
            ExampleCase("zero_denominator", args=(1.0, 0.0), expect_exception=ZeroDivisionError),
        ),
    )

    report = OAKValidator().validate(state)
    print(report.to_markdown())

    mutation = probe_mutant(state, "multiply_instead_of_divide", mutant_ratio)
    print(f"Mutation killed: {mutation.killed}")
    return 0 if report.passed and mutation.killed else 1


if __name__ == "__main__":
    raise SystemExit(main())
