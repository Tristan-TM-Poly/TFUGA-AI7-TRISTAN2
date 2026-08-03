"""Evidence lifecycle, claim coverage and non-authoritative promotion proofs."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Mapping, Sequence
from .contracts import AuthorityLevel, EvidenceState, Serializable, digest, stable_id, utc_now

def _parse_time(value):
    if not value:return None
    parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    if parsed.tzinfo is None:parsed=parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

@dataclass(slots=True)
class EvidenceEnvelope(Serializable):
    id:str;subject_id:str;kind:str;payload_digest:str;observed_at:str;expires_at:str|None=None;dependency_digest:str="";environment_digest:str="";test_contract_digest:str="";independent:bool=False;limitations:list[str]=field(default_factory=list);superseded_by:str="";revoked:bool=False;state:EvidenceState=EvidenceState.CURRENT;metadata:dict=field(default_factory=dict)
    @classmethod
    def build(cls,subject_id,kind,payload,*,observed_at=None,expires_at=None,dependency_digest="",environment_digest="",test_contract_digest="",independent=False,limitations=(),metadata=None):
        observed=observed_at or utc_now();payload_hash=digest(payload);identity=stable_id("EVID",subject_id,kind,payload_hash,observed,dependency_digest,environment_digest,test_contract_digest)
        return cls(identity,subject_id,kind,payload_hash,observed,expires_at,dependency_digest,environment_digest,test_contract_digest,independent,sorted(set(limitations)),metadata=dict(metadata or {}))

@dataclass(slots=True)
class EvidenceContext:
    now:str=field(default_factory=utc_now);dependency_digest:str="";environment_digest:str="";test_contract_digest:str="";invalidated_subjects:set[str]=field(default_factory=set);invalidated_evidence_ids:set[str]=field(default_factory=set)

def classify_evidence(envelope,context):
    if envelope.revoked:envelope.state=EvidenceState.REVOKED;return envelope.state
    if envelope.superseded_by:envelope.state=EvidenceState.SUPERSEDED;return envelope.state
    if envelope.subject_id in context.invalidated_subjects or envelope.id in context.invalidated_evidence_ids:envelope.state=EvidenceState.INVALIDATED;return envelope.state
    now,expiry=_parse_time(context.now),_parse_time(envelope.expires_at)
    if now and expiry and now>=expiry:envelope.state=EvidenceState.EXPIRED;return envelope.state
    drift=[]
    if context.dependency_digest and envelope.dependency_digest and context.dependency_digest!=envelope.dependency_digest:drift.append("dependency")
    if context.environment_digest and envelope.environment_digest and context.environment_digest!=envelope.environment_digest:drift.append("environment")
    if context.test_contract_digest and envelope.test_contract_digest and context.test_contract_digest!=envelope.test_contract_digest:drift.append("test_contract")
    if drift:envelope.state=EvidenceState.STALE;envelope.metadata["stale_dimensions"]=sorted(drift);return envelope.state
    envelope.state=EvidenceState.CURRENT;return envelope.state

@dataclass(slots=True)
class ClaimCoverage(Serializable):
    claim_id:str;positive_tests:int;negative_tests:int;required_tests:int;passed_required_tests:int;skipped_required_tests:int;failed_required_tests:int;oracle_quality:float;falsifier_present:bool;provenance_complete:bool;environment_recorded:bool;limitations_declared:bool;required_evidence_kinds:list[str];present_evidence_kinds:list[str];score:float;blocked_reasons:list[str]

def assess_claim_coverage(claim_id,*,positive_tests,negative_tests,required_tests,passed_required_tests,skipped_required_tests=0,failed_required_tests=0,oracle_quality=0.0,falsifier_present=False,provenance_complete=False,environment_recorded=False,limitations_declared=False,required_evidence_kinds=(),present_evidence_kinds=()):
    for name,value in {"positive_tests":positive_tests,"negative_tests":negative_tests,"required_tests":required_tests,"passed_required_tests":passed_required_tests,"skipped_required_tests":skipped_required_tests,"failed_required_tests":failed_required_tests}.items():
        if value<0:raise ValueError(f"{name} cannot be negative")
    if not 0<=oracle_quality<=1:raise ValueError("oracle_quality must be between 0 and 1")
    required=sorted(set(required_evidence_kinds));present=sorted(set(present_evidence_kinds));blocked=[]
    if required_tests and passed_required_tests<required_tests:blocked.append("required_tests_incomplete")
    if skipped_required_tests:blocked.append("required_tests_skipped")
    if failed_required_tests:blocked.append("required_tests_failed")
    if positive_tests<=0:blocked.append("no_positive_test")
    if negative_tests<=0:blocked.append("no_negative_or_adversarial_test")
    if not falsifier_present:blocked.append("missing_falsifier")
    if not provenance_complete:blocked.append("broken_or_missing_provenance")
    if not environment_recorded:blocked.append("missing_environment_record")
    if not limitations_declared:blocked.append("missing_limitations")
    missing=sorted(set(required)-set(present));blocked.extend(f"missing_evidence_kind:{kind}" for kind in missing)
    completion=1.0 if required_tests==0 else min(1.0,passed_required_tests/required_tests)
    dimensions=[completion,min(1.0,positive_tests/max(1,required_tests or positive_tests)),min(1.0,negative_tests/max(1,positive_tests)),oracle_quality,float(falsifier_present),float(provenance_complete),float(environment_recorded),float(limitations_declared),1.0 if not missing else max(0.0,1.0-len(missing)/max(1,len(required)))]
    return ClaimCoverage(claim_id,positive_tests,negative_tests,required_tests,passed_required_tests,skipped_required_tests,failed_required_tests,oracle_quality,falsifier_present,provenance_complete,environment_recorded,limitations_declared,required,present,round(sum(dimensions)/len(dimensions),6),sorted(set(blocked)))

@dataclass(slots=True)
class PromotionAssessment(Serializable):
    id:str;claim_id:str;eligible_for_human_review:bool;evidence_ids:list[str];coverage_score:float;blocked_reasons:list[str];authority:AuthorityLevel=AuthorityLevel.A3_REVIEW_CANDIDATE;human_review_required:bool=True;automatic_merge_allowed:bool=False;automatic_publication_allowed:bool=False
    def __post_init__(self):
        if not self.human_review_required or self.automatic_merge_allowed or self.automatic_publication_allowed:raise ValueError("promotion assessment cannot authorize irreversible actions")

def assess_promotion(claim_id,evidence,coverage,*,min_coverage=.80,critical_residuals=()):
    if not 0<=min_coverage<=1:raise ValueError("min_coverage must be between 0 and 1")
    blocked=list(coverage.blocked_reasons);named=sorted(e.id for e in evidence)
    if not named:blocked.append("no_named_evidence")
    blocked.extend(f"evidence_not_current:{e.id}" for e in evidence if e.state!=EvidenceState.CURRENT)
    if coverage.score<min_coverage:blocked.append("coverage_below_threshold")
    blocked.extend(f"critical_residual:{item}" for item in critical_residuals);eligible=not blocked
    return PromotionAssessment(stable_id("PROMOTION",claim_id,named,coverage.to_dict(),sorted(critical_residuals)),claim_id,eligible,named,coverage.score,sorted(set(blocked)))

def evidence_state_counts(evidence:Iterable[EvidenceEnvelope]):
    counts={state.value:0 for state in EvidenceState}
    for envelope in evidence:counts[envelope.state.value]+=1
    counts["total"]=sum(counts.values());return counts
