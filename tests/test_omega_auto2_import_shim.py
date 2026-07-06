def test_omega_auto2_imports():
    import omega_auto2

    assert omega_auto2 is not None


def test_omega_auto2_submodule_imports():
    from omega_auto2.capabilities import assess_capability

    assert callable(assess_capability)
