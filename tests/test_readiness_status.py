from tools.merge_readiness_gate import ReadinessState, assess_merge_readiness


def test_missing_items_is_audit_ready():
    decision = assess_merge_readiness()
    assert decision.state == ReadinessState.AUDIT_READY
    assert decision.missing


def test_complete_items_is_review_ready():
    decision = assess_merge_readiness(
        import_smoke=True,
        layer_index=True,
        connector_aliases=True,
        ci_path_known=True,
        micro_pr_plan=True,
        oak_reports=True,
    )
    assert decision.state == ReadinessState.REVIEW_READY
    assert decision.missing == ()
