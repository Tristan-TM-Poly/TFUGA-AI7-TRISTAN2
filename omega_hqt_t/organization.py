from __future__ import annotations
from .hypergraph import EnergyHypergraph
from .models import Evidence, Hyperedge, Node

CAPABILITIES=(
    "generation-planning","hydraulic-coordination","transmission-planning","distribution-resilience",
    "asset-management","outage-restoration","engineering-construction","supply-chain",
    "customer-efficiency","regulatory-affairs","environment-territories","research-innovation",
    "data-governance","cybersecurity","workforce-development","finance-portfolio",
)

def build_public_capability_mirror() -> EnergyHypergraph:
    g=EnergyHypergraph("omega-hqt:public-capability-mirror:r0.1")
    ev=Evidence("ev-org-ontology","generated_fixture","docs/omega-hqt-t/ORGANIZATION_MIRROR.md","2026-08-03T00:00:00+00:00","capability ontology, not an internal org chart",1.0,"public","synthetic_fixture")
    g.add_evidence(ev); g.add_node(Node("hq-public-mission","organization_mirror","Hydro-Québec public mission mirror","organization",{"not_internal_org_chart":True},(ev.evidence_id,)))
    for cap in CAPABILITIES:
        nid="cap:"+cap; g.add_node(Node(nid,"capability",cap.replace("-"," ").title(),"capability",{},(ev.evidence_id,)))
        g.add_hyperedge(Hyperedge("has:"+cap,"requires_capability",("hq-public-mission",),(nid,),{},(ev.evidence_id,)))
    return g
