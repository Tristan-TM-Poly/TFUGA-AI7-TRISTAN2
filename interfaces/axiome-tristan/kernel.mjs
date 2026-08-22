export const STATUS_LEVEL = Object.freeze({IDEA:0,CONJECTURE:1,FORMALIZED:2,TESTABLE:3,TESTED:4,BOUNDED:4,CORROBORATED:5,REPLICATED:6,FORMALLY_VERIFIED:6,REFUTED:4});

export function localFingerprint(text){let h=2166136261;for(let i=0;i<text.length;i+=1){h^=text.charCodeAt(i);h=Math.imul(h,16777619);}return `local-${(h>>>0).toString(16).padStart(8,"0")}`;}
export function parseCsv(value){return String(value||"").split(",").map(x=>x.trim()).filter(Boolean);}

export function auditClaim(claim){
  const results=[]; const gate=(name,passed,reason)=>results.push({gate:name,passed:Boolean(passed),reason});
  gate("EXPLICIT_DEFINITIONS",claim.definitions.length>0,"At least one operational definition is required.");
  gate("EXPLICIT_SCOPE",claim.scope.length>0,"Claim scope must be explicit.");
  gate("PROVENANCE",claim.provenance.length>0,"At least one provenance pointer is required.");
  gate("FALSIFIER_OR_PROOF_OBLIGATION",claim.falsifiers.length>0||claim.proofObligations.length>0,"Empirical claims need falsifiers; formal claims need proof obligations.");
  gate("GENERATOR_NE_JUDGE",!claim.generatorId||!claim.judgeId||claim.generatorId!==claim.judgeId,"Generator and judge must be separated when both are declared.");
  const types=new Set(claim.evidence.map(e=>e.type)); const onlySimulation=claim.evidence.length>0&&[...types].every(t=>["SIMULATION","DERIVATION"].includes(t));
  gate("SIMULATION_NE_REALITY",!["CORROBORATED","REPLICATED"].includes(claim.status)||!onlySimulation,"Simulation/derivation alone cannot justify empirical promotion.");
  const coverage=new Set(claim.evidence.flatMap(e=>e.scope)); const missing=claim.scope.filter(s=>!coverage.has(s));
  gate("CLAIM_SCOPE_LE_EVIDENCE_SCOPE",(STATUS_LEVEL[claim.status]||0)<STATUS_LEVEL.TESTED||missing.length===0,missing.length?`Uncovered: ${missing.join(", ")}`:"Scope coverage acceptable.");
  gate("REVENUE_NE_TRUTH",true,"Revenue metadata is ignored by epistemic gates.");
  const passed=results.every(r=>r.passed); return {passed,promotionEligible:passed&&!["IDEA","REFUTED"].includes(claim.status),results};
}

export function mutateClaim(claim){
  const out=[{...claim,id:`${claim.id}:NEG`,statement:`NOT (${claim.statement})`,mutation:"NEGATE",generatedCandidate:true},{...claim,id:`${claim.id}:BOUNDARY`,statement:`Boundary candidate: determine where (${claim.statement}) ceases to hold`,mutation:"BOUNDARY_HUNT",generatedCandidate:true}];
  if(claim.scope.length>1){const narrowed=claim.scope.slice(0,-1);out.splice(1,0,{...claim,id:`${claim.id}:NARROW`,scope:narrowed,statement:`[NARROWED to ${narrowed.join(", ")}] ${claim.statement}`,mutation:"NARROW_SCOPE",generatedCandidate:true});}
  return out;
}

export function supportScore(claim){const support=claim.evidence.reduce((s,e)=>s+Number(e.strength||0)*(e.independent?1.25:1),0);const counter=claim.counterevidence.reduce((s,e)=>s+Number(e.strength||0)*(e.independent?1.25:1),0);return Number(((support-counter)/Math.max(1,claim.scope.length)).toFixed(4));}

export function claimPassport(claim){return {claim:claim.statement,kind:claim.kind,domain:claim.domain,definitions:claim.definitions,scope:claim.scope,assumptions:claim.assumptions,evidence:claim.evidence,counterevidence:claim.counterevidence,uncertainty:claim.uncertainty,falsifiers:claim.falsifiers,proofObligations:claim.proofObligations,provenance:claim.provenance,status:claim.status,version:claim.version,invariant:"ClaimScope <= EvidenceScope",fingerprint:localFingerprint(JSON.stringify(claim))};}
