import math

import pytest

from omega_pure_math_t import (
    BrickLanguage,
    FactorizationWitness,
    Grid,
    orbit_partition,
    strongest_interior_sources,
)


def test_recorded_nontrivial_factorization_blocks_irreducible_promotion():
    language = BrickLanguage("B")
    language.add(FactorizationWitness("p", ("p",)))
    assert language.irreducible("p")

    language.add(FactorizationWitness("p", ("a", "b")))
    assert not language.irreducible("p")
    assert not language.irreducible("unknown")


def test_orbit_partition_rejects_nonbijective_semigroup_generator():
    with pytest.raises(ValueError, match="not bijective"):
        orbit_partition({0, 1, 2}, [lambda _: 0])


def test_zero_source_extractor_never_promotes_negative_density():
    nan = math.nan
    grid = Grid(
        xs=(0.0, 1.0, 2.0),
        ys=(0.0, 1.0, 2.0),
        values=(
            (nan, nan, nan),
            (nan, -10.0, 2.0),
            (nan, 1.0, nan),
        ),
    )
    sources = strongest_interior_sources(grid, count=3)
    assert sources == ((complex(2.0, 1.0), 2.0), (complex(1.0, 2.0), 1.0))
