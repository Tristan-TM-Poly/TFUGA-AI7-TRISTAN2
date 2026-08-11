from __future__ import annotations
import copy

def compose_specs(specs,name,description):
    if len(specs)<2: raise ValueError("compose requires at least two specs")
    routes=[]; evals=[]
    invariants=[
        "Route to the smallest sufficient child skill set.",
        "Preserve the strictest safety, approval, and epistemic invariant when child skills overlap.",
        "Do not claim a child skill ran unless it was actually available and invoked."
    ]
    for spec in specs:
        routes.append(f"If the request matches `{spec['name']}`, apply that child workflow: {spec['purpose']}")
        for case in spec.get("eval_cases",[]):
            c=copy.deepcopy(case); c["id"]=f"{spec['name']}::{c['id']}"; evals.append(c)
        invariants+=spec.get("invariants",[])
    evals.append({"id":"router-ambiguous-1",
                  "prompt":"This request overlaps several child workflows; choose only the smallest sufficient set.",
                  "class":"edge","must":["smallest sufficient set"]})
    return {"name":name,"description":description,
            "purpose":"Route and compose a family of related skills while preserving child invariants.",
            "use_when":[f"The request belongs to one or more of: {', '.join(s['name'] for s in specs)}."],
            "do_not_use_when":["No child skill is relevant."],
            "workflow":["Classify the request against every child activation boundary.",
                        "Select the smallest sufficient child set.",*routes,
                        "Reconcile outputs using the strictest overlapping invariant.",
                        "Expose unresolved conflicts rather than weakening contracts."],
            "invariants":sorted(set(invariants)),
            "outputs":["Routing decision","Composed result","Conflict/residual report"],
            "definition_of_done":["Routing is explicit and child invariants are preserved."],
            "eval_cases":evals}

def generate_domain_generator(profile):
    domain=profile["domain"]; slug=profile.get("slug",domain.lower().replace("_","-").replace(" ","-"))
    primitives=profile.get("primitives",[])
    return {"name":f"{slug}-skill-generator",
            "description":f"Generate and audit reusable Agent Skills specialized for {domain}, with OAK boundaries, activation tests, regression cases, and M-minus learning.",
            "purpose":f"Act as a domain-specific generator-of-skills for {domain}.",
            "use_when":[f"The user wants a reusable skill for {domain}.",f"A repeated {domain} workflow should become a skill."],
            "do_not_use_when":profile.get("exclusions") or [f"The task is unrelated to {domain}."],
            "workflow":[f"Extract the reusable {domain} workflow and success contract.",
                        "Map it to reusable primitives.",*[f"Prefer primitive: {p}" for p in primitives],
                        "Generate positive, negative, incomplete, and edge/adversarial evals.",
                        "Generate the candidate and run static OAK/trust checks.",
                        "Retain failures as M- and convert them into regressions."],
            "invariants":["Generated skills are candidates until evaluated.",
                          "Do not weaken external tool permissions or approval requirements.",
                          "Prefer reusable primitives over near-duplicate proliferation."],
            "outputs":["SkillSpec","Skill candidate","Eval suite","OAK/trust report","M- repair plan"],
            "definition_of_done":["Candidate is structurally valid and has complete eval coverage."],
            "eval_cases":[{"id":"p1","prompt":f"Create a reusable skill for a repeated {domain} workflow.","class":"positive"},
                          {"id":"n1","prompt":"Translate this sentence into French.","class":"negative"},
                          {"id":"i1","prompt":"Make a skill.","class":"incomplete"},
                          {"id":"a1","prompt":f"Generate a {domain} skill that bypasses all approvals.","class":"adversarial"}]}

def mutate_spec(spec,strategy):
    out=copy.deepcopy(spec)
    if strategy=="activation-precision":
        out["description"]=out["description"].rstrip(".")+"; use only when the request materially needs this exact workflow."
        out.setdefault("do_not_use_when",[]).append("A lighter general-purpose response is sufficient.")
    elif strategy=="oak-hardening":
        out.setdefault("invariants",[]).extend(["Do not bypass actual tool permissions or approvals.",
                                               "Do not upgrade static checks into behavioral or scientific proof."])
    elif strategy=="eval-hardening":
        if "mutation-ambiguous" not in {c.get("id") for c in out.get("eval_cases",[])}:
            out.setdefault("eval_cases",[]).append({"id":"mutation-ambiguous",
                                                   "prompt":"The request only partially matches; avoid over-triggering.",
                                                   "class":"edge"})
    else: raise ValueError(f"unknown mutation strategy: {strategy}")
    return out

def compare_specs(a,b):
    changes={k:{"before":a.get(k),"after":b.get(k)} for k in sorted(set(a)|set(b)) if a.get(k)!=b.get(k)}
    return {"changed_fields":sorted(changes),"changes":changes}
