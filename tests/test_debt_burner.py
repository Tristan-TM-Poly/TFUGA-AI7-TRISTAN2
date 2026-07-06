import pytest

from tools.debt_burner import DebtPacket, DebtType, burn_debt_packets, convert_debt_to_task


def test_proof_debt_becomes_test_or_benchmark_task():
    task = convert_debt_to_task(DebtType.PROOF, "missing falsification")
    assert task.task_type == "generate_test_or_benchmark"
    assert task.queue == "Q3"
    assert task.artifact == "tests/"


def test_risk_debt_routes_to_oak_report():
    task = convert_debt_to_task("risk_debt", "public claim needs boundary")
    assert task.task_type == "generate_oak_report"
    assert task.artifact == "docs/oak_reports/"


def test_high_severity_debt_routes_to_review_queue():
    task = convert_debt_to_task(DebtType.SOURCE, "source uncertain", severity=9)
    assert task.queue == "Q10"


def test_unknown_debt_type_rejected():
    with pytest.raises(ValueError):
        convert_debt_to_task("unknown_debt", "gap")


def test_burn_debt_packets_preserves_order():
    tasks = burn_debt_packets(
        (
            DebtPacket(DebtType.TEST, "missing unit test"),
            DebtPacket(DebtType.CANON_LINK, "missing canon edge"),
        )
    )
    assert [task.task_type for task in tasks] == ["generate_test_skeleton", "generate_canon_graph_edge"]
