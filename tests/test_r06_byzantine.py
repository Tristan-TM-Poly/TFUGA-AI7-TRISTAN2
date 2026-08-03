import pytest

from omega_re_t.byzantine_sim_r06 import WorkerVote, decide_quorum, deterministic_fault_campaign


def test_honest_quorum_accepts():
    votes = [WorkerVote(f"w{i}", "item", "sha256:p", "sha256:r", 1, f"g{i}") for i in range(4)]
    decision = decide_quorum(votes, expected_payload_digest="sha256:p", epoch=1, threshold=3, minimum_identity_groups=2)
    assert decision.accepted_result_digest == "sha256:r"
    assert decision.valid_votes == 4


def test_equivocator_removed():
    votes = [
        WorkerVote("w0", "item", "sha256:p", "sha256:r", 1, "g0"),
        WorkerVote("w0", "item", "sha256:p", "sha256:x", 1, "g0"),
        WorkerVote("w1", "item", "sha256:p", "sha256:r", 1, "g1"),
        WorkerVote("w2", "item", "sha256:p", "sha256:r", 1, "g2"),
    ]
    decision = decide_quorum(votes, expected_payload_digest="sha256:p", epoch=1, threshold=2, minimum_identity_groups=2)
    assert decision.equivocations == ("w0",)
    assert decision.accepted_result_digest == "sha256:r"


def test_wrong_epoch_payload_and_revoked_rejected():
    votes = [
        WorkerVote("a", "item", "sha256:p", "sha256:r", 0, "g"),
        WorkerVote("b", "item", "sha256:x", "sha256:r", 1, "g"),
        WorkerVote("c", "item", "sha256:p", "sha256:r", 1, "g", revoked=True),
    ]
    decision = decide_quorum(votes, expected_payload_digest="sha256:p", epoch=1, threshold=1)
    assert decision.accepted_result_digest is None
    assert len(decision.rejected_reasons) == 3


def test_conflicting_quorums_block():
    votes = [
        WorkerVote("a", "item", "sha256:p", "sha256:r1", 1, "g1"),
        WorkerVote("b", "item", "sha256:p", "sha256:r1", 1, "g2"),
        WorkerVote("c", "item", "sha256:p", "sha256:r2", 1, "g3"),
        WorkerVote("d", "item", "sha256:p", "sha256:r2", 1, "g4"),
    ]
    decision = decide_quorum(votes, expected_payload_digest="sha256:p", epoch=1, threshold=2, minimum_identity_groups=2)
    assert decision.accepted_result_digest is None
    assert "conflicting_quorums" in decision.rejected_reasons


def test_mixed_item_ids_rejected():
    with pytest.raises(ValueError):
        decide_quorum((WorkerVote("a", "x", "p", "r", 1, "g"), WorkerVote("b", "y", "p", "r", 1, "g")), expected_payload_digest="p", epoch=1, threshold=1)


def test_fault_campaign_is_deterministic():
    assert deterministic_fault_campaign(honest_workers=5, byzantine_workers=2, threshold=4) == deterministic_fault_campaign(honest_workers=5, byzantine_workers=2, threshold=4)


def test_identity_group_threshold_enforced():
    votes = [
        WorkerVote("a", "item", "sha256:p", "sha256:r", 1, "same"),
        WorkerVote("b", "item", "sha256:p", "sha256:r", 1, "same"),
        WorkerVote("c", "item", "sha256:p", "sha256:r", 1, "same"),
    ]
    decision = decide_quorum(votes, expected_payload_digest="sha256:p", epoch=1, threshold=3, minimum_identity_groups=2)
    assert decision.accepted_result_digest is None


def test_empty_votes_rejected():
    with pytest.raises(ValueError):
        decide_quorum((), expected_payload_digest="sha256:p", epoch=1, threshold=1)
