import pytest

from omega_re_t.probabilistic_cfg_r05 import ProbabilisticCFG
from omega_re_t.protocol_negotiation_r05 import NegotiationPolicy, ProtocolVersion, negotiate


def pcfg():
    return ProbabilisticCFG(
        start="S",
        terminal_rules={"N": {"id": 1.0}, "EQ": {"=": 1.0}, "V": {"1": 0.75, "2": 0.25}},
        binary_rules={"S": {("N", "R"): 1.0}, "R": {("EQ", "V"): 1.0}},
    )


def test_inside_probability_and_viterbi():
    parsed = pcfg().inside(("id", "=", "1"))
    assert parsed.accepted
    assert parsed.probability == pytest.approx(0.75)
    assert parsed.viterbi_probability == pytest.approx(0.75)
    assert parsed.viterbi_witness


def test_pcfg_rejects_unknown_token():
    parsed = pcfg().inside(("id", "=", "3"))
    assert not parsed.accepted
    assert parsed.probability == 0.0


def test_pcfg_sampling_is_seeded():
    assert pcfg().sample(seed=1, max_tokens=3) == pcfg().sample(seed=1, max_tokens=3)
    assert len(pcfg().sample(seed=2, max_tokens=3)) == 3


def test_pcfg_token_budget_blocks():
    with pytest.raises(RuntimeError):
        pcfg().sample(seed=1, max_tokens=2)


def versions():
    client = (
        ProtocolVersion(3, "3", frozenset({"auth", "receipts"})),
        ProtocolVersion(2, "2", frozenset({"auth"})),
    )
    server = (
        ProtocolVersion(3, "3", frozenset({"auth", "receipts"})),
        ProtocolVersion(2, "2", frozenset({"auth"})),
    )
    return client, server


def test_protocol_selects_highest_compatible():
    client, server = versions()
    result = negotiate(client, server, policy=NegotiationPolicy(required_capabilities=frozenset({"auth"})))
    assert result.selected_version == "3"
    assert result.selected_rank == 3
    assert result.transcript_digest.startswith("sha256:")


def test_protocol_blocks_downgrade():
    client, server = versions()
    server = tuple(item for item in server if item.version == "2")
    result = negotiate(client, server, policy=NegotiationPolicy(prevent_downgrade_from_rank=3))
    assert result.selected_version is None
    assert result.downgrade_blocked
    assert ("2", "downgrade_blocked") in result.rejected


def test_protocol_requires_capability():
    client, server = versions()
    result = negotiate(client, server, policy=NegotiationPolicy(required_capabilities=frozenset({"nonexistent"})))
    assert result.selected_version is None
    assert all(reason == "missing_required_capability" for _, reason in result.rejected)


def test_experimental_version_blocked_by_default():
    candidate = ProtocolVersion(4, "4", frozenset({"auth"}), experimental=True)
    result = negotiate((candidate,), (candidate,))
    assert result.selected_version is None
    assert result.rejected == (("4", "experimental"),)
