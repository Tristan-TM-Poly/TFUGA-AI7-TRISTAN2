from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re


@dataclass
class CodeForgeResult:
    equation_id: str
    source_latex: str
    level: int
    python_code: str
    tests: str
    assumptions: list[str] = field(default_factory=list)
    oak_status: str = "skeleton_only"

    def to_dict(self) -> dict:
        return asdict(self)


def forge_equation_code(latex: str, equation_id: str = "E1", level: int = 1) -> CodeForgeResult:
    compact = re.sub(r"\s+", "", latex)
    is_decay_ode = any(token in compact for token in ["dx/dt", "\\frac{dx}{dt}"]) and ("kx" in compact or "k*x" in compact)
    if not is_decay_ode or level <= 0:
        code = (
            f"def equation_{equation_id.lower()}(*args, **kwargs):\n"
            f"    '''Source LaTeX: {latex}\n    OAK: not translated or validated.'''\n"
            "    raise NotImplementedError('Translate and validate this equation before use.')\n"
        )
        return CodeForgeResult(equation_id, latex, 0, code, "", ["manual translation required"], "skeleton_only")

    code = """def dxdt(x: float, t: float, k: float, u) -> float:
    '''dx/dt = -k*x + u(t). OAK: validate units and source equation before use.'''
    return -k * x + u(t)
"""
    tests = """def test_zero_input_decay():
    assert dxdt(x=1.0, t=0.0, k=2.0, u=lambda t: 0.0) == -2.0
"""
    if level >= 3:
        code += """
def simulate_euler(x0: float, k: float, u, dt: float, steps: int) -> list[float]:
    '''Minimal Euler simulation. OAK: not a substitute for solver validation.'''
    xs = [x0]
    x = x0
    for i in range(steps):
        t = i * dt
        x += dt * dxdt(x, t, k, u)
        xs.append(x)
    return xs
"""
        tests += """
def test_euler_returns_steps_plus_one():
    xs = simulate_euler(1.0, 1.0, lambda t: 0.0, 0.1, 5)
    assert len(xs) == 6
"""
    return CodeForgeResult(
        equation_id=equation_id,
        source_latex=latex,
        level=level,
        python_code=code,
        tests=tests,
        assumptions=["scalar state x", "k has units 1/time", "u(t) has units state/time"],
        oak_status="translated_needs_validation",
    )
