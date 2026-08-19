from tools.dead_end_converter import DeadEndType, convert_dead_end


def test_no_test_creates_test_skeleton():
    conversion = convert_dead_end(DeadEndType.NO_TEST)
    assert conversion.safe_artifact == "test_skeleton"


def test_no_benchmark_creates_simple_baseline():
    conversion = convert_dead_end(DeadEndType.NO_BENCHMARK)
    assert conversion.safe_artifact == "simple_baseline"


def test_no_authorized_decision_creates_review_packet():
    conversion = convert_dead_end(DeadEndType.NO_AUTHORIZED_DECISION)
    assert conversion.safe_artifact == "review_packet"
