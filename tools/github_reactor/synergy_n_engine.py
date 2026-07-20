#!/usr/bin/env python3
"""Read-only Ω-SYNERGY-N-T inventory and bounded n-order research planner."""
from __future__ import annotations

import argparse, hashlib, itertools, json, math, pathlib, re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass

SUFFIXES={'.md','.py','.json','.yaml','.yml','.toml','.txt'}
IGNORE={'.git','.venv','venv','node_modules','__pycache__','.pytest_cache','dist','build'}
OMEGA=re.compile(r'(?:Ω-[A-Z0-9][A-Z0-9+²³∞/]*(?:-[A-Z0-9+²³∞/]+)*-T(?:∞)?|OMEGA_[A-Z0-9][A-Z0-9_]*_T)')
CORE=('OAKGate','OAKBench','OAK','CVCD','HGFM','HGFMnD','AUTO²','Bayes-Tristan','Noether-Tristan','Rosette-Tristan','DCT-Ω','M⁺','M⁻','TFUGA','AI-7','AIT','EAIT')
DOMAINS={
 'proof':('proof','preuve','evidence','claim','oak','audit','falsif'),
 'automation':('auto','workflow','agent','reactor','pipeline'),
 'software':('code','python','api','cli','schema','github','test'),
 'mathematics':('tensor','graph','algebra','transform','svd','theorem','math'),
 'physics':('energy','laser','opt','quantum','gravity','circuit','fluid','physics'),
 'biology':('bio','cell','protein','neuro','organism','evolution'),
 'materials':('material','crystal','mems','manufactur','print'),
 'knowledge':('document','rosette','knowledge','information','atlas','search'),
 'business':('company','revenue','venture','product','market','licens','ip'),
 'governance':('legal','privacy','govern','policy','quebec','canada'),
 'art':('game','manga','story','world','narrative','creative'),
}
COMPLEMENTS={frozenset(x) for x in [('proof','software'),('proof','physics'),('proof','biology'),('automation','knowledge'),('automation','business'),('mathematics','physics'),('mathematics','software'),('materials','physics'),('knowledge','business'),('governance','business'),('art','software')]}

@dataclass
class Node:
    name:str; paths:list[str]; mentions:int; domains:list[str]; tokens:list[str]; evidence:float; risk:float
@dataclass
class Candidate:
    order:int; systems:list[str]; score:float; pair_mean:float; bottleneck:float; coverage:float; evidence:float; risk:float; packet_id:str

def sid(parts,prefix): return f"{prefix}-{hashlib.sha256(chr(31).join(parts).encode()).hexdigest()[:16]}"
def words(s): return {x.lower() for x in re.findall(r'[A-Za-zÀ-ÿ0-9²³∞]+',s) if len(x)>2}
def jac(a,b): return len(a&b)/len(a|b) if a|b else 0.0

def files(root):
    for p in root.rglob('*'):
        if p.is_file() and p.suffix.lower() in SUFFIXES and not any(x in IGNORE for x in p.relative_to(root).parts):
            try:
                if p.stat().st_size<=1_000_000: yield p
            except OSError: pass

def ids(text):
    out={m.group(0).replace('_','-') for m in OMEGA.finditer(text)}
    for name in CORE:
        if re.search(rf'(?<![\w-]){re.escape(name)}(?![\w-])',text,re.I): out.add(name)
    return out

def domains(text):
    low=text.lower(); out={d for d,ks in DOMAINS.items() if any(k in low for k in ks)}
    return out or {'general'}

def evidence(path,mentions):
    s=.08; q=path.as_posix().lower()
    if any(x in path.parts for x in ('src','tools','core','prototypes')): s+=.22
    if 'test' in q: s+=.25
    if 'schema' in q: s+=.12
    if 'report' in q or 'oak' in q: s+=.12
    if 'docs/canon' in q: s+=.12
    return min(1.0,s+.05*math.log1p(mentions))

def risk(text):
    low=text.lower(); risky=('weapon','medical','diagnos','crime','fraud','high voltage','laser','biohazard')
    hype=('universal','absolute','infinite','omniversal','proof of everything')
    return min(.9,.12*sum(x in low for x in risky)+.06*sum(x in low for x in hype))

def discover(roots,max_nodes=800):
    rec={}; file_ids={}
    for root in roots:
        root=root.resolve()
        for p in files(root):
            local=p.relative_to(root); text=p.read_text(encoding='utf-8',errors='replace'); found=sorted(ids(text))
            if not found: continue
            key=f'{root.name}/{local.as_posix()}'; file_ids[key]=found
            ds=domains(key+'\n'+text[:12000]); ts=words(key+'\n'+text[:12000]); rr=risk(text[:12000])
            for name in found:
                r=rec.setdefault(name,{'paths':set(),'mentions':0,'domains':Counter(),'tokens':Counter(),'risks':[],'base':[]})
                n=text.lower().count(name.lower()) or 1; r['paths'].add(key); r['mentions']+=n; r['domains'].update(ds); r['tokens'].update(ts); r['risks'].append(rr); r['base'].append((local,n))
    nodes=[]
    for name,r in rec.items():
        ev=max((evidence(p,n) for p,n in r['base']),default=0)
        nodes.append(Node(name,sorted(r['paths']),r['mentions'],[x for x,_ in r['domains'].most_common(6)],[x for x,_ in r['tokens'].most_common(40)],round(ev,4),round(sum(r['risks'])/len(r['risks']),4)))
    nodes.sort(key=lambda x:(-x.evidence,-x.mentions,x.name)); return nodes[:max_nodes],file_ids

def pair_score(a,b,shared=0):
    ta,tb=set(a.tokens),set(b.tokens); da,db=set(a.domains),set(b.domains)
    comp=min(1.0,.35*len({frozenset((x,y)) for x in da for y in db if x!=y}&COMPLEMENTS))
    lexical=jac(ta,tb); overlap=jac(da,db); co=min(1.0,shared/3); ev=math.sqrt(a.evidence*b.evidence); rr=(a.risk+b.risk)/2
    same=1.0 if re.sub(r'[-_](R|V)?\d.*$','',a.name)==re.sub(r'[-_](R|V)?\d.*$','',b.name) else 0.0
    return max(0,min(1,.22*lexical+.14*overlap+.22*comp+.18*co+.24*ev-.16*rr-.10*same))

def pair_graph(nodes,file_ids,limit):
    by={n.name:n for n in nodes}; buckets=defaultdict(set); shared=Counter()
    for n in nodes:
        for x in n.domains[:4]: buckets['d:'+x].add(n.name)
        for x in n.tokens[:18]: buckets['t:'+x].add(n.name)
    pairs=set()
    for members in buckets.values():
        members=sorted(members)[:120]
        if len(members)>1: pairs.update(itertools.combinations(members,2))
    for found in file_ids.values():
        active=sorted(set(found)&by.keys())
        if 1<len(active)<=80: pairs.update(itertools.combinations(active,2)); shared.update(itertools.combinations(active,2))
    pairs.update(itertools.combinations([n.name for n in nodes[:50]],2))
    scored=sorted(((pair_score(by[a],by[b],shared[(a,b)]),(a,b)) for a,b in pairs),key=lambda x:(-x[0],x[1]))[:limit]
    return {p:round(s,6) for s,p in scored}

def combo(names,by,ps):
    vals=[ps.get(tuple(sorted((a,b))),pair_score(by[a],by[b])) for a,b in itertools.combinations(names,2)]
    pm=sum(vals)/len(vals); bn=min(vals); cov=min(1,len({d for n in names for d in by[n].domains})/max(3,len(names)+1)); ev=sum(by[n].evidence for n in names)/len(names); rr=sum(by[n].risk for n in names)/len(names)
    score=max(0,min(1,.48*pm+.16*bn+.18*cov+.22*ev-.18*rr-.035*max(0,len(names)-2)))
    return Candidate(len(names),list(names),round(score,6),round(pm,6),round(bn,6),round(cov,6),round(ev,6),round(rr,6),sid(names,'RPK'))

def search(nodes,file_ids,max_order=4,beam=96,top=25):
    by={n.name:n for n in nodes}; ps=pair_graph(nodes,file_ids,max(beam*10,top*20)); neigh=defaultdict(set)
    for a,b in ps: neigh[a].add(b); neigh[b].add(a)
    cur=sorted((combo(p,by,ps) for p in ps),key=lambda c:(-c.score,c.systems))[:beam]; out={2:cur[:top]}
    for order in range(3,max_order+1):
        nxt={}
        for c in cur:
            have=set(c.systems); pool=set().union(*(neigh[n] for n in have))-have or set(by)-have
            for x in sorted(pool):
                names=tuple(sorted((*have,x)))
                if len(names)==order and names not in nxt: nxt[names]=combo(names,by,ps)
        cur=sorted(nxt.values(),key=lambda c:(-c.score,c.systems))[:beam]; out[order]=cur[:top]
        if not cur: break
    return out,ps

def packet(c,by):
    terms=sorted({t for n in c.systems for t in by[n].tokens[:8]})[:18]
    return {'id':c.packet_id,'order':c.order,'systems':c.systems,'status':'REVIEW_ONLY_HYPOTHESIS','question':'Sous quelles hypothèses la combinaison produit-elle un gain mesurable supérieur aux composants isolés?','search_queries':[' '.join(terms[:8]),' '.join(c.systems[:3])+' benchmark baseline',' '.join(c.systems[:3])+' failure modes limitations'],'experiments':['interface minimale et données synthétiques','baseline externe et composants isolés','ablations, bruit, cas limites et contre-exemples','résidus, incertitudes, coût, latence et M⁻'],'oak_gates':['provenance_required','baseline_required','ablation_required','uncertainty_required','no_claim_promotion_without_evidence'],'score':c.score}

def write(out,roots,nodes,result,ps,args):
    out.mkdir(parents=True,exist_ok=True); by={n.name:n for n in nodes}; allc=[c for k in sorted(result) for c in result[k]]
    report={'schema_version':'0.1','engine':'OMEGA-SYNERGY-N-T','authority':'review_only_heuristic','repo_roots':[str(x) for x in roots],'parameters':{'max_order':args.max_order,'beam_width':args.beam_width,'top_k':args.top_k,'max_nodes':args.max_nodes},'counts':{'systems':len(nodes),'retained_pairs':len(ps),'synergy_candidates':len(allc),'research_packets':len(allc)},'synergies_by_order':{str(k):[asdict(c) for c in v] for k,v in result.items()},'m_minus':['Scores are heuristic, not proof.','Co-mention is not causality.','Beam search can miss useful combinations.','Weakly documented systems may be under-ranked.']}
    (out/'system_inventory.json').write_text(json.dumps([asdict(n) for n in nodes],indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (out/'synergy_n.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (out/'research_queue.json').write_text(json.dumps([packet(c,by) for c in allc],indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    md=['# Ω-SYNERGY-N-T Report','','Authority: **review-only heuristic**.','',f'Discovered systems: **{len(nodes)}**',f'Retained pairs: **{len(ps)}**','']
    for k,vals in result.items():
        md += [f'## Order {k}','']+[f'{i}. **{c.score:.3f}** — '+' × '.join(c.systems) for i,c in enumerate(vals,1)]+['']
    md += ['## M⁻','']+[f'- {x}' for x in report['m_minus']]
    (out/'SYNERGY_N_REPORT.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    names={n for c in allc[:40] for n in c.systems}; dot=['graph omega_synergy_n {','  overlap=false;']+[f'  "{n}";' for n in sorted(names)]
    dot += [f'  "{a}" -- "{b}" [label="{s:.2f}"];' for (a,b),s in sorted(ps.items(),key=lambda x:-x[1])[:120] if a in names and b in names]+['}']
    (out/'synergy_graph.dot').write_text('\n'.join(dot)+'\n',encoding='utf-8')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--repo-root',action='append',dest='roots'); p.add_argument('--out',default='reports/github-autonomous-reactor/synergy-n'); p.add_argument('--max-order',type=int,default=4); p.add_argument('--beam-width',type=int,default=96); p.add_argument('--top-k',type=int,default=25); p.add_argument('--max-nodes',type=int,default=800); a=p.parse_args()
    if not 2<=a.max_order<=8 or a.beam_width<a.top_k or a.top_k<1: p.error('require 2<=max-order<=8 and beam-width>=top-k>=1')
    roots=[pathlib.Path(x).resolve() for x in (a.roots or ['.']) if pathlib.Path(x).exists()]
    if not roots: p.error('at least one repo root must exist')
    nodes,file_ids=discover(roots,a.max_nodes); result,ps=search(nodes,file_ids,a.max_order,a.beam_width,a.top_k); write(roots[0]/a.out,roots,nodes,result,ps,a)
    print(json.dumps({'systems':len(nodes),'orders':sorted(result),'pairs':len(ps),'out':a.out},indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
