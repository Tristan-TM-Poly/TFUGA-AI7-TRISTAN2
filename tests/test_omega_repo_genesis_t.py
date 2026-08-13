import json
from pathlib import Path

import pytest

from omega_repo_genesis_t.model import Constellation, RepoSpec
from omega_repo_genesis_t.plan import bootstrap_files, build_plan, load_constellation

PATH = Path("data/omega_repo_genesis_t/constellation_v01.json")


def test_constellation_is_private_unique_and_materializable():
    c = load_constellation(PATH)
    assert len(c.repositories) == 8
    assert len({r.name for r in c.repositories}) == 8
    assert all(r.visibility == "private" for r in c.repositories)
    plan = build_plan(c)
    assert plan["counts"] == {"declared": 8, "create_candidates": 8, "holds": 0}
    assert plan["policy"]["public_creation_allowed"] is False
    assert len(plan["fingerprint"]) == 64


def test_public_spec_fails_closed():
    with pytest.raises(ValueError):
        RepoSpec.from_dict({"name": "bad-public", "description": "x", "role": "x", "visibility": "public"})


def test_low_split_score_holds():
    payload = json.loads(PATH.read_text())
    payload["repositories"][0]["split_score"] = 0.2
    c = Constellation.from_dict(payload)
    plan = build_plan(c)
    assert plan["counts"]["holds"] == 1
    assert plan["holds"][0]["hold_reason"] == "split_score_below_materialization_threshold"


def test_bootstrap_is_provenance_and_oak_bound():
    c = load_constellation(PATH)
    plan = build_plan(c)
    files = bootstrap_files(plan["create_candidates"][0], c)
    assert set(files) == {
        "README.md", "repo.genome.json", "capabilities.json", "relations.json", ".github/workflows/oak-repo-cell.yml"
    }
    genome = json.loads(files["repo.genome.json"])
    assert genome["source_sha"] == c.source_sha
    assert genome["visibility"] == "private"
    assert genome["authority"]["automatic_merge"] is False
    assert genome["authority"]["public_release"] is False
