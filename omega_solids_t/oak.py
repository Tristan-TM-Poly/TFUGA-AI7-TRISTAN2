from __future__ import annotations
from dataclasses import asdict
import hashlib,json
from typing import Callable
from .models import CandidateCell,OAKFinding,OAKReport
from .vocabularies import WORLDS,ARCHITECTURES,DEFECT_PROFILES,PROCESS_PROFILES,ENVIRONMENT_PROFILES
WORLD_IDS={x['id'] for x in WORLDS}; ARCH_IDS={x['id'] for x in ARCHITECTURES}; DEFECTS={x['id']:x for x in DEFECT_PROFILES}; PROCESS_IDS={x['id'] for x in PROCESS_PROFILES}; ENV_IDS={x['id'] for x in ENVIRONMENT_PROFILES}
def _finding(gate_id,passed,score,message,severity='warning',evidence=(),remediation=()): return OAKFinding(gate_id,passed,max(0.0,min(1.0,score)),severity,message,tuple(evidence),tuple(remediation))
def _g1(c):
    ok=all((c.candidate_id,c.world_id,c.architecture_id,c.defect_profile_id,c.process_profile_id,c.environment_profile_id)); return _finding('OAK-01-schema',ok,1.0 if ok else 0.0,'Required structural identifiers are present.','blocker' if not ok else 'info')
def _g2(c):
    ok=c.world_id in WORLD_IDS and c.architecture_id in ARCH_IDS and c.defect_profile_id in DEFECTS and c.process_profile_id in PROCESS_IDS and c.environment_profile_id in ENV_IDS; return _finding('OAK-02-vocabulary',ok,1.0 if ok else 0.0,'All identifiers resolve to versioned vocabularies.','blocker' if not ok else 'info')
def _g3(c):
    d=c.descriptor; ok=float(d.get('temperature_K',0))>0 and float(d.get('pressure_Pa',0))>=0; return _finding('OAK-03-units',ok,1.0 if ok else 0.0,'Temperature and pressure use explicit SI units.','blocker' if not ok else 'info',remediation=('repair unit-bearing descriptors',))
def _g4(c):
    ok='domain_of_validity' in c.required_checks; return _finding('OAK-04-domain',ok,0.8 if ok else 0.2,'Domain-of-validity review is required before promotion.')
def _g5(c):
    criticality=float(c.descriptor.get('defect_criticality',1.0)); score=max(0.0,1.0-criticality*0.75); ok=criticality<0.85; return _finding('OAK-05-stability',ok,score,'Heuristic defect criticality is below the quarantine threshold.' if ok else 'Critical defect profile requires quarantine and explicit stability analysis.','blocker' if not ok else 'warning')
def _g6(c):
    distinct=len(set(c.mechanism_ids)); score=min(1.0,distinct/max(1,len(c.mechanism_ids))); ok=distinct==len(c.mechanism_ids); return _finding('OAK-06-identifiability',ok,score,'Mechanism labels are non-duplicated; quantitative identifiability remains unproven.')
def _g7(c):
    ok='baseline' in c.required_checks; return _finding('OAK-07-baseline',ok,0.75 if ok else 0.0,'A baseline comparison is mandatory but not yet executed.')
def _g8(c):
    ok='uncertainty' in c.required_checks; return _finding('OAK-08-uncertainty',ok,0.65 if ok else 0.0,'Uncertainty accounting is required; generated descriptors are not calibrated measurements.')
def _g9(c): return _finding('OAK-09-countermodel',False,0.25,'No candidate is promoted until a counter-model or negative control is evaluated.',remediation=('attach a discriminating counter-hypothesis',))
def _g10(c):
    process_ok=c.process_profile_id in PROCESS_IDS; depth=int(c.descriptor.get('hierarchy_depth',0)); ok=process_ok and c.world_id!='unknown-solid'; return _finding('OAK-10-fabricability',ok,0.7 if process_ok and depth<=3 else 0.45,'A process family exists, but tolerances, yield and equipment remain unvalidated.')
def _g11(c):
    extreme=any(token in c.world_id for token in ('extreme-containment','extreme-defect-flux','extreme-compression','unknown')); return _finding('OAK-11-safety',not extreme,0.2 if extreme else 0.7,'Consequential or unknown-material classes require specialist safety review.' if extreme else 'No automatic safety certification is implied.','blocker' if extreme else 'warning')
def _g12(c):
    ok=len(c.provenance_ids)>=2; return _finding('OAK-12-provenance',ok,min(1.0,len(c.provenance_ids)/3),'Candidate lineage contains vocabulary and campaign references; experimental provenance is absent.')
GATES:tuple[Callable[[CandidateCell],OAKFinding],...]=(_g1,_g2,_g3,_g4,_g5,_g6,_g7,_g8,_g9,_g10,_g11,_g12)
def evaluate_candidate(candidate:CandidateCell)->OAKReport:
    findings=tuple(g(candidate) for g in GATES); weights={'blocker':3.0,'warning':1.5,'info':1.0}; total=sum(weights[f.severity] for f in findings); aggregate=sum(f.score*weights[f.severity] for f in findings)/total; blockers=tuple(f.gate_id for f in findings if not f.passed and f.severity=='blocker'); status='QUARANTINED' if blockers else ('BENCHMARK_READY' if aggregate>=0.80 else ('EXPLORATORY' if aggregate>=0.60 else 'REJECTED')); payload={'object_id':candidate.candidate_id,'aggregate':aggregate,'findings':[asdict(f) for f in findings],'blockers':blockers}; fp=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest(); return OAKReport(candidate.candidate_id,status,aggregate,findings,blockers,fp)
