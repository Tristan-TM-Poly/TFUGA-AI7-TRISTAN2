from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re


@dataclass
class DimensionalCheck:
    equation_id: str
    latex: str
    dimensional_status: str
    inferred_units: dict[str, str]
    missing_units: list[str] = field(default_factory=list)
    oak_status: str = "needs_review"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


VAR_PATTERN = re.compile(r"[A-Za-z](?:_\{?\w+\}?)?")


def extract_variables(latex: str) -> list[str]:
    raw = VAR_PATTERN.findall(latex.replace("frac", "").replace("dt", "t"))
    ignore = {"d", "t"}
    out: list[str] = []
    for item in raw:
        item = item.strip("{}")
        if item not in ignore and item not in out:
            out.append(item)
    return out


def dimensional_oak(latex: str, equation_id: str = "E1") -> DimensionalCheck:
    compact = re.sub(r"\s+", "", latex)
    inferred: dict[str, str] = {}
    missing: list[str] = []
    notes: list[str] = []

    looks_like_dxdt = any(token in compact for token in ["dx/dt", "\\frac{dx}{dt}", "\\dot{x}"])
    has_decay = "kx" in compact or "k*x" in compact
    has_input = "u(t)" in compact or "+u" in compact

    if looks_like_dxdt and has_decay:
        inferred = {"x": "state", "t": "time", "k": "1/time"}
        if has_input:
            inferred["u(t)"] = "state/time"
        else:
            notes.append("No explicit input term detected.")
        missing = ["x", "u(t)"] if has_input else ["x"]
        return DimensionalCheck(
            equation_id=equation_id,
            latex=latex,
            dimensional_status="consistent_partial",
            inferred_units=inferred,
            missing_units=missing,
            oak_status="needs_user_or_paper_units",
            notes=notes + ["Pattern check only; not a proof of physical validity."],
        )

    variables = extract_variables(latex)
    return DimensionalCheck(
        equation_id=equation_id,
        latex=latex,
        dimensional_status="unknown",
        inferred_units={var: "unknown" for var in variables},
        missing_units=variables,
        oak_status="uncertain",
        notes=["No supported dimensional template matched this equation."],
    )
