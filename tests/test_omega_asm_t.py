from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_asm_t.analysis import (
    analyze,
    binary_entropy,
    critical_path,
    cvcd_signature,
    dependency_graph,
    register_lifetime_metrics,
)
from omega_asm_t.backends import emit_dot_u64, static_instruction_count, supported_variants
from omega_asm_t.cli import main
from omega_asm_t.ir import dot_u64_block_program, program_from_dict, validate_program
from omega_asm_t.models import Candidate, Instruction, Program
from omega_asm_t.oak import oak_report
from omega_asm_t.search import dominates, estimate_builtin_candidates, pareto_front


def test_dot_block_is_valid_and_nonempty():
    program = dot_u64_block_program(4)
    validate_program(program)
    assert program.name == "dot_u64_block_4"
    assert len(program.instructions) == 16


def test_dot_block_has_tree_reduction_critical_path():
    assert critical_path(dot_u64_block_program(4)) == pytest.approx(9.0)


def test_dot_block_memory_accounting():
    metrics = analyze(dot_u64_block_program(4))
    assert metrics.memory_bytes == 64
    assert metrics.instruction_count == 16
    assert metrics.useful_ops_per_memory_byte == pytest.approx(7 / 64)


def test_register_time_metrics_are_positive():
    volume, peak = register_lifetime_metrics(dot_u64_block_program(4))
    assert volume > 0
    assert peak >= 4


def test_dependency_graph_points_backward_only():
    graph = dependency_graph(dot_u64_block_program(4))
    assert all(parent < node for node, parents in graph.items() for parent in parents)


def test_binary_entropy_extremes_and_half():
    assert binary_entropy(0.0) == 0.0
    assert binary_entropy(1.0) == 0.0
    assert binary_entropy(0.5) == pytest.approx(1.0)


def test_cvcd_signature_has_declared_axes():
    signature = cvcd_signature(dot_u64_block_program(2))
    assert set(signature) == {
        "F_instruction_count",
        "D_critical_path",
        "M_memory_bytes",
        "R_register_time_volume",
        "R_peak_live_values",
        "B_branch_entropy_bits",
        "V_mean_vector_width",
        "C_ilp_upper_bound",
        "I_useful_ops_per_memory_byte",
    }


def test_program_round_trip_from_dict():
    program = dot_u64_block_program(3)
    assert program_from_dict(program.to_dict()).to_dict() == program.to_dict()


def test_undefined_input_is_rejected():
    with pytest.raises(ValueError, match="undefined inputs"):
        validate_program(
            Program("bad", (), (Instruction("add", "x", ("missing", "#1")),), ("x",))
        )


def test_duplicate_ssa_output_is_rejected():
    with pytest.raises(ValueError, match="SSA-unique"):
        validate_program(
            Program(
                "bad",
                (),
                (
                    Instruction("const", "x", ("#1",)),
                    Instruction("const", "x", ("#2",)),
                ),
                ("x",),
            )
        )


def test_invalid_branch_probability_is_rejected():
    with pytest.raises(ValueError, match="outside"):
        validate_program(
            Program(
                "bad",
                (),
                (Instruction("branch", None, (), branch_probability=1.2),),
                (),
            )
        )


def test_zero_width_fixture_is_rejected():
    with pytest.raises(ValueError, match="positive"):
        dot_u64_block_program(0)


def test_x86_variants_are_declared():
    assert supported_variants("x86-64") == ("indexed", "ptr")


def test_arm_variant_is_declared():
    assert supported_variants("arm64") == ("ptr",)


def test_unknown_architecture_is_rejected():
    with pytest.raises(ValueError, match="unsupported"):
        supported_variants("quantum-potato")


def test_x86_pointer_backend_has_system_v_operands():
    assembly = emit_dot_u64("x86_64", "ptr")
    assert "(%rdi)" in assembly
    assert "(%rsi)" in assembly
    assert "testq %rdx, %rdx" in assembly
    assert "ret" in assembly


def test_x86_indexed_backend_has_scaled_addressing():
    assembly = emit_dot_u64("x86_64", "indexed")
    assert "(%rdi,%rcx,8)" in assembly
    assert "(%rsi,%rcx,8)" in assembly


def test_aarch64_backend_uses_post_increment_loads():
    assembly = emit_dot_u64("aarch64", "ptr")
    assert "ldr x4, [x0], #8" in assembly
    assert "ldr x5, [x1], #8" in assembly
    assert "subs x2, x2, #1" in assembly


def test_static_instruction_count_ignores_directives_and_labels():
    assert static_instruction_count(".text\nfoo:\n  xorq %rax,%rax\n  ret\n") == 2


def test_builtin_tournament_produces_two_x86_candidates():
    candidates = estimate_builtin_candidates("x86_64")
    assert {candidate.variant for candidate in candidates} == {"indexed", "ptr"}


def test_dominance_is_strict_pareto():
    a = Candidate("a", "x", "a", 1, 1, 1)
    b = Candidate("b", "x", "b", 2, 2, 2)
    assert dominates(a, b)
    assert not dominates(b, a)


def test_pareto_front_removes_dominated_candidate():
    a = Candidate("a", "x", "a", 1, 1, 1)
    b = Candidate("b", "x", "b", 2, 2, 2)
    assert pareto_front([b, a]) == [a]


def test_oak_report_never_grants_merge_authority():
    report = oak_report(dot_u64_block_program(4), native_verified=True)
    assert report.valid is True
    assert report.authority == "review_only"
    assert report.human_review_required is True
    assert report.automatic_merge_allowed is False
    assert any("native CI" in claim for claim in report.claims)


def test_oak_report_separates_static_estimate_from_benchmark():
    report = oak_report(dot_u64_block_program(4))
    assert any("not runtime benchmarks" in item for item in report.limitations)


def test_native_fixture_contains_both_generated_x86_kernels():
    fixture = Path("examples/native/omega_dot_u64_x86_64.S").read_text(encoding="utf-8")
    assert emit_dot_u64("x86_64", "indexed").strip() in fixture
    assert emit_dot_u64("x86_64", "ptr").strip() in fixture


def test_cli_capabilities_is_json(capsys):
    assert main(["capabilities"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["x86_64"] == ["indexed", "ptr"]
    assert payload["aarch64"] == ["ptr"]


def test_cli_demo_emits_cvcd(capsys):
    assert main(["demo", "--width", "2"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["program"]["name"] == "dot_u64_block_2"
    assert payload["cvcd"]["M_memory_bytes"] == 32
