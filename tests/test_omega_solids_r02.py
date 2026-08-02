from dataclasses import asdict
import pytest
from omega_solids_t.vocabularies import *
from omega_solids_t.mixed_radix import MixedRadixSpace
from omega_solids_t.campaign import default_campaign_spec
from omega_solids_t.models import Quantity,SolidGenomeR2
from omega_solids_t.oak import evaluate_candidate
from omega_solids_t.hypergraph import from_candidate
from omega_solids_t.physics import *
from omega_solids_t.uncertainty import *
from omega_solids_t.compiler import Objective,SolidCompiler,maximum_defect_criticality
from omega_solids_t.storage import AtomicJSONLShardWriter,verify_manifest
from omega_solids_t.materialize import hot_candidates,evidence_templates,world_mechanism_mappings,materialize

def test_vocab_cardinalities(): assert validate_vocabularies()=={'worlds':64,'architectures':64,'defect_profiles':16,'process_profiles':8,'environment_profiles':4,'mechanisms':64}
def test_world_indices_contiguous(): assert [x['index'] for x in WORLDS]==list(range(64))
def test_arch_indices_contiguous(): assert [x['index'] for x in ARCHITECTURES]==list(range(64))
def test_unique_world_names(): assert len({x['name'] for x in WORLDS})==64
def test_every_world_has_checks(): assert all(x['required_checks'] for x in WORLDS)
def test_every_mechanism_has_evidence_requirements(): assert all(len(x['required_evidence'])==4 for x in MECHANISMS)
@pytest.mark.parametrize('radices',[(2,3),(64,64,16,8),(1,7,5)])
def test_mixed_radix_roundtrip(radices):
    space=MixedRadixSpace(radices)
    for index in {0,space.cardinality//2,space.cardinality-1}: assert space.encode(space.decode(index))==index
def test_mixed_radix_rejects_out_of_range():
    space=MixedRadixSpace((2,3))
    with pytest.raises(IndexError): space.decode(6)
    with pytest.raises(ValueError): space.encode((2,0))
def test_default_campaign_cardinality():
    spec=default_campaign_spec(); assert spec.base_cardinality==524288; assert spec.contextual_cardinality==2097152
def test_campaign_fingerprint_stable(): assert default_campaign_spec().fingerprint==default_campaign_spec().fingerprint
def test_campaign_candidate_deterministic():
    spec=default_campaign_spec(); a=spec.candidate_at(12345,2); b=spec.candidate_at(12345,2); assert a==b and a.fingerprint==b.fingerprint
def test_campaign_endpoints():
    spec=default_campaign_spec(); assert spec.candidate_at(0).logical_index==0; assert spec.candidate_at(spec.base_cardinality-1).logical_index==spec.base_cardinality-1
def test_campaign_plan_complete():
    plan=default_campaign_spec().plan(10000); assert sum(x['records'] for x in plan['partitions'])==524288; assert plan['no_permanent_total_candidate_cap'] is True
def test_candidate_required_checks_unique():
    candidate=default_campaign_spec().candidate_at(42); assert len(candidate.required_checks)==len(set(candidate.required_checks))
def test_candidate_mechanisms_unique(): assert len(set(default_campaign_spec().candidate_at(1).mechanism_ids))==4
@pytest.mark.parametrize('index',[0,1,17,999,524287])
def test_oak_has_twelve_gates(index):
    report=evaluate_candidate(default_campaign_spec().candidate_at(index)); assert len(report.findings)==12; assert 0<=report.aggregate_score<=1
def test_oak_quarantines_unknown_world():
    spec=default_campaign_spec(); index=spec.base_space.encode((63,0,0,0)); assert evaluate_candidate(spec.candidate_at(index)).status=='QUARANTINED'
def test_oak_quarantines_critical_defect():
    spec=default_campaign_spec(); index=spec.base_space.encode((0,0,15,0)); assert 'OAK-05-stability' in evaluate_candidate(spec.candidate_at(index)).blockers
def test_hypergraph_integrity():
    graph=from_candidate(default_campaign_spec().candidate_at(4)); assert graph.validate()['valid']; assert len(graph.nodes)>=10; assert len(graph.edges)>=5
def test_hypergraph_graphml_has_hyperedge_nodes():
    text=from_candidate(default_campaign_spec().candidate_at(4)).to_graphml(); assert 'hyperedge::' in text and 'candidate_context' in text
def test_elasticity_relations():
    elasticity=IsotropicElasticity(210e9,0.3); assert elasticity.shear_modulus_Pa==pytest.approx(80.769230769e9); assert elasticity.bulk_modulus_Pa==pytest.approx(175e9)
def test_mixture_bounds():
    voigt=rule_of_mixtures([100,10],[.5,.5],'voigt'); reuss=rule_of_mixtures([100,10],[.5,.5],'reuss'); hill=rule_of_mixtures([100,10],[.5,.5],'hill'); assert reuss<hill<voigt
def test_hall_petch_decreases_with_grain_size(): assert hall_petch_strength(1e8,1e5,1e-6)>hall_petch_strength(1e8,1e5,1e-4)
def test_gibson_ashby_limit(): assert gibson_ashby_modulus(1e9,1.0)==pytest.approx(1e9)
def test_fracture_safety_factor_decreases_with_crack(): assert fracture_safety_factor(1e6,1e5,1e-6)>fracture_safety_factor(1e6,1e5,1e-4)
def test_arrhenius_increases_with_temperature(): assert arrhenius_diffusivity(1e-6,1e5,1000)>arrhenius_diffusivity(1e-6,1e5,500)
def test_thermal_stress_zero_delta(): assert constrained_thermal_stress(1e9,1e-5,0)==0
def test_interval_intersection(): assert Interval(0,2).intersect(Interval(1,3))==Interval(1,2)
def test_independent_uncertainty(): assert combine_independent_standard_uncertainties([3,4])==5
def test_u2_coverage_improves(): assert u2_from_coverage(measurement_coverage=.9,provenance_coverage=.9,model_validation=.9,repeatability=.9).aggregate < u2_from_coverage(measurement_coverage=.1,provenance_coverage=.1,model_validation=.1,repeatability=.1).aggregate
def test_monte_carlo_reproducible(): assert monte_carlo(lambda x:x,[normal(0,1)],samples=1000,seed=7)==monte_carlo(lambda x:x,[normal(0,1)],samples=1000,seed=7)
def test_quantity_validation():
    with pytest.raises(ValueError): Quantity(float('nan'),'Pa')
    with pytest.raises(ValueError): Quantity(1,'Pa',-1)
def test_genome_fraction_validation():
    quantity=Quantity(1,'Pa'); genome=SolidGenomeR2('g','n','f',{'A':1.0},{'covalent':1.0},{},[],[],[],{'E':quantity},{},[],[],[]); assert len(genome.fingerprint)==64
    with pytest.raises(ValueError): SolidGenomeR2('g','n','f',{'A':.7},{'covalent':1.0},{},[],[],[],{'E':quantity},{},[],[],[])
def test_compiler_ranks():
    spec=default_campaign_spec(); candidates=[spec.candidate_at(i) for i in range(50)]; compiler=SolidCompiler([Objective('defect_criticality',0.1,.2,mode='minimize')],[maximum_defect_criticality(.8)]); ranked=compiler.rank(candidates,limit=5); assert len(ranked)==5; assert ranked==sorted(ranked,key=lambda r:(-r.total_score,r.candidate.candidate_id))
def test_sharded_writer_and_verify(tmp_path):
    writer=AtomicJSONLShardWriter(tmp_path,records_per_shard=7,prefix='x'); manifest=writer.write(default_campaign_spec().iter_candidates(0,20)); assert manifest['records']==20 and len(manifest['shards'])==3; assert verify_manifest(tmp_path,'x_manifest.json')['valid']
def test_hot_projection_count(): assert sum(1 for _ in hot_candidates())==8192
def test_evidence_template_count(): assert sum(1 for _ in evidence_templates())==8192
def test_world_mechanism_count(): assert sum(1 for _ in world_mechanism_mappings())==4096
def test_materialize_counts(tmp_path):
    result=materialize(tmp_path,records_per_shard=1000); assert result['total_materialized_logical_objects']==20480; assert result['campaign']['base_cardinality']==524288
def test_hot_projection_unique_ids():
    ids=[candidate.candidate_id for candidate in hot_candidates()]; assert len(ids)==len(set(ids))
def test_hot_projection_unique_fingerprints():
    fingerprints=[candidate.fingerprint for candidate in hot_candidates()]; assert len(fingerprints)==len(set(fingerprints))
def test_context_variants_change_fingerprint():
    spec=default_campaign_spec(); assert spec.candidate_at(10,0).fingerprint!=spec.candidate_at(10,1).fingerprint
def test_no_fixed_candidate_max_constant():
    import inspect,omega_solids_t.campaign as campaign
    source=inspect.getsource(campaign); assert 'MAX_CANDIDATES' not in source and 'MAX_ADDITIONS' not in source
