from __future__ import annotations

from dataclasses import dataclass, asdict
from itertools import product
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs'

@dataclass(frozen=True)
class TileSeed:
    id: str
    name: str
    dimension: int
    fills_space: bool
    category: str
    symmetry: str
    uses: tuple[str, ...]

@dataclass(frozen=True)
class FractalRule:
    id: str
    name: str
    dimension: int
    base: int
    mask: tuple[int, ...]
    description: str

    @property
    def kept(self) -> int:
        return sum(1 for x in self.mask if x)

    @property
    def theoretical_dimension(self) -> float:
        if self.kept <= 0 or self.base <= 1:
            return 0.0
        return math.log(self.kept) / math.log(self.base)

def top27():
    names = [
        ('tri2','Equilateral triangle',2,'2d','D3','sierpinski,fem,membrane'),
        ('square2','Square',2,'2d','D4','carpet,grid,circuit'),
        ('hex2','Hexagon',2,'2d','D6','honeycomb,hqc,lc-fractal'),
        ('rect2','Rectangle',2,'2d','D2','anisotropic-grid,waveguide'),
        ('rhombus2','Rhombus',2,'2d','D2','shear,mechanical-lattice'),
        ('kite_dart2','Kite dart proxy',2,'2d-quasi','quasi','penrose-proxy,quasicrystal'),
        ('pentagon2','Tiling pentagon proxy',2,'2d','varied','complex-tiling,education'),
        ('oct_square2','Octagon square mix',2,'2d-semi-regular','D8+D4','semi-regular,mixed-field'),
        ('free_poly2','Optimized polygon',2,'2d-generated','optimized','constraint-design,topology'),
        ('cube3','Cube dice',3,'3d','Oh','voxel,menger,fabrication'),
        ('tri_prism3','Triangular prism',3,'3d','D3h','extrusion,anisotropic-layer'),
        ('hex_prism3','Hexagonal prism',3,'3d','D6h','channels,thermal,battery'),
        ('rhombic_dodeca3','Rhombic dodecahedron',3,'3d','FCC Voronoi','foam,isotropic-cell'),
        ('truncated_octa3','Truncated octahedron',3,'3d','Kelvin-like','foam,cellular-material'),
        ('tet_octa3','Tetra-octa mix',3,'3d-mixed','octet','stiff-lattice,metamaterial'),
        ('parallelepiped3','Parallelepiped',3,'3d','affine cube','anisotropic-crystal,mesh'),
        ('voronoi3','Voronoi cells',3,'3d-generated','adaptive','mycelium,defect-tolerance'),
        ('optimized_poly3','Optimized polyhedron',3,'3d-generated','optimized','mass-stiffness,conductivity'),
        ('void_center_rule','Void-center rule',3,'rule','substitution','carpet,sponge'),
        ('skeleton_rule','Skeleton rule',3,'rule','graph','edges,junctions'),
        ('channel_rule','Channel rule',3,'rule','transport','fluid,thermal'),
        ('lc_rule','LC rule',3,'rule','circuit','inductance,capacitance'),
        ('optical_rule','Optical rule',3,'rule','resonator','cavity,photonic'),
        ('mechanical_rule','Mechanical rule',3,'rule','mechanics','stiffness,mass'),
        ('mycelial_rule','Mycelial rule',3,'rule','adaptive','resource-growth,redundancy'),
        ('multiscale_rule','Multiscale rule',3,'rule','scale','nano-micro-macro,hierarchy'),
        ('antifragile_rule','Antifragile rule',3,'rule','resilience','repair,alternate-paths'),
    ]
    return [TileSeed(i,n,d,True,c,s,tuple(u.split(','))) for i,n,d,c,s,u in names]

def sierpinski_carpet():
    return FractalRule('sierpinski_carpet','Square carpet 3x3 minus center',2,3,(1,1,1,1,0,1,1,1,1),'Classic 2D void-center substitution.')

def sierpinski_triangle_proxy():
    return FractalRule('sierpinski_triangle_proxy','Triangle 2x2 keep 3',2,2,(1,1,1,0),'Triangular proxy encoded as tensor mask.')

def menger_sponge():
    mask=[]
    for z,y,x in product(range(3), repeat=3):
        mid = (x==1)+(y==1)+(z==1)
        mask.append(0 if mid>=2 else 1)
    return FractalRule('menger_sponge','Cube 3x3x3 keep 20',3,3,tuple(mask),'Classic Menger sponge mask.')

def binary_cube():
    return FractalRule('binary_cube','Binary cube keep all',3,2,tuple([1]*8),'Dense voxel baseline.')

def all_rules():
    return [sierpinski_carpet(), sierpinski_triangle_proxy(), menger_sponge(), binary_cube()]

def iterate(rule: FractalRule, depth: int):
    cells={tuple([0]*rule.dimension)}
    offsets=[]
    for idx, keep in enumerate(rule.mask):
        if not keep:
            continue
        val=idx; coords=[]
        for _ in range(rule.dimension):
            coords.append(val % rule.base); val//=rule.base
        offsets.append(tuple(coords))
    for _ in range(depth):
        cells={tuple(c[i]*rule.base + off[i] for i in range(rule.dimension)) for c in cells for off in offsets}
    return cells

def adjacency_graph(cells):
    cells=set(cells)
    if not cells:
        return {'nodes': [], 'edges': []}
    dim=len(next(iter(cells)))
    nodes=[{'id': ','.join(map(str,c)), 'coord': list(c)} for c in sorted(cells)]
    edges=[]; seen=set()
    for c in cells:
        for axis in range(dim):
            nb=list(c); nb[axis]+=1; nb=tuple(nb)
            if nb in cells:
                a=','.join(map(str,c)); b=','.join(map(str,nb)); key=tuple(sorted([a,b]))
                if key not in seen:
                    seen.add(key); edges.append({'source': a, 'target': b, 'contact': 'face'})
    return {'nodes': nodes, 'edges': edges}

def basic_metrics(cells, rule, depth):
    side=rule.base ** depth if depth else 1
    total=side ** rule.dimension
    filled=len(cells)
    return {
        'rule_id': rule.id,
        'depth': depth,
        'dimension': rule.dimension,
        'side': side,
        'filled_cells': filled,
        'total_cells': total,
        'relative_density': round(filled/total, 8),
        'porosity': round(1-filled/total, 8),
        'theoretical_fractal_dimension': round(rule.theoretical_dimension, 8),
    }

def graph_metrics(graph):
    n=len(graph['nodes']); m=len(graph['edges'])
    return {'node_count': n, 'edge_count': m, 'avg_degree': round(0 if n==0 else 2*m/n, 4), 'connectivity_proxy': round(m/max(1,n-1),4)}

def power_score(fertility=.92, verifiability=.82, reusability=.94, impact=.86, compression=.88, stability=.72, complexity=.55, noise=.22, speculation=.30, risk=.28):
    num=fertility*verifiability*reusability*impact*compression*stability
    den=max(1e-9, complexity*noise*speculation*risk)
    raw=num/den
    return round(raw/(1+raw),6)

def lc_export(graph, r=1.0, l=1e-6, c=1e-9):
    return {'kind':'LCNetworkExport','node_count':len(graph['nodes']),'component_count':len(graph['edges']),'components':[{'id':f'Z{i}','source':e['source'],'target':e['target'],'R_ohm':r,'L_H':l,'C_F':c,'impedance':'R + j*w*L + 1/(j*w*C)'} for i,e in enumerate(graph['edges'])]}

def material_metrics(geom):
    rho=geom['relative_density']
    return {'relative_density':rho,'porosity':geom['porosity'],'E_eff_over_E_s_proxy':round(rho**2,8),'kappa_eff_over_kappa_s_proxy':round(rho,8),'status':'coarse-scaling-proxy-not-physical-validation'}

def write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')

def run_all():
    OUT.mkdir(parents=True, exist_ok=True)
    candidates=[]
    for rule in all_rules():
        depth=2 if rule.dimension==3 else 3
        cells=iterate(rule, depth)
        graph=adjacency_graph(cells)
        candidates.append({'rule_id':rule.id,'rule_name':rule.name,'power':power_score(),'metrics':basic_metrics(cells,rule,depth),'graph_metrics':graph_metrics(graph)})
    candidates.sort(key=lambda x: x['power'], reverse=True)
    top=candidates[0]
    best=sierpinski_carpet()
    best_cells=iterate(best,3)
    best_graph=adjacency_graph(best_cells)
    payload={'status':'succeeded','decision':'PUBLISH_AS_CRYSTALLIZABLE_SOFTWARE_PACKET','stable_canon_allowed':False,'top_candidate':top,'candidate_count':len(candidates)}
    payload['receipt_sha256']=hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    write_json(OUT/'top27_catalogue.json',[asdict(t) for t in top27()])
    write_json(OUT/'top_candidates.json',candidates)
    write_json(OUT/'hgfm_graph.json',{'kind':'HGFM-tiling-graph','nodes':best_graph['nodes'],'edges':best_graph['edges'],'hyperedges':[{'id':'tile-rule-metric-export','members':['tile','rule','fractal','graph','metrics','lc','material','dct'],'type':'pipeline'}]})
    write_json(OUT/'lc_network.json',lc_export(best_graph))
    write_json(OUT/'material_metrics.json',material_metrics(basic_metrics(best_cells,best,3)))
    write_json(OUT/'validation_receipt.json',payload)
    (OUT/'DCTPP_REPORT.md').write_text('# DCT++ Report - FTTE-AI7 v0.3\n\nDecision: '+payload['decision']+'\n\nStable canon allowed: false\n\nAntiHype: geometric/code packet only; physical claims require experiments.\n', encoding='utf-8')
    return payload

if __name__ == '__main__':
    print(json.dumps(run_all(), indent=2, ensure_ascii=False))
