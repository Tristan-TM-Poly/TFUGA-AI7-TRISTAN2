from __future__ import annotations
from pathlib import Path
from .campaign import default_campaign_spec
from .oak import evaluate_candidate
from .storage import AtomicJSONLShardWriter,atomic_write_json
from .vocabularies import WORLDS,PROCESS_PROFILES,DEFECT_PROFILES,MECHANISMS
HOT_ARCHITECTURES=16; HOT_PROCESSES=8
def hot_candidates():
    spec=default_campaign_spec()
    for wi,_world in enumerate(WORLDS):
        for ai in range(HOT_ARCHITECTURES):
            for pi in range(HOT_PROCESSES):
                defect_index=(wi*5+ai*3+pi*7)%len(DEFECT_PROFILES); index=spec.base_space.encode((wi,ai,defect_index,pi)); yield spec.candidate_at(index,environment_index=(wi+ai+pi)%len(spec.environment_profiles))
def evidence_templates():
    for candidate in hot_candidates():
        report=evaluate_candidate(candidate); yield {'evidence_id':f'evidence-template::{candidate.candidate_id}','candidate_id':candidate.candidate_id,'required_claim_types':['composition','structure','property','stability','fabricability'],'required_methods':['independent_baseline','uncertainty_budget','negative_control','out_of_sample_test'],'oak_status':report.status,'oak_score':round(report.aggregate_score,8),'blockers':report.blockers,'status':'template_not_evidence'}
def world_mechanism_mappings():
    for world in WORLDS:
        for mechanism in MECHANISMS: yield {'mapping_id':f"{world['id']}::{mechanism['id']}",'world_id':world['id'],'mechanism_id':mechanism['id'],'compatibility':'candidate_mapping_requires_domain_review','required_checks':tuple(dict.fromkeys((*world['required_checks'],*mechanism['required_evidence']))),'status':'generated_relation_not_physical_proof'}
def materialize(output_dir:str|Path,records_per_shard:int=1024):
    root=Path(output_dir); root.mkdir(parents=True,exist_ok=True); hot=AtomicJSONLShardWriter(root/'hot_atlas',records_per_shard=records_per_shard,prefix='candidates').write(hot_candidates()); evidence=AtomicJSONLShardWriter(root/'evidence',records_per_shard=records_per_shard,prefix='evidence').write(evidence_templates()); mappings=AtomicJSONLShardWriter(root/'world_mechanisms',records_per_shard=records_per_shard,prefix='mappings').write(world_mechanism_mappings()); spec=default_campaign_spec(); manifest={'system':'Ω-SOLID-T∞ R0.2','campaign':spec.plan(),'hot_projection':{'worlds':64,'architectures':HOT_ARCHITECTURES,'processes':HOT_PROCESSES,'records':64*HOT_ARCHITECTURES*HOT_PROCESSES},'evidence_templates':evidence['records'],'world_mechanism_mappings':mappings['records'],'total_materialized_logical_objects':hot['records']+evidence['records']+mappings['records'],'hot_atlas_manifest':hot,'evidence_manifest':evidence,'mapping_manifest':mappings,'boundary':'Generated objects are ontology/campaign records, not discoveries, certified materials, experiments or safety claims.'}; atomic_write_json(root/'manifest.json',manifest); return manifest
