from dataclasses import replace
import pytest

from omega_re_t.transparency_log_r06 import (
    InclusionStep,
    TransparencyLog,
    inclusion_proof,
    leaf_hash,
    merkle_root,
    node_hash,
    verify_inclusion,
)


def build_log(count=5):
    log = TransparencyLog()
    for index in range(count):
        log.append(kind="evidence", payload={"index": index}, provenance="fixture")
    return log


def test_empty_and_single_roots():
    assert len(merkle_root(())) == 64
    leaf = leaf_hash({"x": 1})
    assert merkle_root((leaf,)) == leaf


def test_node_hash_order_matters():
    left, right = leaf_hash({"x": 1}), leaf_hash({"x": 2})
    assert node_hash(left, right) != node_hash(right, left)


def test_inclusion_for_every_leaf():
    log = build_log(7)
    hashes = log.leaf_hashes()
    root = merkle_root(hashes)
    for index, leaf in enumerate(hashes):
        assert verify_inclusion(leaf, inclusion_proof(hashes, index), root)


def test_tampered_leaf_or_proof_fails():
    log = build_log(4)
    hashes = log.leaf_hashes()
    proof = list(inclusion_proof(hashes, 1))
    assert not verify_inclusion(leaf_hash({"tampered": True}), proof, merkle_root(hashes))
    proof[0] = replace(proof[0], sibling_hash=leaf_hash({"wrong": True}))
    assert not verify_inclusion(hashes[1], proof, merkle_root(hashes))


def test_invalid_side_fails():
    leaf = leaf_hash({"x": 1})
    assert not verify_inclusion(leaf, (InclusionStep(leaf, "middle"),), leaf)


def test_checkpoint_chain_and_proof():
    log = build_log(2)
    first = log.checkpoint()
    log.append(kind="evidence", payload={"index": 2}, provenance="fixture")
    second = log.checkpoint()
    entry, proof, checkpoint = log.prove(2)
    assert second.previous_checkpoint_digest == first.checkpoint_digest
    assert verify_inclusion(leaf_hash(entry.__dict__), proof, checkpoint.root_hash)
    assert log.audit_checkpoints() == (True, ())


def test_blank_metadata_rejected():
    log = TransparencyLog()
    with pytest.raises(ValueError):
        log.append(kind="", payload={}, provenance="fixture")


def test_out_of_range_proof_rejected():
    with pytest.raises(IndexError):
        inclusion_proof((leaf_hash({"x": 1}),), 2)
