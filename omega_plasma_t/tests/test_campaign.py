from omega_plasma_t.campaign import *
def test_campaign_has_no_permanent_cap(tmp_path):
    g=CampaignGenerator([CampaignAxis("density",(1e16,1e17,1e18)),CampaignAxis("B",(0,0.1)),CampaignAxis("model",("fluid","kinetic"))],CampaignPolicy(checkpoint_every=2))
    out=tmp_path/"c.jsonl"; r=g.emit_jsonl(out,work_budget=7)
    assert r["written"]==7 and r["permanent_cap"] is False and len(out.read_text().splitlines())==7
