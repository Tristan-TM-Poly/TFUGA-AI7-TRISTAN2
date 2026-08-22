"""CVCD atlas for finite R10 Hankel principal-minor constraints.

The atlas enumerates exact finite PSD obligations, fingerprints algebraically
identical normalized-Theta polynomials, and stores a single canonical
representation with all occurrences. This is structural compression only; it
never promotes a finite atlas to all-orders positivity or RH.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from typing import Iterable

from .principal_constraints import hankel_principal_minor_polynomial
from .xi_constraints import theta_polynomial_to_xi_integer_polynomial


def _fraction_text(value: Fraction) -> str:
    return str(value)


def _canonical_terms(poly) -> list[dict]:
    return [
        {
            "exponents": list(exp),
            "coefficient": _fraction_text(coeff),
        }
        for exp, coeff in sorted(poly.items(), key=lambda item: (sum(item[0]), item[0]))
    ]


def polynomial_fingerprint(poly) -> str:
    payload = _canonical_terms(poly)
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _xi_integer_payload(poly) -> dict:
    scale, d0_power, terms = theta_polynomial_to_xi_integer_polynomial(poly)
    return {
        "common_integer_scale": scale,
        "d0_power_denominator": d0_power,
        "terms": [
            {"exponents": list(exp), "coefficient": coeff}
            for exp, coeff in sorted(terms.items(), key=lambda item: (sum(item[0]), item[0]))
        ],
    }


def build_constraint_atlas(
    max_size: int = 3,
    shifts: Iterable[int] = (0, 1),
) -> dict:
    """Enumerate and CVCD-deduplicate all principal-minor obligations up to N."""

    if not isinstance(max_size, int) or not 1 <= max_size <= 5:
        raise ValueError("max_size must be an integer in 1..5")
    shifts = tuple(shifts)
    if not shifts or any(not isinstance(shift, int) or shift < 0 for shift in shifts):
        raise ValueError("shifts must be a non-empty iterable of non-negative integers")

    groups: dict[str, dict] = {}
    raw_count = 0
    for size in range(1, max_size + 1):
        for shift in shifts:
            for mask in range(1, 1 << size):
                indices = tuple(index for index in range(size) if mask & (1 << index))
                poly = hankel_principal_minor_polynomial(size, indices, shift)
                fingerprint = polynomial_fingerprint(poly)
                occurrence = {
                    "full_size": size,
                    "shift": shift,
                    "indices": list(indices),
                    "order": len(indices),
                }
                raw_count += 1
                if fingerprint not in groups:
                    groups[fingerprint] = {
                        "fingerprint": fingerprint,
                        "theta_polynomial": _canonical_terms(poly),
                        "xi_integer_polynomial": _xi_integer_payload(poly),
                        "occurrences": [],
                    }
                groups[fingerprint]["occurrences"].append(occurrence)

    unique = sorted(groups.values(), key=lambda item: item["fingerprint"])
    duplicate_occurrences = raw_count - len(unique)
    return {
        "schema": "omega-zeta-square-constraint-atlas/1",
        "max_size": max_size,
        "shifts": list(shifts),
        "raw_occurrence_count": raw_count,
        "unique_polynomial_count": len(unique),
        "duplicate_occurrence_count": duplicate_occurrences,
        "compression_ratio": raw_count / len(unique) if unique else 1.0,
        "constraints": unique,
        "oak": {
            "structural_cvcd_only": True,
            "finite_atlas_only": True,
            "all_orders_required_for_r10": True,
            "proves_rh": False,
        },
        "proves_rh": False,
    }
