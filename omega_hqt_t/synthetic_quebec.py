from __future__ import annotations
from datetime import datetime, timezone
from .hypergraph import EnergyHypergraph
from .models import Corridor, Evidence, Hyperedge, Node, RegionState

REGIONS = (
    ("bas-saint-laurent", "Bas-Saint-Laurent", 780, 1050, 170),
    ("saguenay-lac-saint-jean", "Saguenay–Lac-Saint-Jean", 1250, 4500, 550),
    ("capitale-nationale", "Capitale-Nationale", 2200, 500, 160),
    ("mauricie", "Mauricie", 1050, 2400, 300),
    ("estrie", "Estrie", 1100, 250, 120),
    ("montreal", "Montréal", 6200, 120, 900),
    ("outaouais", "Outaouais", 1450, 450, 180),
    ("abitibi-temiscamingue", "Abitibi-Témiscamingue", 850, 1900, 250),
    ("cote-nord", "Côte-Nord", 1700, 7300, 850),
    ("nord-du-quebec", "Nord-du-Québec", 1500, 14500, 1800),
    ("gaspesie-iles", "Gaspésie–Îles-de-la-Madeleine", 620, 1600, 200),
    ("chaudiere-appalaches", "Chaudière-Appalaches", 1400, 350, 150),
    ("laval", "Laval", 1800, 50, 250),
    ("lanaudiere", "Lanaudière", 1950, 180, 220),
    ("laurentides", "Laurentides", 2100, 350, 260),
    ("monteregie", "Montérégie", 5300, 900, 650),
    ("centre-du-quebec", "Centre-du-Québec", 1150, 280, 140),
)

# Deliberately fictitious connectivity: administrative-region graph, not a real grid map.
CORRIDOR_PAIRS = (
    ("nord-du-quebec","cote-nord",4600), ("nord-du-quebec","abitibi-temiscamingue",3900),
    ("cote-nord","saguenay-lac-saint-jean",3600), ("saguenay-lac-saint-jean","capitale-nationale",2700),
    ("abitibi-temiscamingue","outaouais",2300), ("outaouais","laurentides",2100),
    ("laurentides","lanaudiere",2200), ("lanaudiere","laval",2500), ("laval","montreal",4200),
    ("montreal","monteregie",4800), ("monteregie","estrie",2600), ("estrie","centre-du-quebec",1900),
    ("centre-du-quebec","mauricie",2200), ("mauricie","capitale-nationale",2600),
    ("capitale-nationale","chaudiere-appalaches",2300), ("chaudiere-appalaches","bas-saint-laurent",2100),
    ("bas-saint-laurent","gaspesie-iles",1600), ("mauricie","lanaudiere",1800),
    ("centre-du-quebec","monteregie",2300), ("saguenay-lac-saint-jean","mauricie",2200),
)

def build_regions() -> dict[str, RegionState]:
    return {rid: RegionState(rid, demand, generation, reserve, storage_mwh=max(0.0,reserve*2.0), flexibility_fraction=0.08 if demand>1500 else 0.05) for rid,_,demand,generation,reserve in REGIONS}

def build_corridors() -> tuple[Corridor, ...]:
    result=[]
    for i,(a,b,cap) in enumerate(CORRIDOR_PAIRS):
        result.append(Corridor(f"syn-corridor-{i:02d}",a,b,reactance_pu=0.09+0.01*(i%5),capacity_mw=float(cap),length_index=1.0+0.15*(i%4),climate_exposure=0.25+0.05*(i%7),repair_hours=5.0+1.5*(i%6)))
    return tuple(result)

def build_synthetic_quebec() -> EnergyHypergraph:
    graph=EnergyHypergraph("omega-hqt:synthetic-quebec:r0.1")
    evidence=Evidence("ev-synthetic-spec-r01","generated_fixture","docs/omega-hqt-t/SYNTHETIC_DATA.md",datetime(2026,8,3,tzinfo=timezone.utc).isoformat(),"deterministic fixture generator",1.0,"public","synthetic_fixture","No operational Hydro-Québec topology or asset data.")
    graph.add_evidence(evidence)
    graph.add_node(Node("quebec","territory","Québec","province",{"synthetic":True},(evidence.evidence_id,)))
    for rid,label,demand,generation,reserve in REGIONS:
        graph.add_node(Node(rid,"region",label,"region",{"synthetic_demand_mw":demand,"synthetic_generation_mw":generation,"synthetic_reserve_mw":reserve},(evidence.evidence_id,)))
        graph.add_hyperedge(Hyperedge(f"contains:{rid}","contains",("quebec",),(rid,),{"resolution":"administrative-region"},(evidence.evidence_id,)))
    for corridor in build_corridors():
        cid=corridor.corridor_id
        graph.add_node(Node(cid,"synthetic_corridor",cid,"corridor",corridor.to_dict(),(evidence.evidence_id,)))
        graph.add_hyperedge(Hyperedge(f"connects:{cid}","synthetically_connects",(corridor.source,cid),(corridor.target,),{"not_operational_topology":True},(evidence.evidence_id,),1.0,"synthetic_fixture"))
    return graph
