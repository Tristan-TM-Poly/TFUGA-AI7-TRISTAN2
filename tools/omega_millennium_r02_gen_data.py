"""Generate canonical specs and large deterministic R0.2 catalogs."""
from __future__ import annotations
from omega_millennium_r02_gen_common import ROOT,PROBLEMS,STRATEGIES,LEMMAS,FALSIFIERS,TARGETS,write

def generate():
    for pid,(title,status,statement,domains,outcomes,objects) in PROBLEMS.items():
        write(f"specs/omega_millennium_r02/{pid}.json",{
            "schema":"omega-millennium-problem-spec/2","problem_id":pid,"title":title,
            "status":status,"statement":statement,"domains":domains,
            "accepted_outcomes":outcomes,"canonical_objects":objects,
            "barrier_roots":[f"{pid}_barrier_{i:02d}" for i in range(8)],
            "formal_contract":{"quantifiers_explicit":True,"domains_explicit":True,"solution_claimed":False},
            "forbidden_promotions":["finite_to_infinite","restricted_to_general","numeric_to_exact","skeleton_to_proof"],
            "research_axes":[{"axis_id":f"{pid}.axis.{i:02d}","strategy":STRATEGIES[(i*9+len(pid))%64],"human_review_required":True} for i in range(32)],
            "negative_memory":[{"rule_id":f"{pid}.mminus.{i:02d}","falsifier":FALSIFIERS[i%32],"action":"reduce_scope_or_refute"} for i in range(32)],
        })
    strategies=[]
    for pid in PROBLEMS:
        for i,name in enumerate(STRATEGIES):
            strategies.append({
                "strategy_id":f"{pid}.strategy.{i:02d}.{name}","problem_id":pid,"family":name,
                "dimensions":{"fertility":((i*17+3)%101)/100,"testability":((i*29+11)%101)/100,
                "formalizability":((i*37+7)%101)/100,"novelty":((i*43+13)%101)/100,
                "dependency_unlock":((i*53+19)%101)/100,"false_progress_risk":((i*61+23)%101)/100},
                "falsifiers":[FALSIFIERS[i%32],FALSIFIERS[(i*7+5)%32]],
                "targets":[TARGETS[i%16],TARGETS[(i+3)%16]],"solution_claimed":False,
            })
    write("data/omega_millennium_r02/strategies.json",{"schema":"omega-millennium-strategies/2","count":len(strategies),"items":strategies})
    lemmas=[{"lemma_family_id":f"lemma.{i:02d}.{name}","name":name,
        "inputs":[f"assumption_{(2*i)%128:03d}",f"assumption_{(2*i+1)%128:03d}"],
        "falsifiers":[FALSIFIERS[i%32],FALSIFIERS[(i+11)%32],FALSIFIERS[(i+23)%32]],
        "targets":[TARGETS[i%16],TARGETS[(i+5)%16]],
        "promotion_requires":["typed_statement","explicit_assumptions","evidence_receipt","independent_audit"]}
        for i,name in enumerate(LEMMAS)]
    write("data/omega_millennium_r02/lemma_families.json",{"schema":"omega-millennium-lemma-families/2","count":64,"items":lemmas})
    falsifiers=[{"falsifier_id":f"falsifier.{i:02d}.{name}","name":name,
        "class":["logical","analytic","numerical","formal"][i%4],"deterministic":True,
        "finite_harness_is_not_proof":True} for i,name in enumerate(FALSIFIERS)]
    write("data/omega_millennium_r02/falsifiers.json",{"schema":"omega-millennium-falsifiers/2","count":32,"items":falsifiers})
    targets=[{"target_id":f"formal.{i:02d}.{name}","name":name,"proof_complete_default":False,
        "requires_version_pin":True,"placeholders":["sorry","admit","unknown"]} for i,name in enumerate(TARGETS)]
    write("data/omega_millennium_r02/formal_targets.json",{"schema":"omega-millennium-formal-targets/2","count":16,"items":targets})
    assumptions=[{"pattern_id":f"assumption.{i:03d}","name":f"assumption_pattern_{i:03d}",
        "risk_class":["scope","limit","regularity","existence","algebraic","computational"][i%6],
        "countercheck":FALSIFIERS[(i*3)%32],"must_be_explicit_above_oak":1+i%4} for i in range(128)]
    write("data/omega_millennium_r02/assumption_patterns.json",{"schema":"omega-millennium-assumptions/2","count":128,"items":assumptions})
    mutations=[{"mutation_id":f"mutation.{i:03d}","name":f"proof_mutation_{i:03d}",
        "class":["quantifier","scope","dependency","numeric","formal","definition","limit","algebraic"][i%8],
        "expected_detection":FALSIFIERS[(i*7)%32],"severity":["low","medium","high","critical"][i%4],
        "valid_proof_should_reject":True} for i in range(128)]
    write("data/omega_millennium_r02/proof_mutations.json",{"schema":"omega-millennium-proof-mutations/2","count":128,"items":mutations})
    barriers=[{"barrier_id":f"{pid}.barrier.{i:02d}","problem_id":pid,"root":f"{pid}_barrier_{i%8:02d}",
        "failure_mode":FALSIFIERS[(i*5+len(pid))%32],"strategy":STRATEGIES[(i*11+3)%64],
        "mminus_action":"record_refutation_or_reduce_scope"} for pid in PROBLEMS for i in range(32)]
    write("data/omega_millennium_r02/barriers.json",{"schema":"omega-millennium-barriers/2","count":224,"items":barriers})
    bridges=[{"bridge_id":f"bridge.{i:02d}","source_domain":f"domain_{i:02d}",
        "target_domain":f"domain_{(i*7)%64:02d}","requires_round_trip":True,
        "forbidden_inference":"domain_analogy_does_not_imply_theorem_transfer"} for i in range(64)]
    write("data/omega_millennium_r02/transfer_bridges.json",{"schema":"omega-millennium-transfer-bridges/2","count":64,"items":bridges})
    claims=[{"claim_id":f"poincare.r02.claim.{i:03d}","kind":"known_theorem" if i<12 else "lemma_candidate",
        "statement":f"Positive-control dependency statement {i:03d}.","solution_claimed":False} for i in range(48)]
    edges=[]
    for i in range(12,48):
        edges.append({"edge_id":f"poincare.r02.edge.{len(edges):03d}",
            "premises":[f"poincare.r02.claim.{i-1:03d}",f"poincare.r02.claim.{(i*7)%12:03d}"],
            "conclusion":f"poincare.r02.claim.{i:03d}","oak_level":4,"benchmark_only":True})
    while len(edges)<72:
        j=len(edges); c=12+(j*5)%36
        edges.append({"edge_id":f"poincare.r02.edge.{j:03d}",
            "premises":[f"poincare.r02.claim.{(j*3)%12:03d}",f"poincare.r02.claim.{max(0,c-2):03d}"],
            "conclusion":f"poincare.r02.claim.{c:03d}","oak_level":2+j%3,"benchmark_only":True})
    write("data/omega_millennium_r02/poincare_reconstruction_fixture.json",{
        "schema":"omega-millennium-poincare-reconstruction/2","claims":claims,"edges":edges,
        "seed_claims":[f"poincare.r02.claim.{i:03d}" for i in range(12)],
        "target_claim":"poincare.r02.claim.047","accepted_proof_reconstructed":False,
        "benchmark_only":True,"solution_claimed":False})
    cells=[]
    problem_ids=tuple(PROBLEMS)
    for index in range(4096):
        p=index%7; s=(index//7)%64; l=(index//(7*64))%64; f=(index//(7*64*64))%32; t=(index*13)%16
        cells.append({"cell_id":f"MPP/{problem_ids[p]}/{s:02d}/{l:02d}/{f:02d}/{t:02d}",
            "problem_id":problem_ids[p],"strategy_id":f"{problem_ids[p]}.strategy.{s:02d}.{STRATEGIES[s]}",
            "lemma_family_id":f"lemma.{l:02d}.{LEMMAS[l]}","falsifier_id":f"falsifier.{f:02d}.{FALSIFIERS[f]}",
            "formal_target":TARGETS[t],"status":"unmaterialized_research_address","solution_claimed":False})
    write("data/omega_millennium_r02/research_cells_seed.json",{"schema":"omega-millennium-research-cells/2","count":4096,"items":cells})
