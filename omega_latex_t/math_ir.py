from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import re
from typing import Any, Mapping


class MathIRError(ValueError):
    pass


class DimensionError(MathIRError):
    pass


@dataclass(frozen=True)
class Dimension:
    powers: tuple[tuple[str, Fraction], ...] = ()

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, int | float | Fraction]) -> "Dimension":
        values = []
        for key, value in mapping.items():
            exponent = value if isinstance(value, Fraction) else Fraction(value)
            if exponent:
                values.append((str(key), exponent))
        return cls(tuple(sorted(values)))

    def as_dict(self) -> dict[str, Fraction]:
        return dict(self.powers)

    def multiply(self, other: "Dimension") -> "Dimension":
        result = self.as_dict()
        for key, value in other.powers:
            result[key] = result.get(key, Fraction(0)) + value
        return Dimension.from_mapping(result)

    def divide(self, other: "Dimension") -> "Dimension":
        result = self.as_dict()
        for key, value in other.powers:
            result[key] = result.get(key, Fraction(0)) - value
        return Dimension.from_mapping(result)

    def power(self, exponent: Fraction) -> "Dimension":
        return Dimension.from_mapping({key: value * exponent for key, value in self.powers})

    @property
    def dimensionless(self) -> bool:
        return not self.powers

    def signature(self) -> str:
        if not self.powers:
            return "1"
        pieces = []
        for key, value in self.powers:
            if value == 1:
                pieces.append(key)
            elif value.denominator == 1:
                pieces.append(f"{key}^{value.numerator}")
            else:
                pieces.append(f"{key}^{value.numerator}/{value.denominator}")
        return " ".join(pieces)


BASE = {
    "M": Dimension.from_mapping({"M": 1}),
    "L": Dimension.from_mapping({"L": 1}),
    "T": Dimension.from_mapping({"T": 1}),
    "I": Dimension.from_mapping({"I": 1}),
    "Theta": Dimension.from_mapping({"Theta": 1}),
    "N": Dimension.from_mapping({"N": 1}),
    "J_base": Dimension.from_mapping({"J": 1}),
}

UNITS = {
    "1": Dimension(),
    "rad": Dimension(),
    "m": BASE["L"],
    "kg": BASE["M"],
    "s": BASE["T"],
    "A": BASE["I"],
    "K": BASE["Theta"],
    "mol": BASE["N"],
    "cd": BASE["J_base"],
    "Hz": Dimension.from_mapping({"T": -1}),
    "N": Dimension.from_mapping({"M": 1, "L": 1, "T": -2}),
    "Pa": Dimension.from_mapping({"M": 1, "L": -1, "T": -2}),
    "J": Dimension.from_mapping({"M": 1, "L": 2, "T": -2}),
    "W": Dimension.from_mapping({"M": 1, "L": 2, "T": -3}),
    "C": Dimension.from_mapping({"I": 1, "T": 1}),
    "V": Dimension.from_mapping({"M": 1, "L": 2, "T": -3, "I": -1}),
    "ohm": Dimension.from_mapping({"M": 1, "L": 2, "T": -3, "I": -2}),
    "F": Dimension.from_mapping({"M": -1, "L": -2, "T": 4, "I": 2}),
    "H": Dimension.from_mapping({"M": 1, "L": 2, "T": -2, "I": -2}),
    "Wb": Dimension.from_mapping({"M": 1, "L": 2, "T": -2, "I": -1}),
    "tesla": Dimension.from_mapping({"M": 1, "T": -2, "I": -1}),
}


_TOKEN = re.compile(r"^(?P<name>[A-Za-z][A-Za-z0-9_]*)(?:\^(?P<exp>-?\d+))?$")


def parse_unit(value: str) -> Dimension:
    text = value.strip()
    if not text or text == "1":
        return Dimension()
    if text in BASE:
        return BASE[text]
    result = Dimension()
    sign = 1
    for token in re.split(r"([*/])", text.replace(" ", "")):
        if not token:
            continue
        if token == "*":
            sign = 1
            continue
        if token == "/":
            sign = -1
            continue
        match = _TOKEN.fullmatch(token)
        if not match:
            raise DimensionError(f"unsupported unit token {token!r}")
        name = match.group("name")
        if name not in UNITS and name not in BASE:
            raise DimensionError(f"unknown unit {name!r}")
        dim = UNITS.get(name, BASE.get(name))
        exponent = int(match.group("exp") or "1") * sign
        result = result.multiply(dim.power(Fraction(exponent)))
        sign = 1
    return result


def _validate_symbol(value: str) -> str:
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", value):
        return value.replace("_", r"\_")
    if re.fullmatch(r"\\[A-Za-z]+(?:_[A-Za-z0-9]+)?", value):
        return value
    raise MathIRError(f"unsafe or unsupported math symbol {value!r}")


def render_math(expr: Any) -> str:
    if isinstance(expr, (int, float)):
        return str(expr)
    if not isinstance(expr, Mapping):
        raise MathIRError("math expression must be a mapping or number")
    op = str(expr.get("op", ""))
    if op == "symbol":
        return _validate_symbol(str(expr["name"]))
    if op == "number":
        return str(expr["value"])
    if op in {"add", "mul"}:
        args = list(expr.get("args", ()))
        if len(args) < 2:
            raise MathIRError(f"{op} requires at least two args")
        sep = " + " if op == "add" else r" \, "
        return sep.join(f"({render_math(x)})" if isinstance(x, Mapping) and x.get("op") in {"add", "sub"} else render_math(x) for x in args)
    if op == "sub":
        return f"{render_math(expr['left'])} - {render_math(expr['right'])}"
    if op == "div":
        return rf"\frac{{{render_math(expr['left'])}}}{{{render_math(expr['right'])}}}"
    if op == "pow":
        return rf"{{{render_math(expr['base'])}}}^{{{render_math(expr['exp'])}}}"
    if op == "neg":
        return f"-({render_math(expr['arg'])})"
    if op == "eq":
        return f"{render_math(expr['lhs'])} = {render_math(expr['rhs'])}"
    if op == "func":
        name = str(expr["name"])
        args = list(expr.get("args", ()))
        if len(args) != 1:
            raise MathIRError("R0.3 functions currently require exactly one argument")
        rendered = render_math(args[0])
        if name in {"sin", "cos", "tan", "exp", "log", "ln"}:
            command = "log" if name == "ln" else name
            return rf"\{command}\left({rendered}\right)"
        if name == "sqrt":
            return rf"\sqrt{{{rendered}}}"
        if name == "abs":
            return rf"\left|{rendered}\right|"
        raise MathIRError(f"unsupported function {name!r}")
    raise MathIRError(f"unsupported math op {op!r}")


def _number_fraction(expr: Any) -> Fraction:
    if isinstance(expr, int):
        return Fraction(expr)
    if isinstance(expr, float):
        return Fraction(str(expr))
    if isinstance(expr, Mapping) and expr.get("op") == "number":
        return Fraction(str(expr["value"]))
    raise DimensionError("dimensioned powers require a numeric exponent")


def infer_dimension(expr: Any, symbol_units: Mapping[str, str]) -> Dimension:
    if isinstance(expr, (int, float)):
        return Dimension()
    if not isinstance(expr, Mapping):
        raise DimensionError("math expression must be a mapping or number")
    op = str(expr.get("op", ""))
    if op == "number":
        return Dimension()
    if op == "symbol":
        name = str(expr["name"])
        if name not in symbol_units or not str(symbol_units[name]).strip():
            raise DimensionError(f"unit unknown for symbol {name!r}")
        return parse_unit(str(symbol_units[name]))
    if op == "add":
        dims = [infer_dimension(x, symbol_units) for x in expr.get("args", ())]
        if len(dims) < 2:
            raise DimensionError("add requires at least two args")
        if any(x != dims[0] for x in dims[1:]):
            raise DimensionError("addends have incompatible dimensions")
        return dims[0]
    if op == "sub":
        left = infer_dimension(expr["left"], symbol_units)
        right = infer_dimension(expr["right"], symbol_units)
        if left != right:
            raise DimensionError("subtraction operands have incompatible dimensions")
        return left
    if op == "mul":
        result = Dimension()
        for item in expr.get("args", ()):
            result = result.multiply(infer_dimension(item, symbol_units))
        return result
    if op == "div":
        return infer_dimension(expr["left"], symbol_units).divide(infer_dimension(expr["right"], symbol_units))
    if op == "pow":
        return infer_dimension(expr["base"], symbol_units).power(_number_fraction(expr["exp"]))
    if op == "neg":
        return infer_dimension(expr["arg"], symbol_units)
    if op == "eq":
        left = infer_dimension(expr["lhs"], symbol_units)
        right = infer_dimension(expr["rhs"], symbol_units)
        if left != right:
            raise DimensionError(f"equation dimensions differ: {left.signature()} != {right.signature()}")
        return left
    if op == "func":
        name = str(expr["name"])
        args = list(expr.get("args", ()))
        if len(args) != 1:
            raise DimensionError("functions currently require exactly one argument")
        arg_dim = infer_dimension(args[0], symbol_units)
        if name in {"sin", "cos", "tan", "exp", "log", "ln"}:
            if not arg_dim.dimensionless:
                raise DimensionError(f"{name} requires a dimensionless argument")
            return Dimension()
        if name == "sqrt":
            return arg_dim.power(Fraction(1, 2))
        if name == "abs":
            return arg_dim
        raise DimensionError(f"unsupported function {name!r}")
    raise DimensionError(f"unsupported math op {op!r}")


def symbol_units_from_specs(symbols: Any) -> dict[str, str]:
    out: dict[str, str] = {}
    for spec in symbols:
        name = str(getattr(spec, "symbol", ""))
        unit = str(getattr(spec, "unit", ""))
        if name and unit:
            out[name] = unit
    return out
