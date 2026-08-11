import json

from omega_rootflow_t import (
    build_partition_lattice,
    derivative_gcd_tower,
    exact_multiplicity_atlas,
    immediate_less_singular,
    immediate_more_singular,
    partition_neighborhood,
    square_free_decomposition,
)
from omega_rootflow_t.cli import main


MIXED = [-4, 8, -5, 3, 0, -4, 1, 1]  # (z-1)^3 (z+2)^2 (z^2+1)


def test_derivative_gcd_tower_encodes_global_multiplicities() -> None:
    tower = derivative_gcd_tower(MIXED)
    degrees = tuple(len(item) - 1 for item in tower)
    assert degrees == (7, 3, 1, 0, 0, 0, 0, 0)


def test_exact_multiplicity_atlas_recovers_partition_without_root_solving() -> None:
    atlas = exact_multiplicity_atlas(MIXED)
    assert atlas.status == "OAK_PASS_EXACT_MULTIPLICITY_ATLAS"
    assert atlas.gcd_degrees == (7, 3, 1, 0, 0, 0, 0, 0)
    assert atlas.at_least_multiplicity_counts == (4, 2, 1, 0, 0, 0, 0)
    assert atlas.exact_multiplicity_counts == (2, 1, 1, 0, 0, 0, 0)
    assert atlas.multiplicity_partition == (3, 2, 1, 1)
    assert atlas.distinct_root_count_over_c == 4
    assert atlas.complex_stratum_codimension == 3
    assert atlas.reconstruction_matches
    assert atlas.theorem_claimed is False


def test_square_free_decomposition_matches_known_factor_families() -> None:
    factors = square_free_decomposition(MIXED)
    assert [(item.multiplicity, item.degree) for item in factors] == [(1, 2), (2, 1), (3, 1)]
    assert factors[0].coefficients == (1, 0, 1)
    assert factors[1].coefficients == (2, 1)
    assert factors[2].coefficients == (-1, 1)


def test_distinct_cubic_is_open_stratum_partition() -> None:
    atlas = exact_multiplicity_atlas([6, -5, -2, 1])
    assert atlas.multiplicity_partition == (1, 1, 1)
    assert atlas.distinct_root_count_over_c == 3
    assert atlas.complex_stratum_codimension == 0
    assert [(item.multiplicity, item.degree) for item in atlas.square_free_factors] == [(1, 3)]


def test_pure_quadruple_root_has_codimension_three() -> None:
    atlas = exact_multiplicity_atlas([1, -4, 6, -4, 1])
    assert atlas.multiplicity_partition == (4,)
    assert atlas.exact_multiplicity_counts[:4] == (0, 0, 0, 1)
    assert atlas.distinct_root_count_over_c == 1
    assert atlas.complex_stratum_codimension == 3


def test_partition_neighbors_change_complex_codimension_by_one() -> None:
    current = partition_neighborhood((3, 2, 1, 1))
    assert current.complex_codimension == 3
    assert current.more_singular == immediate_more_singular((3, 2, 1, 1))
    assert current.less_singular == immediate_less_singular((3, 2, 1, 1))
    for partition in current.more_singular:
        assert partition_neighborhood(partition).complex_codimension == 4
    for partition in current.less_singular:
        assert partition_neighborhood(partition).complex_codimension == 2


def test_degree_four_partition_lattice_has_known_hasse_shape() -> None:
    lattice = build_partition_lattice(4)
    assert lattice.status == "OAK_PASS_MULTIPLICITY_PARTITION_LATTICE"
    assert lattice.nodes == ((4,), (3, 1), (2, 2), (2, 1, 1), (1, 1, 1, 1))
    assert len(lattice.edges_less_to_more_singular) == 5
    assert ((1, 1, 1, 1), (2, 1, 1)) in lattice.edges_less_to_more_singular
    assert ((2, 1, 1), (3, 1)) in lattice.edges_less_to_more_singular
    assert ((2, 1, 1), (2, 2)) in lattice.edges_less_to_more_singular
    assert ((3, 1), (4,)) in lattice.edges_less_to_more_singular
    assert ((2, 2), (4,)) in lattice.edges_less_to_more_singular


def test_partition_lattice_optional_resource_guard_is_enforced() -> None:
    try:
        build_partition_lattice(8, maximum_nodes=2)
    except RuntimeError as exc:
        assert "maximum_nodes" in str(exc)
    else:
        raise AssertionError("resource guard should have refused the lattice")


def test_r09_cli_exact_atlas_and_partition_lattice(tmp_path) -> None:
    atlas_path = tmp_path / "atlas.json"
    lattice_path = tmp_path / "lattice.json"
    assert main([
        "multiplicity-atlas",
        "--coeffs=-4,8,-5,3,0,-4,1,1",
        "--output", str(atlas_path),
    ]) == 0
    assert main([
        "partition-lattice",
        "--degree", "4",
        "--output", str(lattice_path),
    ]) == 0
    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    lattice = json.loads(lattice_path.read_text(encoding="utf-8"))
    assert atlas["version"] == "R0.9"
    assert atlas["atlas"]["multiplicity_partition"] == [3, 2, 1, 1]
    assert lattice["version"] == "R0.9"
    assert lattice["lattice"]["node_count"] == 5
    assert lattice["lattice"]["edge_count"] == 5
