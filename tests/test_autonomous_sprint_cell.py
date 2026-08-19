from tools.autonomous_sprint_cell import create_sprint_cell


def test_sprint_cell_has_required_outputs():
    sprint = create_sprint_cell("advance queue")
    assert "doc_or_tool_or_test" in sprint.artifacts
    assert "minimal_regression_or_consistency_check" in sprint.checks
    assert sprint.next_sprint == "choose_next_safe_queue_item"
