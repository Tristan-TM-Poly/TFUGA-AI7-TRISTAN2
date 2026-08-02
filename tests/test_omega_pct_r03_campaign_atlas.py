from pathlib import Path
from tools.audit_omega_pct_r03_campaign import audit

def test_campaign_atlas_is_exact_unique_and_guarded():
    report=audit(Path(__file__).parents[1])
    assert report['passed'] is True
    assert report['records']==8192
    assert report['unique']==8192
    assert report['permanent_total_ceiling'] is None
    assert report['automatic_scientific_promotion'] is False
