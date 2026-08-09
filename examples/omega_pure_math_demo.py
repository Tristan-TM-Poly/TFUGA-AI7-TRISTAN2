"""Small deterministic Ω-PURE-MATH-T∞ demonstration."""

import json
import operator

from omega_pure_math_t import (
    FactorizationWitness,
    Invariant,
    StructuralDNA,
    bracket_spectrum,
    compose_witnesses,
    generate_research_protocol,
)


def main() -> None:
    spectrum = bracket_spectrum([10, 3, 2], operator.sub)

    left = FactorizationWitness("X", ("A", "B"))
    right = FactorizationWitness("Y", ("C",))
    composite = compose_witnesses(left, right, composite_name="X⊗Y")

    dimension = Invariant("dimension", len)
    obstruction = dimension.obstructs_isomorphism([1, 2], [1, 2, 3])

    dna = StructuralDNA.from_mapping(
        {
            "invariants": ["dimension", "rank"],
            "defects": ["associator"],
            "representations": ["matrix", "graph"],
        }
    )

    payload = {
        "bracket_spectrum": {
            "parenthesizations": spectrum.parenthesization_count,
            "values": spectrum.distinct_values,
            "diameter": spectrum.diameter,
        },
        "factorization": {
            "object": composite.object_name,
            "expression": composite.expression,
            "length": composite.length,
        },
        "invariant_obstruction": obstruction,
        "structural_dna_sha256": dna.digest(),
        "research_protocol": [
            item.to_dict() for item in generate_research_protocol("StructuralDNA")
        ],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
