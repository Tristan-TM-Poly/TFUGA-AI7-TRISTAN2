from omega_pure_math_t import BrickLanguage, FactorizationWitness


def test_recorded_nontrivial_factorization_blocks_irreducible_promotion():
    language = BrickLanguage("B")
    language.add(FactorizationWitness("p", ("p",)))
    assert language.irreducible("p")

    language.add(FactorizationWitness("p", ("a", "b")))
    assert not language.irreducible("p")
    assert not language.irreducible("unknown")
