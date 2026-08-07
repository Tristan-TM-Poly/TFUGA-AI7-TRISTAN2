from __future__ import annotations

import math
from pathlib import Path

import pytest

from omega_asm_t.analysis import binary_entropy, register_lifetime_metrics
from omega_asm_t.ir import program_from_dict, validate_program
from omega_asm_t.models import Instruction, Program
from omega_asm_t.oak import oak_report


def test_duplicate_program_inputs_are_rejected():
    with pytest.raises(ValueError, match="inputs must be unique"):
        validate_program(Program("duplicate-inputs", ("x", "x"), (), ("x",)))


def test_reserved_immediate_prefix_is_rejected_for_identifiers():
    with pytest.raises(ValueError, match="reserved for immediate"):
        validate_program(Program("reserved-input", ("#x",), (), ()))
    with pytest.raises(ValueError, match="reserved for immediate"):
        validate_program(
            Program(
                "reserved-output",
                (),
                (Instruction("const", "#x", ("#1",)),),
                ("#x",),
            )
        )


def test_non_finite_latency_is_rejected():
    for latency in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError, match="finite and non-negative"):
            validate_program(
                Program(
                    "bad-latency",
                    (),
                    (Instruction("const", "x", ("#1",), latency=latency),),
                    ("x",),
                )
            )


def test_binary_entropy_rejects_invalid_probability():
    for probability in (-0.1, 1.1, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="inside"):
            binary_entropy(probability)


def test_register_lifetime_proxy_counts_program_inputs():
    program = Program(
        "input-liveness",
        ("x", "y"),
        (Instruction("add", "z", ("x", "y")),),
        ("z",),
    )
    volume, peak = register_lifetime_metrics(program)
    assert volume == 3
    assert peak == 3


def test_oak_report_refuses_invalid_direct_program_object():
    invalid = Program(
        "invalid-direct",
        (),
        (Instruction("add", "z", ("missing", "#1")),),
        ("z",),
    )
    with pytest.raises(ValueError, match="undefined inputs"):
        oak_report(invalid)


def test_json_parser_rejects_non_finite_latency():
    with pytest.raises(ValueError, match="finite and non-negative"):
        program_from_dict(
            {
                "name": "nan-latency",
                "instructions": [
                    {"op": "const", "output": "x", "inputs": ["#1"], "latency": math.nan}
                ],
                "outputs": ["x"],
            }
        )


def test_native_benchmark_protocol_blocks_loop_invariant_reference_hoisting():
    source = Path("examples/native/omega_dot_u64_benchmark.c").read_text(encoding="utf-8")
    assert "#define OMEGA_MEMORY_BARRIER()" in source
    assert source.count("OMEGA_MEMORY_BARRIER();") >= 5
    assert "uint64_t result = fn(a, b, n);" in source
    assert "local = mix_checksum(local, result, i);" in source


def test_native_benchmark_protocol_version_records_anti_hoist_control():
    source = Path("examples/native/omega_dot_u64_benchmark.c").read_text(encoding="utf-8")
    assert "benchmark_protocol_version\\\":2" in source
    assert "anti_hoist_memory_barrier\\\":true" in source
    assert "rotate-xor-index-v2" in source
