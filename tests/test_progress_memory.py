from tools.progress_memory import create_progress_trace


def test_progress_trace_records_next_step():
    trace = create_progress_trace(
        what_changed="created file",
        why="advance repo work",
        next_safe_action="add check"
    )
    assert trace.what_changed == "created file"
    assert trace.next_safe_action == "add check"
