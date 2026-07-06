def test_omega_game_imports():
    import omega_game

    assert omega_game is not None


def test_omega_game_submodule_imports():
    from omega_game.engines import PolyglotLanguageEngine

    assert PolyglotLanguageEngine is not None
