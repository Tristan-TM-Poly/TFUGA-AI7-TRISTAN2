from pathlib import Path
from omega_org_fam_t.codec import MixedRadixCodec
from omega_org_fam_t.frontier import AdaptiveFrontierController
from omega_org_fam_t.packed_atlas import audit_packed_atlas, generate_packed_atlas
from omega_org_fam_t.reaction_grammar import evaluate_reaction
from omega_org_fam_t.registry import default_ultra_registry
from omega_org_fam_t.spectral_grammar import evaluate_family
from omega_org_fam_t.ultra_atlas import audit_ultra_atlas, generate_ultra_atlas


def test_registry_scale_and_exact_roundtrip():
    registry=default_ultra_registry(); codec=MixedRadixCodec(registry)
    assert registry.family_space_size == 17_179_869_184
    assert registry.linked_object_space_size == 68_719_476_736
    for index in (0,1,262_143,2**32,registry.family_space_size-1):
        assert codec.encode(codec.decode(index).coordinate)==index


def test_frontier_expands_without_permanent_total_ceiling(tmp_path: Path):
    controller=AdaptiveFrontierController(initial_batch=1024)
    for _ in range(10): controller.success(controller.state.batch_size,latency_s=1,memory_ratio=.2)
    assert controller.state.batch_size > 1_000_000
    event=controller.failure("simulated_memory_pressure")
    assert event["next_batch"] < event["previous_batch"]
    controller.save(tmp_path/"checkpoint.json")
    restored=AdaptiveFrontierController.load(tmp_path/"checkpoint.json")
    assert restored.state.next_index==controller.state.next_index


def test_jsonl_reference_atlas_and_audit(tmp_path: Path):
    manifest=generate_ultra_atlas(tmp_path/"jsonl",family_records=1024,family_shard_size=256,evidence_shard_size=768)
    assert manifest["total_objects"]==4096
    assert audit_ultra_atlas(tmp_path/"jsonl")["valid"]


def test_packed_atlas_represents_each_object_and_audits(tmp_path: Path):
    manifest=generate_packed_atlas(tmp_path/"packed",family_records=4096,shard_families=1024)
    assert manifest["total_objects"]==16384
    audit=audit_packed_atlas(tmp_path/"packed",sample_stride=17)
    assert audit["valid"] and audit["samples_checked"]>0


def test_spectral_match_remains_compatibility_not_identity():
    result=evaluate_family("alcohol_phenol","ftir",["O-H environment","C-O mode"])
    assert result["score"]==1.0
    assert result["status"]=="compatible_not_identified"


def test_reaction_promotion_requires_atom_and_charge_balance():
    fail=evaluate_reaction("alcohol_oxidation",reactants=("alcohol_phenol",),conditions=("oxidizing_context",))
    assert not fail["promotable"]
    passed=evaluate_reaction("alcohol_oxidation",reactants=("alcohol_phenol",),conditions=("oxidizing_context",),atom_balance={"C":0,"H":0,"O":0},charge_balance=0)
    assert passed["promotable"]
