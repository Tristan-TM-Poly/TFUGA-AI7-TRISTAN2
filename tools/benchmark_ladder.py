"""Benchmark Ladder for Ω-AIT-RESEARCH-FACTORY-T.

Classifies benchmark maturity B0-B10. This is a conservative status labeler,
not proof by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class BenchmarkLevel(IntEnum):
    B0_NONE = 0
    B1_TOY_EXAMPLE = 1
    B2_SYNTHETIC_TEST = 2
    B3_SIMPLE_BASELINE = 3
    B4_STANDARD_BASELINE = 4
    B5_REALISTIC_DATASET = 5
    B6_STRESS_TEST = 6
    B7_REPRODUCIBLE_BENCHMARK = 7
    B8_EXTERNAL_COMPARISON = 8
    B9_CONTROLLED_USE = 9
    B10_FIELD_STANDARD = 10


@dataclass(frozen=True)
class BenchmarkAssessment:
    level: BenchmarkLevel
    label: str
    next_upgrade: str


def assess_benchmark_level(
    *,
    toy_example: bool = False,
    synthetic_test: bool = False,
    simple_baseline: bool = False,
    standard_baseline: bool = False,
    realistic_dataset: bool = False,
    stress_test: bool = False,
    reproducible: bool = False,
    external_comparison: bool = False,
    controlled_use: bool = False,
    field_standard: bool = False,
) -> BenchmarkAssessment:
    if field_standard and controlled_use:
        level = BenchmarkLevel.B10_FIELD_STANDARD
    elif controlled_use:
        level = BenchmarkLevel.B9_CONTROLLED_USE
    elif external_comparison:
        level = BenchmarkLevel.B8_EXTERNAL_COMPARISON
    elif reproducible:
        level = BenchmarkLevel.B7_REPRODUCIBLE_BENCHMARK
    elif stress_test:
        level = BenchmarkLevel.B6_STRESS_TEST
    elif realistic_dataset:
        level = BenchmarkLevel.B5_REALISTIC_DATASET
    elif standard_baseline:
        level = BenchmarkLevel.B4_STANDARD_BASELINE
    elif simple_baseline:
        level = BenchmarkLevel.B3_SIMPLE_BASELINE
    elif synthetic_test:
        level = BenchmarkLevel.B2_SYNTHETIC_TEST
    elif toy_example:
        level = BenchmarkLevel.B1_TOY_EXAMPLE
    else:
        level = BenchmarkLevel.B0_NONE

    labels = {
        BenchmarkLevel.B0_NONE: "no benchmark",
        BenchmarkLevel.B1_TOY_EXAMPLE: "toy example",
        BenchmarkLevel.B2_SYNTHETIC_TEST: "synthetic test",
        BenchmarkLevel.B3_SIMPLE_BASELINE: "simple baseline",
        BenchmarkLevel.B4_STANDARD_BASELINE: "standard baseline",
        BenchmarkLevel.B5_REALISTIC_DATASET: "realistic dataset",
        BenchmarkLevel.B6_STRESS_TEST: "stress test",
        BenchmarkLevel.B7_REPRODUCIBLE_BENCHMARK: "reproducible benchmark",
        BenchmarkLevel.B8_EXTERNAL_COMPARISON: "external comparison",
        BenchmarkLevel.B9_CONTROLLED_USE: "controlled use",
        BenchmarkLevel.B10_FIELD_STANDARD: "field standard",
    }
    nexts = {
        BenchmarkLevel.B0_NONE: "add toy example",
        BenchmarkLevel.B1_TOY_EXAMPLE: "add synthetic test",
        BenchmarkLevel.B2_SYNTHETIC_TEST: "add simple baseline",
        BenchmarkLevel.B3_SIMPLE_BASELINE: "add standard baseline",
        BenchmarkLevel.B4_STANDARD_BASELINE: "add realistic dataset",
        BenchmarkLevel.B5_REALISTIC_DATASET: "add stress test",
        BenchmarkLevel.B6_STRESS_TEST: "make benchmark reproducible",
        BenchmarkLevel.B7_REPRODUCIBLE_BENCHMARK: "add external comparison",
        BenchmarkLevel.B8_EXTERNAL_COMPARISON: "validate in controlled use",
        BenchmarkLevel.B9_CONTROLLED_USE: "standardize scope",
        BenchmarkLevel.B10_FIELD_STANDARD: "maintain regression suite",
    }
    return BenchmarkAssessment(level, labels[level], nexts[level])
