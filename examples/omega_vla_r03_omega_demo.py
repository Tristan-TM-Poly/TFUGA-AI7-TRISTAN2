"""Executable demonstration of Ω-VLA-T∞³ R0.3-OMEGA wave 1."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

from omega_vla_t.r03 import (
    Backend,
    IdentityFactory,
    OperatorExpr,
    audit_operator_expression,
    audit_program,
    compile_graphml,
    default_registry,
    evaluate_operator,
    finite_operator_fixture,
    run_identity_trials,
    typed_equation_program,
)


def main() -> int:
    program = typed_equation_program()
    program_report = audit_program(program)

    expression, environment = finite_operator_fixture()
    evaluation = evaluate_operator(expression, environment)
    operator_report = audit_operator_expression(expression, environment)

    operator_type = expression.infer_type()
    a = OperatorExpr.symbol("A", operator_type)
    b = OperatorExpr.symbol("B", operator_type)
    identity_report = run_identity_trials(
        IdentityFactory.adjoint_of_composition(a, b),
        trials=16,
        seed=2026,
    )

    registry = default_registry()
    with tempfile.TemporaryDirectory(prefix="omega-vla-r03-") as directory:
        root = Path(directory)
        (root / "program.json").write_text(program.canonical_json(indent=2) + "\n")
        (root / "program.graphml").write_text(compile_graphml(program).content)
        for backend in (Backend.NUMPY, Backend.LATEX, Backend.LEAN4, Backend.RUST_NALgebra):
            artifact = registry.compile(expression.simplify(), backend)
            suffix = {
                Backend.NUMPY: ".py",
                Backend.LATEX: ".tex",
                Backend.LEAN4: ".lean",
                Backend.RUST_NALgebra: ".rs",
            }[backend]
            (root / f"operator{suffix}").write_text(artifact.content)

        payload = {
            "system": "Ω-VLA-T∞³",
            "version": "R0.3-OMEGA-WAVE-1",
            "program_digest": program.digest(),
            "program_oak": program_report.to_dict(),
            "operator_digest": expression.digest(),
            "simplified_digest": expression.simplify().digest(),
            "evaluation": evaluation.to_dict(),
            "operator_oak": operator_report.to_dict(),
            "identity_fixture": identity_report.to_dict(),
            "generated_files": sorted(path.name for path in root.iterdir()),
            "theorem_claimed": False,
            "formal_proof_claimed": False,
            "scientific_validation_claimed": False,
        }
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))

    return 0 if program_report.passed and operator_report.passed and identity_report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
