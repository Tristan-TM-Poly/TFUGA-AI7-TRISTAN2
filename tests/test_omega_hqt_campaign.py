from omega_hqt_t.experiment import run_campaign
from omega_hqt_t.interventions import catalog
from omega_hqt_t.parliament import deliberate
from omega_hqt_t.scenarios import compound_ice_storm

def test_campaign_is_deterministic():
    a=run_campaign(compound_ice_storm(),catalog(),world_count=12); b=run_campaign(compound_ice_storm(),catalog(),world_count=12)
    assert a.evidence_hash==b.evidence_hash; assert len(a.outcomes)==72; assert a.pareto_interventions

def test_parliament_preserves_claim_boundaries():
    d=deliberate(run_campaign(compound_ice_storm(),catalog(),world_count=8)); assert d.status.endswith("PASS"); assert not d.claims["operational_authority_claimed"]
