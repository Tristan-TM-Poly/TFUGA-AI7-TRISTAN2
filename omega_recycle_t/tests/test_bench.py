from omega_recycle.bench import run_oakbench


def test_oakbench_is_reproducible_and_oak_safe() -> None:
    first = run_oakbench()
    second = run_oakbench()
    assert first == second
    assert first["deterministic"] is True
    assert first["plan"]["dry_run_only"] is True
    assert first["oak"]["physical_execution_authorized"] is False
    assert first["oak"]["status"] == "D-MVP"
