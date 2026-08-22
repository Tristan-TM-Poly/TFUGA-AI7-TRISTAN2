from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import comb
from typing import Iterable, Sequence


def as_fraction(value: int | float | str | Fraction) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, float):
        return Fraction(str(value))
    return Fraction(value)


def trim_coefficients(coefficients: Sequence[Fraction]) -> tuple[Fraction, ...]:
    values = list(coefficients)
    while len(values) > 1 and values[-1] == 0:
        values.pop()
    return tuple(values or [Fraction(0)])


@dataclass(frozen=True)
class RationalPolynomial:
    """Power-basis polynomial p(x)=sum c_k x^k with exact coefficients."""
    coefficients: tuple[Fraction, ...]

    @classmethod
    def from_values(cls, coefficients: Iterable[int | float | str | Fraction]) -> "RationalPolynomial":
        return cls(trim_coefficients(tuple(as_fraction(x) for x in coefficients)))

    @property
    def degree(self) -> int:
        return len(self.coefficients) - 1

    def evaluate(self, x: int | float | str | Fraction) -> Fraction:
        point = as_fraction(x)
        result = Fraction(0)
        for coefficient in reversed(self.coefficients):
            result = result * point + coefficient
        return result

    def shifted_scaled_power_coefficients(
        self,
        left: int | float | str | Fraction,
        right: int | float | str | Fraction,
    ) -> tuple[Fraction, ...]:
        """Coefficients d_j of p(left + (right-left)t)."""
        a = as_fraction(left)
        b = as_fraction(right)
        if not a < b:
            raise ValueError("left must be strictly less than right")
        width = b - a
        n = self.degree
        d = [Fraction(0) for _ in range(n + 1)]
        for m, c_m in enumerate(self.coefficients):
            for j in range(m + 1):
                d[j] += c_m * comb(m, j) * (a ** (m - j)) * (width ** j)
        return tuple(d)

    def bernstein_coefficients(
        self,
        left: int | float | str | Fraction,
        right: int | float | str | Fraction,
    ) -> tuple[Fraction, ...]:
        """Exact Bernstein coefficients on [left,right] at polynomial degree n.

        If every returned coefficient is nonnegative, p(x)>=0 throughout the
        interval. This is a sufficient exact certificate, not a necessary one.
        """
        power = self.shifted_scaled_power_coefficients(left, right)
        n = self.degree
        beta: list[Fraction] = []
        for k in range(n + 1):
            value = Fraction(0)
            for j in range(k + 1):
                value += power[j] * Fraction(comb(k, j), comb(n, j))
            beta.append(value)
        return tuple(beta)

    def negate(self) -> "RationalPolynomial":
        return RationalPolynomial(tuple(-c for c in self.coefficients))

    def one_minus(self) -> "RationalPolynomial":
        coeffs = list(-c for c in self.coefficients)
        if coeffs:
            coeffs[0] += 1
        else:
            coeffs = [Fraction(1)]
        return RationalPolynomial(trim_coefficients(tuple(coeffs)))

    def to_dict(self) -> dict:
        return {
            "coefficients": [fraction_text(c) for c in self.coefficients],
            "degree": self.degree,
        }


def fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


@dataclass(frozen=True)
class IntervalPolynomialCheck:
    interval: tuple[Fraction, Fraction]
    bernstein_coefficients: tuple[Fraction, ...]
    nonnegative_certified: bool

    def to_dict(self) -> dict:
        return {
            "interval": [fraction_text(x) for x in self.interval],
            "bernstein_coefficients": [fraction_text(x) for x in self.bernstein_coefficients],
            "nonnegative_certified": self.nonnegative_certified,
            "verification": "exact_rational_bernstein_sufficient_condition",
        }


@dataclass(frozen=True)
class SpectralDualCertificate:
    polynomial: RationalPolynomial
    spectral_radius: Fraction
    normalized_moments: tuple[Fraction, ...]
    domain_control_proven: bool
    domain_control_source: str

    def validate(self) -> None:
        if self.spectral_radius <= 0:
            raise ValueError("spectral_radius must be positive")
        if not self.domain_control_source:
            raise ValueError("domain_control_source is required")
        if len(self.normalized_moments) <= self.polynomial.degree:
            raise ValueError("moments through the polynomial degree are required")
        if self.normalized_moments[0] != 1:
            raise ValueError("normalized moment m0 must equal 1")

    def negative_side_check(self) -> IntervalPolynomialCheck:
        self.validate()
        q = self.polynomial.negate()
        beta = q.bernstein_coefficients(-self.spectral_radius, Fraction(0))
        return IntervalPolynomialCheck(
            interval=(-self.spectral_radius, Fraction(0)),
            bernstein_coefficients=beta,
            nonnegative_certified=all(x >= 0 for x in beta),
        )

    def positive_side_check(self) -> IntervalPolynomialCheck:
        self.validate()
        q = self.polynomial.one_minus()
        beta = q.bernstein_coefficients(Fraction(0), self.spectral_radius)
        return IntervalPolynomialCheck(
            interval=(Fraction(0), self.spectral_radius),
            bernstein_coefficients=beta,
            nonnegative_certified=all(x >= 0 for x in beta),
        )

    @property
    def moment_objective(self) -> Fraction:
        self.validate()
        return sum(
            coefficient * self.normalized_moments[k]
            for k, coefficient in enumerate(self.polynomial.coefficients)
        )

    @property
    def polynomial_constraints_certified(self) -> bool:
        return (
            self.negative_side_check().nonnegative_certified
            and self.positive_side_check().nonnegative_certified
        )

    @property
    def lower_bound_certified(self) -> bool:
        return self.domain_control_proven and self.polynomial_constraints_certified

    def to_dict(self) -> dict:
        self.validate()
        lower = self.moment_objective if self.lower_bound_certified else None
        return {
            "polynomial": self.polynomial.to_dict(),
            "spectral_radius": fraction_text(self.spectral_radius),
            "normalized_moments": [fraction_text(x) for x in self.normalized_moments],
            "domain_control_proven": self.domain_control_proven,
            "domain_control_source": self.domain_control_source,
            "negative_side": self.negative_side_check().to_dict(),
            "positive_side": self.positive_side_check().to_dict(),
            "moment_objective": fraction_text(self.moment_objective),
            "polynomial_constraints_certified": self.polynomial_constraints_certified,
            "lower_bound_certified": self.lower_bound_certified,
            "certified_lower_bound": fraction_text(lower) if lower is not None else None,
            "certificate_scope": (
                "finite_exact_moment_problem_under_supplied_proven_spectral_domain"
                if self.lower_bound_certified
                else "conditional_or_rejected"
            ),
            "zeta_theorem_claimed": False,
            "rh_solved_claimed": False,
        }


def moments_from_exact_spectrum(
    eigenvalues: Sequence[int | str | Fraction],
    max_order: int,
) -> tuple[Fraction, ...]:
    if not eigenvalues:
        raise ValueError("eigenvalues must be non-empty")
    if max_order < 0:
        raise ValueError("max_order must be nonnegative")
    values = tuple(as_fraction(x) for x in eigenvalues)
    n = Fraction(len(values))
    return tuple(
        sum(value ** order for value in values) / n
        for order in range(max_order + 1)
    )


def synthetic_dual_fixture() -> SpectralDualCertificate:
    """Exact finite fixture: spectrum (-1,1,1), p(x)=x on [-1,1].

    The certificate proves only a 1/3 positive-mass lower bound for this exact
    synthetic measure, while the true positive mass is 2/3. The gap is useful:
    certificate validity and certificate optimality remain separate concepts.
    """
    polynomial = RationalPolynomial.from_values((0, 1))
    moments = moments_from_exact_spectrum((-1, 1, 1), polynomial.degree)
    return SpectralDualCertificate(
        polynomial=polynomial,
        spectral_radius=Fraction(1),
        normalized_moments=moments,
        domain_control_proven=True,
        domain_control_source="exact_synthetic_spectrum_fixture",
    )
